import math
import networkx as nx

def haversine(lat1,lon1,lat2,lon2):
    R=6371.0
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def construir_grafo(datos):
    G=nx.Graph()
    for r in datos["stations"].itertuples():
        G.add_node(r.station_id,name=r.name,lat=float(r.lat),lon=float(r.lon))
    for r in datos["edges"].itertuples():
        G.add_edge(r.u,r.v,lines=list(r.lines))
    for u,v,d in G.edges(data=True):
        d["distance_km"]=haversine(G.nodes[u]["lat"],G.nodes[u]["lon"],
                                    G.nodes[v]["lat"],G.nodes[v]["lon"])
        d["weight"]=max(d["distance_km"],0.05)
    return G

def construir_grafo_estado(G):
    H=nx.Graph()
    for u,v,d in G.edges(data=True):
        for line in d.get("lines",[]):
            H.add_node((u,line),station=u,line=line,**G.nodes[u])
            H.add_node((v,line),station=v,line=line,**G.nodes[v])
            H.add_edge((u,line),(v,line),weight=max(0.05,d["distance_km"]*2),kind="metro")
    by={}
    for n in H: by.setdefault(n[0],[]).append(n)
    for station,nodes in by.items():
        for i,a in enumerate(nodes):
            for b in nodes[i+1:]:
                if a[1]!=b[1]:
                    H.add_edge(a,b,weight=4.0,kind="transfer",station=station)
    return H
