import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import json_p2

st.title("Proyecto 2 · Recomendador por contenido")

d = json_p2("contenido_ejemplos.json")
m, h = d["meta"], d["meta"]["hnsw"]

encabezado(
    "¿Se puede recomendar a una entidad proveedores nuevos solo por lo que venden, sin mirar quién contrata a quién?",
    f"Sí, con límites. Cada proveedor se resume en un vector de texto ({m['dim']} números) y la entidad en el promedio de sus proveedores; "
    f"el índice HNSW encuentra los más cercanos con {100 * h['recall_10_vs_exacta']:.1f}% de acierto frente a la búsqueda exacta. En el test acierta ~3.6 veces más que recomendar los más populares.",
)

st.markdown(f"""
### Cómo funciona
1. **Texto del proveedor:** se juntan los títulos y descripciones de hasta {m['textos_por_proveedor_max']} procesos que ganó antes del {m['fecha_corte']}.
2. **TF-IDF:** cada palabra (y par de palabras) pesa más si aparece mucho en ese texto y poco en los demás.
3. **Proyección aleatoria a {m['dim']} números:** acorta el vector conservando casi las distancias.
   Tras reducir, {100 * m['solape_tfidf_vs_512']:.0f}% de los 10 vecinos más parecidos coinciden con los del vector completo.
4. **HNSW:** índice de vecinos aproximados (M={h['M']}, efConstruction={h['efConstruction']}, efSearch={h['efSearch']}); encuentra el {100 * h['recall_10_vs_exacta']:.1f}% de los vecinos que halla la búsqueda exacta.
5. **Perfil de la entidad:** promedio de los vectores de sus proveedores. Se recomiendan los más cercanos que la entidad **todavía no tiene**.

Se indexaron **{m['proveedores_indexados']:,}** proveedores y se recomendó a **{m['entidades']:,}** entidades.
""")

st.subheader("Ejemplos")
ej = d["ejemplos"]
i = st.selectbox("Entidad", range(len(ej)), format_func=lambda i: ej[i]["entidad"])
e = ej[i]
st.markdown(f"**{e['entidad']}** · {e['tipo']} · {e['departamento']}")
a, b = st.columns(2)
with a:
    st.markdown("**Con quién ya trabaja** (los 5 con más adjudicaciones)")
    for p in e["proveedores_actuales"]:
        st.markdown(f"- {p['nombre']} — {p['n_adjudicaciones']} adj.  \n  <small>{p['palabras_clave']}</small>", unsafe_allow_html=True)
with b:
    st.markdown("**Recomendados** (similitud coseno: 1 = idénticos)")
    for p in e["recomendados"]:
        st.markdown(f"- {p['nombre']} — {p['score']:.2f}  \n  <small>{p['palabras_clave']}</small>", unsafe_allow_html=True)

with st.expander("Límites"):
    st.markdown("""
- Solo se usan los procesos **ganados** con texto; la mediana es de 4 procesos por proveedor, así que muchos perfiles son poco estables.
- Se recomienda por parecido, no por conveniencia: si una entidad compra de todo, el perfil promedio queda "al medio" y no se parece a nada.
- Los consorcios están fuera. Los nombres de personas naturales se enmascaran.
""")

st.caption("Notebook: `P2_04_Recomendador_Contenido` (scikit-learn + FAISS). Los resultados sobre el test están en la página de evaluación.")
siguiente("pages/15_Rec_Colaborativo.py", "Recomendador colaborativo")
