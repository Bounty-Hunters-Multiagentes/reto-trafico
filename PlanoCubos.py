import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame import image
from pygame.image import load
from PIL import Image

from constants import FLOOR_PATH, SKY_PATH
# Se carga el archivo de la clase Cubo
import sys
sys.path.append('..')
#from Cubo import Cubo

screen_width = 500
screen_height = 500
#vc para el obser.
FOVY=60.0
ZNEAR=0.01
ZFAR=900.0
#Variables para definir la posicion del observador
#gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
EYE_X=300.0
EYE_Y=200.0
EYE_Z=300.0
CENTER_X=0
CENTER_Y=0
CENTER_Z=0
UP_X=0
UP_Y=1
UP_Z=0
#Variables para dibujar los ejes del sistema
X_MIN=-500
X_MAX=500
Y_MIN=-500
Y_MAX=500
Z_MIN=-500
Z_MAX=500

pygame.init()


def Axis():
    glShadeModel(GL_FLAT)
    glLineWidth(3.0)
    #X axis en rojo
    glColor3f(1.0,0.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN,0.0,0.0)
    glVertex3f(X_MAX,0.0,0.0)
    glEnd()
    #Y axis en verde
    glColor3f(0.0,1.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,Y_MIN,0.0)
    glVertex3f(0.0,Y_MAX,0.0)
    glEnd()
    #Z axis en azul
    glColor3f(0.0,0.0,1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,0.0,Z_MIN)
    glVertex3f(0.0,0.0,Z_MAX)
    glEnd()
    glLineWidth(1.0)

def draw_skybox():
    glPushMatrix()
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    # Get current camera position
    x, y, z = EYE_X, EYE_Y, EYE_Z

    #Move the skybox to follow the camera
    glTranslatef(x, y, z)
    
    glBindTexture(GL_TEXTURE_2D, skybox_texture)
    glEnable(GL_TEXTURE_2D)
    
    size = 10.0

    glBegin(GL_QUADS)
    glColor3f(1.0, 1.0, 1.0)

    # Front face
    glTexCoord2f(0.1, 0.333); glVertex3f(-size, -size, -size)
    glTexCoord2f(0.1, 0.333); glVertex3f(size, -size, -size)
    glTexCoord2f(0.1, 0.666); glVertex3f(size, size, -size)
    glTexCoord2f(0.25, 0.666); glVertex3f(-size, size, -size)

    # Back face (positive z)
    glTexCoord2f(0.75, 0.333); glVertex3f(-size, -size, size)
    glTexCoord2f(1.00, 0.333); glVertex3f(size, -size, size)
    glTexCoord2f(1.00, 0.666); glVertex3f(size, size, size)
    glTexCoord2f(0.75, 0.666); glVertex3f(-size, size, size)
    
    # Left face (negative x)
    glTexCoord2f(0.00, 0.333); glVertex3f(-size, -size, -size)
    glTexCoord2f(0.25, 0.333); glVertex3f(-size, -size, size)
    glTexCoord2f(0.25, 0.666); glVertex3f(-size, size, size)
    glTexCoord2f(0.00, 0.666); glVertex3f(-size, size, -size)
    
    # Right face (positive x)
    glTexCoord2f(0.50, 0.333); glVertex3f(size, -size, -size)
    glTexCoord2f(0.75, 0.333); glVertex3f(size, -size, size)
    glTexCoord2f(0.75, 0.666); glVertex3f(size, size, size)
    glTexCoord2f(0.50, 0.666); glVertex3f(size, size, -size)
    
    # Top face (positive y)
    glTexCoord2f(0.25, 0.666); glVertex3f(-size, size, -size)
    glTexCoord2f(0.50, 5.666); glVertex3f(size, size, -size)
    glTexCoord2f(0.50, 5.000); glVertex3f(size, size, size)
    glTexCoord2f(0.25, 1.000); glVertex3f(-size, size, size)
    
    # Bottom face (negative y)
    glTexCoord2f(0.1, 0.333); glVertex3f(-size, -size, -size)
    glTexCoord2f(0.9, 0.333); glVertex3f(size, -size, -size)
    glTexCoord2f(0.1, 0.000); glVertex3f(size, -size, size)
    glTexCoord2f(0.25, 0.000); glVertex3f(-size, -size, size)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()

def load_texture(filename):
    image = Image.open(filename) # OpenGL expects textures flipped
    
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    textureData = image.tobytes()
    width, height = image.size
    
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 
                0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)
    
    # Set texture parameters for better quality
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    
    return texture_id

def Init():
    global floor_texture, skybox_texture
    screen = pygame.display.set_mode(
        (screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: cubos")
    
    # Load skybox and floor textures
    skybox_texture = load_texture(SKY_PATH)  
    floor_texture = load_texture(FLOOR_PATH) 

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width/screen_height, ZNEAR, ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
    glClearColor(0,0,0,0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    
    glLightfv(GL_LIGHT0, GL_POSITION,  (0, 200, 0, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glShadeModel(GL_SMOOTH)           # most obj files expect to be smooth-shaded 

def display(DimBoard):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    draw_skybox()  # Add this before drawing other objects
    
    Axis()

    # Draw the floor
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, floor_texture)
    
    glBegin(GL_QUADS)
    glColor3f(1.0, 1.0, 1.0)
    
    glTexCoord2f(0.0, 0.0); glVertex3d(-DimBoard, 0, -DimBoard)
    glTexCoord2f(0.0, 1.0); glVertex3d(-DimBoard, 0, DimBoard)
    glTexCoord2f(1.0, 1.0); glVertex3d(DimBoard, 0, DimBoard)
    glTexCoord2f(1.0, 0.0); glVertex3d(DimBoard, 0, -DimBoard)
    
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    
