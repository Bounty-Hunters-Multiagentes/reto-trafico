import math
import os
import pickle
from enum import Enum

import agentpy as ap
import matplotlib.pyplot as plt
import numpy as np
import pygame

import Car
import Cubo
import PlanoCubos
from Building import Building
from camera import Camera, load_camera, modify_cam, set_camera_pose
from constants import BENCH_PATH, BUILDING_PATH, CAMERA_POSES_DIR, DEBUG, TREE_PATH
from Decoration import Decoration
from Lane import get_start_position, lane_map, lanes
from Message import Message
from SemaforoAgent import SemaforoAgent


class Direction(Enum):
    UP = 1
    LEFT = 2
    RIGHT = 3
    DOWN = 4

class JerkState(Enum):
    NONE = 0
    START = 1
    WAIT = 2
    REVERSE = 3

class CarMovement(Enum):
    NONE = 0
    ACCELERATING = 1
    STOPPING = 2
    
time_per_step = 0.1
tar_ref = None

class CuboAgentVelocity(ap.Agent):
    
    '''
    Required agent functions
    '''
    def setup(self):
        
        self.is_active = True
        
        self.vel = 0
        self.acc = 0
        self.jerk = 0
        
        # State variables to control car movement
        self.jerk_delta = 100 # How much jerk to increase or decrease when accelerating or stopping
        self.jerk_time_acc = 0.2 # How much time to have jerk positive 
        self.jerk_time_wait = 0.1 # How much time to have jerk at 0
        self.jerk_state = JerkState.NONE # State of accelerating of deaccelerating
        self.state_timer = 0 # Timer to know when to change states
        self.car_movement = CarMovement.ACCELERATING # Whether accelerating, stopping, or none.
        self.last_seen_lights = False
        
        self.brake_distance = 50
        
        self.lane = self.model.nprandom.choice(list(lane_map.values()))
        self.set_lane(self.lane)
        
        self.scale = self.model.p.Scale
        self.radio = math.sqrt(self.scale*self.scale + self.scale*self.scale)
        self.DimBoard = self.model.p.dim
        
        # Se inicializa una posicion aleatoria en el tablero
        self.Position = [0, 0, 0]
        
        # Se normaliza el vector de direccion
        m = math.sqrt(self.Direction[0]*self.Direction[0] + self.Direction[2]*self.Direction[2])
        self.Direction[0] /= m
        self.Direction[2] /= m
        
        # Se cambia la maginitud del vector direccion
        self.delta_pos = np.array(self.Direction)
        self.delta_pos *= self.vel
        
        # Deteccion de colision
        self.collision = False
        
        # Agent knowledge
        self.perception = None
        self.intention = CarMovement.NONE
        self.nearest_light = None
        self.rules = [self.rule_0, self.rule_1, self.rule_2, self.rule_3] # Orden importa
        self.actions = [CarMovement.STOPPING, CarMovement.ACCELERATING, CarMovement.NONE] # Orden importa
        
        # Variables para girar
        self.distance_to_turn = 80
        self.ideal_direction = self.Direction
        self.rotation_per_step = 90
        self.update_rot_per_step()
        self.in_rotation = False
        self.want_to_turn = np.random.choice([True, False])
        self.pending_deg_to_rotate = 0

        if self.id == 1 and DEBUG['cube']:
            global tar_ref
            self.g_cubo = Cubo.Cubo(self.Position, scale=5)
            tar_ref = self
        else:
            self.g_cubo = Car.Car(self.Position,scale=5, id=self.id)
            
        # Metrics
        self.speed_log = []
        self.stopped_time = 0
        self.moving_time = 0
        self.stop_treshold = 0.1 # Cualquier velocidad menor o igual a esto se considera "parado", todo mayor se considera "moviendo"
            
    #    self.g_cubo.draw(self.Position, direction=self.Direction)
    
    def step(self):
        if not self.is_active:
            return
        
        # Handle collisions (this gets executed once per every pair of agents, as other agents are marked as inactive)
        if self.collisionDetection():
            self.is_active = False
            self.model.collisions += 1
        
        self.speed_log.append(self.vel)
        if self.vel <= self.stop_treshold:
            self.stopped_time += time_per_step
        else:
            self.moving_time += time_per_step
        
        if DEBUG['movement']:
            print(f"\n=== Car {self.id} Movement State ===")
            print(f"Movement Type: {self.car_movement}")
            print(f"Jerk State: {self.jerk_state}")
            print(f"Current Speed: {round(self.vel, 2)}")
            print(f"Current Acceleration: {round(self.acc, 2)}")
        
        if self.id == 1 and DEBUG['cube']:
            return
        
        self.see()
        self.next()
        self.action()
        
        # ENSURING AGENT POSITION
        new_pos = np.array(self.Position) + self.delta_pos 
        if abs(new_pos[0]) > self.DimBoard or abs(new_pos[2]) > self.DimBoard:
            self.reset_position()
        else:
            # Only turns if its moving 
            if not self.equal_vectors(self.Position, new_pos):
                self.update_direction()
            self.Position[0] = new_pos[0]
            self.Position[2] = new_pos[2]

    def update(self):
        if self.is_active:
            self.g_cubo.draw(self.Position, direction=self.Direction)
    
    def set_lane(self, lane):
        # print("Setting lane for agent", self.id, "to", lane.name)
        self.lane = lane
        self.Direction = np.array(self.lane.direction, dtype=np.float64)
        self.ideal_direction = self.Direction
        self.Position = get_start_position(self.lane.name)
    
    '''
    Deductive reasoning functions
    '''
    def see(self):
        self.perception = self.perceive_environment()
        if self.perception['lights']:
            self.nearest_light = min(self.perception['lights'], 
                                key=lambda x: np.linalg.norm(np.array(x['position']) - np.array(self.Position)))
        else: 
            self.nearest_light = None
            
        if self.perception['cars']:
            self.nearest_car = min(self.perception['cars'], 
                                key=lambda x: np.linalg.norm(np.array(x.Position) - np.array(self.Position)))
        else: 
            self.nearest_car = None  
    
        if self.want_to_turn:
            dist = math.sqrt(self.Position[0]**2 + self.Position[2]**2)
            # Close to center 
            if dist < self.distance_to_turn:
                if not self.in_rotation:
                    self.ideal_direction = self.rotate_vector(self.Direction, 90)   
                    self.pending_deg_to_rotate = 90
                    # print("old direction = ", self.Direction)
                    # print("new direction = ", self.ideal_direction)
                    # print("----")
                self.in_rotation = True # While in the rotation range, do not trigger it again 
            else:
                self.in_rotation = False
                # print("dist", dist)
    
    def next(self):
        for action in self.actions:
            for rule in self.rules:
                if rule(action):
                    self.intention = action
                    if DEBUG['move_decision'] and self.intention != CarMovement.NONE:
                        print("car", self.id, "decided to", self.intention)
                    return
    
    def action(self):
        # COMUNICATION
        if self.perception['lights'] and not self.last_seen_lights:
            self.send_arrival_message()
            
        self.last_seen_lights = bool(self.perception['lights'])
        
        # CAR MOVEMENT
        if self.intention == CarMovement.ACCELERATING:
            self.start_movement(CarMovement.ACCELERATING)
        elif self.intention == CarMovement.STOPPING:
            self.start_movement(CarMovement.STOPPING)
        
        # Updating current accelerating or stopping process
        if self.car_movement == CarMovement.ACCELERATING:
            self.control_jerk(self.jerk_delta)
        elif self.car_movement == CarMovement.STOPPING:
            self.control_jerk(-self.jerk_delta)
            
        self.update_velocity()
    
    def rule_0(self, action):
        return bool(self.nearest_car and action == CarMovement.STOPPING and self.compute_distance(self.nearest_car) < self.brake_distance)

    def rule_1(self, action):
        return bool(
            self.nearest_light and action == CarMovement.ACCELERATING and self.nearest_light['state'] == 'Green'
            or 
            not self.nearest_light and action == CarMovement.ACCELERATING
            )

    def rule_2(self, action):
        return bool(self.nearest_light and action == CarMovement.STOPPING and self.nearest_light['state'] == 'Red' and not self.want_to_turn)
    
    def rule_3(self, action):
        return bool(action == CarMovement.NONE)
        
    '''
    Interaction, communication and perception
    '''
    def collisionDetection(self):
        collision = False
        
        for ag in self.model.cubos:
            if self.id != ag.id:
                d_x = self.Position[0] - ag.Position[0]
                d_z = self.Position[2] - ag.Position[2]
                d_c = math.sqrt(d_x * d_x + d_z * d_z)
                
                if d_c - (self.radio + ag.radio) < 0.0:
                    ag.is_active = False
                    collision = True
                    
                    if DEBUG["collision"]:
                        print(f"Collision detected between car {self.id} and car {ag.id}")

        return collision                  
        
    # Posible funcion para reemplazar objects_perceived
    def perceive_environment(self):
        # Handle test object
        if self.id == 1 and DEBUG['cube']:
            cars = []
            lights = []
        else:
            cars = self.g_cubo.perceive_objects(self.model.cubos)
            lights = self.g_cubo.perceive_objects(self.model.semaforos)
        
        if DEBUG['perception']:
            print(f"\n=== Car {self.id} Perception State ===")
            print(f"Position: {[round(p, 2) for p in self.Position]}")
            print(f"Velocity: {round(self.vel, 2)}")
            
            if lights:
                print("\nDetected Traffic Lights:")
                for light in lights:
                    distance = np.linalg.norm(np.array(light.semaforo.Position) - np.array(self.Position))
                    print(f"  - Direction: {light.direction}")
                    print(f"  - State: {light.state}")
                    print(f"  - Distance: {round(distance, 2)}")
            
            if cars:
                print("\nDetected Cars:")
                for car in cars:
                    distance = np.linalg.norm(np.array(car.Position) - np.array(self.Position))
                    print(f"  - Car ID: {car.id}")
                    print(f"  - Distance: {round(distance, 2)}")
        
        light_info = []
        for light in lights:
            light_info.append({
                'light': light,
                'state': light.state,
                'position': light.semaforo.Position
            })
            
        return {
            'cars': cars,
            'lights': light_info
        }
    
    def compute_distance(self, car):
        if car is None:
            return 1e9
        return np.linalg.norm(np.array(car.Position) - np.array(self.Position))
    
    def send_arrival_message(self):
        if self.perception['lights'] and self.nearest_light: # Antes pedia que estuviera en rojo pero creo que es mejor que siempre se pueda
            if DEBUG['messages']:
                print(f"\n=== Car {self.id} Sending Message ===")
                print(f"To Traffic Light: {self.nearest_light['light'].direction}")
                print(f"Time: {self.model.t}")
                print(f"Distance to light: {round(np.linalg.norm(np.array(self.nearest_light['position']) - np.array(self.Position)), 2)}")
            
            Message(
                sender=self.id,
                receiver=self.nearest_light['light'].direction,
                performative="car_arrival",
                content={"time": self.model.t}
            ).send()

    """ 
    Functions to simulate movement 
    """
    
    """ Currently, if you start acceleration twice, it start going double the usual max_speed """
    def start_movement(self, new_car_movement):
        # Cannot start movement when other is in progrees
        if self.car_movement != CarMovement.NONE:
            return
        
        if new_car_movement == CarMovement.STOPPING and self.vel <= 0:
            return
        
        if new_car_movement == CarMovement.ACCELERATING and self.vel > 0:
            return

        self.car_movement = new_car_movement
    
    """ jerk_change is either self.jerk_delta or -self.jerk_delta, to accelerate or stop """
    def control_jerk(self, jerk_change):
        self.state_timer -= time_per_step
        
        # Do nothing if timer has not ended AND we have some operation in progress
        if self.state_timer > 0 and self.jerk_state != JerkState.NONE:
            return
        
        if self.jerk_state == JerkState.NONE:
            self.change_jerk_state(JerkState.START, jerk_change, self.jerk_time_acc)
        elif self.jerk_state == JerkState.START:
            self.change_jerk_state(JerkState.WAIT, 0, self.jerk_time_wait)
        elif self.jerk_state == JerkState.WAIT:
            self.change_jerk_state(JerkState.REVERSE, -jerk_change, self.jerk_time_acc)
        elif self.jerk_state == JerkState.REVERSE:
            self.change_jerk_state(JerkState.NONE, 0, 0) # Return time at 0
            self.car_movement = CarMovement.NONE
        # print("myState", self.jerk_state)
        
    def change_jerk_state(self, new_state, new_jerk, jerk_time):
        self.jerk_state = new_state
        self.jerk = new_jerk
        self.state_timer = jerk_time
        
    def set_jerk(self, jerk):
        self.jerk += jerk
    
    def update_velocity(self): 
        self.acc += self.jerk * time_per_step
        self.vel += self.acc * time_per_step
        if abs(self.acc) < 1e-5:
            self.acc = 0
        if abs(self.vel) < 1e-5:
            self.vel = 0
        
        self.delta_pos = np.array(self.Direction)
        self.delta_pos *= self.vel
        # print("jerk", self.jerk)
        # print("vel", self.vel)
        # print("acc", self.acc)
        # print("delta_pos", self.delta_pos)
        # print("---------")
        
    def update_direction(self): 
        if self.pending_deg_to_rotate < self.rotation_per_step:
            self.Direction = self.rotate_vector(self.Direction, self.pending_deg_to_rotate)
            self.pending_deg_to_rotate = 0
        else:
            self.Direction = self.rotate_vector(self.Direction, self.rotation_per_step)
            self.pending_deg_to_rotate -= self.rotation_per_step
    
    # Assumes degrees are clockwise
    def rotate_vector(self, vec, degrees):
        new_vec = np.array(vec)
        rad = np.radians(-degrees)
        x, y, z = vec
        new_vec[0] = z * np.sin(rad) + x * np.cos(rad)
        new_vec[2] = z * np.cos(rad) - x * np.sin(rad)     
        return new_vec
    
    # TODO: delete if unused later
    def equal_vectors(self, v1, v2):
        if len(v1) != len(v2):
            return False

        for i in range(len(v1)):
            if abs(v1[i] - v2[i]) > 1e-5:
                return False
        return True
    
    def update_rot_per_step(self):
        # Que min sea 5, max 90
        rot = min(
            max(0.105 * self.jerk_delta - 3, 5), 
            90
        )
        
        self.rotation_per_step = rot
         
    def reset_position(self):
        self.is_active = False
        # self.set_lane(self.model.nprandom.choice(list(lane_map.values())))
        # self.set_lane(self.lane)
        self.Position = [10000, 10000, 10000] # sends to a position thats far away 

        # TODO: Verify this is also changed on spawn
        self.ideal_direction = self.Direction
        self.want_to_turn = np.random.choice([True, False])
        self.acc = 0
        self.vel = 0
        # self.start_movement(CarMovement.ACCELERATING)

        
