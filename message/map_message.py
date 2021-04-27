from copy import deepcopy

from Utils import get_view_distance_neighbors
from graph import Node

MESSAGE_VALUE = {
    "id": 1,
    "map": 10,
}
DELIM = '!'
CONSTANT = 34
# 00 -> 0 ; 01 -> 1-3 ; 10 -> 4-6 ; 11 -> 7+
UNIT_COUNT_MAP = [0] + [1] * 3 + [2] * 3 + [3]


def direction_enc(direction):
    return f'{direction:03b}'


def direction_dec(s):
    return int(s, 2)


def unit_count_enc(cnt: int) -> str:
    return f'{UNIT_COUNT_MAP[min(cnt, 7)]:02b}'


def unit_count_dec(s: str) -> int:
    x = int(s, 2)
    t = [i for i in range(len(UNIT_COUNT_MAP)) if UNIT_COUNT_MAP[i] == x]
    # could return min, max, and avg
    return min(t)
    # return sum(t) // len(t)


def pos_str(pos, w, h):
    # return f"{pos[0] + CONSTANT:06b}{pos[1] + CONSTANT:06b}"
    return f"{chr(pos[0] + CONSTANT)}{chr(pos[1] + CONSTANT)}"


def str_pos(s, w, h):
    # return int(s[:6], 2) - CONSTANT, int(s[6:], 2) - CONSTANT
    return ord(s[0]) - CONSTANT, ord(s[1]) - CONSTANT


def encode_graph_nodes(pos, nodes: dict, w, h, view, ant_id, direction,
                       shot: bool, enemy_base_pos=None):
    # CURRENT SCHEME:
    # id 1c, pos 2c (14b), walls w*1c,
    # breads b*2c, grasses g*2c, ally workers aw*1c, ally soldiers as*1c,
    # enemy workers ew*1c, enemy soldiers es*1c, status 1c
    neighbors = get_view_distance_neighbors(pos, w, h, view)
    arr = [[], [], [], [], [], []]  # for the values (b, g, aw, as, ew, es)
    s = chr(ant_id + CONSTANT) + pos_str(pos, w, h)
    for p, n in nodes.items():
        if n.wall:
            s += chr(neighbors.index(p) + CONSTANT)
    s += DELIM
    
    for p, n in nodes.items():
        values = list(n.__dict__.values())[3:]
        for i, v in enumerate(values):
            if v > 0:
                if i < 2:
                    arr[i].append(chr(neighbors.index(p) + CONSTANT))
                    arr[i].append(chr(v + CONSTANT))
                else:
                    pos_cnt = f'{neighbors.index(p):06b}' + unit_count_enc(v)
                    arr[i].append(chr(int(pos_cnt, 2) + CONSTANT))
    
    status = direction_enc(direction) + str(int(shot))
    
    for a in arr:
        s = s + ''.join(a) + DELIM
    s += chr(int(status, 2) + CONSTANT) + DELIM
    if enemy_base_pos is not None:
        s += pos_str(enemy_base_pos, w, h)
    
    return s


def decode_nodes(nodes_str: str, w, h, view):
    ret = {}
    ant_id = ord(nodes_str[0]) - CONSTANT
    pos = str_pos(nodes_str[1:3], w, h)
    nodes_str = nodes_str[3:]
    neighbors = get_view_distance_neighbors(pos, w, h, view)
    direction = direction_dec('000')
    shot = bool(int('0'))
    enemy_base_pos = None
    non_empties = []
    
    part = nodes_str.split(DELIM)[0]  # wall
    for c in part:
        idx = ord(c) - CONSTANT
        non_empties.append(idx)
        ret[neighbors[idx]] = Node(neighbors[idx], True, True)
    
    for i, part in enumerate(nodes_str.split(DELIM)):
        if i == 1:  # bread
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                non_empties.append(idx)
                ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                           bread=ord(v) - CONSTANT)
        if i == 2:  # grass
            for j in range(0, len(part), 2):
                c, v = part[j], part[j + 1]
                idx = ord(c) - CONSTANT
                non_empties.append(idx)
                ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                           grass=ord(v) - CONSTANT)
        if i == 3:  # ally worker
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                non_empties.append(idx)
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].ally_workers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               ally_workers=v)
        if i == 4:  # ally soldier
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                non_empties.append(idx)
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].ally_soldiers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               ally_soldiers=v)
        if i == 5:  # enemy worker
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                non_empties.append(idx)
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].enemy_workers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               enemy_workers=v)
        if i == 6:  # enemy soldier
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                non_empties.append(idx)
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].enemy_soldiers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               enemy_soldiers=v)
    
        if i == 7:  # status
            status = f'{ord(part[0]) - CONSTANT:08b}'
            direction = direction_dec(status[:3])
            shot = bool(int(status[3]))
            
        if i == 8 and len(part) > 0:  # enemy base pos
            enemy_base_pos = str_pos(part, w, h)
    
    for i in range(len(neighbors)):
        if i not in non_empties:
            ret[neighbors[i]] = Node(neighbors[i], True, False)
    
    return ant_id, pos, direction, shot, ret, enemy_base_pos
