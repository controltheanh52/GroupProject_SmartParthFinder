import json

def load_queries(filename):
    with open(filename, "r") as f:
        queries = json.load(f)

    # json files always have content
    for q in queries:
        q.setdefault("avoid_nodes", [])
        q.setdefault("avoid_edges", [])

    return queries