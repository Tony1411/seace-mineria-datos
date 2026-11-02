import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Clustering de proveedores y entidades")

encabezado(
    "¿Qué tipos de proveedores existen según cómo contratan con el Estado, y cuáles se salen de su tipo?",
    "Hay tres tipos: los que no ganan (51%), los que ganan poco (37%) y los activos en varias entidades (13%). Con k = 5 se afinan dos de ellos: "
    "entre los que no ganan se separan los que «pasaron de largo» (4 meses activos) de los que «insisten» (20 meses). "
    "Se salen de su tipo los proveedores muy grandes y generalistas. Es una señal para revisar, no una acusación.",
)

st.markdown("""
### Cómo se hizo
Cada proveedor (o entidad) se resume en **9 características** (participaciones, tasa de éxito, adjudicaciones, monto total, entidades con las que trabaja, etc.).
Los montos y conteos se pasan a logaritmo, se **estandarizan** (promedio 0, desviación 1) y se reducen con **PCA** hasta explicar el 90% de la variación.
Luego se agrupa con tres métodos: **K-Means** (grupos redondos, hay que elegir *k*), **DBSCAN/HDBSCAN** (grupos por densidad, lo aislado es "ruido") y **jerárquico** (árbol de uniones).
""")

sujeto = st.radio("Qué se agrupa", ["proveedor", "entidad"], horizontal=True, format_func=lambda x: "Proveedores" if x == "proveedor" else "Entidades")
plural = "proveedores" if sujeto == "proveedor" else "entidades"

kk = csv_p2("kmeans_k.csv"); kk = kk[kk.sujeto == sujeto]
est = csv_p2("kmeans_estabilidad.csv"); est = est[est.sujeto == sujeto]
kdist = csv_p2("dbscan_kdist.csv"); kdist = kdist[kdist.sujeto == sujeto]
pca = csv_p2("pca_varianza.csv"); pca = pca[pca.sujeto == sujeto]
pts = csv_p2("puntos.csv"); pts = pts[pts.sujeto == sujeto].dropna(axis=1, how="all")
perf = csv_p2("kmeans_perfiles.csv"); perf = perf[perf.sujeto == sujeto]
out = csv_p2("outliers.csv"); out = out[out.sujeto == sujeto].dropna(axis=1, how="all")

tabs = st.tabs(["¿Cuántos grupos?", "Grupos (K-Means)", "Densidad", "Jerarquía", "Casos atípicos"])

