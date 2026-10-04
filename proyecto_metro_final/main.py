from src.datos import cargar_datos
from src.grafo import construir_grafo
from src.metricas import calcular_metricas
from src.robustez import analizar_robustez

def main():
    print("="*65)
    print(" METRO DE MADRID — VALIDACIÓN DEL MODELO")
    print("="*65)
    datos=cargar_datos()
    G=construir_grafo(datos); m=calcular_metricas(G); r=analizar_robustez(G)
    print("Líneas modeladas: 13 (1-12 + R)")
    print("Estaciones:",G.number_of_nodes())
    print("Conexiones:",G.number_of_edges())
    print("Componentes:",m["components"])
    print("Diámetro:",m["diameter"])
    print("Densidad:",f"{m['density']:.6f}")
    print("Grado promedio:",f"{m['avg_degree']:.3f}")
    print("Puntos de articulación:",len(r["articulation_points"]))
    print("\nTop por grado:")
    for n,d in sorted(m["degrees"].items(),key=lambda x:x[1],reverse=True)[:10]:
        print(f"  {G.nodes[n]['name']}: {d}")
    print("\nTop por betweenness:")
    for n,d in sorted(m["betweenness"].items(),key=lambda x:x[1],reverse=True)[:10]:
        print(f"  {G.nodes[n]['name']}: {d:.5f}")
    print("\nListo. Ejecuta: streamlit run app.py")
if __name__=="__main__": main()
