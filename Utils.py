import Model


INIT_ANTS_NUM = 4


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
    x_diff = min(abs(p[0] - q[0]), h - abs(p[0] - q[0]))
    y_diff = min(abs(p[1] - q[1]), w - abs(p[1] - q[1]))
    return x_diff + y_diff


def get_view_distance_neighbors(pos, w, h, view: int) -> list:
    ret = []
    for i in range(-view, view + 1):
        for j in range(-view, view + 1):
            p = fix((pos[0] + i, pos[1] + j), w, h)
            if manhattan_dist(pos, p, w, h) <= view:
                ret.append(p)
    return sorted(ret)
