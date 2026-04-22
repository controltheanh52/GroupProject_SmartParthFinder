import random
import math
from graphClass import Graph

def get_edge_direction(one, reversed_way, two):
    dice = random.random() 
    
    reversedChance = one + reversed_way
    twoChance = reversedChance + two
    
    if dice < (one/100):
        return "one-way"
    elif dice < (reversedChance/100): 
        return "reversed-way"
    elif dice < (twoChance/100): 
        return "two-way"
    else:     
        return "blocked"
  
def random_properties():
    # random distance
    distance = random.randint(2, 30)
    
    # random time array
    multipliers = [1,   1,   1,   1,   1,    1,    1.4,  1.4, 1.4, 1.2, 1.2, 1.2,\
                   1.1, 1.1, 1.1, 1.1, 1.35, 1.35, 1.35, 1.3, 1.3, 1.3, 1,   1   ]
    
    random_speed = random.randint(30, 50) # 30 to 50km/h
    base_time = (distance / random_speed) * 60
    base_time = math.ceil(base_time)
    
    timeArr = [base_time * mul for mul in multipliers]
    
    # edge direction
    edge_direction = get_edge_direction(0,0,100)
    return distance, timeArr, edge_direction

def grid_generator(col_num, row_num, exist_chance = 1, diagonals = False, random_degree = False):
    graph = Graph()
    
    for row in range(row_num):
        for col in range(col_num):
            if random.random < exist_chance:
                graph.add_vertex(f'{row},{col}')

    for row in range(row_num):
        for col in range(col_num):
            vertex = graph.vertices[f'{row},{col}']
            
            directions = [(1, 0), (0, 1)] # Down, Right
            if diagonals:
                directions += [(1, 1), (-1, 1)] # Down-Right, Up-Right
                
            neighbors = []
            for row_direction, col_direction in directions:
                neighbor_row = row + row_direction
                neighbor_column = col + col_direction
                
                if 0 <= neighbor_row < row_num and 0 <= neighbor_column < col_num:
                    # use get for safety
                    neighbor_vertex = graph.vertices.get(f'{neighbor_row},{neighbor_column}')
                    if neighbor_vertex:
                        neighbors.append(neighbor_vertex)  
            
            for vertex2 in neighbors:
                distance, timeArr, direction = random_properties() 
                
                if direction == "one-way":
                    graph.add_edge(vertex, vertex2, distance, timeArr)
                elif direction == "reversed-way":
                    graph.add_edge(vertex2, vertex, distance, timeArr)
                elif direction == "two-way": 
                    graph.add_edge(vertex, vertex2, distance, timeArr, True)
                    
    return graph

def display_grid(graph, row_num, col_num):
    print("--- GRID VISUALIZATION---")
    print("Symbols: ↔ (Two-way), → (One-way), ← (Reversed), . (Blocked)")
    print("-------------------------------------------\n")

    # Configuration for fixed widths
    NODE_W = 7
    EDGE_W = 9

    for r in range(row_num):
        # --- LINE 1: NODES AND HORIZONTAL EDGES ---
        node_line = ""
        for c in range(col_num):
            u_name = f"{r},{c}"
            u_obj = graph.vertices[u_name]
            
            # Format Node: e.g., "( 0,0 )" padded to 7 chars
            node_label = f"({u_name})"
            node_line += f"{node_label:^{NODE_W}}" 
            
            if c < col_num - 1:
                v_obj = graph.vertices[f"{r},{c+1}"]
                edge_fwd = graph.adjList.get(u_obj, {}).get(v_obj)
                edge_bwd = graph.adjList.get(v_obj, {}).get(u_obj)
                
                # Format Edge: e.g., "< 10.5 >" padded to 9 chars
                if edge_fwd and edge_bwd:
                    e_str = f"<{edge_fwd.distance:^3.1f}>"
                elif edge_fwd:
                    e_str = f"-{edge_fwd.distance:^3.1f}>"
                elif edge_bwd:
                    e_str = f"<{edge_bwd.distance:^3.1f}-"
                else:
                    e_str = " . "
                
                node_line += f"{e_str:^{EDGE_W}}"
        print(node_line)

        # --- LINE 2: VERTICAL EDGES ---
        if r < row_num - 1:
            vert_line = ""
            for c in range(col_num):
                u_obj = graph.vertices[f"{r},{c}"]
                v_obj = graph.vertices[f"{r+1},{c}"]
                
                edge_down = graph.adjList.get(u_obj, {}).get(v_obj)
                edge_up = graph.adjList.get(v_obj, {}).get(u_obj)
                
                # Format Vertical: e.g., "v 5.0 ^" padded to 7 chars
                if edge_down and edge_up:
                    v_str = f"v{edge_down.distance:^3.1f}^"
                elif edge_down:
                    v_str = f"{edge_down.distance:^3.1f}v"
                elif edge_up:
                    v_str = f"^{edge_up.distance:^3.1f}"
                else:
                    v_str = "|"
                
                # Add the vertical symbol centered under the node, 
                # then add whitespace matching the horizontal edge width
                vert_line += f"{v_str:^{NODE_W}}" + (" " * EDGE_W)
            print(vert_line)
            
    print("\n-------------------------------------------\n") 
    
if __name__ == "__main__":
    rows, cols = 5, 5
    my_grid = grid_generator(cols, rows)

    display_grid(my_grid, rows, cols)

    # Testing specific vertices
    test_u = my_grid.vertices["0,0"]
    test_v = my_grid.vertices["0,1"]

    if test_v in my_grid.adjList[test_u]:
        edge = my_grid.adjList[test_u][test_v]
        print(f"Edge (0,0)->(0,1) exists!")
        print(f"Distance: {edge.distance} km")
        print(f"9 AM Travel Time: {edge.timeArr[9]} mins")
    else:
        print("Edge (0,0)->(0,1) is blocked or one-way reversed.")