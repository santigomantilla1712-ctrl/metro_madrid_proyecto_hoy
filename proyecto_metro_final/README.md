# Metro de Madrid — Proyecto final

Proyecto académico basado en teoría de grafos y NetworkX.

## Ejecutar en VS Code

```powershell
python -m pip install -r requirements.txt
python main.py
streamlit run app.py
```

## Módulos
- `src/datos.py`: descarga y normalización GTFS.
- `src/grafo.py`: grafo físico y grafo estación-línea.
- `src/rutas.py`: BFS y Dijkstra.
- `src/metricas.py`: grado, betweenness, closeness, densidad y diámetro.
- `src/robustez.py`: conectividad, articulaciones y simulación de fallos.
- `src/visualizacion.py`: mapa interactivo.
- `app.py`: interfaz.
- `main.py`: validación por consola.

## Fuente
Fuente primaria: Consorcio Regional de Transportes de Madrid (CRTM), feed GTFS de Metro. El programa usa un espejo público como respaldo si la descarga primaria falla.

## Nota académica
La red se modela con estaciones como nodos y conexiones consecutivas como aristas. Las líneas se conservan como atributos de las aristas. Para rutas con transbordos se construye además un grafo de estados `(estación, línea)`.
