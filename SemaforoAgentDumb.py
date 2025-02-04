from Message import Message
import agentpy as ap
import math
from Semaforo import Semaforo

class SemaforoAgentDumb(ap.Agent):
    global_index = 5
    def setup(self):
        """
        Initialize the traffic light agent with its direction and initial settings.
        """
        self.direction = ""  # up, down, left, right
        self.green_time = None  # Time for green light
        self.yellow_time = None  # Time for yellow light
        self.red_time = 0  # Red time is infinite until another light decides
        self.state = "Red"  # Initial state
        self.intention = None  # Intended next state
        self.time_counter = 0  # Counter for state transitions
        self.semaforo = None
        self.Position = [0, 0, 0]
        
    def setup_direction(self, direction):
        self.direction = direction
        
    def setup_semaforo(self, semaforoInfo):
        self.semaforo = Semaforo(semaforoInfo['init_pos'], semaforoInfo['rotation'])
        self.Position = semaforoInfo['init_pos']
        
    def setup_color_time(self, green, yellow):
        self.green_time = green
        self.yellow_time = yellow     
   
    def see(self):
        """
        Checks if it's its time to turn green
        """
        if SemaforoAgentDumb.global_index == self.id and self.state == "Red":
            self.intention = "Green"
        pass

    def next(self):
        """
        Decide the next state transition based on the current state and timing.
        """
        if self.state == "Green":
            self.time_counter += 1
            if self.time_counter >= self.green_time:
                self.intention = "Yellow"  # Set intention to Yellow
                self.time_counter = 0
        elif self.state == "Yellow":
            self.time_counter += 1
            if self.time_counter >= self.yellow_time:
                self.intention = "Red"  # Set intention to Red
                SemaforoAgentDumb.global_index += 1
                if SemaforoAgentDumb.global_index == 9:
                    SemaforoAgentDumb.global_index = 5
                self.time_counter = 0
        elif self.state == "Red":
            # Intention may already be set by incoming messages in take_msg
            pass

    def action(self):
        """
        Perform actions based on the intention and current state.
        Change colors and send notifications if necessary.
        """
        if self.intention:
            # Update the state
            self.state = self.intention
            self.intention = None  # Reset intention after applying it
 
    def step(self):
        """
        Main step function: see, decide the next state, and perform the action.
        """
        self.see()
        self.next()
        self.action()
        
    def update(self):
        self.semaforo.current_color = self.state
        self.semaforo.draw(self.semaforo.Position, scale=10.5)