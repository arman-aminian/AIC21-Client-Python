from graph import Node


DELIM = '!'
CONSTANT = 34


def pos_str(pos, w, h):
    # return f"{pos[0] + pos[1] * w}"
    return f"{pos[0]},{pos[1]}"


def str_pos(s, w, h):
    # return s % w, s // w
    return int(s.split(',')[0]), int(s.split(',')[1])


def encode_node(n):
    # remember to encode non-trivial attributes (if any)
    temp = n.__dict__.copy()
    if temp["wall"]:
        return []
    values = list(temp.values())[3:]
    if values == [0] * 6:
        return [0]
    return values


def fix(pos, w, h):
    x = pos[0] % w
    y = pos[1] % h
    if x < 0:
        x += w
    if y < 0:
        y += h
    return x, y


def manhattan(p, q, w, h) -> int:
    x_diff = min(abs(p[0] - q[0]), h - abs(p[0] - q[0]))
    y_diff = min(abs(p[1] - q[1]), w - abs(p[1] - q[1]))
    return x_diff + y_diff


def get_neighbor_positions(pos, w, h, view: int) -> list:
    ret = []
    for i in range(-view, view + 1):
        for j in range(-view, view + 1):
            p = fix((pos[0] + i, pos[1] + j), w, h)
            if manhattan(pos, p, w, h) <= view:
                ret.append(p)
    return sorted(ret)


def encode_graph_nodes(pos, nodes: dict, w, h, view) -> str:
    # second version
    neighbors = get_neighbor_positions(pos, w, h, view)
    # building the string:
    arr = [[], [], [], [], [], []]  # for the values (b, g, aw, as, ew, es)
    s = pos_str(pos, w, h) + ":"
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
    
    # first version which is too long
    # new_dict = {}
    # for k, v in nodes.items():
    #     print(k, pos_str(k, w, h))
    #     new_dict[pos_str(k, w, h)] = encode_node(v)
    #
    # ret2 = [str(k) + ':' + str(v) + ';' for k, v in new_dict.items()]
    #
    # ret = [[] for _ in range(len(new_dict.keys()))]
    # for p in new_dict.keys():
    #     ret[int(p)] = new_dict[p]
    # ret2 = [str(r) + ';' for r in ret]
    #
    # return str(ret2).replace(' ', '').replace('\'', '').replace('[', '') \
    #     .replace(']', '').replace(';,', ';').replace(',0,', ',,') \
    #     .replace(',0;', ',;').replace(':0,', ':,')


def decode_nodes(nodes_str: str, w, h, view) -> dict:
    ret = {}
    pos = str_pos(nodes_str[:nodes_str.index(':')], w, h)
    nodes_str = nodes_str[nodes_str.index(':') + 1:]
    neighbors = get_neighbor_positions(pos, w, h, view)
    # for the second version
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
    
    # for the first version
    # for i, cell in enumerate(nodes_str.split(";")):
    #     is_wall = cell == ''
    #     if is_wall or cell == '0':
    #         b, g, aw, ally_s, ew, es = [0] * 6
    #     else:
    #         cell = [int(x) if x != '' else 0 for x in cell.split(',')]
    #         b, g, aw, ally_s, ew, es = cell
    #     ret[str_pos(i, w, h)] = Node(str_pos(i, w, h), True, is_wall, b, g, aw,
    #                                  ally_s, ew, es)
    return ret
