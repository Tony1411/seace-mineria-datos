import pandas as pd
import plotly.express as px
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Parte VI · Embeddings de nodos")

res = json_p2("p6_resumen.json")
nuc, par = res["nucleo"], res["parametros"]
met = csv_p2("emb_metricas.csv")
nodos = csv_p2("emb_nodos.csv")
tsne = csv_p2("emb_tsne.csv")

svd_m = met[met.embedding == "SVD"].iloc[0]
n2v = met[met.embedding != "SVD"]

encabezado(
    "¿Se puede representar a cada proveedor con un vector corto que conserve su posición en la red, y qué estructura captura?",
    f"Sí. De los 10 vecinos más cercanos de un proveedor, {100 * svd_m.pureza_vecinos:.0f}% (SVD) y entre {100 * n2v.pureza_vecinos.min():.0f}% y {100 * n2v.pureza_vecinos.max():.0f}% (node2vec) están en su misma comunidad de Louvain; al azar sería {100 * res['linea_base_pureza_azar']:.0f}%. "
    f"Ninguno de los dos gana con claridad, y p y q casi no cambian el resultado. Son vectores de similitud de posición en la red; no dicen nada sobre la conducta de ningún proveedor.",
)

st.markdown(f"""
### Qué se hizo
- **Núcleo:** los {nuc['nodos']:,} proveedores con al menos 120 participaciones y sus {nuc['aristas']:,} conexiones del grafo de co-participación (grado medio {nuc['grado_medio']:.0f}).
- **Embedding:** un vector de {par['D']} números por proveedor.
  - **SVD** (clase): descompone la matriz de conexiones y se queda con los {par['D']} conceptos más fuertes.
  - **node2vec** (clase): simula caminatas aleatorias por el grafo y aprende que los nodos que aparecen juntos tienen vectores parecidos. **p** y **q** sesgan la caminata.
- **Tareas:** agrupar con K-Means (K = {par['K']}, el número de comunidades grandes de Louvain) y visualizar con t-SNE.
""")

tab_mapa, tab_met, tab_vec, tab_lect = st.tabs(["Mapa t-SNE con p y q ajustables", "Métricas", "Vecinos más cercanos", "Qué estructura captura"])

with tab_mapa:
    c = st.columns(4)
    emb = c[0].radio("Embedding", ["node2vec", "SVD"], horizontal=True)
    p = c[1].select_slider("p (volver atrás)", options=[0.5, 1.0, 2.0], value=1.0, disabled=(emb == "SVD"),
                           help="p alto: evita volver al nodo anterior, explora más. p bajo: se queda cerca del origen.")
    q = c[2].select_slider("q (alejarse)", options=[0.5, 1.0, 2.0], value=0.5, disabled=(emb == "SVD"),
                           help="q alto: se queda cerca (tipo BFS, roles). q bajo: se aleja (tipo DFS, comunidades).")
    color = c[3].selectbox("Colorear por", ["comunidad", "departamento", "categoria"])
    conf = "svd" if emb == "SVD" else f"n2v_p{p}_q{q}"
    nombre_met = "SVD" if emb == "SVD" else f"node2vec (p={p}, q={q})"
    f = met[met.embedding == nombre_met].iloc[0]
    m = st.columns(3)
    m[0].metric("Coincidencia con Louvain (ARI)", f"{f.ARI_vs_louvain:.3f}", help="1 = los grupos de K-Means son iguales a las comunidades de Louvain; 0 = como el azar.")
    m[1].metric("Pureza de vecinos", f"{f.pureza_vecinos:.3f}", help="De los 10 vecinos más cercanos de cada proveedor, qué fracción está en su misma comunidad.")
    m[2].metric("Silueta de los grupos", f"{f.silueta:.3f}", help="Qué tan separados quedan los grupos de K-Means (−1 a 1).")
    d = tsne[tsne.config == conf].merge(nodos, on="proveedor_idx")
    if color == "comunidad":
        orden = sorted(d.comunidad.unique(), key=lambda s: (s == "Otras comunidades", s))
        d["comunidad"] = pd.Categorical(d.comunidad, categories=orden)
        d = d.sort_values("comunidad")
    paleta = px.colors.qualitative.Dark24
    cats = [c for c in d[color].dropna().unique() if c != "Otras comunidades"]
    mapa = {c: paleta[i % len(paleta)] for i, c in enumerate(sorted(cats, key=str))}
    mapa["Otras comunidades"] = "#bdbdbd"
    fig = px.scatter(d, x="x", y="y", color=color, color_discrete_map=mapa, hover_name="nombre",
                     hover_data={"x": False, "y": False, "ruc": True, "conexiones": True, "departamento": True, "categoria": True},
                     opacity=0.75, render_mode="webgl", height=620)
    fig.update_traces(marker=dict(size=5))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    st.plotly_chart(fig, width="stretch")
    st.markdown("""
**Cómo leerlo.** Cada punto es un proveedor. **Puntos cercanos = vectores parecidos** = proveedores que se cruzan con los mismos rivales.
t-SNE solo cuida los vecinos cercanos: la distancia entre grupos lejanos **no** es exacta. Fíjese si los colores forman **manchas separadas**.
Los RUC que no empiezan con 20 están enmascarados y los nombres de personas naturales se reemplazan.
""")

