import plotly.graph_objects as go

COLORS={"1":"#007EBA","2":"#E91E63","3":"#FFD800","4":"#704F38",
"5":"#9B0058","6":"#808080","7":"#FF7F00","8":"#F07F3C",
"9":"#8A2BE2","10":"#003CA6","11":"#00A88E","12":"#B3B300","R":"#008C95"}

def mapa_grafo(G,highlight=None):
    highlight=set(highlight or [])
    fig=go.Figure()
    for u,v,d in G.edges(data=True):
        line=str(d.get("lines",["?"])[0])
        fig.add_trace(go.Scattermap(lon=[G.nodes[u]["lon"],G.nodes[v]["lon"]],
            lat=[G.nodes[u]["lat"],G.nodes[v]["lat"]],mode="lines",
            line={"width":3,"color":COLORS.get(line,"#666")},
            hoverinfo="none",showlegend=False))
    fig.add_trace(go.Scattermap(
        lon=[G.nodes[n]["lon"] for n in G],lat=[G.nodes[n]["lat"] for n in G],
        mode="markers",marker={"size":[12 if n in highlight else 6 for n in G]},
        text=[f"{G.nodes[n]['name']}<br>Grado: {G.degree(n)}" for n in G],
        hovertemplate="%{text}<extra></extra>",showlegend=False))
    fig.update_layout(map={"style":"open-street-map","center":{"lat":40.4168,"lon":-3.7038},"zoom":9.7},
                      margin={"l":0,"r":0,"t":35,"b":0},height=700)
    return fig
