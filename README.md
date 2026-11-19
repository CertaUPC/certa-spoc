# Certa. Prueba de concepto del objetivo específico 1

Artefactos de la prueba de concepto que sustenta el objetivo específico primero
del proyecto Certa: la selección de la clase de modelo de lenguaje y la
verificación del anclaje de la justificación, medidas sobre un conjunto de
referencia con verdad conocida. Los datos permiten recalcular cada cifra
informada sobre los mismos hallazgos.

## La corrida

- Fecha (UTC): 2026-09-15T05:42:17
- Identificador de ejecución: `75aa891c-4e35-4ca8-84bf-7153fd3a7d48`
- Huella del lote: `4ecccf2c0bdc2df7d13fbba47538da53f6905c9379d7d237e08b2af64d382110`
- Conjunto: 100 hallazgos del OWASP Benchmark con verdad conocida (72 vulnerabilidades reales, 28 falsos positivos declarados)
- Analizador: Semgrep OSS, versión de reglas 1.177.0
- Consulta: temperatura 0.0, hasta 250 líneas de contexto, profundidad de llamadores y de llamados 2, versión del prompt `v1+9afd750e5880c1c6+656d34e6db69c90f`
- Modelos evaluados: `anthropic/claude-opus-5`, `google/gemini-3.8-flash`, `qwen/qwen3.8-27b`
- Repeticiones: 3 por modelo, 9 corridas en total
- Totales: 817 consultas, USD 9.6461, acuerdo entre corridas 0.7561

## Resultados por modelo (media de las tres repeticiones)

| Modelo | F1 | Precisión | Exhaustividad | Anclaje a la 1.ª | Cobertura | USD por corrida |
|---|---|---|---|---|---|---|
| anthropic/claude-opus-5 | 0.973 | 0.962 | 0.983 | 1.000 | 0.95 | 2.33 |
| google/gemini-3.8-flash | 0.953 | 0.969 | 0.939 | 1.000 | 0.89 | 0.45 |
| qwen/qwen3.8-27b | 0.969 | 0.946 | 0.994 | 0.996 | 0.86 | 0.43 |

El analizador sin asistencia, sobre el mismo conjunto, alcanza una exactitud de
0.821. El detalle por repetición está en `scorecard.csv`.

## Archivos

- `manifest.json`: configuración y huella de la corrida.
- `scorecard.csv`: métricas por modelo y repetición (F1, precisión, exhaustividad, anclaje, cobertura, costo, tokens).
- `verdicts.csv`: veredicto emitido por cada hallazgo, modelo y repetición.
- `verdicts_sin_filtro.csv`: veredictos antes del filtro determinista.
- `verificacion_independiente_anclaje.py`: comprueba, de forma independiente, que cada línea citada en la justificación existe en el contexto entregado al modelo.
- `lanzar_spoc.ps1`: guion de lanzamiento de la corrida.
- `BITACORA_SPOC.txt`: bitácora de la ejecución, con sus marcas de tiempo y las interrupciones que sobrevivió.

## Reproducir

La corrida se lanza con `lanzar_spoc.ps1`. La verificación del anclaje se vuelve
a comprobar con `verificacion_independiente_anclaje.py` sobre `verdicts.csv`. La
huella del lote registrada en `manifest.json` identifica el conjunto exacto de
hallazgos, de modo que cualquier cambio en los datos se detecta al recalcular.
El identificador de versión de cada modelo queda en `manifest.json`, sin el cual
los resultados no se podrían reproducir ante un cambio del proveedor.
