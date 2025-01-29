from dataclasses import dataclass

@dataclass
class Lane:
    name: str
    direction: list[int]
    max_x: int
    max_z: int
    min_x: int
    min_z: int
    
lanes = [Lane('Up', [-1,0,0], max_x=200, max_z=0, min_x=-200, min_z=-50), Lane('Down', [1,0,0], max_x=200, max_z=50, min_x=-200, min_z=0),
         Lane('Left', [0,0,1], max_x=0, max_z=200, min_x=-50, min_z=-200 ), Lane('Right', [0,0,-1], max_x=50, max_z=200, min_x=0, min_z=-200)]

lane_map = {lane.name: lane for lane in lanes}

directions = ['Up', 'Down', 'Left', 'Right']