from message.map_message import CONSTANT


def pos_str(pos, w, h):
    return f"{chr(pos[0] + CONSTANT)}{chr(pos[1] + CONSTANT)}"


def str_pos(s, w, h):
    return ord(s[0]) - CONSTANT, ord(s[1]) - CONSTANT


def encode_support_cell(ant_id, pos, w, h, resource_count):
    s = "sc" + chr(ant_id + CONSTANT)
    
    s += pos_str(pos, w, h)
    
    s += chr(min(resource_count, 220) + CONSTANT)
    
    return s


def decode_support_cell(s, w, h):
    ant_id = ord(s[2]) - CONSTANT
    pos = str_pos(s[3:5], w, h)
    resource_count = ord(s[5]) - CONSTANT
    return ant_id, pos, resource_count
