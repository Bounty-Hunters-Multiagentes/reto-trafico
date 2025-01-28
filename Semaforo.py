import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import time

class Semaforo:
    def __init__(self, init_pos=(0,0,0), rotation=0):
        
        self.rotation = rotation
        # Points for the pole (a thin rectangular prism)
        self.pole_points = np.array([
            [-1.8, -2.0, 0.2], [-1.4, -2.0, 0.2], [-1.4, -2.0, -0.2], [-1.8, -2.0, -0.2],
            [-1.8, 2.0, 0.2], [-1.4, 2.0, 0.2], [-1.4, 2.0, -0.2], [-1.8, 2.0, -0.2]
        ])
        
        # Points for the light housing (a wider rectangular prism)
        self.housing_points = np.array([
            [-2, 1.0, 0.4],  # Wider along x-axis, taller along y-axis
            [2, 1.0, 0.4],
            [2, 1.0, -0.4],
            [-2, 1.0, -0.4],
            [-2, 2.0, 0.4],  # Increased height along y-axis
            [2, 2.0, 0.4],
            [2, 2.0, -0.4],
            [-2, 2.0, -0.4]
        ])
        
        self.Position = list(init_pos)
        self.current_color = "Red"
        self.last_change = time.time()
        self.color_duration = 2.0  # Duration for each color in seconds
        
    def draw_rectangular_prism(self, points):
        # Front face
        glBegin(GL_QUADS)
        glVertex3fv(points[0])
        glVertex3fv(points[1])
        glVertex3fv(points[2])
        glVertex3fv(points[3])
        glEnd()
        
        # Back face
        glBegin(GL_QUADS)
        glVertex3fv(points[4])
        glVertex3fv(points[5])
        glVertex3fv(points[6])
        glVertex3fv(points[7])
        glEnd()
        
        # Right face
        glBegin(GL_QUADS)
        glVertex3fv(points[1])
        glVertex3fv(points[2])
        glVertex3fv(points[6])
        glVertex3fv(points[5])
        glEnd()
        
        # Left face
        glBegin(GL_QUADS)
        glVertex3fv(points[0])
        glVertex3fv(points[3])
        glVertex3fv(points[7])
        glVertex3fv(points[4])
        glEnd()
        
        # Top face
        glBegin(GL_QUADS)
        glVertex3fv(points[4])
        glVertex3fv(points[5])
        glVertex3fv(points[1])
        glVertex3fv(points[0])
        glEnd()
        
        # Bottom face
        glBegin(GL_QUADS)
        glVertex3fv(points[7])
        glVertex3fv(points[6])
        glVertex3fv(points[2])
        glVertex3fv(points[3])
        glEnd()
    
    def update_color(self):
        current_time = time.time()
        if current_time - self.last_change >= self.color_duration:
            if self.current_color == "Red":
                self.current_color = "Yellow"
            elif self.current_color == "Yellow":
                self.current_color = "Green"
            else:
                self.current_color = "Red"
            self.last_change = current_time
    
    def get_color_values(self):
        if self.current_color == "Red":
            return (1.0, 0.0, 0.0) 
        elif self.current_color == "Yellow":
            return (1.0, 1.0, 0.0)
        else:
            return (0.0, 1.0, 0.0) 
    
    def draw(self, Position, scale=1.0):
        self.update_color()
        
        glPushMatrix()
        glTranslatef(Position[0], Position[1], Position[2])
        glRotatef(self.rotation, 0, 1, 0)  # Add rotation around Y axis
        glScaled(scale, scale, scale)
        
        # Draw pole (gray color)
        glColor3f(0.5, 0.5, 0.5)
        self.draw_rectangular_prism(self.pole_points)
        
        # Draw housing with current traffic light color
        color = self.get_color_values()
        glColor3f(color[0], color[1], color[2])
        self.draw_rectangular_prism(self.housing_points)
        
        glPopMatrix()
        
def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)
    
    # Create traffic light
    semaforo = Semaforo()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        glRotatef(1, 0, 1, 0)  # Rotate scene
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # Draw traffic light
        semaforo.draw((0,0,0))
        
        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == "__main__":
    main()