import agentpy as ap 
import Cubo
import Car
import PlanoCubos 
import math
import random
import pygame
import matplotlib.pyplot as plt

from enum import Enum
import numpy as np

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
        
        
        self.scale = self.model.p.Scale
        self.radio = math.sqrt(self.scale*self.scale + self.scale*self.scale)
        self.DimBoard = self.model.p.dim
        
        # Se inicializa una posicion aleatoria en el tablero
        self.Position = []
        self.Position.append(random.randint(-1 * self.DimBoard, self.DimBoard))
        self.Position.append(self.scale)
        self.Position.append(random.randint(-1 * self.DimBoard, self.DimBoard))
        
        # Se inicializa un vector de direccion aleatorio
        self.Direction = []
        self.Direction.append(random.random())
        self.Direction.append(self.scale)
        self.Direction.append(random.random())
        
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
            self.g_cubo = Car.Car(self.Position,scale=5)
        else:
            self.g_cubo = Cubo.Cubo(self.Position, scale=5)
            
            if self.id == 2:
                global tar_ref
                tar_ref = self

        self.g_cubo.draw(self.Position)

    def step(self):
        if self.car_movement == CarMovement.ACCELERATING:
            self.control_jerk(self.jerk_delta)
        elif self.car_movement == CarMovement.STOPPING:
            self.control_jerk(-self.jerk_delta)
        
        self.update_velocity()
        
        if self.id == 1:
            self.objects_perceived()

        # No colisión por ahora, solo limites del mapa
        new_pos = np.array(self.Position) + self.delta_pos 
        if abs(new_pos[0]) > self.DimBoard or abs(new_pos[2]) > self.DimBoard:
             self.reset_position()
        else:
            self.Position[0] = new_pos[0]
            self.Position[2] = new_pos[2]

    def update(self):
        self.g_cubo.draw(self.Position)

    def CollitionDetection(self):
        for ag in self.model.cubos:
            if self.id != ag.id:
                d_x = self.Position[0] - ag.Position[0]
                d_z = self.Position[2] - ag.Position[2]
                d_c = math.sqrt(d_x * d_x + d_z * d_z)
                if d_c - (self.radio + ag.radio) < 0.0:
                    self.collision = True
                    self.model.collisions += 1
                    
    def objects_perceived(self):
        perceived = self.g_cubo.perceive_objects(self.model.cubos)
       
        print(f"Perceived  {len(perceived)} objects")

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
    
    def reset_position(self):
        self.Position = [0,self.scale,0]
        # self.acc = 0
        # self.vel = 0

class CuboModel(ap.Model):

    def setup(self):
        self.cubos = ap.AgentList(self,self.p.cubos,CuboAgentVelocity)
        self.collisions = 0
        pass

    def step(self):
        self.cubos.step()
        pass

    def update(self):
        self.cubos.update()
        self.record('Cantidad de colisiones', self.collisions)
        self.collisions = 0
        pass

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

# print(model.output.info)
# model.output.variables.CuboModel.plot()
# plt.show()


