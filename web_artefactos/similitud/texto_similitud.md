# Módulo: Textos similares (MinHash y LSH)

*Texto para la página web. Todas las cifras salen de los archivos JSON de esta carpeta.*

## Pregunta de interés
¿Qué contrataciones públicas tienen descripciones casi iguales, y se pueden encontrar sin comparar los 13,318,344,028 pares posibles?

## Pipeline (de qué se compone)
1. **Textos.** Se toman los 163,208 textos distintos de las descripciones de procesos (normalizados: minúsculas, sin tildes). Los textos repetidos se analizan aparte.
2. **Shingles.** Cada texto se convierte en el conjunto de sus pares de palabras seguidas (unos 29 por texto).
3. **Jaccard.** La similitud entre dos textos es (shingles en común) ÷ (shingles en total), de 0 a 1.
4. **MinHash.** Cada texto se resume en una firma de 128 números. La fracción de posiciones en que dos firmas coinciden estima el Jaccard.
5. **LSH.** La firma se corta en *b* bandas de *r* números. Dos textos son candidatos si coinciden en alguna banda completa. Solo los candidatos se verifican con el Jaccard exacto.

## Controles interactivos y cómo leerlos
**MinHash: número de hashes (k).** Al subir k baja el error de la estimación.
- Con k = 8, el error medio es 0.115. Con k = 128 baja a 0.027.
- Con k = 128, el 95% de los pares tiene un error menor a 0.07. Con k = 16 ese valor es 0.20.
- El error baja con la raíz de k: para reducirlo a la mitad hay que cuadruplicar los hashes.
- El error depende del Jaccard del par. Es máximo cerca de 0.5 y mínimo cerca de 0 y de 1. La teoría dice que el error estándar es `sqrt(s·(1−s)/k)`.

**LSH: bandas (b) y filas (r).** Dos efectos opuestos:
- Con **filas pequeñas** casi no se pierden pares similares, pero hay muchos candidatos falsos. Por ejemplo, con 32 bandas x 4 filas hay 22,802 candidatos y solo el 7% es realmente similar (umbral 0.7).
- Con **filas grandes** casi todos los candidatos son buenos, pero se pierden muchos pares. Con 8 x 16 la precisión es 94% y el recall 19%.
- La curva en S, `1 − (1 − s^r)^b`, da la probabilidad de que un par con Jaccard *s* sea candidato. El umbral efectivo es aproximadamente `(1/b)^(1/r)`.
- Un **falso positivo** se descarta al verificar. Un **falso negativo** (un par similar que LSH no vio) es la pérdida real.

## Interpretación (hallazgos)
- **LSH revisó el 0.0052% de los pares** (693,144 de 13,318,344,028) con 21 bandas x 6 filas, y encontró **71,424 pares con Jaccard ≥ 0.7**, 27,170 con ≥ 0.8 y 3,916 con ≥ 0.9.
- Con esa configuración, en el subconjunto de evaluación se pierden 17 de 1,569 pares similares (recall 0.989).
- **Textos repetidos.** Los textos que más se repiten son del Organismo de Evaluación y Fiscalización Ambiental (OEFA). El más frecuente, "servicio de supervisión ambiental", aparece en 550 procesos entre diciembre de 2024 y marzo de 2025. Es una descripción genérica: no dice qué se compró, a quién ni por cuánto.
- **Pares casi iguales.** De los pares con Jaccard entre 0.8 y 1 cuyos textos pertenecen a una sola entidad, el **96.6% ocurre dentro de la misma entidad**, el 2.4% entre entidades de departamentos distintos y el 1.0% entre entidades del mismo departamento.
  - *Dentro de una entidad* son compras en serie o renovaciones que cambian un dato (el lugar, el año, el mercado) y algunos errores de tipeo.
  - *Entre entidades* son plantillas: la misma redacción con el nombre de la entidad cambiado.

## Limitaciones y cuidado con la lectura
- **Un texto parecido no prueba una irregularidad.** Puede ser una plantilla, una compra recurrente o un error de digitación. Los hallazgos sirven para agrupar compras, limpiar duplicados y elegir casos que una persona debe revisar. No sirven para acusar a nadie.
- Solo se compara el texto. No se miran montos, fechas ni proveedores.
- La precisión y el recall se midieron en un subconjunto (los 3,493 textos de EsSalud, 7,599 pares con Jaccard ≥ 0.5). En otras entidades pueden variar.
- Los 20 casos de cada tipo de `casos_similares.json` son una muestra balanceada, **no proporcional**: en los datos reales dominan los pares de la misma entidad.
