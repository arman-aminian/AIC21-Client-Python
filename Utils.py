import Model


def reverse_list(lst):
    return [ele for ele in reversed(lst)]


# todo check the directions
def get_next_move(cur, path):
    if path[0].pos[0] == cur.pos[0]:
        if path[0].pos[1] == cur.pos[1] - 1:
            return Model.Direction.DOWN
        elif path[0].pos[1] - 1 == cur.pos[1]:
            return Model.Direction.UP
    elif path[0].pos[1] == cur.pos[1]:
        if path[0].pos[0] == cur.pos[0] - 1:
            return Model.Direction.LEFT
        elif path[0].pos[0] - 1 == cur.pos[0]:
            return Model.Direction.RIGHT
    return Model.Direction.CENTER
