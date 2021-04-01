import math

from graph import Graph


def get_tsp(src_pos, dest_pos, graph):
    shortest_path_info = graph.find_all_shortest_path()
    nodes = graph.get_random_nodes()

    bread_tsp = make_tsp(nodes[src_pos], nodes[dest_pos], 'bread', shortest_path_info, nodes)
    grass_tsp = make_tsp(nodes[src_pos], nodes[dest_pos], 'grass', shortest_path_info, nodes)

    return {
        'bread_tsp': bread_tsp,
        'grass_tsp': grass_tsp,
    }


def make_dist_graph(src, dest, name_of_node_object, shortest_path_info, dist_nodes):
    number_of_dist_vertex = len(dist_nodes) + 2

    dist = [number_of_dist_vertex * [-math.inf] for _ in range(number_of_dist_vertex)]

    dist_src = 0
    dist_dest = number_of_dist_vertex - 1

    dist[dist_src][dist_dest] = getattr(src, f'{name_of_node_object}_value')(src, dest, shortest_path_info)
    for i in range(number_of_dist_vertex - 2):
        node1 = dist_nodes[i]
        dist[dist_src][i] = getattr(node1, f'{name_of_node_object}_value')(src, dest, shortest_path_info)
        dist[i][dist_dest] = getattr(dest, f'{name_of_node_object}_value')(node1, dest, shortest_path_info)
        for j in range(number_of_dist_vertex - 2):
            node2 = dist_nodes[j]
            dist[i + 1][j + 1] = getattr(node2, f'{name_of_node_object}_value')(node1, dest, shortest_path_info)

    return dist


def make_tsp(src, dest, name_of_node_object, shortest_path_info, nodes):
    dist_nodes = getattr(Graph, f'get_nearest_{name_of_node_object}_nodes')(src, dest, nodes, shortest_path_info)
    dist = make_dist_graph(src, dest, name_of_node_object, shortest_path_info, dist_nodes)

    number_of_dist_vertex = len(dist_nodes) + 2

    dp = [number_of_dist_vertex * [-math.inf] for _ in range(1 << number_of_dist_vertex)]
    dp_path = [number_of_dist_vertex * [-1] for _ in range(1 << number_of_dist_vertex)]

    dist_src = 0

    for i in range(1 << number_of_dist_vertex):
        vertices = []
        for j in range(number_of_dist_vertex):
            if i & (1 << j):
                vertices.append(j)
        if len(vertices) == 1 and dist_src not in vertices:
            continue
        elif len(vertices) == 1:
            dp[i][dist_src] = 0
            dp_path[i][dist_src] = dist_src
        for j in vertices:
            for k in vertices:
                if j == k:
                    continue
                value = dp[i - (1 << j)][k] + dist[k][j]
                if dp[i][j] < value:
                    dp[i][j] = value
                    dp_path[i][j] = k

    return {
        'dp': dp,
        'dp_path': dp_path
    }
