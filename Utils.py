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

INIT_MODE = 0
DISCOVER_MODE = 1
COLLECT_MODE = 2


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
