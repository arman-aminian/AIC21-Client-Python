import time

import Model


def print_with_debug(*args, f=None, debug=True):
    if debug:
        print(*args)
    if f is not None:
        print(*args, file=f)


INIT_ANTS_NUM = 4
MAX_MESSAGES_PER_TURN = 5
MAX_MESSAGES_INIT = 60

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

GENERATE_KARGAR = 10
GENERATE_SARBAAZ = 10
WORKER_MAX_CARRYING_RESOURCE_AMOUNT = 10

GRASS_ONLY_ID = 1
NEW_GRASS_PRIORITY_PER_ROUND = 3
GRASS_PRIORITY_ID1 = 2
GRASS_PRIORITY_ID2 = 3
BREAD_PRIORITY_ID = 4
PRIORITY_GAP = 4

BASE_DMG = 3
SOLDIER_DMG = 2
HP = [8, 6]  # soldier, worker
MAX_TURN_COUNT = 200
BASE_RANGE = 6
SWAMP_TURNS = 3
VALUES = {
    "id": 10000,
    "enemy_base": 5000,
    "shot": 4000,
    "bg": 700,
    "disc_gt_5": 600,
    "es": 500,
    "disc_lt_5": 400,
    "bg_add": 300,
    "bg_sub": 200,
    "none": 100,
}
ALLIES_REQUIRED_TO_ATTACK = 2


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

def get_view_distance_neighbors(pos, w, h, view: int, exact: bool = False, sort=True):
    ret = []
    for i in range(-view, view + 1):
        for j in range(-view, view + 1):
            p = fix((pos[0] + i, pos[1] + j), w, h)
            if exact and manhattan_dist(pos, p, w, h) == view:
                ret.append(p)
            elif not exact and manhattan_dist(pos, p, w, h) <= view:
                ret.append(p)
    return sorted(ret) if sort else ret


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
        print_with_debug(f'{fn.__name__} took {delay} seconds!', debug=True)

        return res

    return wrapper


def add_pos_dir(pos, direction, w, h):
    temp = [(0, 0), (1, 0), (0, -1), (-1, 0), (0, 1)]
    new_pos = tuple(map(sum, zip(pos, temp[direction])))
    new_pos = fix(new_pos, w, h)
    return new_pos


def handle_exception(fn):
    def wrapper(*args, **kwargs):
        try:
            res = fn(*args, **kwargs)
        except Exception as e:
            # print('ERROR ERROR ERROR')
            # print(e)
            res = '', -50000, Model.Direction.get_random_direction()
            # todo: Raise Error
            # raise

        return res

    return wrapper


def print_map(input_map, pos, f=None):
    for j in range(input_map.dim[1]):
        for i in range(input_map.dim[0]):
            if (i, j) == input_map.base_pos:
                if f is not None:
                    print('B', end='', file=f)
                else:
                    print('B', end='')
            elif (i, j) == pos:
                if f is not None:
                    print('P', end='', file=f)
                else:
                    print('P', end='')
            elif input_map.nodes[(i, j)].wall:
                if f is not None:
                    print('W', end="", file=f)
                else:
                    print('W', end="", file=f)
            elif input_map.nodes[(i, j)].swamp:
                if f is not None:
                    print('S', end="", file=f)
                else:
                    print('S', end="", file=f)
            elif input_map.nodes[(i, j)].trap:
                if f is not None:
                    print('T', end="", file=f)
                else:
                    print('T', end="", file=f)
            else:
                if f is not None:
                    print('N' if not input_map.nodes[(i, j)].discovered else 'D', end='', file=f)
                else:
                    print('N' if not input_map.nodes[(i, j)].discovered else 'D', end='')
        if f is not None:
            print('', file=f)
        else:
            print()
