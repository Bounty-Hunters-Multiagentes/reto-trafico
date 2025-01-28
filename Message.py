
"""
Messages:
Entre semáforos -> Para determinar su estatus (un semáforo requiere leer el estatus del otro antes de indicar verde)
Entre carro y semáforo -> para indicar la presencia de un carro al semáforo


"""

class Message():
    """
    The message class is used to wrap messages and send messages between agents.
    It also contains the environment buffer that stores all messages.
    """
    environment_buffer = [] # The environment buffer
    
    def __init__(self,sender=None,receiver=None,performative=None,content=None):
        """
        The __init__ function is called when the class is instantiated.
        It sets the sender, receiver, performative and content of the message.
        """
        self.sender = sender
        self.receiver = receiver
        self.performative = performative
        self.content = content
    
    def __str__(self):
        """
        The __str__ function is called when the class is converted to a string.
        It returns a string representation of the message.
        """
        return f"\n\
        Sender: {self.sender}, \n\
        Receiver: {self.receiver}, \n\
        Performative: {self.performative}, \n\
        Content: {self.content}"
    
    def send(self):
        """
        The send function is used to send a message to the environment buffer.
        """
        Message.environment_buffer.append(self)
        
    @staticmethod
    def receive(receiver_id):
        """
        The receive function is used to receive a message from the environment buffer.
        """
        received_messages = []
        for message in Message.environment_buffer:
            if message.receiver == receiver_id:
                received_messages.append(message)
            
        for message in received_messages:
            Message.environment_buffer.remove(message)
        
        return received_messages