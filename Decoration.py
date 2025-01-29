from math import radians
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from objloader import OBJ

class Decoration:
    def __init__(self, path, init_pos=(0,0,0), scale = 1, rotation=[0, 0, 0]):
        self.obj = OBJ(path, swapyz=True)
        self.obj.generate()

        self.rotation = rotation
        self.scale = scale
        self.Position = list(init_pos)
    
    def draw(self):        
        glPushMatrix()
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])
        glRotatef(self.rotation[0], 1, 0, 0)  # Rota en el eje X
        glRotatef(self.rotation[1], 0, 1, 0)  # Rota en el eje Y
        glRotatef(self.rotation[2], 0, 0, 1)  # Rota en el eje Z


        glScaled(self.scale, self.scale, self.scale)
        self.obj.render()
        glPopMatrix()