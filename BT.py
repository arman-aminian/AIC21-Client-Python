import time

from Model import Direction
from Utils import get_view_distance_neighbors, time_measure


MAX_DISTANCE = 10


class BT:
    def __init__(self, graph, cur):
        self.start = time.time()
        self.graph = graph
        self.best_path = None
        self.path = MAX_DISTANCE * [-1]
        self.best = None
        self.visited = set(get_view_distance_neighbors(cur, self.graph.dim[0], self.graph.dim[1], 4))

        for pos, node in graph.nodes.items():
            if node.discovered:
                self.visited.add(pos)

    def bt(self, cur, dist):
        delay = time.time() - self.start
        if delay > 0.08:
            return
        now = len(self.visited)
        # print(cur, dist, now)
        if not self.best or now > self.best:
            # print(self.path)
            self.best_path = self.path.copy()
            self.best = now
        if dist == MAX_DISTANCE:
            return

        neighbors = self.graph.get_neighbors_with_not_discovered_nodes(cur)
        # print(neighbors)
        for next_node in neighbors:
            vis = set(get_view_distance_neighbors(next_node, self.graph.dim[0], self.graph.dim[1], 4))
            not_changed = self.visited.copy()
            if len(vis & not_changed) == len(vis):
                continue
            self.visited |= vis
            self.path[dist] = next_node
            self.bt(next_node, dist + 1)
            self.visited = not_changed


@time_measure
def solve_bt(graph, pos):
    self = BT(graph, pos)
    self.bt(pos, 0)
    if not self.best_path:
        return 0
    return Direction.get_value(self.graph.step(pos, self.best_path[0]))
