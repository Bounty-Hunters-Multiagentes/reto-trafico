import agentpy as ap 
import Cubo
import Car
import PlanoCubos 
import math
import pygame
import matplotlib.pyplot as plt
from SemaforoAgent import SemaforoAgent

from enum import Enum
from Message import Message
from constants import DEBUG
import numpy as np

from Lane import lane_map

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
        self.jerk_delta = 10 # How much jerk to increase or decrease when accelerating or stopping
        self.jerk_time_acc = 0.5 # How much time to have jerk positive 
        self.jerk_time_wait = 0.5 # How much time to have jerk at 0
        self.jerk_state = JerkState.NONE # State of accelerating of deaccelerating
        self.state_timer = 0 # Timer to know when to change states
        self.car_movement = CarMovement.NONE # Whether accelerating, stopping, or none
        self.last_seen_lights = False
        
        self.lane = self.model.nprandom.choice(list(lane_map.values()))        
        
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

        if self.id == 1:
            global tar_ref
            self.g_cubo = Cubo.Cubo(self.Position, scale=5)
            tar_ref = self
        else:
            self.g_cubo = Car.Car(self.Position,scale=5, id=self.id)
            
        self.g_cubo.draw(self.Position)

    def step(self):
        perception = self.perceive_environment()
        
        if DEBUG['movement']:
            print(f"\n=== Car {self.id} Movement State ===")
            print(f"Movement Type: {self.car_movement}")
            print(f"Jerk State: {self.jerk_state}")
            print(f"Current Speed: {round(self.vel, 2)}")
            print(f"Current Acceleration: {round(self.acc, 2)}")
        
        if perception['lights'] and not self.last_seen_lights:
            self.send_arrival_message()
            
        self.last_seen_lights = bool(perception['lights'])
        
        if self.car_movement == CarMovement.ACCELERATING:
            self.control_jerk(self.jerk_delta)
        elif self.car_movement == CarMovement.STOPPING:
            self.control_jerk(-self.jerk_delta)
        
        self.update_velocity()

        # No colisión por ahora, solo limites del mapa
        new_pos = np.array(self.Position) + self.delta_pos 
        if abs(new_pos[0]) > self.DimBoard or abs(new_pos[2]) > self.DimBoard:
             self.reset_position()
        else:
            self.Position[0] = new_pos[0]
            self.Position[2] = new_pos[2]

    def update(self):
        self.g_cubo.draw(self.Position)
        
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
        if self.id == 1:
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
    
    def send_arrival_message(self):
        perception = self.perceive_environment()
        
        if perception['lights']:
            nearest_light = min(perception['lights'],
                                key=lambda x: np.linalg.norm(np.array(x['position']) - np.array(self.Position)))
            
            if DEBUG['messages']:
                print(f"\n=== Car {self.id} Sending Message ===")
                print(f"To Traffic Light: {nearest_light['light'].direction}")
                print(f"Time: {self.model.t}")
                print(f"Distance to light: {round(np.linalg.norm(np.array(nearest_light['position']) - np.array(self.Position)), 2)}")
            
            Message(
                sender=self.id,
                receiver=nearest_light['light'].direction,
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
        
        if self.id == 2:
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
        
    def update_velocity_considering_lights(self):
        perception = self.perceive_environment()
        
        if perception['lights']:
            nearest_light = min(perception['lights'], 
                                key=lambda x: np.linalg.norm(np.array(x['position']) - np.array(self.Position)))
            
            if nearest_light['state'] == 'Red':
                self.start_movement(CarMovement.STOPPING)
            elif nearest_light['state'] == "Green":
                self.start_movement(CarMovement.ACCELERATING)
    
    def reset_position(self):
        self.Position = [0,self.scale,0]
        # self.acc = 0
        # self.vel = 0

class CuboModel(ap.Model):

    def setup(self):
        self.cubos = ap.AgentList(self, self.p.cubos, CuboAgentVelocity)
        self.semaforos = ap.AgentList(self, 4, SemaforoAgent)
        directions = ['up', 'down', 'left', 'rigth']
        semaforo_info = [
            {'init_pos': (45, 10, 60), 'rotation': 180},  # For 'up'
            {'init_pos': (-45, 10, -60), 'rotation': 0},  # For 'down'
            {'init_pos': (60, 10, -45), 'rotation': 270}, # For 'right'
            {'init_pos': (-60, 10, 45), 'rotation': 90},  # For 'left'
        ]
        
        for i, semaforo in enumerate(self.semaforos):
            semaforo.setup_direction(directions[i])
            semaforo.setup_semaforo(semaforo_info[i])
            semaforo.setup_color_time(300, 100) # la cantidad de pasos que va a estar prendida la luz verde y la amarilla antes de cambiar de semaforo
        
        self.collisions = 0

    def step(self):
        self.semaforos.step()
        self.cubos.step()

    def update(self):
        self.semaforos.update()
        self.cubos.update()
        self.record('Cantidad de colisiones', self.collisions)
        self.collisions = 0

    def end(self):
        pass


parameters = {
   'cubos' : 2,
   'dim' : 200,
   'vel' : 2.0,
   'Scale' : 5.0,
   #'steps' : 100
}

model = CuboModel(parameters)

STEP = 5

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
plt.show()