class GrandmaDrivingAgent(CuboAgentVelocity):
    def setup(self):
        super().setup()
        self.jerk_delta = 50
        self.update_rot_per_step()
        
class WannabeRacerAgent(CuboAgentVelocity):
    def setup(self):
        super().setup()
        self.jerk_delta = 80
        self.update_rot_per_step()
        
class LawAbidingAgent(CuboAgentVelocity):
    def setup(self):
        super().setup()
        self.jerk_delta = 200
        self.update_rot_per_step()

class CuboModel(ap.Model):

    def setup(self):
        self.cartype1 = ap.AgentList(self, 1, CuboAgentVelocity)
        self.cartype2 = ap.AgentList(self, 1, GrandmaDrivingAgent)
        self.cartype3 = ap.AgentList(self, 1, WannabeRacerAgent)
        self.cartype4 = ap.AgentList(self, 1, LawAbidingAgent)
        self.car_types = [CuboAgentVelocity, GrandmaDrivingAgent, WannabeRacerAgent, LawAbidingAgent]
        
        # Initialize agents
        self.cubos = self.cartype1 + self.cartype2 + self.cartype3 + self.cartype4
        
        
        self.semaforos = ap.AgentList(self, 4, SemaforoAgent)
        directions = ['up', 'down', 'left', 'right']
        offset = 35
        semaforo_info = [
            {'init_pos': (45, 10, 60), 'rotation': 180},  # For 'down'
            {'init_pos': (-45, 10, -70), 'rotation': 0},  # For 'up'
            {'init_pos': (60, 10, -45), 'rotation': 270}, # For 'right'
            {'init_pos': (-60, 10, 45), 'rotation': 90},  # For 'left'
        ]
        
        # self.spawn_points = {
        #     'north': {'pos': (-offset, self.p.Scale, -self.p.dim), 'direction': [0.0, 0.0, 1.0]},
        #     'south': {'pos': (offset, self.p.Scale, self.p.dim), 'direction': [0.0, 0.0, -1.0]},
        #     'east': {'pos': (self.p.dim, self.p.Scale, -offset), 'direction': [-1.0, 0.0, 0.0]},
        #     'west': {'pos': (-self.p.dim, self.p.Scale, offset), 'direction': [1.0, 0.0, 0.0]}
        # }
        
        # Distribute cars evenly among spawn points
        # spawn_locations = list(self.spawn_points.values())
        for i, agent in enumerate(self.cubos):
            agent.set_lane(lanes[i % len(lanes)])    
        
        for i, semaforo in enumerate(self.semaforos):
            semaforo.setup_direction(directions[i])
            semaforo.setup_semaforo(semaforo_info[i])
            semaforo.setup_color_time(30, 10) # la cantidad de pasos que va a estar prendida la luz verde y la amarilla antes de cambiar de semaforo
        
        global decorations
        decorations = [
            Decoration(BENCH_PATH, init_pos=(130,1,70), scale=0.05, rotation=[-90, 0, 0]),
            Decoration(BENCH_PATH, init_pos=(70,1,130), scale=0.05, rotation=[-90, 0, 90]),
            Decoration(BENCH_PATH, init_pos=(-70,1,130), scale=0.05, rotation=[-90, 0, -90]),
            Decoration(BENCH_PATH, init_pos=(-74,1,-70), scale=0.05, rotation=[-90, 0, -125]),
            
            Decoration(TREE_PATH, init_pos=(180,1,-70), scale=0.1, rotation=[-90, 0, 0]),
            Decoration(TREE_PATH, init_pos=(-70,1,180), scale=0.1, rotation=[-90, 0, 0]),
        ]
        global edificios
        edificios = [
            Building(init_pos=(-60, 50, -120), texture_file=BUILDING_PATH),
            Building(init_pos=(150, 50, -120), texture_file=BUILDING_PATH)
        ]
        self.collisions = 0

    def spawn_new_car(self):
        spawn_lane = np.random.choice(lanes)  # Select a random spawn location
        
        # Create a new car of a random type
        new_car_type = np.random.choice(self.car_types)
        new_car = new_car_type(self)
        
        # Set its lane
        new_car.set_lane(spawn_lane)
        
        # Check for collisions with existing cars
        can_spawn = True
        for agent in self.cubos:
            d_x = new_car.Position[0] - agent.Position[0]
            d_z = new_car.Position[2] - agent.Position[2]
            d_c = math.sqrt(d_x * d_x + d_z * d_z)
            if d_c - (new_car.radio + agent.radio + 30) < 0.0:
                can_spawn = False
                break
        
        # Only add the car if there are no collisions
        if can_spawn:
            # print("spawned a car")
            self.cubos.append(new_car)
        else:
            pass
            # print("Collision detected. Car not spawned.", spawn_lane)
        
    def step(self):
        self.semaforos.step()
        self.cubos.step()
        
        if DEBUG['lane']:
            for agent in self.cubos:
                print(f"Car {agent.id} is in lane {agent.lane.name}")
        
        # Contar carros por carril
        vehicles_per_lane = {lane.name: 0 for lane in lanes}
        for agent in self.cubos:
            vehicles_per_lane[agent.lane.name] += 1
            
        for lane_name, count in vehicles_per_lane.items():
            self.record(f"Carros en carril {lane_name}", count)
        
        if np.random.random() < 0.10:
            self.spawn_new_car()

    def update(self):
        # Remove inactive cars (to free memory)
        self.model.remove_inactive()
        
        # print("entered", len(self.cubos), self.t)
        self.semaforos.update()
        self.cubos.update()
        self.record('Cantidad de colisiones', self.collisions)
        
        # Calcular velocidad promedio
        total_speeds = [agent.speed_log for agent in self.cubos]
        flattened_speeds = [speed for sublist in total_speeds for speed in sublist]
        avg_speed = sum(flattened_speeds) / len(flattened_speeds) if flattened_speeds else 0
        self.report("Velocidad promedio (unidades / segundo)", avg_speed)
        
        # Calcular tiempo promedio detenido
        total_stopped_time = sum(agent.stopped_time for agent in self.cubos)
        avg_stopped_time = total_stopped_time / len(self.cubos) if self.cubos else 0
        self.report("Tiempo promedio detenido (segundos)", avg_stopped_time)
        
        # Calcular tiempo promedio avanzando
        total_moving_time = sum(agent.moving_time for agent in self.cubos)
        avg_moving_time = total_moving_time / len(self.cubos) if self.cubos else 0
        self.report("Tiempo promedio avanzando (segundos)", avg_moving_time)
        
        # global decorations
        for decoration in decorations:
            decoration.draw()
            
        # global edificios
        for edificio in edificios:
            edificio.draw()
            
    def remove_inactive(self):
        for agent in self.cubos:
            if not agent.is_active:
                self.cubos.remove(agent)

    def end(self):
        pass


