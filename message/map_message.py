from copy import deepcopy
# from typing import Tuple

from graph import Node
from Utils import get_view_distance_neighbors


MESSAGE_VALUE = {
    "id": 1,
    "map": 10,
}
DELIM = '!'
CONSTANT = 34


def pos_str(pos, w, h):
    return f"{chr(pos[0] + CONSTANT)}{chr(pos[1] + CONSTANT)}"


def str_pos(s, w, h):
    return ord(s[0]) - CONSTANT, ord(s[1]) - CONSTANT


def encode_node(n):
    # remember to encode non-trivial attributes (if any)
    temp = deepcopy(n)
    if temp["wall"]:
        return []
    values = list(temp.values())[3:]
    if values == [0] * 6:
        return [0]
    return values


def encode_graph_nodes(pos, nodes: dict, w, h, view, ant_id) -> str:
    neighbors = get_view_distance_neighbors(pos, w, h, view)
    arr = [[], [], [], [], [], []]  # for the values (b, g, aw, as, ew, es)
    s = chr(ant_id + CONSTANT) + pos_str(pos, w, h)
    for p, n in nodes.items():
        if n.wall:
            s += chr(neighbors.index(p) + CONSTANT)
    s += DELIM
    
    for p, n in nodes.items():
        if not n.wall and list(n.__dict__.values())[3:] == [0] * 6:
            s += chr(neighbors.index(p) + CONSTANT)
    s += DELIM
    
    for p, n in nodes.items():
        values = list(n.__dict__.values())[3:]
        for i, v in enumerate(values):
            if v > 0:
                arr[i].append(chr(neighbors.index(p) + CONSTANT))
                arr[i].append(chr(v + CONSTANT))
    
    for a in arr:
        s = s + ''.join(a) + DELIM
    
    return s
    

def decode_nodes(nodes_str: str, w, h, view):
    ret = {}
    ant_id = ord(nodes_str[0]) - CONSTANT
    pos = str_pos(nodes_str[1:3], w, h)
    nodes_str = nodes_str[3:]
    neighbors = get_view_distance_neighbors(pos, w, h, view)

    part = nodes_str.split(DELIM)[0]  # wall
    for c in part:
        idx = ord(c) - CONSTANT
        ret[neighbors[idx]] = Node(neighbors[idx], True, True)
        
    part = nodes_str.split(DELIM)[1]  # empty
    for c in part:
        idx = ord(c) - CONSTANT
        ret[neighbors[idx]] = Node(neighbors[idx], True, False)
        
    for i, part in enumerate(nodes_str.split(DELIM)):
        if i == 2:  # bread
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                           bread=ord(v) - CONSTANT)
        if i == 3:  # grass
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                           grass=ord(v) - CONSTANT)
        if i == 4:  # ally worker
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].ally_workers = ord(v) - CONSTANT
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               ally_workers=ord(v) - CONSTANT)
        if i == 5:  # ally soldier
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].ally_soldiers = ord(v) - CONSTANT
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               ally_soldiers=ord(v) - CONSTANT)
        if i == 6:  # enemy worker
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].enemy_workers = ord(v) - CONSTANT
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               enemy_workers=ord(v) - CONSTANT)
        if i == 7:  # enemy soldier
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].enemy_soldiers = ord(v) - CONSTANT
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               enemy_soldiers=ord(v) - CONSTANT)
    
    return ant_id, pos, ret
