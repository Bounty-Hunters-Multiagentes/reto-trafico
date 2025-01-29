import math
import random
from enum import Enum

import agentpy as ap
import numpy as np
import pygame

import Car
import Cubo
import PlanoCubos
from constants import DEBUG
from Decoration import Decoration
from Lane import lane_map
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


"""
    Fast accelerating agent
self.jerk_delta = 100 # How much jerk to increase or decrease when accelerating or stopping
self.jerk_time_acc = 0.3 # How much time to have jerk positive 
self.jerk_time_wait = 0.4 # How much time to have jerk at 0

    Normal speed agent
self.jerk_delta = 10 # How much jerk to increase or decrease when accelerating or stopping
self.jerk_time_acc = 0.5 # How much time to have jerk positive 
self.jerk_time_wait = 0.5 # How much time to have jerk at 0
"""
class CuboAgentVelocity(ap.Agent):
    
    '''
    Required agent functions
    '''
    def setup(self):
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
        
        self.Direction = np.array(self.lane.direction, dtype=np.float64)   
        
        self.scale = self.model.p.Scale
        self.radio = math.sqrt(self.scale*self.scale + self.scale*self.scale)
        self.DimBoard = self.model.p.dim
        
        # Se inicializa una posicion aleatoria en el tablero
        self.Position = []
        self.Position.append(self.model.random.uniform(self.lane.min_x, self.lane.max_x))
        # self.Position.append(self.lane.max_x)
        # self.Position.append((self.lane.max_x + self.lane.min_x) / 2)


        self.Position.append(self.scale)
        self.Position.append(self.model.random.randint(self.lane.min_z, self.lane.max_z))
        # self.Position.append((self.lane.max_z + self.lane.min_z) / 2)
        # self.Position.append(self.lane.min_z)

        # Se inicializa un vector de direccion aleatorio
        self.Direction = self.lane.direction
        # self.Direction.append(random.random())
        # self.Direction.append(self.scale)
        # self.Direction.append(random.random())
        
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

        if self.id == 1 and DEBUG['cube']:
            global tar_ref
            self.g_cubo = Cubo.Cubo(self.Position, scale=5)
            tar_ref = self
        else:
            self.g_cubo = Car.Car(self.Position,scale=5, id=self.id)
            
        self.g_cubo.draw(self.Position, direction=self.Direction)
    
    def step(self):
        if DEBUG['movement']:
            print(f"\n=== Car {self.id} Movement State ===")
            print(f"Movement Type: {self.car_movement}")
            print(f"Jerk State: {self.jerk_state}")
            print(f"Current Speed: {round(self.vel, 2)}")
            print(f"Current Acceleration: {round(self.acc, 2)}")
        
        self.see()
        self.next()
        self.action()
        
        # ENSURING AGENT POSITION
        # TODO: Colission detection
        new_pos = np.array(self.Position) + self.delta_pos 
        if abs(new_pos[0]) > self.DimBoard or abs(new_pos[2]) > self.DimBoard:
            self.reset_position()
        else:
            self.Position[0] = new_pos[0]
            self.Position[2] = new_pos[2]

    def update(self):
        self.g_cubo.draw(self.Position, direction=self.Direction)
    
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
        return bool(self.nearest_light and action == CarMovement.ACCELERATING and self.nearest_light['state'] == 'Green')

    def rule_2(self, action):
        return bool(self.nearest_light and action == CarMovement.STOPPING and self.nearest_light['state'] == 'Red')
    
    def rule_3(self, action):
        return bool(action == CarMovement.NONE)
        
    '''
    Interaction, communication and perception
    '''
    def CollitionDetection(self):
        for ag in self.model.cubos:
            if self.id != ag.id:
                d_x = self.Position[0] - ag.Position[0]
                d_z = self.Position[2] - ag.Position[2]
                d_c = math.sqrt(d_x * d_x + d_z * d_z)
                if d_c - (self.radio + ag.radio) < 0.0:
                    self.collision = True
                    self.model.collisions += 1                    
        
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
        if self.perception['lights'] and self.nearest_light and self.nearest_light['state'] == 'Red':
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
    
    def reset_position(self):
        spawn = random.choice(list(self.model.spawn_points.values()))
        self.Position = list(spawn['pos'])
        self.Direction = np.array(spawn['direction'], dtype=np.float64)
        self.acc = 0
        self.vel = 0
        self.start_movement(CarMovement.ACCELERATING)

        
class GrandmaDrivingAgent(CuboAgentVelocity):
    def setup(self):
        super().setup()
        self.jerk_delta = 50
        
class WannabeRacerAgent(CuboAgentVelocity):
    def setup(self):
        super().setup()
        self.jerk_delta = 80
        
class LawAbidingAgent(CuboAgentVelocity):
    def setup(self):
        super().setup()
        self.jerk_delta = 200

