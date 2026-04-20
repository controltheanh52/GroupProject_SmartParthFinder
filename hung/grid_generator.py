import random
import math
# Assuming you renamed the method to add_vertex in your Graph class
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
    edge_direction = get_edge_direction(45, 25, 20)
    return distance, timeArr, edge_direction

def grid_generator(col_num, row_num):
    graph = Graph()
    
    for row in range(row_num):
        for col in range(col_num):
            # Changed to add_vertex
            vertex = graph.add_vertex(f'{row},{col}')
            
            neighbors = []
            if row < row_num - 1:
                neighbors.append(graph.add_vertex(f'{row+1},{col}'))
            if col < col_num - 1:
                neighbors.append(graph.add_vertex(f'{row},{col+1}'))
            
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
    print("\n--- GRID VISUALIZATION ---")
    print("Symbols: ↔ (Two-way), → (One-way), ← (Reversed), . (Blocked)")
    print("---------------------------\n")

    for r in range(row_num):
        # --- LINE 1: VERTICES AND HORIZONTAL EDGES ---
        vertex_line = ""
        for c in range(col_num):
            u_name = f"{r},{c}"
            u_obj = graph.vertices[u_name]
            
            # Vertex Block: Exactly 7 chars e.g. "( 0,0 )"
            vertex_line += f"({u_name:^5})" 
            
            if c < col_num - 1:
                v_obj = graph.vertices[f"{r},{c+1}"]
                fwd = v_obj in graph.adjList.get(u_obj, {})
                bwd = u_obj in graph.adjList.get(v_obj, {})
                
                if fwd and bwd: vertex_line += "  ↔  "
                elif fwd:      vertex_line += "  →  "
                elif bwd:      vertex_line += "  ←  "
                else:          vertex_line += "  .  "
        print(vertex_line)

        # --- LINE 2: VERTICAL EDGES ---
        if r < row_num - 1:
            vert_line = ""
            for c in range(col_num):
                u_obj = graph.vertices[f"{r},{c}"]
                v_obj = graph.vertices[f"{r+1},{c}"]
                
                fwd = v_obj in graph.adjList.get(u_obj, {})
                bwd = u_obj in graph.adjList.get(v_obj, {})
                
                if fwd and bwd: symbol = "↕"
                elif fwd:      symbol = "↓"
                elif bwd:      symbol = "↑"
                else:          symbol = "."
                
                vert_line += f"{symbol:^7}" + "     "
            print(vert_line)
            
    print("\n---------------------------\n")            
    
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