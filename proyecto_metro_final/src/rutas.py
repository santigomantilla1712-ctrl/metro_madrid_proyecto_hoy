import networkx as nx
from .grafo import construir_grafo_estado

def bfs(G,origen,destino):
    return nx.shortest_path(G,origen,destino)

def dijkstra(G,origen,destino,weight="weight"):
    return nx.shortest_path(G,origen,destino,weight=weight)

def describir_ruta(G,ruta):
    return {
        "node_ids":ruta,
        "stations":[G.nodes[n].get("name",n) for n in ruta],
        "stops":max(0,len(ruta)-1),
        "distance_km":sum(G.edges[a,b].get("distance_km",0) for a,b in zip(ruta,ruta[1:]))
    }

def ruta_con_transbordos(G,origen,destino):
    H=construir_grafo_estado(G)
    origins=[n for n in H if n[0]==origen]
    dests=[n for n in H if n[0]==destino]
    best=None
    for o in origins:
        for d in dests:
            try:
                p=nx.shortest_path(H,o,d,weight="weight")
                cost=nx.path_weight(H,p,"weight")
                if best is None or cost<best[0]: best=(cost,p)
            except nx.NetworkXNoPath: pass
    if best is None: raise nx.NetworkXNoPath("No existe ruta.")
    stations=[]; transfers=0; last=None
    for station,line in best[1]:
        if not stations or stations[-1]!=station: stations.append(station)
        if last is not None and line!=last: transfers+=1
        last=line
    return {"stations":[G.nodes[s]["name"] for s in stations],"node_ids":stations,
            "transfers":transfers,"cost":best[0],"states":best[1]}
