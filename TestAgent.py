from Message import Message
import agentpy as ap
import math
from Semaforo import Semaforo
import random
from Message import Message

class TestAgent(ap.Agent):

    def setup(self):
        """
        Initialize the traffic light agent with its direction and initial settings.
        """
        self.direction = ""  
        
    def setup_direction(self, direction):
        self.direction = direction # up down left right
        
   
    def see(self):
       pass

    def next(self):
        pass
    
    def action(self):
        if random.random() < 0.03:  # 3% chance
            traffic_light = next((s for s in self.model.semaforos if s.direction == self.direction), None) # Get the traffic light for this direction
            if traffic_light and traffic_light.state == "Red":  # Check if it's red
                Message(
                    sender=self.direction,
                    receiver=self.direction,  # Assuming the message is sent to the traffic light of the same direction
                    performative="car_arrival",
                    content={"time": self.model.t}  # Include the current simulation time
                ).send()
        
    
    def step(self):
        self.see()
        self.next()
        self.action()
        
    def update(self):
        pass