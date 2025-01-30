from dataclasses import dataclass


@dataclass
class Lane:
    name: str
    direction: list[int]
    max_x: int
    max_z: int
    min_x: int
    min_z: int

lanes = [Lane('Up', [-1,0,0], max_x=200, max_z=0, min_x=-200, min_z=-50), 
         Lane('Down', [1,0,0], max_x=200, max_z=50, min_x=-200, min_z=0) ,
         Lane('Left', [0,0,1], max_x=0, max_z=200, min_x=-50, min_z=-200 ), Lane('Right', [0,0,-1], max_x=50, max_z=200, min_x=0, min_z=-200)]
lane_map = {lane.name: lane for lane in lanes}

directions = ['Up', 'Down', 'Left', 'Right']

def get_start_position(lane_name):
    if lane_name == 'Up':
        return [lane_map[lane_name].max_x, 0, (lane_map[lane_name].max_z + lane_map[lane_name].min_z) / 2]

    if lane_name == 'Down':
        return [lane_map[lane_name].min_x, 0, (lane_map[lane_name].max_z + lane_map[lane_name].min_z) / 2]
    if lane_name == 'Left':
        return [(lane_map[lane_name].min_x + lane_map[lane_name].max_x) / 2, 0, lane_map[lane_name].min_z]
    if lane_name == 'Right':
        return [(lane_map[lane_name].min_x + lane_map[lane_name].max_x) / 2, 0, lane_map[lane_name].max_z]
    