with tab_met:
    t = met.copy()
    t["embedding"] = t.embedding
    st.dataframe(t.drop(columns=["p", "q"]).rename(columns={"embedding": "Embedding", "ARI_vs_louvain": "ARI vs Louvain", "pureza_vecinos": "Pureza de vecinos", "silueta": "Silueta", "ARI_vs_departamento": "ARI vs departamento"}),
                 width="stretch", hide_index=True)
    g = n2v.pivot(index="q", columns="p", values="ARI_vs_louvain")
    h = n2v.pivot(index="q", columns="p", values="pureza_vecinos")
    a, b = st.columns(2)
    a.markdown("**ARI contra Louvain según p y q**")
    a.plotly_chart(px.imshow(g, text_auto=".3f", aspect="auto", labels=dict(x="p", y="q", color="ARI"), color_continuous_scale="Blues"), width="stretch")
    b.markdown("**Pureza de vecinos según p y q**")
    b.plotly_chart(px.imshow(h, text_auto=".3f", aspect="auto", labels=dict(x="p", y="q", color="Pureza"), color_continuous_scale="Blues"), width="stretch")
    st.markdown(f"""
**Cómo leerlo.**
- **ARI** y **pureza** se calculan contra las comunidades de Louvain de la Parte V, que **no usaron ningún embedding**. Línea base de pureza por azar: {res['linea_base_pureza_azar']:.3f}.
- **No hay un ganador claro:** node2vec tiene un poco más de pureza de vecinos; SVD tiene mayor ARI y mejor silueta.
- **p y q casi no cambian la pureza.** El ARI sí varía, pero **sin un patrón claro** (K-Means con varios grupos es sensible y se probó una sola semilla de caminatas). **No se puede afirmar** que un q bajo favorezca a las comunidades, como sugiere la teoría: aquí el núcleo es muy denso y las caminatas se parecen entre sí sin importar p y q. En la práctica, p y q se ajustan con *grid search*.
- **Región:** los grupos casi no coinciden con el departamento (ARI vs departamento cercano a 0): los embeddings capturan con quién se cruza el proveedor, que depende más del rubro que de la región.
- Se mide solo sobre los proveedores de las {par['K']} comunidades grandes ({par['proveedores_en_comunidades_grandes']:,} proveedores).
""")

with tab_vec:
    v = csv_p2("emb_vecinos.csv")
    prov = st.selectbox("Proveedor", sorted(v.proveedor.unique()))
    x = v[v.proveedor == prov]
    a, b = st.columns(2)
    for col, nombre in [(a, "node2vec"), (b, "SVD")]:
        s = x[x.embedding == nombre].sort_values("rango")
        col.markdown(f"**Sus 5 vecinos más cercanos en {nombre}**")
        s["misma_comunidad"] = s.misma_comunidad.map({True: "sí", False: "no"})
        col.dataframe(s[["rango", "vecino", "misma_comunidad"]].rename(columns={"rango": "Rango", "vecino": "Proveedor vecino", "misma_comunidad": "¿Misma comunidad?"}), width="stretch", hide_index=True)
    st.markdown("""
**Cómo leerlo.** Los vecinos son los proveedores con el vector más parecido: los que **se cruzan con los mismos rivales**. Que estén en la misma comunidad es esperable porque ambos métodos miran la misma red.
Que dos proveedores sean vecinos **no significa que se conozcan ni que hayan actuado juntos**.
""")

with tab_lect:
    cg = res["correlacion_con_grado"]
    ari3 = res.get("ari_vs_tipos_parte2")
    st.markdown(f"""
- **SVD refleja el tamaño del proveedor.** Sin normalizar, un componente llega a una correlación de {cg['svd_sin_normalizar']:.2f} con el número de conexiones (con node2vec: {cg['node2vec']:.2f}). Es la «dirección dominante» de la matriz, el mismo efecto que con HITS en la Parte IV.
- **Los dos embeddings reflejan con quién se cruza el proveedor** (su vecindario): sus vecinos más cercanos están en su misma comunidad, y también suelen coincidir en región y rubro.
- **Relación con las comunidades de la Parte V:** los grupos de los embeddings coinciden en buena parte con Louvain (ver ARI en la pestaña Métricas). Los embeddings sirven además para **visualizar** y comparar proveedores sin recalcular nada.
- **Relación con los tipos de proveedor de la Parte II** (que no miran la red): ARI de {ari3['SVD']} (SVD) y {ari3['node2vec']} (node2vec), es decir, **cercano a 0**. Son dos miradas distintas: los tipos agrupan por **cómo se comporta** el proveedor (cuánto gana, con cuántas entidades); los embeddings agrupan por **con quién se cruza**. El núcleo es casi todo del tipo de proveedores muy activos.
- **Límites:** el núcleo son solo los proveedores más activos; los embeddings son de la posición en la red, no de la conducta; y node2vec es *transductivo* (un vector por nodo, no sirve para un proveedor nuevo sin recalcular).
""")

st.warning("Dos proveedores con vectores parecidos **se cruzan con los mismos rivales**; eso no significa que se conozcan ni que hayan actuado juntos. Es una medida de similitud de posición, no de conducta.")

st.caption("Notebook: `P2_09_Embeddings` (local: SVD de scikit-learn, node2vec con caminatas propias y gensim, K-Means y t-SNE).")
siguiente("pages/20_Discusion_Proyecto2.py", "Análisis y discusión (Parte VII)")