parameters = {
   'cubos' : 0,
   'dim' : 200,
   'vel' : 2.0,
   'Scale' : 8.0,
   #'steps' : 100
}

model = CuboModel(parameters)

STEP = 10

done = False
PlanoCubos.Init()
model.sim_setup()
camera = Camera()

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
            model.stop()
            model.create_output()
            model.output.info['Mensaje'] = 'Puedes añadir información al registro de esta forma.'
        elif event.type == pygame.KEYDOWN:
            
            if event.key == pygame.K_r:
               camera = Camera()
            if event.key == pygame.K_y:
                with open(os.path.join(CAMERA_POSES_DIR, f"pose_{len(os.listdir(CAMERA_POSES_DIR))}" ), 'wb') as f:
                    pickle.dump(camera, f)
            if event.key == pygame.K_t:
                camera = set_camera_pose()
            
            load_camera(camera)
            
            # if event.key == pygame.K_UP:  # UP key
            #     for agent in model.cubos:
            #         agent.start_movement(CarMovement.ACCELERATING)
            # if event.key == pygame.K_DOWN:  # DOWN key
            #     for agent in model.cubos:
            #         agent.start_movement(CarMovement.STOPPING)
            # if event.key == pygame.K_SPACE:  # SPACE key
            #     for agent in model.cubos:
            #         agent.reset_position()
            # debug using cube movement  
            # if event.key == pygame.K_a:
            #     tar_ref.Position[0] -= STEP
            # elif event.key == pygame.K_d:
            #     tar_ref.Position[0] += STEP
            # elif event.key == pygame.K_w:
            #     tar_ref.Position[2] -= STEP
            # elif event.key == pygame.K_s:
            #     tar_ref.Position[2] += STEP

    keys = pygame.key.get_pressed()
    
    next_cam = modify_cam(keys, camera)
    
    if next_cam != camera:
        load_camera(camera)
        camera = next_cam

    PlanoCubos.display(parameters['dim'], camera)
    
    if model.running:
        model.sim_step()

    pygame.display.flip()
    pygame.time.wait(100)

pygame.quit()

print(model.output.info)
reporters = {key: value for key, value in model.reporters.items() if key != "seed"}

model.output.variables.CuboModel.plot()

plt.figure(figsize=(9, 8))
plt.title("Metricas reportadas")

metric_names = list(reporters.keys())
metric_values = list(reporters.values())

plt.bar(metric_names, metric_values, color='skyblue', edgecolor='black')

plt.xlabel("Metricas")
plt.ylabel("Valores")
plt.xticks(rotation=45, ha='right') 
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()