class CuboModel(ap.Model):

    def setup(self):
        self.cartype1 = ap.AgentList(self, 1, CuboAgentVelocity)
        self.cartype2 = ap.AgentList(self, 1, GrandmaDrivingAgent)
        self.cartype3 = ap.AgentList(self, 1, WannabeRacerAgent)
        self.cartype4 = ap.AgentList(self, 1, LawAbidingAgent)
        
        # Initialize agents
        self.cubos = self.cartype1 + self.cartype2 + self.cartype3 + self.cartype4
        
        
        self.semaforos = ap.AgentList(self, 4, SemaforoAgent)
        directions = ['up', 'down', 'left', 'rigth']
        offset = 35
        semaforo_info = [
            {'init_pos': (45, 10, 60), 'rotation': 180},  # For 'up'
            {'init_pos': (-45, 10, -60), 'rotation': 0},  # For 'down'
            {'init_pos': (60, 10, -45), 'rotation': 270}, # For 'right'
            {'init_pos': (-60, 10, 45), 'rotation': 90},  # For 'left'
        ]
        
        self.spawn_points = {
            'north': {'pos': (-offset, self.p.Scale, -self.p.dim), 'direction': [0.0, 0.0, 1.0]},
            'south': {'pos': (offset, self.p.Scale, self.p.dim), 'direction': [0.0, 0.0, -1.0]},
            'east': {'pos': (self.p.dim, self.p.Scale, -offset), 'direction': [-1.0, 0.0, 0.0]},
            'west': {'pos': (-self.p.dim, self.p.Scale, offset), 'direction': [1.0, 0.0, 0.0]}
        }
        
        
        
        
        
        # Distribute cars evenly among spawn points
        spawn_locations = list(self.spawn_points.values())
        for i, agent in enumerate(self.cubos):
            spawn = spawn_locations[i % len(spawn_locations)]
            agent.Position = list(spawn['pos'])
            agent.Direction = spawn['direction']
        
        
        for i, semaforo in enumerate(self.semaforos):
            semaforo.setup_direction(directions[i])
            semaforo.setup_semaforo(semaforo_info[i])
            semaforo.setup_color_time(30, 10) # la cantidad de pasos que va a estar prendida la luz verde y la amarilla antes de cambiar de semaforo
        
        global decorations
        decorations = [
            Decoration("Assets/bench/Obj/Bench_LowRes.obj", init_pos=(200,50,140), scale=0.2, rotation=[-90, 0, 0]),
            Decoration("Assets/bench/Obj/Bench_LowRes.obj", init_pos=(140,50,200), scale=0.2, rotation=[-90, 0, 90]),
            Decoration("Assets/bench/Obj/Bench_LowRes.obj", init_pos=(20,50, 200), scale=0.2, rotation=[-90, 0, -90]),

            Decoration("Assets/tree_2.obj", init_pos=(200,50,200), scale=0.1, rotation=[-90, 0, 0]),
            Decoration("Assets/tree_2.obj", init_pos=(200,50,0), scale=0.1, rotation=[-90, 0, 0]),
            Decoration("Assets/tree_2.obj", init_pos=(0,50,200), scale=0.1, rotation=[-90, 0, 0]),
        ]
        self.collisions = 0

    def step(self):
        self.semaforos.step()
        self.cubos.step()
        
        global decorations
        for decoration in decorations:
            decoration.draw()

    def update(self):
        self.semaforos.update()
        self.cubos.update()
        self.record('Cantidad de colisiones', self.collisions)
        self.collisions = 0

    def end(self):
        pass


parameters = {
   'cubos' : 0,
   'dim' : 200,
   'vel' : 2.0,
   'Scale' : 5.0,
   #'steps' : 100
}

model = CuboModel(parameters)

STEP = 10

done = False
PlanoCubos.Init()
model.sim_setup()
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
            model.stop()
            model.create_output()
            model.output.info['Mensaje'] = 'Puedes añadir información al registro de esta forma.'
        elif event.type == pygame.KEYDOWN:
            # Check for a specific key (e.g., SPACE key) to change velocity
            if event.key == pygame.K_UP:  # UP key
                for agent in model.cubos:
                    agent.start_movement(CarMovement.ACCELERATING)
                    
            if event.key == pygame.K_DOWN:  # DOWN key
                for agent in model.cubos:
                    agent.start_movement(CarMovement.STOPPING)
                    
            if event.key == pygame.K_SPACE:  # SPACE key
                for agent in model.cubos:
                    agent.reset_position()
                    
            if event.key == pygame.K_a:
                tar_ref.Position[0] -= STEP
                
            elif event.key == pygame.K_d:
                tar_ref.Position[0] += STEP
                
            elif event.key == pygame.K_w:
                tar_ref.Position[2] -= STEP
                
                
            elif event.key == pygame.K_s:
                tar_ref.Position[2] += STEP
            

    PlanoCubos.display(parameters['dim'])
    
    if model.running:
        model.sim_step()
    

    pygame.display.flip()
    pygame.time.wait(100)

pygame.quit()

print(model.output.info)
model.output.variables.CuboModel.plot()
# plt.show()


