"""
Generador de esta pagina: terremotos del mundo en las ultimas 24 horas.

    python -m fuente.construir
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import datos
from .enlaces import HUB, MENU

AQUI = Path(__file__).parent
PROYECTO = AQUI.parent
SALIDA = PROYECTO / "docs"

BASE_URL = "https://adrianezd.github.io/proyecciones-terremotos"

entorno = Environment(
    loader=FileSystemLoader(AQUI / "plantillas"),
    autoescape=select_autoescape(["html"]),
)

HOY = dt.date.today().isoformat()


def json_seguro(obj) -> str:
    texto = json.dumps(obj, ensure_ascii=False)
    return (texto
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace(" ", "\\u2028")
            .replace(" ", "\\u2029"))


def escribir(plantilla: str, **contexto) -> None:
    destino = SALIDA / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)

    contexto.setdefault("raiz", "./")
    contexto.setdefault("menu", MENU)
    contexto.setdefault("hub", HUB)
    contexto.setdefault("base_url", BASE_URL)
    contexto.setdefault("ruta", "")
    contexto.setdefault("generado", HOY)

    destino.write_text(entorno.get_template(plantilla).render(**contexto), encoding="utf-8")
    print("  escrito     index.html")


def main() -> None:
    print("Construyendo: terremotos\n")

    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir(parents=True)
    shutil.copytree(PROYECTO / "estatico", SALIDA / "estatico")

    eventos = datos.sismos_hoy()
    if len(eventos) < 5:
        print("  SALTADA     terremotos (el feed diario vino vacio)")
        (SALIDA / ".nojekyll").write_text("", encoding="utf-8")
        return

    ahora = dt.datetime.now(dt.timezone.utc)
    horas = {h: 0 for h in range(24)}
    for e in eventos:
        if e["tiempo"]:
            t = dt.datetime.fromtimestamp(e["tiempo"] / 1000, dt.timezone.utc)
            delta = int((ahora - t).total_seconds() // 3600)
            if 0 <= delta < 24:
                horas[23 - delta] += 1

    tramos = [(0, 2, "menos de 2"), (2, 3, "2 a 3"), (3, 4, "3 a 4"),
              (4, 5, "4 a 5"), (5, 6, "5 a 6"), (6, 10, "6 o mas")]
    magnitudes = [{"tramo": etiqueta,
                   "cuantos": sum(1 for e in eventos if lo <= e["mag"] < hi)}
                  for lo, hi, etiqueta in tramos]

    hondos = [e["profundidad"] for e in eventos if e["profundidad"] is not None]

    escribir(
        "terremotos.html",
        acento="terremotos",
        titulo="Terremotos de las ultimas 24 horas en el mundo",
        descripcion="Todos los sismos registrados por el USGS en las ultimas "
                    "veinticuatro horas, con su magnitud y profundidad.",
        total=len(eventos),
        mayor=max(e["mag"] for e in eventos),
        hondo=round(max(hondos)) if hondos else "?",
        lista=sorted(eventos, key=lambda e: -e["mag"])[:20],
        datos_json=json_seguro({
            "horas": [{"etiqueta": f"-{23-h}h", "cuantos": horas[h]} for h in range(24)],
            "magnitudes": magnitudes,
        }),
    )

    (SALIDA / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    (SALIDA / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'\n  <url><loc>{BASE_URL}/</loc><lastmod>{HOY}</lastmod></url>\n</urlset>\n',
        encoding="utf-8",
    )
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    print("\nListo.")


if __name__ == "__main__":
    main()
