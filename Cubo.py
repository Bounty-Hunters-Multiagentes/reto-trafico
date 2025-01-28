#Autor: Ivan Olmos Pineda


import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import numpy as np
import random
import math

class Cubo:
    
    def __init__(self, init_pos=(0,0,0), id=-1):
        self.points = np.array([[-1.0,-1.0, 1.0], [1.0,-1.0, 1.0], [1.0,-1.0,-1.0], [-1.0,-1.0,-1.0],
                                [-1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0,-1.0], [-1.0, 1.0,-1.0]])

        self.Position = list(init_pos)
        self.rotation = 0
        
        self.id = id
        
        self.frustum = Frustum(0.3, 3, 10, 32, car_reference=self, scale=5)

    def drawFaces(self):
        glBegin(GL_QUADS)
        glVertex3fv(self.points[0])
        glVertex3fv(self.points[1])
        glVertex3fv(self.points[2])
        glVertex3fv(self.points[3])
        glEnd()
        glBegin(GL_QUADS)
        glVertex3fv(self.points[4])
        glVertex3fv(self.points[5])
        glVertex3fv(self.points[6])
        glVertex3fv(self.points[7])
        glEnd()
        glBegin(GL_QUADS)
        glVertex3fv(self.points[0])
        glVertex3fv(self.points[1])
        glVertex3fv(self.points[5])
        glVertex3fv(self.points[4])
        glEnd()
        glBegin(GL_QUADS)
        glVertex3fv(self.points[1])
        glVertex3fv(self.points[2])
        glVertex3fv(self.points[6])
        glVertex3fv(self.points[5])
        glEnd()
        glBegin(GL_QUADS)
        glVertex3fv(self.points[2])
        glVertex3fv(self.points[3])
        glVertex3fv(self.points[7])
        glVertex3fv(self.points[6])
        glEnd()
        glBegin(GL_QUADS)
        glVertex3fv(self.points[3])
        glVertex3fv(self.points[0])
        glVertex3fv(self.points[4])
        glVertex3fv(self.points[7])
        glEnd()
    
    def set_position(self, position):
        self.Position = position
        
    def draw(self, Position, scale):
        glPushMatrix()
        glTranslatef(Position[0], Position[1], Position[2])
        glScaled(scale,scale,scale)
        glColor3f(1.0, 1.0, 1.0)
        
        if self.id == 1:
            glColor3f(1.0,0,0)
        
        self.drawFaces()
        
        glPushMatrix()
        self.frustum.draw()
        glPopMatrix()
        
        glPopMatrix()
        
    def perceive_objects(self, objects):
        
        if self.id != 1:
            return []
        
        objects_perceived = []
        for object in objects:
            if self.frustum.is_point_inside_frustum(object.Position):
                # print(object.Position)
                # print(f"Object {object.id} is inside the frustum")
                objects_perceived.append(object)
                
        return objects_perceived
        

class Frustum:
    def __init__(self, R, r, h, n, car_reference, scale):
        self.R = R  # Radius of the larger base
        self.r = r  # Radius of the smaller base
        self.h = h  # Height of the frustum
        self.n = n  # Number of sides to approximate the circles

        # Use car reference to transform the frustum and check for collision
        self.car_reference = car_reference
        self.scale = scale

        # Generate frustum vertices in local coordinates
        self.vertices = self.generate_frustum_vertices(R, r, h, n)

    def generate_frustum_vertices(self, R, r, h, n):
        vertices = []
        angle_step = 2 * math.pi / n

        # Larger base (z = 0)
        vertices.append((0.0, 0.0, 0.0))  # Center
        for i in range(n):
            angle = i * angle_step
            x = R * math.cos(angle)
            y = R * math.sin(angle)
            vertices.append((x, y, 0.0))

        # Smaller base (z = h)
        vertices.append((0.0, 0.0, h))  # Center
        for i in range(n):
            angle = i * angle_step
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            vertices.append((x, y, h))

        return vertices

    def draw(self):
        # Save the current modelview matrix
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glPushMatrix()
        glColor4f(1.0, 1.0, 1.0, 0.5)

        # Apply transformations based on the car's position and rotation
        # glTranslatef(*self.car_reference.Position)  # Translate to the car's position
        # glRotatef(self.car_reference.rotation, 0, 1, 0)  # Rotate around the Y-axis

        # Draw the larger base
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(*self.vertices[0])  # Center
        for i in range(1, self.n + 1):
            glVertex3f(*self.vertices[i])
        glVertex3f(*self.vertices[1])  # Close the loop
        glEnd()

        # Draw the smaller base
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(*self.vertices[self.n + 1])  # Center
        for i in range(self.n + 2, 2 * self.n + 2):
            glVertex3f(*self.vertices[i])
        glVertex3f(*self.vertices[self.n + 2])  # Close the loop
        glEnd()

        # Draw the sides
        glBegin(GL_QUAD_STRIP)
        for i in range(1, self.n + 1):
            glVertex3f(*self.vertices[i])  # Larger base
            glVertex3f(*self.vertices[self.n + 1 + i])  # Smaller base
        glVertex3f(*self.vertices[1])  # Close the loop
        glVertex3f(*self.vertices[self.n + 2])
        glEnd()

        # Restore the modelview matrix
        glPopMatrix()

    def is_point_inside_frustum(self, point):
        """
        Check if a point is inside the frustum.
        The point is assumed to be in world coordinates.
        scale: The scaling factor applied to the frustum.
        """
        px, py, pz = point
        
        # Get the car's position and rotation
        car_position = self.car_reference.Position
        car_rotation = self.car_reference.rotation

        # Transform the point into the frustum's local coordinate system
        rotation_rad = math.radians(car_rotation)
        cos_theta = math.cos(rotation_rad)
        sin_theta = math.sin(rotation_rad)

        # Translate the point relative to the car's position
        px -= car_position[0]
        py -= car_position[1]
        pz -= car_position[2]

        # Rotate the point around the Y-axis (inverse of the car's rotation)
        px_rot = px * cos_theta - pz * sin_theta
        pz_rot = px * sin_theta + pz * cos_theta

        # Apply scaling to the frustum dimensions
        scaled_R = self.R * self.scale  # Scale the larger base radius
        scaled_r = self.r * self.scale  # Scale the smaller base radius
        scaled_h = self.h * self.scale  # Scale the height

        # Check if the point lies between the two bases (scaled)
        if pz_rot < 0 or pz_rot > scaled_h:
            return False

        # Compute the radius of the frustum at height pz_rot (scaled)
        Rd = scaled_R - ((scaled_R - scaled_r) / scaled_h) * pz_rot

        # Compute the distance of the point from the z-axis
        distance_sq = px_rot**2 + py**2

        # Check if the point lies within the frustum's radius (scaled)
        return distance_sq <= Rd**2

    def transform_frustum(self):
        """
        Transform the frustum's vertices based on the car's position and rotation.
        """
        transformed_vertices = []
        car_position = self.car_reference.position
        car_rotation = self.car_reference.rotation

        rotation_rad = math.radians(car_rotation)
        cos_theta = math.cos(rotation_rad)
        sin_theta = math.sin(rotation_rad)

        for vertex in self.vertices:
            x, y, z = vertex

            # Apply rotation around the Y-axis
            x_rot = x * cos_theta - z * sin_theta
            z_rot = x * sin_theta + z * cos_theta

            # Apply translation
            x_trans = x_rot + car_position[0]
            y_trans = y + car_position[1]
            z_trans = z_rot + car_position[2]

            transformed_vertices.append((x_trans, y_trans, z_trans))

        return transformed_vertices