# ---------------------------------------------------------------- k
with tabs[0]:
    c1, c2 = st.columns(2)
    f = px.line(kk, x="k", y="silueta", markers=True, labels={"k": "Número de grupos (k)", "silueta": "Silueta"})
    f.update_layout(title="Silueta (más alto = grupos más separados)")
    c1.plotly_chart(f, width="stretch")
    f = px.line(kk, x="k", y="inercia", markers=True, labels={"k": "Número de grupos (k)", "inercia": "Inercia"})
    f.update_layout(title="Inercia (suma de distancias al centro; siempre baja)")
    c2.plotly_chart(f, width="stretch")
    k_el = int(kk[kk.elegido].k.iloc[0])
    st.markdown(f"""
- **Silueta:** va de −1 a 1. Mide si cada punto está más cerca de su grupo que de los otros. Cerca de 1 = grupos claros; cerca de 0 = grupos mezclados.
- **Inercia:** suma de las distancias al cuadrado de cada punto al centro de su grupo. Siempre baja al subir k. El **codo** está donde la mejora se frena.
- **Estabilidad (ARI):** se parten los datos en dos mitades al azar, se agrupa cada mitad por separado y se compara el resultado (1 = grupos idénticos; 0 = tanto como el azar). Se repite 20 veces.
- **Elegido: k = {k_el}.** No es automático: el codo no es nítido, así que se miran los tres criterios y se explica la decisión (más abajo).
""")
    if "baja_inercia" in kk.columns:
        t = kk[["k", "inercia", "baja_inercia", "baja_pct", "silueta"]].copy()
        t["ritmo"] = (t.baja_inercia / t.baja_inercia.shift(1)).round(2)
        t = t[["k", "inercia", "baja_inercia", "baja_pct", "ritmo", "silueta"]].rename(columns={
            "inercia": "Inercia", "baja_inercia": "Cuánto baja respecto al k anterior", "baja_pct": "Baja (%)",
            "ritmo": "Ritmo (baja ÷ baja anterior)", "silueta": "Silueta"})
        st.markdown("**El codo, con números:** cuánto baja la inercia al agregar un grupo más.")
        st.dataframe(t.round(3), hide_index=True, width="stretch")
        st.caption("Si el ritmo cae mucho de un paso al siguiente (menor que 1), la mejora se frena: ahí hay un codo.")
    f = go.Figure()
    f.add_scatter(x=est.k, y=est.ari_medio, mode="lines+markers", name="ARI promedio")
    f.add_scatter(x=est.k, y=est.ari_peor, mode="lines+markers", name="ARI del peor caso", line=dict(dash="dot"))
    f.add_vline(x=k_el, line_dash="dash", annotation_text=f"elegido: k = {k_el}")
    f.update_layout(title="Estabilidad de los grupos (1 = idénticos al cambiar los datos)", xaxis_title="Número de grupos (k)", yaxis_title="ARI", yaxis_range=[0, 1.02])
    st.plotly_chart(f, width="stretch")
    if sujeto == "proveedor":
        st.info("**El codo no es único en proveedores:** la inercia se frena después de k = 3 y con fuerza después de k = 5. "
                "Se eligió **k = 5**: es el último antes de la caída fuerte, tiene la misma silueta que k = 4 (0.462 y 0.463) y es más estable (ARI 0.98; k = 4 es el menos estable, 0.93). "
                "Mira la pestaña «Grupos (K-Means)» con k = 3, 4 y 5: los dos extremos (los que no ganan y los activos en varias entidades) se mantienen; cambia cuántos detalles se separan.")
    if sujeto == "entidad":
        st.warning("En entidades la silueta (~0.25) y la estabilidad (~0.80) son **bajas**: los grupos se solapan y cambian si cambian los datos. "
                   "Son **tendencias**, no fronteras. Entre k = 5 y k = 6 casi no hay diferencia.")
    p = pca.assign(componente=pca.componente.astype(str))
    f = px.bar(p, x="componente", y="var_explicada", text=p.var_acumulada.map(lambda v: f"acum. {100*v:.0f}%"),
               labels={"componente": "Componente principal", "var_explicada": "Variación que explica"})
    f.update_layout(title=f"PCA: {len(p)} componentes explican {100*p.var_acumulada.max():.0f}% de la variación")
    st.plotly_chart(f, width="stretch")

# ---------------------------------------------------------------- kmeans
with tabs[1]:
    ks = sorted(kk.k.unique())
    k = st.select_slider("Número de grupos (k)", options=ks, value=int(kk[kk.elegido].k.iloc[0]))
    col = f"km_{k}"
    d = pts.assign(grupo=pts[col].astype(int).astype(str))
    f = px.scatter(d, x="cp1", y="cp2", color="grupo", hover_name="nombre", opacity=0.6,
                   category_orders={"grupo": sorted(d.grupo.unique(), key=int)},
                   labels={"cp1": "Componente 1 (tamaño de la actividad)", "cp2": "Componente 2"})
    f.update_traces(marker=dict(size=5))
    st.plotly_chart(f, width="stretch")
    st.caption(f"Se dibuja una muestra de {len(d):,} {plural}. Los grupos se calcularon con todos; el plano muestra solo las dos primeras componentes.")
    pk = perf[perf.k == k]
    tabla = pk.pivot(index="cluster", columns="caracteristica", values="mediana")
    tabla.insert(0, "n", pk.groupby("cluster").n.first())
    tabla.insert(1, "% del total", (100 * tabla.n / tabla.n.sum()).round(1))
    st.markdown(f"**Perfil de cada grupo** (mediana de cada característica; k = {k}):")
    st.dataframe(tabla.round(3), width="stretch")
    with st.expander("Qué significa cada característica"):
        if sujeto == "proveedor":
            st.markdown("""
- `n_participaciones`: procesos en que presentó oferta. `tasa_exito`: procesos ganados / procesos en que participó (0 a 1).
- `n_adjudicaciones`, `monto_total`, `monto_mediano`: lo ganado (cantidad y soles).
- `n_entidades`, `n_departamentos`: con cuántas entidades y en cuántos departamentos ganó.
- `concentracion`: parte de lo ganado que viene de su entidad principal (1 = todo de una sola; cerca de 0 = muy repartido).
- `meses_activo`: meses entre su primera y su última participación.
""")
        else:
            st.markdown("""
- `n_procesos`, `n_proveedores`: procesos convocados y proveedores distintos a los que adjudicó.
- `monto_total`, `monto_mediano`: soles adjudicados.
- `pct_bienes`, `pct_servicios`, `pct_obras`: reparto de sus procesos por rubro.
- `postores_promedio`: cuántos postores se presentan en promedio.
- `concentracion`: parte de lo adjudicado que va a su proveedor principal (1 = a uno solo).
""")

