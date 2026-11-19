# -*- coding: utf-8 -*-
"""Audita el anclaje sin usar el verificador del sistema, y avisa si no se puede.

POR QUÉ EXISTE. La tasa de anclaje la calcula, durante la corrida, el
AnchorVerifier del propio producto. Es la única métrica del protocolo donde el
artefacto mide una propiedad de su propio mecanismo: en las demás el sistema
registra y quien juzga es la verdad del corpus, que es externa. Un defecto en
ese verificador produciría una tasa alta sin que nada lo delatara.

QUÉ HACE. Dos cosas, y la primera importa tanto como la segunda.

1. COMPRUEBA QUE LA CORRIDA SEA AUDITABLE. Para recalcular el anclaje hacen
   falta las líneas del fragmento que se entregó al modelo. Si no están, no hay
   nada que verificar y conviene saberlo el mismo día de la corrida y no meses
   después. El guion termina con código distinto de cero cuando la cobertura no
   llega al umbral, de modo que puede encadenarse detrás de un lote.

2. RECALCULA EL ANCLAJE. Lee las líneas del fragmento y las que la respuesta
   citó, y comprueba la inclusión de un conjunto en otro. No importa ninguna
   parte del código del producto, de modo que un defecto del verificador no
   puede propagarse hasta aquí.

QUÉ NO HACE. No comprueba que la lectura de esas líneas sea correcta. El
anclaje certifica que la referencia apunta a código entregado, no que su
interpretación sea acertada, y la distinción se mantiene también aquí.

USO
    py verificacion_independiente_anclaje.py [ruta.db] [--umbral 1.0]

Las líneas del fragmento son números y no código fuente, de manera que
conservarlas es compatible con la política de retención, que elimina el texto
recuperado cumplida su ventana.
"""
import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POR_OMISION = Path("D:/CHRISTOPHER/Universidad/Tesis/certa/codigo"
                   "/certa-backend-api/certa.db")


def lineas(valor):
    """Las líneas guardadas, vengan como JSON, como lista o como texto suelto."""
    if valor is None:
        return set()
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode("utf-8", "replace")
    texto = str(valor).strip()
    if not texto:
        return set()
    try:
        dato = json.loads(texto)
        if isinstance(dato, list):
            return {int(x) for x in dato}
    except (ValueError, TypeError):
        pass
    return {int(x) for x in texto.replace(",", " ").split()
            if x.strip("-").isdigit()}


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cli.add_argument("base", nargs="?", default=str(POR_OMISION))
    cli.add_argument("--umbral", type=float, default=1.0,
                     help="cobertura mínima de contextos para dar por "
                          "auditable la corrida, entre 0 y 1")
    args = cli.parse_args()

    base = Path(args.base)
    if not base.exists():
        print(f"No existe la base {base}")
        return 2

    con = sqlite3.connect(base)
    con.row_factory = sqlite3.Row
    print(f"base: {base.name}\n")

    # ---- 1. ¿Es auditable? -------------------------------------------------
    total = con.execute(
        "SELECT COUNT(*) FROM verdicts "
        "WHERE cited_lines IS NOT NULL AND cited_lines <> ''").fetchone()[0]
    con_contexto = con.execute("""
        SELECT COUNT(*) FROM verdicts v
          JOIN code_contexts c ON c.finding_id = v.finding_id
         WHERE v.cited_lines IS NOT NULL AND v.cited_lines <> ''
           AND c.available_lines IS NOT NULL AND c.available_lines <> ''
    """).fetchone()[0]

    cobertura = con_contexto / total if total else 0.0
    print("### Auditabilidad de la corrida")
    print(f"  veredictos con líneas citadas        {total}")
    print(f"  de esos, con contexto conservado     {con_contexto}")
    print(f"  cobertura                            {cobertura:.4f}")

    if cobertura < args.umbral:
        print(f"\n  AVISO: la cobertura no alcanza el umbral {args.umbral}.")
        print("  Sin las líneas del fragmento el anclaje no se puede")
        print("  reauditar. Conviene resolverlo antes de dar la corrida por")
        print("  buena: son números de línea, no código, de modo que")
        print("  conservarlos no afecta a la política de retención.")
        if con_contexto == 0:
            return 1

    # ---- 2. Recálculo ------------------------------------------------------
    filas = con.execute("""
        SELECT v.id, v.model, v.repetition, v.anchor_verified, v.cited_lines,
               c.available_lines, c.degraded_to_file
          FROM verdicts v
          JOIN code_contexts c ON c.finding_id = v.finding_id
         WHERE v.cited_lines IS NOT NULL AND v.cited_lines <> ''
    """).fetchall()

    por_modelo, anclados, degradados = Counter(), Counter(), Counter()
    discrepancias = []
    for f in filas:
        citadas, disponibles = lineas(f["cited_lines"]), lineas(f["available_lines"])
        if not citadas or not disponibles:
            continue
        ancla = citadas <= disponibles
        por_modelo[f["model"]] += 1
        anclados[f["model"]] += int(ancla)
        degradados[f["model"]] += int(bool(f["degraded_to_file"]))
        if int(bool(ancla)) != int(f["anchor_verified"] or 0):
            discrepancias.append((f["id"], f["model"], f["anchor_verified"],
                                  int(ancla), sorted(citadas - disponibles)[:6]))

    if not por_modelo:
        print("\nNo hay nada que recalcular.")
        return 1

    print("\n### Anclaje recalculado de manera independiente")
    print(f"  {'modelo':30} {'veredictos':>11} {'anclados':>9} {'tasa':>8} "
          f"{'degradados':>11}")
    for m in sorted(por_modelo):
        n, a = por_modelo[m], anclados[m]
        print(f"  {m:30} {n:>11} {a:>9} {a / n:>8.4f} {degradados[m]:>11}")
    n, a = sum(por_modelo.values()), sum(anclados.values())
    print(f"  {'TOTAL':30} {n:>11} {a:>9} {a / n:>8.4f} "
          f"{sum(degradados.values()):>11}")

    print(f"\n### Contraste con lo que registró el verificador del sistema")
    print(f"  discrepancias: {len(discrepancias)}")
    for d in discrepancias[:10]:
        print(f"    veredicto {d[0][:8]} modelo {d[1]}: sistema={d[2]} "
              f"independiente={d[3]} líneas fuera del fragmento={d[4]}")
    if not discrepancias:
        print("    Ninguna. Las dos mediciones coinciden sobre los datos "
              "conservados.")

    return 0 if (cobertura >= args.umbral and not discrepancias) else 1


if __name__ == "__main__":
    raise SystemExit(main())
