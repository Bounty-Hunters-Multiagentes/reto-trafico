from Message import Message
import agentpy as ap
import math
from Semaforo import Semaforo

class SemaforoAgent(ap.Agent):

    def setup(self):
        """
        Initialize the traffic light agent with its direction and initial settings.
        """
        self.direction = ""  # up, down, left, right
        self.first_car_arrival = 99999999  # Initially very large number
        self.green_time = None  # Time for green light
        self.yellow_time = None  # Time for yellow light
        self.red_time = 0  # Red time is infinite until another light decides
        self.state = "Red"  # Initial state
        self.intention = None  # Intended next state
        self.time_counter = 0  # Counter for state transitions
        self.first_car_arrivals = { "up": 99999999, "down": 99999999, "left": 99999999, "right": 99999999 }  # Initialize dictionary for all directions
        self.reported = False  # To track if the agent has already reported its first car arrival
        self.semaforo = None
        self.Position = [0, 0, 0]
        
    def setup_direction(self, direction):
        self.direction = direction
        # Si somos el primer semaforo se manda el mensaje de que inicialmente todos estamos en rojo
        for other_light in self.model.semaforos:
            if True: # lo vamos a dejar asi por ahora (deberia funcionar igual)
                 Message(
                    sender= None,
                    receiver=other_light.direction,
                    performative="red_finished",
                    content={"time": 0}
                ).send()
        
    def setup_semaforo(self, semaforoInfo):
        self.semaforo = Semaforo(semaforoInfo['init_pos'], semaforoInfo['rotation'])
        self.Position = semaforoInfo['init_pos']
        
    def setup_color_time(self, green, yellow):
        self.green_time = green
        self.yellow_time = yellow
        
    def take_msg(self):
        """
        Process incoming messages from cars or other traffic lights.
        """
        red_finished_msgs = []
        car_arrival_msgs = []
        first_car_arrival_msgs = []

        # Separate messages into categories before processing
        for msg in list(Message.environment_buffer):  # Use list() to avoid modifying while iterating
            if msg.receiver == self.direction:
                if msg.performative == "red_finished":
                    red_finished_msgs.append(msg)
                elif msg.performative == "car_arrival":
                    car_arrival_msgs.append(msg)
            if msg.performative == "send_first_car_arrival":
                first_car_arrival_msgs.append(msg)

        # Process red_finished messages first
        for msg in red_finished_msgs:
            arrival_times = [(time, dir) for dir, time in self.first_car_arrivals.items()]
            arrival_times.sort()  # Sort by earliest arrival time

            # print("these were the arrival times: ", self.direction, self.first_car_arrival)
            # print(arrival_times)

            if (arrival_times[0][0], self.direction) == arrival_times[0]:
                self.intention = "Green"

            # Reset the first_car_arrivals dictionary after processing red_finished messages
            self.first_car_arrivals = { "up": 99999999, "down": 99999999, "left": 99999999, "right": 99999999 }
            self.first_car_arrival = 99999999
            # Do NOT reset first_car_arrivals immediately—wait until all messages are processed
            Message.environment_buffer.remove(msg)

        # Process car arrival messages
        for msg in car_arrival_msgs:
            self.first_car_arrival = min(msg.content["time"], self.first_car_arrival)
            Message.environment_buffer.remove(msg)

        # Process send_first_car_arrival messages from other lights
        for msg in first_car_arrival_msgs:
            self.first_car_arrivals[msg.content["direction"]] = msg.content["time"]
            if msg.sender == self.direction:
                    Message.environment_buffer.remove(msg)


    def see(self):
        """
        Check messages in the environment buffer and update state accordingly.
        """
        self.take_msg()

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
            if self.state == "Yellow" and self.intention == "Red":
                # print()
                # print()
                # print("Became Red", self.direction, self.model.t)
                # Notify other traffic lights when switching to Red
                for other_light in self.model.semaforos:
                    if other_light.direction != self.direction or True: # lo vamos a dejar asi por ahora (deberia funcionar igual)
                        Message(
                            sender=self.direction,
                            receiver=other_light.direction,
                            performative="red_finished",
                            content={"time": self.first_car_arrival}
                        ).send()
                        
                self.first_car_arrival = 99999999
            # Update the state
            self.state = self.intention
            self.intention = None  # Reset intention after applying it
            
        # After updating the first_car_arrival, send the update to all other traffic lights
        # print("sending message")
        
        # print(self.direction, self.first_car_arrivals, self.first_car_arrival, self.model.t)
        Message(
            sender=self.direction,
            receiver="all",  # Broadcast to all lights
            performative="send_first_car_arrival",
            content={"direction": self.direction, "time": self.first_car_arrival}
        ).send()

        # Print current state
        
        """
        if self.state == "Green":
            pass
            print(f"Traffic light {self.direction} is GREEN.")
        elif self.state == "Yellow":
            pass
            print(f"Traffic light {self.direction} is YELLOW.")
        elif self.state == "Red":
            pass
            print(f"Traffic light {self.direction} is RED.")
        """
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