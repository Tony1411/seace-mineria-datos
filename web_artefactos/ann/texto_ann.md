# Módulo: Vecinos más cercanos (IVF y HNSW)

*Texto para la página web. Todas las cifras salen de los archivos JSON de esta carpeta.*

## Pregunta de interés
Dado un proceso, ¿cuáles son los 10 procesos con el texto más parecido, y se puede responder sin compararlo con todos los demás?

## Pipeline (de qué se compone)
1. **Textos.** Los mismos 163,208 textos distintos del módulo anterior.
2. **TF-IDF.** Cada texto pasa a ser un vector con el peso de sus palabras y pares de palabras: pesan más las palabras raras. Son 100,000 posiciones, casi todas en cero.
3. **Reducción.** Una proyección aleatoria lleva el vector a 512 números y se normaliza, de modo que el producto punto es la similitud coseno.
4. **Índices.** La búsqueda **exacta** compara la consulta con todos los vectores. **IVF** agrupa los vectores en 512 listas y revisa solo las `nprobe` más cercanas. **HNSW** arma un grafo de vecinos por capas y lo recorre con un esfuerzo `efSearch`.
5. **Medición.** Con 1,000 consultas se mide el **recall@10** (de los 10 vecinos reales, cuántos encontró el método) y el tiempo por consulta.

## Controles interactivos y cómo leerlos
**IVF: nprobe** (cuántas listas se revisan) y **HNSW: efSearch** (cuántos candidatos se mantienen). Más grande significa más preciso y más lento.
- **HNSW** con efSearch = 16 encuentra el 96.1% de los vecinos reales y es unas 20 veces más rápido que la búsqueda exacta (0.097 contra 1.91 ms). Con 64 llega a 97.9% (unas 6.6 veces más rápido) y con 256 a 98.9% (1.8 veces más rápido).
- **IVF** con nprobe = 1 es 35 veces más rápido, pero solo encuentra el 56.7%. Con nprobe = 32 llega a 83.8% y todavía es 1.5 veces más rápido. Desde nprobe = 64 (87.4%) ya es **más lento que la búsqueda exacta**, y con nprobe = 128 llega a 91.6% pero es 2.6 veces más lento.
- La línea de referencia es la búsqueda exacta: recall 1.0 y 1.91 ms por consulta.

## Interpretación (hallazgos)
- **HNSW gana claramente** con estos vectores. Incluso efSearch = 8 (93.1%, 0.069 ms) supera a nprobe = 128 de IVF (91.6%, 4.9 ms). IVF no funciona bien: una explicación probable, no verificada, es que los textos no forman grupos bien separados en 512 dimensiones.
- **Costos.** HNSW tarda más en construirse (89 s contra 10 s de IVF) y ocupa más (379 MB contra 334 MB de los vectores solos, un 13% más).
- **¿Vale la pena?** Con 163,208 textos, la búsqueda exacta ya tarda unos 2 ms por consulta. Para una consulta suelta no hace falta nada más. HNSW se justifica con muchas consultas o con muchos más datos: la búsqueda exacta crece en proporción al número de vectores, y HNSW en general crece mucho más lento (aquí no se midió).
- **Qué se pierde.** Con efSearch = 16 se pierde cerca del 4% de los vecinos reales.
- **La reducción conserva lo esencial.** Los 10 vecinos de los vectores reducidos coinciden en un 64% con los del TF-IDF completo, y el Jaccard medio del primer vecino es 0.502 contra 0.513 del TF-IDF completo (dos textos al azar dan unos 0.03).

## Limitaciones y cuidado con la lectura
- **TF-IDF compara palabras, no significado.** Una consulta sobre un "sistema de sonido para el proyecto mejoramiento de los servicios operativos o misionales..." tiene como primer vecino (0.70) una compra de equipos de cómputo, porque comparten la frase de plantilla del proyecto. Los parlantes de sonido, que sí se parecen en significado, quedan terceros (0.40).
- **Los milisegundos dependen de la máquina** donde se midieron (Colab, un solo hilo). La comparación entre métodos es la que importa.
- Las conclusiones valen para estos vectores y estos parámetros (512 dimensiones, 163 mil textos). Con otros datos podrían cambiar, sobre todo las de IVF.
