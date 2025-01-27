# Importaciones: PyGame y OpenGL
import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from constants import (
    ANIMATION_SAVE_PATH,
    ASPHALT_ASSET,
    BASE_Y,
    COLUMNS,
    DISCARGE_Y,
    NB_PATH,
    ROWS,
    RUBRIK_ASSET,
    X_MAX,
    X_MIN,
    Y_MAX,
    Y_MIN,
    Z_MAX,
    Z_MIN,
    DimBoard,
    screen_height,
    screen_width,
    toggle_camera_view,
)
import CuboModel
from objects import Camera

import numpy as np
import matplotlib.pyplot as plt

def Axis():
    glShadeModel(GL_FLAT)
    glLineWidth(3.0)
    #X axis in red
    glColor3f(1.0,0.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN,0.0,0.0)
    glVertex3f(X_MAX,0.0,0.0)
    glEnd()
    #Y axis in green
    glColor3f(0.0,1.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,Y_MIN,0.0)
    glVertex3f(0.0,Y_MAX,0.0)
    glEnd()
    #Z axis in blue
    glColor3f(0.0,0.0,1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,0.0,Z_MIN)
    glVertex3f(0.0,0.0,Z_MAX)
    glEnd()
    glLineWidth(1.0)
    
def display(DimBoard):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    Axis()
    #Se dibuja el plano gris
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3d(-DimBoard, 0, -DimBoard)
    glVertex3d(-DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, -DimBoard)
    glEnd()

def Init():
    screen = pygame.display.set_mode(
        (screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: cubos")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width/screen_height, ZNEAR, ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
    glClearColor(0,0,0,0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
def main():
    # Definición de parámetros de la simulación

    parameters = {
    'cubos' : 10,
    'dim' : 200,
    'vel' : 2.0,
    'Scale' : 5.0,
    #'steps' : 100
    }

    model = CuboModel(parameters) # instanciación de Cubo Model

    done = False # Flag de detención de la app
    Init() # Inicialización del mundo gráfico
    model.sim_setup() # Inicialización manual de Simulación

    # Ciclo principal
    while not done:
        # Si se ha cerrado la aplicación, activar flags
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True # Flag de dentención
                model.stop() # Llamar a detención de simulación manualmente
                model.create_output() # Crear registro manualmente
                # Agregar información al registro postSimulación
                model.output.info['Mensaje'] = 'Puedes añadir información al registro de esta forma.'

        # Dibujado del mundo gráfico
        display(parameters['dim'])

        # Si la simulación está corriendo...
        if model.running:
            # Llamar a la iteración de la simulación manualmente
            model.sim_step()


        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit() # Finalizar entorno gráfico

    print(model.output.info)
    # Graficar variable registrada
    model.output.variables.CuboModel.plot()
    plt.show()
    
if __name__ == "__main__":
    main()
    