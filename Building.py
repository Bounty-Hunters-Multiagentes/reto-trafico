import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import time
from constants import BUILDING_PATH


class Building:
    def __init__(self, init_pos=(0,0,0), rotation=0, texture_file=None, scale=1.0):
        self.rotation = rotation
        self.scale = scale
        # Points for building
        self.pole_points = np.array([
            # Front face
            [-3.0, -2.0, 1.2], 
            [-1.0, -2.0, 1.2],  
            [-1.0, -2.0, -1.2], 
            [-3.0, -2.0, -1.2], 
            
            # Back face
            [-3.0, 2.0, 1.2],   
            [-1.0, 2.0, 1.2],   
            [-1.0, 2.0, -1.2],  
            [-3.0, 2.0, -1.2]   
        ])
        
        self.Position = list(init_pos)
        self.current_color = "Red"
        self.last_change = time.time()
        self.color_duration = 2.0

        # Load texture if a texture file is provided
        if texture_file:
            self.texture = self.load_texture(texture_file)
        else:
            self.texture = None

    def load_texture(self, texture_file):
        # load the texture file
        texture_surface = pygame.image.load(texture_file)
        # Convert the surface to RGB mode
        texture_surface = pygame.Surface.convert(texture_surface)
        # Flip the image vertically (OpenGL expects different coordinate system)
        texture_surface = pygame.transform.flip(texture_surface, False, True)
        texture_data = pygame.image.tostring(texture_surface, "RGBA", False)
        width, height = texture_surface.get_size()

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Specify 2D texture
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data
        )

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # Generate mipmaps
        glGenerateMipmap(GL_TEXTURE_2D)
        
        return texture_id

    def draw_rectangular_prism(self, points):
        # Front face
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3fv(points[0])
        glTexCoord2f(1.0, 0.0); glVertex3fv(points[1])
        glTexCoord2f(1.0, 1.0); glVertex3fv(points[2])
        glTexCoord2f(0.0, 1.0); glVertex3fv(points[3])
        glEnd()
        
        # Back face
        glBegin(GL_QUADS)
        glTexCoord2f(1.0, 0.0); glVertex3fv(points[4])
        glTexCoord2f(0.0, 0.0); glVertex3fv(points[5])
        glTexCoord2f(0.0, 1.0); glVertex3fv(points[6])
        glTexCoord2f(1.0, 1.0); glVertex3fv(points[7])
        glEnd()
        
        # Right face
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3fv(points[1])
        glTexCoord2f(1.0, 0.0); glVertex3fv(points[2])
        glTexCoord2f(1.0, 1.0); glVertex3fv(points[6])
        glTexCoord2f(0.0, 1.0); glVertex3fv(points[5])
        glEnd()
        
        # Left face
        glBegin(GL_QUADS)
        glTexCoord2f(1.0, 0.0); glVertex3fv(points[0])
        glTexCoord2f(0.0, 0.0); glVertex3fv(points[3])
        glTexCoord2f(0.0, 1.0); glVertex3fv(points[7])
        glTexCoord2f(1.0, 1.0); glVertex3fv(points[4])
        glEnd()
        
        # Top face
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex3fv(points[4])
        glTexCoord2f(1.0, 1.0); glVertex3fv(points[5])
        glTexCoord2f(1.0, 0.0); glVertex3fv(points[1])
        glTexCoord2f(0.0, 0.0); glVertex3fv(points[0])
        glEnd()
        
        # Bottom face
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3fv(points[7])
        glTexCoord2f(1.0, 0.0); glVertex3fv(points[6])
        glTexCoord2f(1.0, 1.0); glVertex3fv(points[2])
        glTexCoord2f(0.0, 1.0); glVertex3fv(points[3])
        glEnd()
    
    def draw(self, scale=25.0):
        glPushMatrix()
        # Add translation to position
        glTranslatef(self.Position[0], self.Position[1], self.Position[2])
        glRotatef(self.rotation, 0, 1, 0)
        glScaled(scale, scale, scale)
        
        if self.texture:
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glColor4f(1.0, 1.0, 1.0, 1.0)
        else:
            glColor3f(0.5, 0.5, 0.5)
        
        self.draw_rectangular_prism(self.pole_points)
        
        if self.texture:
            glDisable(GL_BLEND)
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)
            
        glScaled(self.scale, self.scale, self.scale)
        glPopMatrix()

# def main():
#     pygame.init()
#     display = (800, 600)
#     pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    
#     gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
#     glTranslatef(0.0, 0.0, -10)
    
#     # Enable depth testing and alpha blending
#     glEnable(GL_DEPTH_TEST)
#     glEnable(GL_BLEND)
#     glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
#     # Create traffic light with a texture
#     texture_file = BUILDING_PATH
#     building = Building(texture_file=texture_file)
    
#     while True:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 return
        
#         glRotatef(1, 0, 1, 0)
#         glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
#         building.draw((0, 0, 0))
        
#         pygame.display.flip()
#         pygame.time.wait(10)

# if __name__ == "__main__":
#     main()