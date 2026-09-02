"""
Descarga del feed de sismos de las ultimas 24 horas en todo el mundo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

CACHE = Path(__file__).parent.parent / "cache"
CACHE.mkdir(exist_ok=True)

CABECERAS = {
    "User-Agent": "proyecciones-terremotos/1.0 (+https://github.com/adrianezd/proyecciones-terremotos)",
    "Accept": "application/json, text/plain, */*",
}

USGS_DIA = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


def _descargar(url: str, clave: str, params: dict | None = None) -> Any:
    fichero = CACHE / f"{clave}.json"
    try:
        r = httpx.get(url, params=params, headers=CABECERAS,
                      timeout=40.0, follow_redirects=True)
        r.raise_for_status()
        datos = r.json()
        fichero.write_text(json.dumps(datos), encoding="utf-8")
        print(f"  descargado  {clave}")
        return datos
    except Exception as e:
        if fichero.exists():
            print(f"  CACHE       {clave}  ({type(e).__name__})")
            return json.loads(fichero.read_text(encoding="utf-8"))
        print(f"  FALLO       {clave}  ({e})")
        return None


def sismos_hoy() -> list[dict]:
    datos = _descargar(USGS_DIA, "sismos-dia")
    if not isinstance(datos, dict):
        return []

    salida = []
    for f in datos.get("features", []):
        p = f.get("properties") or {}
        g = (f.get("geometry") or {}).get("coordinates") or [None, None, None]
        if not isinstance(p.get("mag"), (int, float)):
            continue
        salida.append({
            "mag": round(float(p["mag"]), 1),
            "lugar": p.get("place") or "",
            "tiempo": p.get("time"),
            "profundidad": round(g[2], 1) if len(g) > 2 and g[2] is not None else None,
            "url": p.get("url"),
        })
    return sorted(salida, key=lambda e: -(e["tiempo"] or 0))
