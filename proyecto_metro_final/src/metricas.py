import networkx as nx
import pandas as pd

def calcular_metricas(G):
    deg=dict(G.degree())
    bet=nx.betweenness_centrality(G,normalized=True)
    close=nx.closeness_centrality(G)
    comps=list(nx.connected_components(G))
    largest=G.subgraph(max(comps,key=len)).copy() if comps else G
    return {"nodes":G.number_of_nodes(),"edges":G.number_of_edges(),
            "avg_degree":sum(deg.values())/len(deg) if deg else 0,
            "density":nx.density(G),"components":len(comps),
            "largest_component":len(largest),
            "diameter":nx.diameter(largest) if len(largest)>1 else 0,
            "degrees":deg,"betweenness":bet,"closeness":close}

def ranking_estaciones(G,m=None,top=20):
    m=m or calcular_metricas(G)
    return pd.DataFrame([{"Estación":G.nodes[n].get("name",n),
                          "Grado":m["degrees"][n],
                          "Betweenness":m["betweenness"][n],
                          "Closeness":m["closeness"][n]} for n in G]).sort_values(
                              ["Betweenness","Grado"],ascending=False).head(top)