# ---------------------------------------------------------------- densidad
with tabs[2]:
    metodo = st.radio("Método", ["DBSCAN", "HDBSCAN"], horizontal=True)
    with st.expander("¿Cómo se elige eps? El gráfico de k-distancias"):
        f = px.line(kdist, x="percentil", y="dist_vecino10", labels={"percentil": "Puntos ordenados de menor a mayor distancia (percentil)", "dist_vecino10": "Distancia al 10.º vecino"})
        for pc in (50, 70, 85, 95):
            f.add_vline(x=pc, line_dash="dot", annotation_text=f"P{pc}")
        f.update_layout(title="Distancia de cada punto a su 10.º vecino (muestra)")
        st.plotly_chart(f, width="stretch")
        st.caption("La curva sube lento y luego de golpe: donde sube de golpe empiezan los puntos aislados. Los eps probados son los percentiles 50, 70, 85 y 95 (líneas punteadas).")
    if metodo == "DBSCAN":
        cols = [c for c in pts.columns if c.startswith("db_")]
        eps_op = sorted({float(c.split("_")[1]) for c in cols}); ms_op = sorted({int(c.split("_")[2]) for c in cols})
        a, b = st.columns(2)
        eps = a.select_slider("eps (radio de vecindad)", options=eps_op, value=eps_op[2] if len(eps_op) > 2 else eps_op[0])
        ms = b.select_slider("min_samples (vecinos mínimos para formar un grupo)", options=ms_op, value=10 if 10 in ms_op else ms_op[0])
        col = f"db_{eps:g}_{ms}"
        col = col if col in pts.columns else [c for c in cols if abs(float(c.split("_")[1]) - eps) < 1e-9 and int(c.split("_")[2]) == ms][0]
    else:
        cols = [c for c in pts.columns if c.startswith("hdb_")]
        mc = st.select_slider("Tamaño mínimo de grupo", options=sorted(int(c.split("_")[1]) for c in cols), value=10)
        col = f"hdb_{mc}"
    lab = pts[col].astype(int)
    d = pts.assign(grupo=lab.map(lambda v: "ruido" if v == -1 else str(v)))
    n_g = len(set(lab[lab >= 0]))
    c = st.columns(2)
    c[0].metric("Grupos encontrados", n_g)
    c[1].metric("Ruido", f"{100 * (lab == -1).mean():.1f}%", help="Puntos que no tienen suficientes vecinos cerca: no pertenecen a ningún grupo.")
    if n_g == 0:
        st.info("Con este ajuste no se forma ningún grupo: todo queda como ruido (no hay una zona lo bastante densa para ese tamaño mínimo).")
    f = px.scatter(d, x="cp1", y="cp2", color="grupo", hover_name="nombre", opacity=0.6,
                   color_discrete_map={"ruido": "#9aa0a6"}, labels={"cp1": "Componente 1", "cp2": "Componente 2"})
    f.update_traces(marker=dict(size=5))
    st.plotly_chart(f, width="stretch")
    st.caption(f"Los métodos de densidad se calcularon sobre esta muestra de {len(pts):,} {plural}; el porcentaje de ruido es de la muestra.")
    st.markdown("""
**Cómo leerlo:** DBSCAN une puntos que tienen al menos `min_samples` vecinos a distancia `eps`. Un `eps` chico rompe el núcleo en pedazos y manda mucho a ruido;
uno grande lo junta todo. Los valores de `eps` salen de la distancia al décimo vecino (percentiles 50, 70, 85 y 95; el valor inicial es el percentil 85). Cambia los controles y mira cómo cambian los grupos y el ruido.
""")
    g = csv_p2("dbscan_grid.csv"); g = g[g.sujeto == sujeto].drop(columns="sujeto").rename(columns={"eps": "eps", "n_clusters": "grupos", "pct_ruido": "% ruido"})
    with st.expander("Tabla completa de la grilla"):
        st.dataframe(g, width="stretch", hide_index=True)

