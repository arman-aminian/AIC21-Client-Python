import json
from graph import Node


def pos_str(pos, w, h):
    # return f"{pos[0]},{pos[1]}"
    return f"{pos[0] * h + pos[1]}"


def str_pos(s, w, h):
    # return int(s.split(',')[0]), int(s.split(',')[1])
    return s // h, s % h


def encode_node(n):
    # remember to encode non-trivial attributes (if any)
    temp = n.__dict__.copy()
    if temp["wall"]:
        return []
    return list(temp.values())[3:]


def encode_graph_nodes(nodes: dict, w, h) -> str:
    new_dict = {}
    for k, v in nodes.items():
        new_dict[pos_str(k, w, h)] = encode_node(v)
    ret = [[] for _ in range(len(new_dict.keys()))]
    for p in new_dict.keys():
        ret[int(p)] = new_dict[p]
    ret2 = [str(r) + ';' for r in ret]
    return str(ret2).replace(' ', '').replace('\'', '').replace('[', '') \
        .replace(']', '').replace(';,', ';').replace('0x', '') \
        .replace(',0,', ',,').replace(',0;', ',;')


def decode_nodes(nodes_str: str, w, h) -> dict:
    ret = {}
    for i, cell in enumerate(nodes_str.split(";")):
        is_wall = cell == ''
        if is_wall:
            b, g, aw, ally_s, ew, es = [0] * 6
        else:
            cell = [int(x) if x != '' else 0 for x in cell.split(',')]
            b, g, aw, ally_s, ew, es = cell
        ret[str_pos(i, w, h)] = Node(str_pos(i, w, h), True, is_wall, b, g, aw,
                                     ally_s, ew, es)
    return ret
