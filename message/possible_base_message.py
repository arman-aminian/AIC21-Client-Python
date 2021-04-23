from message.map_message import CONSTANT


def ps(pos, w, h):
    return f"{pos[0] + CONSTANT:06b}{pos[1] + CONSTANT:06b}"


def sp(s, w, h):
    return int(s[:6], 2) - CONSTANT, int(s[6:], 2) - CONSTANT


def encode_possible_cells(ant_id, pos, prev_pos, w, h, possible_cells):
    s = "s" + chr(ant_id + CONSTANT)
    
    binary = ps(pos, w, h) + ps(prev_pos, w, h)
    for p in possible_cells:
        binary += ps(p, w, h)
    
    for i in range(0, len(binary), 8):
        part = binary[i:i + 8]
        s += chr(int(part, 2) + CONSTANT)
    
    return s


def decode_possible_cells(s, w, h):
    ant_id = ord(s[1]) - CONSTANT
    temp = ''.join([f"{ord(c) - CONSTANT:08b}" for c in s[2:]])
    # print("decode possible msg error:", temp[:12])
    # print(temp)
    pos = sp(temp[:12], w, h)
    prev_pos = sp(temp[12:24], w, h)
    possible_cells = []
    for i in range(24, len(temp) - 12, 12):
        p = temp[i: i + 12]
        possible_cells.append(sp(p, w, h))
    
    return ant_id, pos, prev_pos, possible_cells