# ---------------------------------------------------------------- jerarquía
with tabs[3]:
    dd = json_p2("dendrograma.json")[sujeto]
    xs, ys = [], []
    for ic, dc in zip(dd["icoord"], dd["dcoord"]):
        xs += list(ic) + [None]; ys += list(dc) + [None]
    f = go.Figure(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=1)))
    f.update_layout(xaxis=dict(showticklabels=False, title=f"{dd['n_puntos']:,} {plural} (muestra, enlace de Ward)"), yaxis_title="Altura de la unión (distancia)", showlegend=False)
    st.plotly_chart(f, width="stretch")
    st.markdown("""
Cada unión del árbol junta dos grupos; **la altura** es cuánto se alejan. Una unión mucho más alta que las anteriores indica un corte natural.
En proveedores la última unión es mucho más alta (124 frente a 20–46): hay **dos grandes bloques** (ganan / no ganan), igual que con k = 2.
En entidades las alturas crecen de forma gradual (29 a 78), lo que concuerda con la silueta baja.
""")

# ---------------------------------------------------------------- atípicos
with tabs[4]:
    st.markdown("""
Se buscan en **todos** los puntos (no solo en la muestra del gráfico). Un caso extremo cumple dos cosas a la vez:
1. Está en una **zona rala**: su distancia al 10.º vecino está entre el 15% más alto (la misma idea de «ruido» de DBSCAN).
2. Está **lejos del centro de su grupo K-Means**. Se muestran los 30 más lejanos.

- **Lejanía:** distancia al centro de su grupo. **Dist. vecino 10:** distancia a su 10.º vecino (más alta = más aislado).
- **Rasgo extremo:** la característica en la que más se aleja del promedio. **z** = cuántas desviaciones estándar por encima (+) o por debajo (−) del promedio.
""")
    base = [c for c in ["nombre", "lejania", "dist_vecino10", "rasgo_extremo", "z", "cluster_kmeans"] if c in out.columns]
    extra = [c for c in out.columns if c not in base + ["sujeto", "id"]]
    n = st.slider("Cuántos mostrar", 5, int(len(out)), min(15, int(len(out))))
    st.dataframe(out[base + extra].head(n), width="stretch", hide_index=True)
    st.warning("Un caso extremo es **una pista para revisar**, no un indicio de irregularidad: un proveedor muy grande y uno de nicho se ven igual de raros para el algoritmo. "
               "Con pocos procesos, una tasa de éxito alta puede ser azar. Los RUC y nombres de personas naturales están enmascarados.")

with st.expander("Límites"):
    st.markdown("""
- Los **consorcios** se dejaron fuera: un proveedor que gana solo dentro de consorcios aparece como "no gana".
- Los datos cubren 2.7 años: un proveedor nuevo puede verse "de una sola entidad" solo por falta de historia.
- Los tipos finos de K-Means son zonas dentro de un núcleo denso grande: con grupos mínimos de 25 o más, HDBSCAN solo ve 2 grupos.
- Los grupos de **entidades** son poco estables (ARI ~0.80, silueta ~0.25): úsalos como tendencias, no como etiquetas.
- El *k* de proveedores (5) se eligió con el codo, la silueta y la estabilidad, pero el codo admite lecturas entre 3 y 5; con k = 3 o 4 los extremos se mantienen.
""")

st.caption("Notebook: `P2_03_Clustering` (scikit-learn + SciPy). Los controles eligen entre experimentos precalculados.")
siguiente("pages/14_Rec_Contenido.py", "Recomendador por contenido")
