import agentpy as ap 
import Cubo
import PlanoCubos 
import math
import random
import pygame
import matplotlib.pyplot as plt

class CuboAgent(ap.Agent):

    def setup(self):
        self.vel = self.model.p.vel
        self.scale = self.model.p.Scale
        self.radio = math.sqrt(self.scale*self.scale + self.scale*self.scale)
        self.DimBoard = self.model.p.dim
        #Se inicializa una posicion aleatoria en el tablero
        self.Position = []
        self.Position.append(random.randint(-1 * self.DimBoard, self.DimBoard))
        self.Position.append(self.scale)
        self.Position.append(random.randint(-1 * self.DimBoard, self.DimBoard))
        #Se inicializa un vector de direccion aleatorio
        self.Direction = []
        self.Direction.append(random.random())
        self.Direction.append(self.scale)
        self.Direction.append(random.random())
        #Se normaliza el vector de direccion
        m = math.sqrt(self.Direction[0]*self.Direction[0] + self.Direction[2]*self.Direction[2])
        self.Direction[0] /= m
        self.Direction[2] /= m
        #Se cambia la maginitud del vector direccion
        self.Direction[0] *= self.vel
        self.Direction[2] *= self.vel
        #deteccion de colision
        self.collision = False

        self.g_cubo = Cubo.Cubo(self.Position)
        self.g_cubo.draw(self.Position,self.scale)
        pass

    def step(self):
        self.collision = False
        self.CollitionDetection()
        if self.collision == False:
            new_x = self.Position[0] + self.Direction[0]
            new_z = self.Position[2] + self.Direction[2]
        else:
            self.Direction[2] *= -1.0
            self.Direction[0] *= -1.0
            new_x = self.Position[0] + self.Direction[0]
            new_z = self.Position[2] + self.Direction[2]

        if(abs(new_x) <= self.DimBoard):
            self.Position[0] = new_x
        else:
            self.Direction[0] *= -1.0
            self.Position[0] += self.Direction[0]
        
        if(abs(new_z) <= self.DimBoard):
            self.Position[2] = new_z
        else:
            self.Direction[2] *= -1.0
            self.Position[2] += self.Direction[2]
        pass

    def update(self):
        self.g_cubo.draw(self.Position, self.scale)

    def CollitionDetection(self):
        for ag in self.model.cubos:
            if self.id != ag.id:
                d_x = self.Position[0] - ag.Position[0]
                d_z = self.Position[2] - ag.Position[2]
                d_c = math.sqrt(d_x * d_x + d_z * d_z)
                if d_c - (self.radio + ag.radio) < 0.0:
                    self.collision = True
                    self.model.collisions += 1

class CuboModel(ap.Model):

    def setup(self):
        self.cubos = ap.AgentList(self,self.p.cubos,CuboAgent)
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
   'cubos' : 100,
   'dim' : 200,
   'vel' : 2.0,
   'Scale' : 5.0,
   #'steps' : 100
}

model = CuboModel(parameters)

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

    PlanoCubos.display(parameters['dim'])
    
    if model.running:
        model.sim_step()
    

    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()

print(model.output.info)
model.output.variables.CuboModel.plot()
plt.show()


