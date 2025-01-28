from Message import Message
import agentpy as ap
import math

class SemaforoAgent(ap.Agent):

    def setup(self, direction):
        """
        Initialize the traffic light agent with its direction and initial settings.
        """
        self.direction = direction  # up, down, left, right
        self.first_car_arrival = 99999999  # Initially very large number
        self.green_time = 30  # Time for green light
        self.yellow_time = 10  # Time for yellow light
        self.red_time = 0  # Red time is infinite until another light decides
        self.state = "Red"  # Initial state
        self.intention = None  # Intended next state
        self.time_counter = 0  # Counter for state transitions
        self.first_car_arrivals = { "up": 99999999, "down": 99999999, "left": 99999999, "right": 99999999 }  # Initialize dictionary for all directions
        self.reported = False  # To track if the agent has already reported its first car arrival

    def take_msg(self):
        """
        Process incoming messages from cars or other traffic lights.
        """
        # Process red_finished messages first
        for msg in Message.environment_buffer:
            if msg.receiver == self.direction and msg.performative == "red_finished":
                # Create an array of pairs (arrival_time, direction) from the first_car_arrivals dictionary
                arrival_times = [(time, dir) for dir, time in self.first_car_arrivals.items()]
                # Sort the array first by arrival_time, then by direction
                arrival_times.sort()

                # Check if the current direction has the earliest arrival time
                if (self.first_car_arrival, self.direction) == arrival_times[0]:
                    self.intention = "Green"  # Set intention to Green

                # Reset the first_car_arrivals dictionary after processing red_finished messages
                self.first_car_arrivals = { "up": 99999999, "down": 99999999, "left": 99999999, "right": 99999999 }

                Message.environment_buffer.remove(msg)

        # Process car arrival messages
        for msg in Message.environment_buffer:
            if msg.receiver == self.direction and msg.performative == "car_arrival":
                self.first_car_arrival = min(msg.content["time"], self.first_car_arrival)
                Message.environment_buffer.remove(msg)

        # Process send_first_car_arrival messages from other lights
        for msg in Message.environment_buffer:
            if msg.performative == "send_first_car_arrival":
                # Update the first_car_arrivals dictionary with the received information
                self.first_car_arrivals[msg.content["direction"]] = min(self.first_car_arrivals[msg.content["direction"]], msg.content["time"])
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
                # Notify other traffic lights when switching to Red
                for other_light in self.model.traffic_lights:
                    if other_light.direction != self.direction:
                        Message(
                            sender=self.direction,
                            receiver=other_light.direction,
                            performative="red_finished",
                            content={"time": self.first_car_arrival}
                        ).send()

            # After updating the first_car_arrival, send the update to all other traffic lights
            Message(
                sender=self.direction,
                receiver="all",  # Broadcast to all lights
                performative="send_first_car_arrival",
                content={"direction": self.direction, "time": self.first_car_arrival}
            ).send()

            # Update the state
            self.state = self.intention
            self.intention = None  # Reset intention after applying it

        # Print current state
        if self.state == "Green":
            print(f"Traffic light {self.direction} is GREEN.")
        elif self.state == "Yellow":
            print(f"Traffic light {self.direction} is YELLOW.")
        elif self.state == "Red":
            print(f"Traffic light {self.direction} is RED.")

    def step(self):
        """
        Main step function: see, decide the next state, and perform the action.
        """
        self.see()
        self.next()
        self.action()
