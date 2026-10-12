# Proyecto SEACE — Transferencia de la web

## Estado
Aplicación Streamlit integrada con:
- Portada con preguntas de interés
- Datos, KDD y limpieza
- EDA
- Bloom Filter
- Count-Min Sketch
- DGIM
- MinHash y LSH
- Casos de similitud
- ANN (resultados actualizados)
- Reglas de asociación
- Apriori y FP-Growth
- Comparaciones Spark
- Discusión crítica (Parte VI)

## Ejecutar
1. Crear un entorno Python.
2. Instalar: pip install -r requirements.txt (notebooks: requirements-notebooks.txt)
3. Ejecutar: streamlit run web/app.py

## Estructura
- web/: aplicación Streamlit
- artifacts/: CSV de los experimentos
- web_artefactos/: JSON de similitud, ANN, datos y discusión
- src/: implementaciones de algoritmos
- notebooks/: experimentos originales

## Pendientes
- Revisar y ajustar la discusión crítica (web_artefactos/discusion/discusion_critica.md).
- Verificar la equivalencia Apriori vs FP-Growth (la comprobación dio False con max_k=5).
- Resolver la comparación antes y después de la ley en las reglas y revisar las reglas casi tautológicas.
- Ajustar las rutas fijas de los notebooks B_* (Path.home()/"dm").
- Completar nombres, enlace de la página y video en el README.
- Publicar la página o grabar una demostración.
- Preparar la presentación final.

## Importante
Los notebooks pueden requerir adaptar rutas locales.
Los artefactos son resultados precalculados.
La página no ejecuta Spark durante la interacción.