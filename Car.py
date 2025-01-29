import math

import numpy as np

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *

from constants import ALL_CAR_PATHS
from objloader import OBJ


def get_rotation_from_direction(direction):
    x, y, z = direction
    yaw = math.degrees(math.atan2(x, z))
    return yaw


class Car:
    def __init__(self, init_pos=(0, 0, 0), scale=1, id=-1):
        car_path = np.random.choice(ALL_CAR_PATHS)
        self.mustang = OBJ(car_path, swapyz=True)
        self.mustang.generate()
        self.Position = list(init_pos)
        self.scale = scale
        self.light_scale = 1
        self.light_offset = [0, 0, 4]
        self.car_light = Frustum(
            0.3,
            5,
            10,
            32,
            car_reference=self,
            scale=scale * self.light_scale,
            car_offset=self.light_offset,
        )
        self.id = id
        self.rotation = 0

    def draw(self, Position, direction):
        self.Position = Position
        self.rotation = get_rotation_from_direction(direction)
        glPushMatrix()
        glTranslatef(Position[0], Position[1], Position[2])
        glRotatef(self.rotation, 0, 1, 0)  # Rota en el eje Y

        glColor3f(1.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(*self.light_offset)
        glScaled(self.scale, self.scale, self.scale) # apply scale after translation
        glScaled(self.light_scale, self.light_scale, self.light_scale)
        self.car_light.draw()

        glPopMatrix()
        # apply scale for the car
        glScaled(self.scale, self.scale, self.scale)

        glRotatef(-90, 1, 0, 0)
        self.mustang.render()

        glPopMatrix()

    def perceive_objects(self, objects):
        objects_perceived = []
        for object in objects:
            if self.id != object.id and self.car_light.is_point_inside_frustum(
                object.Position
            ):
                # print(object.Position)
                # print(f"Object {object.id} is inside the frustum")
                objects_perceived.append(object)

        return objects_perceived


""" Used for the car light"""


class Frustum:
    def __init__(self, R, r, h, n, car_reference, scale, car_offset):
        self.R = R  # Radius of the larger base
        self.r = r  # Radius of the smaller base
        self.h = h  # Height of the frustum
        self.n = n  # Number of sides to approximate the circles

        self.car_reference = car_reference
        self.scale = scale
        self.car_offset = car_offset
        self.vertices = self.generate_frustum_vertices(R, r, h, n)

    def generate_frustum_vertices(self, R, r, h, n):
        vertices = []
        angle_step = 2 * math.pi / n

        vertices.append((0.0, 0.0, 0.0))
        for i in range(n):
            angle = i * angle_step
            x = R * math.cos(angle)
            y = R * math.sin(angle)
            vertices.append((x, y, 0.0))

        vertices.append((0.0, 0.0, h))
        for i in range(n):
            angle = i * angle_step
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            vertices.append((x, y, h))

        return vertices

    def draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glPushMatrix()
        glColor4f(1.0, 1.0, 1.0, 0.5)

        # base larga
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(*self.vertices[0])
        for i in range(1, self.n + 1):
            glVertex3f(*self.vertices[i])
        glVertex3f(*self.vertices[1])
        glEnd()

        # base pequeña
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(*self.vertices[self.n + 1])
        for i in range(self.n + 2, 2 * self.n + 2):
            glVertex3f(*self.vertices[i])
        glVertex3f(*self.vertices[self.n + 2])
        glEnd()

        glBegin(GL_QUAD_STRIP)
        for i in range(1, self.n + 1):
            glVertex3f(*self.vertices[i])
            glVertex3f(*self.vertices[self.n + 1 + i])
        glVertex3f(*self.vertices[1])
        glVertex3f(*self.vertices[self.n + 2])
        glEnd()

        glPopMatrix()

    def is_point_inside_frustum(self, point):
        px, py, pz = point

        car_position = self.car_reference.Position
        car_rotation = self.car_reference.rotation

        rotation_rad = math.radians(car_rotation)
        cos_theta = math.cos(rotation_rad)
        sin_theta = math.sin(rotation_rad)

        # trasnformar considerando la posicion del carro
        px -= car_position[0] - self.car_offset[0]
        py -= car_position[1] - self.car_offset[1]
        pz -= car_position[2] - self.car_offset[2]

        # Rotar Y-axis
        px_rot = px * cos_theta - pz * sin_theta
        pz_rot = px * sin_theta + pz * cos_theta

        # considerar scaling
        scaled_R = self.R * self.scale
        scaled_r = self.r * self.scale
        scaled_h = self.h * self.scale

        if pz_rot < 0 or pz_rot > scaled_h:
            return False

        Rd = scaled_R - ((scaled_R - scaled_r) / scaled_h) * pz_rot

        distance_sq = px_rot**2 + py**2

        return distance_sq <= Rd**2
