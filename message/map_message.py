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


def unit_count_enc(cnt: int) -> str:
    return f'{UNIT_COUNT_MAP[min(cnt, 7)]:02b}'


def unit_count_dec(s: str) -> int:
    x = int(s, 2)
    t = [i for i in range(len(UNIT_COUNT_MAP)) if UNIT_COUNT_MAP[i] == x]
    # could also return min or max
    return sum(t) // len(t)


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
        values = list(n.__dict__.values())[3:]  # for bread and grass
        for i, v in enumerate(values):
            if v > 0:
                if i < 2:
                    arr[i].append(chr(neighbors.index(p) + CONSTANT))
                    arr[i].append(chr(v + CONSTANT))
                else:
                    pos_cnt = f'{neighbors.index(p):06b}' + unit_count_enc(v)
                    arr[i].append(chr(int(pos_cnt, 2) + CONSTANT))
    
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
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].ally_workers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               ally_workers=v)
        if i == 5:  # ally soldier
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].ally_soldiers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               ally_soldiers=v)
        if i == 6:  # enemy worker
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].enemy_workers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               enemy_workers=v)
        if i == 7:  # enemy soldier
            for j in range(len(part)):
                p, v = int(f'{ord(part[j]) - CONSTANT:08b}'[:6], 2), \
                       unit_count_dec(f'{ord(part[j]) - CONSTANT:08b}'[6:])
                idx = p
                if neighbors[idx] in ret:
                    ret[neighbors[idx]].enemy_soldiers = v
                else:
                    ret[neighbors[idx]] = Node(neighbors[idx], True, False,
                                               enemy_soldiers=v)
    
    return ant_id, pos, ret
