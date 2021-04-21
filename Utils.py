import time

import Model

INIT_ANTS_NUM = 4
MAX_MESSAGES_PER_TURN = 5

INIT_STRAIGHT_ANTS_MOVES = [[1, 2, 3, 4],
                            [2, 3, 4, 1],
                            [3, 4, 1, 2],
                            [4, 1, 2, 3]]

INIT_CENTER_ANTS_MOVES1 = [[4, 1, 2, 3],  # left-up
                           [2, 1, 4, 3],  # left-down
                           [4, 3, 2, 1],  # right-up
                           [2, 3, 4, 1]]  # right-down

INIT_CENTER_ANTS_MOVES2 = [[1, 4, 2, 3],  # left-up
                           [1, 2, 4, 3],  # left-down
                           [3, 4, 2, 1],  # right-up
                           [3, 2, 4, 1]]  # right-down


def reverse_list(lst):
    return [ele for ele in reversed(lst)]


def get_next_move(cur, path):
    if path[0].pos[0] == cur.pos[0]:
        if path[0].pos[1] == cur.pos[1] - 1:
            return Model.Direction.UP
        elif path[0].pos[1] - 1 == cur.pos[1]:
            return Model.Direction.DOWN
    elif path[0].pos[1] == cur.pos[1]:
        if path[0].pos[0] == cur.pos[0] - 1:
            return Model.Direction.LEFT
        elif path[0].pos[0] - 1 == cur.pos[0]:
            return Model.Direction.RIGHT
    return Model.Direction.CENTER


def fix(pos, w, h):
    x = pos[0] % w if pos[0] % w >= 0 else (pos[0] % w) + w
    y = pos[1] % h if pos[1] % h >= 0 else (pos[1] % h) + h
    return x, y


def manhattan_dist(p, q, w, h) -> int:
    x_diff = min(abs(p[0] - q[0]), w - abs(p[0] - q[0]))
    y_diff = min(abs(p[1] - q[1]), h - abs(p[1] - q[1]))
    return x_diff + y_diff


def get_view_distance_neighbors(pos, w, h, view: int) -> list:
    ret = []
    for i in range(-view, view + 1):
        for j in range(-view, view + 1):
            p = fix((pos[0] + i, pos[1] + j), w, h)
            if manhattan_dist(pos, p, w, h) <= view:
                ret.append(p)
    return sorted(ret)


def shortest_path(src, dest, w, h):
    if src[0] == dest[0]:  # up and down
        up = []
        down = []
        i = src[1]
        while i != dest[1]:
            up.append(fix((src[0], i + 1), w, h))
            i = up[-1][1]
        
        i = src[1]
        while i != dest[1]:
            down.append(fix((src[0], i - 1), w, h))
            i = down[-1][1]
        
        return up if len(up) <= len(down) else down
    
    if src[1] == dest[1]:  # left and right
        left = []
        right = []
        i = src[0]
        while i != dest[0]:
            right.append(fix((i + 1, src[1]), w, h))
            i = right[-1][0]
        
        i = src[0]
        while i != dest[0]:
            left.append(fix((i - 1, src[1]), w, h))
            i = left[-1][0]
        
        return right if len(right) <= len(left) else left
    
    path1 = shortest_path(src, (dest[0], src[1]), w, h) + shortest_path(
        (dest[0], src[1]), dest, w, h)
    path2 = shortest_path(src, (src[0], dest[1]), w, h) + shortest_path(
        (src[0], dest[1]), dest, w, h)


def time_measure(fn):
    def wrapper(*args, **kwargs):
        now = time.time()
        res = fn(*args, **kwargs)
        delay = time.time() - now

        print(f'{fn.__name__} took {delay} seconds!')

        return res

    return wrapper
