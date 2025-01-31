import math
import os
import pickle
from dataclasses import dataclass, field

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from constants import (
    CAMERA_POSES_DIR,
    INVERT_CAMERA_ROTATION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


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
    
    yaw: float = field(default=45.0)
    pitch: float = field(default=200.0)
    
    
    def rotate(self, angle_x=0, angle_y=0):
        
        angle_x *= INVERT_CAMERA_ROTATION
        angle_y *= INVERT_CAMERA_ROTATION
        self.yaw += angle_y
        self.pitch += angle_x
        
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        
        self.CENTER_X = self.EYE_X + math.cos(rad_pitch) * math.sin(rad_yaw)
        self.CENTER_Y = self.EYE_Y + math.sin(rad_pitch)
        self.CENTER_Z = self.EYE_Z + math.cos(rad_pitch) * math.cos(rad_yaw)
        
    def move(self, forward=0, right=0, up=0):
        rad_yaw = math.radians(self.yaw)
        forward_x = math.sin(rad_yaw) * forward
        forward_z = math.cos(rad_yaw) * forward
        right_x = math.cos(rad_yaw) * right
        right_z = -math.sin(rad_yaw) * right
        
        self.EYE_X += forward_x + right_x
        self.EYE_Y += up
        self.EYE_Z += forward_z + right_z
        self.CENTER_X += forward_x + right_x
        self.CENTER_Y += up
        self.CENTER_Z += forward_z + right_z

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
    
def modify_cam(keys, camera):
    camera = Camera(**vars(camera)) # Make a copy to avoid modifying the original camera
    
    if keys[pygame.K_w]:
        camera.move(forward=-10)  # Move forward relative to camera
    if keys[pygame.K_s]:
        camera.move(forward=10)
        # camera.move(forward=-10)  # Move backward relative to camera
    if keys[pygame.K_a]:
        camera.move(right=-10)  # Move left relative to camera
    if keys[pygame.K_d]:
        camera.move(right=10)  # Move right relative to camera
        
    if keys[pygame.K_q]:
        camera.move(up=-10)  # Move down
    if keys[pygame.K_e]:
        camera.move(up=10)  # Move up
        
    if keys[pygame.K_LEFT]:
        camera.rotate(angle_y=-5)  # Rotate left
    if keys[pygame.K_RIGHT]:
        camera.rotate(angle_y=5)  # Rotate right
    if keys[pygame.K_UP]:
        camera.rotate(angle_x=5)  # Look up
    if keys[pygame.K_DOWN]:
        camera.rotate(angle_x=-5)  # Look down

    if keys[pygame.K_r]:
        camera = Camera() # reset
    if keys[pygame.K_r]:
        camera = Camera() # reset
    # Save new camera poses
    # if keys[pygame.K_y]:
    #     with open(os.path.join(CAMERA_POSES_DIR, f"pose_{len(os.listdir(CAMERA_POSES_DIR))}" ), 'wb') as f:
    #         pickle.dump(camera, f)
        
    return camera

pose_index = 0
camera_paths = os.listdir(CAMERA_POSES_DIR)

def set_camera_pose() -> Camera:
    global pose_index, camera_paths
    pose_index += 1
    if pose_index >= len(camera_paths):
        pose_index = 0
    
    with open(os.path.join(CAMERA_POSES_DIR, camera_paths[pose_index]), 'rb') as f:
        return pickle.load(f)