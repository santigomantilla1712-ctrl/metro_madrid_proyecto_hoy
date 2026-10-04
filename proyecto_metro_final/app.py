import streamlit as st
import pandas as pd
from src.datos import cargar_datos,LINE_NAMES
from src.grafo import construir_grafo
from src.metricas import calcular_metricas,ranking_estaciones
from src.rutas import bfs,dijkstra,ruta_con_transbordos,describir_ruta
from src.robustez import analizar_robustez,simular_fallo_estacion
from src.visualizacion import mapa_grafo

st.set_page_config(page_title="Metro Madrid | Teoría de Grafos",page_icon="🚇",layout="wide")
st.title("🚇 Metro de Madrid — Teoría de Grafos")
st.caption("13 líneas · datos GTFS · NetworkX · rutas · métricas · robustez")

@st.cache_data
def load(): return cargar_datos()
@st.cache_resource
def graph(data): return construir_grafo(data)

try:
    data=load(); G=graph(data); M=calcular_metricas(G); R=analizar_robustez(G)
except Exception as e:
    st.error("No se pudo cargar el GTFS o construir el grafo.")
    st.exception(e); st.stop()

page=st.sidebar.radio("Módulo",["Inicio","Mapa","Rutas","Métricas","Robustez","Datos"])

if page=="Inicio":
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Estaciones",G.number_of_nodes()); c2.metric("Conexiones",G.number_of_edges())
    c3.metric("Componentes",M["components"]); c4.metric("Diámetro",M["diameter"])
    st.markdown("""### Modelo
**Estaciones = nodos** · **Conexiones = aristas** · **líneas = atributos**.
El sistema implementa BFS, Dijkstra, métricas de teoría de grafos y análisis de robustez.
""")
    st.info("Fuente primaria: GTFS de la red de Metro publicado por CRTM. Se contempla un espejo público como respaldo.")

elif page=="Mapa":
    st.subheader("Mapa interactivo de la red")
    st.plotly_chart(mapa_grafo(G),use_container_width=True)

elif page=="Rutas":
    names={d["name"]:n for n,d in G.nodes(data=True)}
    opts=sorted(names)
    o=st.selectbox("Origen",opts); d=st.selectbox("Destino",opts,index=min(1,len(opts)-1))
    method=st.radio("Algoritmo",["BFS — menos paradas","Dijkstra — menor distancia","Dijkstra — transbordos"])
    if st.button("Calcular",type="primary"):
        try:
            if method.startswith("BFS"): res=describir_ruta(G,bfs(G,names[o],names[d]))
            elif method.startswith("Dijkstra — menor distancia"): res=describir_ruta(G,dijkstra(G,names[o],names[d]))
            else: res=ruta_con_transbordos(G,names[o],names[d])
            st.success(f"Ruta encontrada · {res.get('stops',len(res['stations'])-1)} paradas")
            st.write(" → ".join(res["stations"]))
            if "distance_km" in res: st.metric("Distancia aproximada",f"{res['distance_km']:.2f} km")
            if "transfers" in res: st.metric("Transbordos",res["transfers"])
        except Exception as e: st.error(str(e))

elif page=="Métricas":
    a,b,c,d=st.columns(4)
    a.metric("Grado promedio",f"{M['avg_degree']:.3f}"); b.metric("Densidad",f"{M['density']:.6f}")
    c.metric("Diámetro",M["diameter"]); d.metric("Betweenness máxima",f"{max(M['betweenness'].values()):.5f}")
    st.dataframe(ranking_estaciones(G,M),use_container_width=True,hide_index=True)

elif page=="Robustez":
    a,b,c=st.columns(3)
    a.metric("Conectado","Sí" if R["connected"] else "No"); b.metric("Componentes",R["components"])
    c.metric("Puntos de articulación",len(R["articulation_points"]))
    st.write("### Estaciones críticas")
    st.write(", ".join(sorted(G.nodes[n]["name"] for n in R["articulation_points"])) or "Ninguna")
    names={d["name"]:n for n,d in G.nodes(data=True)}
    s=st.selectbox("Simular fallo",sorted(names))
    if st.button("Simular"):
        st.write(simular_fallo_estacion(G,names[s]))

else:
    st.subheader("13 líneas")
    st.dataframe(pd.DataFrame([{"Código":k,"Nombre":v} for k,v in LINE_NAMES.items()]),
                 hide_index=True,use_container_width=True)
    st.subheader("Estaciones")
    st.dataframe(data["stations"],hide_index=True,use_container_width=True)
    st.subheader("Conexiones")
    st.dataframe(data["edges"],hide_index=True,use_container_width=True)
