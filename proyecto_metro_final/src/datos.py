from __future__ import annotations

import zipfile
from pathlib import Path
import pandas as pd
import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datos"
CACHE_ZIP = DATA_DIR / "metro_gtfs.zip"

OFFICIAL_URL = (
    "https://crtm.maps.arcgis.com/sharing/rest/content/items/"
    "5c7f2951962540d69ffe8f640d94c246/data"
)

MIRROR_URL = (
    "https://files.mobilitydatabase.org/mdb-794/"
    "mdb-794-202505310235/mdb-794-202505310235.zip"
)

LINE_NAMES = {str(i): f"Línea {i}" for i in range(1, 13)}
LINE_NAMES["R"] = "Ramal Ópera–Príncipe Pío"


# ============================================================
# DESCARGA DEL GTFS
# ============================================================

def _download(url):
    response = requests.get(
        url,
        timeout=90,
        headers={"User-Agent": "ProyectoMetroMadrid/1.0"}
    )

    response.raise_for_status()

    if not response.content.startswith(b"PK"):
        raise ValueError("La respuesta no parece un ZIP GTFS.")

    return response.content


def descargar_gtfs(force=False):
    DATA_DIR.mkdir(exist_ok=True)

    # Si ya tenemos el GTFS, lo reutilizamos
    if (
        CACHE_ZIP.exists()
        and CACHE_ZIP.stat().st_size > 100_000
        and not force
    ):
        return CACHE_ZIP

    errores = []

    for url in (OFFICIAL_URL, MIRROR_URL):
        try:
            CACHE_ZIP.write_bytes(_download(url))
            return CACHE_ZIP

        except Exception as e:
            errores.append(str(e))

    raise RuntimeError(
        "No fue posible descargar el GTFS. Errores: "
        + " | ".join(errores)
    )


# ============================================================
# LECTURA DE ARCHIVOS GTFS
# ============================================================

def _read(zf, name):
    with zf.open(name) as file:
        return pd.read_csv(file, dtype=str)


def cargar_gtfs(force=False):
    path = descargar_gtfs(force)

    with zipfile.ZipFile(path) as zf:

        nombres = set(zf.namelist())

        required = {
            "stops.txt",
            "routes.txt",
            "trips.txt",
            "stop_times.txt"
        }

        missing = required - nombres

        if missing:
            raise ValueError(
                f"Faltan archivos GTFS: {sorted(missing)}"
            )

        datos = {
            archivo[:-4]: _read(zf, archivo)
            for archivo in required
        }

        for archivo in ("shapes.txt", "frequencies.txt"):
            if archivo in nombres:
                datos[archivo[:-4]] = _read(zf, archivo)

    return datos


# ============================================================
# PREPARAR DATOS
# ============================================================

