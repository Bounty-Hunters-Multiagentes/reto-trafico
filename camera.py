import math
from dataclasses import dataclass, field

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from constants import SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass
class Camera:
    FOVY: float = field(default=60.0)
    ZNEAR: float = field(default=0.01)
    ZFAR: float = field(default=900.0)

    EYE_X: float = field(default=300.0)
    EYE_Y: float = field(default=200.0)
    EYE_Z: float = field(default=300.0)
    CENTER_X: float = field(default=0)
    CENTER_Y: float = field(default=0)
    CENTER_Z: float = field(default=0)
    UP_X: float = field(default=0)
    UP_Y: float = field(default=1)
    UP_Z: float = field(default=0)
    
    yaw: float = field(default=0.0)
    pitch: float = field(default=0.0)
    
    def rotate(self, angle_x=0, angle_y=0):
        self.yaw += angle_y
        self.pitch += angle_x
        
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        
        self.CENTER_X = self.EYE_X + math.cos(rad_pitch) * math.sin(rad_yaw)
        self.CENTER_Y = self.EYE_Y + math.sin(rad_pitch)
        self.CENTER_Z = self.EYE_Z + math.cos(rad_pitch) * math.cos(rad_yaw)
        
    def move(self, dx=0, dy=0, dz=0):
        self.EYE_X += dx
        self.EYE_Y += dy
        self.EYE_Z += dz
        self.CENTER_X += dx
        self.CENTER_Y += dy
        self.CENTER_Z += dz

def load_camera(camera: Camera):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(camera.FOVY, SCREEN_WIDTH / SCREEN_HEIGHT, camera.ZNEAR, camera.ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(
        camera.EYE_X,
        camera.EYE_Y,
        camera.EYE_Z,
        camera.CENTER_X,
        camera.CENTER_Y,
        camera.CENTER_Z,
        camera.UP_X,
        camera.UP_Y,
        camera.UP_Z,
    )