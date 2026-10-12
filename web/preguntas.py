"""Las cinco preguntas de interés. La portada y la página de cierre usan esta misma lista."""

PREGUNTAS = [
    {
        "titulo": "1. ¿Qué cambió en las contrataciones después de la Ley 32069 (abril de 2025), "
                  "y qué parte parece cambio de régimen y no de comportamiento?",
        "relevancia": "Si no se separa el antes y el después, cualquier comparación entre años engaña.",
        "hallazgo": "Abril de 2025 tiene el máximo de la serie (9,356 procesos) y mayo cae a 3,646. "
                    "Coincide con la nueva ley y con la aparición de procedimientos nuevos. "
                    "La coincidencia en el tiempo no prueba causa.",
        "respuesta": "Abril de 2025 tiene 9,356 procesos y mayo 3,646. Coincide con la ley, pero no prueba causa.",
        "links": [("pages/0_EDA.py", "Análisis exploratorio")],
    },
    {
        "titulo": "2. ¿Cuánto del texto de las convocatorias se repite o sigue plantillas, "
                  "entre quiénes ocurre, y cómo encontrar rápido los textos más parecidos?",
        "relevancia": "Sirve para detectar compras en serie y duplicados, y para elegir casos que una persona revise.",
        "hallazgo": "El 96.6% de los pares casi iguales ocurre dentro de la misma entidad. "
                    "Un solo texto genérico se repite en 550 procesos de una entidad.",
        "respuesta": "El 96.6% de los pares casi iguales es de la misma entidad. MinHash y LSH los encuentran "
                     "revisando el 0.005% de los pares posibles, y HNSW busca vecinos unas 20 veces más rápido.",
        "links": [("pages/4_Minhash_LSH.py", "MinHash y LSH"),
                  ("pages/5_Casos_de_Textos.py", "Casos de textos"),
                  ("pages/6_ANN.py", "Vecinos aproximados (ANN)")],
    },
    {
        "titulo": "3. ¿Qué tan recurrentes y concentrados están los postores, "
                  "y se puede medirlo con poca memoria mientras llegan los datos?",
        "relevancia": "La concentración de proveedores es un tema clásico de contratación pública.",
        "hallazgo": "El 90.9% de las participaciones es de postores que ya habían aparecido antes. "
                    "Los 10 postores más frecuentes suman solo el 2.7% de las participaciones. "
                    "Esto describe RUC, no poder de mercado.",
        "respuesta": "El 90.9% de las participaciones son reapariciones y el top 10 suma el 2.7%. "
                     "Un Bloom Filter y un Count-Min Sketch lo miden con muy poca memoria y poco error.",
        "links": [("pages/1_Bloom_Filter.py", "Bloom Filter"),
                  ("pages/2_Count_Min_Sketch.py", "Count-Min Sketch"),
                  ("pages/3_DGIM.py", "DGIM (desiertos recientes)")],
    },
    {
        "titulo": "4. ¿Qué características de un proceso se asocian con que quede desierto o nulo?",
        "relevancia": "Cerca del 18% de los procesos termina desierto (12.05%) o nulo (5.66%). "
                      "Entender dónde falla la competencia sirve para mejorar las convocatorias.",
        "hallazgo": "Con cero postores registrados, la frecuencia de DESIERTO sube de 12.88% a 35.45%. "
                    "Son asociaciones, no causas.",
        "respuesta": "Con cero postores, DESIERTO sube de 12.88% a 35.45%. En municipalidades con cero postores, "
                     "NULO llega a 59.5%. Son asociaciones, no causas.",
        "links": [("pages/8_Apriori_FPGrowth.py", "Apriori y FP-Growth"),
                  ("pages/7_Reglas_Asociacion.py", "Reglas de asociación")],
    },
    {
        "titulo": "5. ¿Cuánta precisión se pierde al usar métodos aproximados y cuándo vale la pena?",
        "relevancia": "Decide qué técnica usar según el volumen de datos.",
        "hallazgo": "LSH es imprescindible (revisa el 0.005% de los pares posibles). "
                    "HNSW pierde 3.9% de los vecinos y es 20 veces más rápido. "
                    "Bloom, Count-Min Sketch y DGIM no hacían falta a esta escala.",
        "respuesta": "LSH sí vale la pena. HNSW pierde 3.9% de los vecinos y gana 20 veces en velocidad. "
                     "Bloom, Count-Min Sketch y DGIM no hacían falta a esta escala.",
        "links": [("pages/9_Spark_Particiones.py", "Spark: RDD, DataFrame y particiones"),
                  ("pages/10_Discusion_Critica.py", "Discusión crítica (Parte VI)")],
    },
]