def preparar_datos(gtfs):

    stops = gtfs["stops"].copy()
    routes = gtfs["routes"].copy()
    trips = gtfs["trips"].copy()
    stop_times = gtfs["stop_times"].copy()

    # --------------------------------------------------------
    # Normalizar columnas básicas
    # --------------------------------------------------------

    for columna in [
        "stop_id",
        "stop_name",
        "parent_station"
    ]:
        if columna not in stops.columns:
            stops[columna] = ""

    stops["stop_id"] = (
        stops["stop_id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    stops["stop_name"] = (
        stops["stop_name"]
        .fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    stops["parent_station"] = (
        stops["parent_station"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    stops["stop_lat"] = pd.to_numeric(
        stops["stop_lat"],
        errors="coerce"
    )

    stops["stop_lon"] = pd.to_numeric(
        stops["stop_lon"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # stop_times utiliza exclusivamente location_type = 0.
    # Por lo tanto, usamos únicamente esas paradas de servicio.
    #
    # Después agrupamos por nombre de estación.
    #
    # El GTFS tiene:
    #   290 paradas de servicio
    #   242 nombres de estación únicos
    #
    # Esto evita crear los 469 nodos incorrectos del modelo
    # anterior.
    # --------------------------------------------------------

    stops_servicio = stops[
        stops["stop_id"].isin(
            stop_times["stop_id"].astype(str)
        )
    ].copy()

    # Identificador lógico de la estación
    stops_servicio["station_key"] = (
        stops_servicio["stop_name"]
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Eliminar registros sin nombre
    stops_servicio = stops_servicio[
        stops_servicio["station_key"] != ""
    ].copy()

    # --------------------------------------------------------
    # Crear tabla de estaciones
    # --------------------------------------------------------

    estaciones = []

    for station_key, grupo in stops_servicio.groupby(
        "station_key",
        sort=True
    ):

        nombre = grupo.iloc[0]["stop_name"]

        lat = grupo["stop_lat"].mean()
        lon = grupo["stop_lon"].mean()

        estaciones.append({
            "station_id": station_key,
            "name": nombre,
            "lat": lat,
            "lon": lon
        })

    stations = pd.DataFrame(estaciones)

    stations = stations.dropna(
        subset=["lat", "lon"]
    )

    # --------------------------------------------------------
    # Relación viaje → línea
    # --------------------------------------------------------

    trips2 = trips[
        ["trip_id", "route_id"]
    ].drop_duplicates()

    stop_times2 = stop_times.merge(
        trips2,
        on="trip_id",
        how="inner"
    )

    # Orden correcto de las estaciones
    stop_times2["stop_sequence"] = pd.to_numeric(
        stop_times2["stop_sequence"],
        errors="coerce"
    )

    stop_times2 = stop_times2.dropna(
        subset=["stop_sequence"]
    )

    stop_times2 = stop_times2.sort_values(
        ["trip_id", "stop_sequence"]
    )

    # --------------------------------------------------------
    # Añadir información de la parada
    # --------------------------------------------------------

    stop_info = stops_servicio[
        [
            "stop_id",
            "station_key",
            "stop_name",
            "stop_lat",
            "stop_lon"
        ]
    ].drop_duplicates("stop_id")

    stop_times2 = stop_times2.merge(
        stop_info,
        on="stop_id",
        how="inner"
    )

    # --------------------------------------------------------
    # Obtener número/nombre de línea
    # --------------------------------------------------------

    route_short = (
        routes
        .set_index("route_id")["route_short_name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .to_dict()
    )

    stop_times2["line"] = (
        stop_times2["route_id"]
        .map(route_short)
        .fillna(
            stop_times2["route_id"].astype(str)
        )
    )

    # --------------------------------------------------------
    # Crear conexiones entre estaciones consecutivas
    # --------------------------------------------------------

    edges_temp = []

    for (trip_id, route_id), grupo in stop_times2.groupby(
        ["trip_id", "route_id"],
        sort=False
    ):

        grupo = grupo.sort_values(
            "stop_sequence"
        )

        valores = grupo[
            ["station_key", "line"]
        ].to_dict("records")

        for anterior, siguiente in zip(
            valores,
            valores[1:]
        ):

            u = str(anterior["station_key"])
            v = str(siguiente["station_key"])
            linea = str(anterior["line"])

            # Evitar una arista consigo misma
            if u == v:
                continue

            edges_temp.append({
                "u": u,
                "v": v,
                "line": linea
            })

    # --------------------------------------------------------
    # Consolidar conexiones repetidas
    # --------------------------------------------------------

    if not edges_temp:

        edges = pd.DataFrame(
            columns=["u", "v", "lines"]
        )

    else:

        edges_temp = pd.DataFrame(
            edges_temp
        )

        # Una arista no depende del sentido
        edges_temp["pair"] = edges_temp.apply(
            lambda fila: tuple(
                sorted(
                    [fila["u"], fila["v"]]
                )
            ),
            axis=1
        )

        filas = []

        for pair, grupo in edges_temp.groupby(
            "pair"
        ):

            filas.append({
                "u": pair[0],
                "v": pair[1],
                "lines": sorted(
                    set(
                        grupo["line"]
                        .astype(str)
                    )
                )
            })

        edges = pd.DataFrame(filas)

    # --------------------------------------------------------
    # Asociar líneas a cada estación
    # --------------------------------------------------------

    lineas_por_estacion = {}

    for station, grupo in stop_times2.groupby(
        "station_key"
    ):

        lineas_por_estacion[station] = sorted(
            set(
                grupo["line"]
                .astype(str)
            )
        )

    stations["lines"] = stations[
        "station_id"
    ].map(
        lineas_por_estacion
    )

    stations["lines"] = stations[
        "lines"
    ].apply(
        lambda x: x if isinstance(x, list) else []
    )

    # --------------------------------------------------------
    # Información útil para validación
    # --------------------------------------------------------

    print(
        f"GTFS procesado: "
        f"{len(stops_servicio)} paradas de servicio → "
        f"{len(stations)} estaciones"
    )

    print(
        f"Conexiones generadas: {len(edges)}"
    )

    return {
        "stations": stations,
        "edges": edges,
        "routes": routes,
        "stop_times": stop_times2,
        "gtfs": gtfs
    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def cargar_datos(force_download=False):
    return preparar_datos(
        cargar_gtfs(force_download)
    