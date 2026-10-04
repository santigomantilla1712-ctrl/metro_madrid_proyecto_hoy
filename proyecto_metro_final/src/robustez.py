import networkx as nx

def analizar_robustez(G):
    return {"connected":nx.is_connected(G) if G else False,
            "components":nx.number_connected_components(G) if G else 0,
            "articulation_points":list(nx.articulation_points(G)),
            "bridges":list(nx.bridges(G))}

def simular_fallo_estacion(G,station):
    H=G.copy(); H.remove_node(station)
    return {"station":station,"connected_after":nx.is_connected(H) if H else False,
            "components_after":nx.number_connected_components(H) if H else 0,
            "largest_component_after":max((len(c) for c in nx.connected_components(H)),default=0),
            "removed_degree":G.degree(station)}
