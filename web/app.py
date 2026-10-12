import streamlit as st

st.set_page_config(
    page_title="Minería de Datos SEACE",
    page_icon="📊",
    layout="wide",
)

pagina = st.navigation(
    {
        "Inicio": [
            st.Page("inicio.py", title="Portada", icon="🏠", default=True),
        ],
        "Datos": [
            st.Page("pages/0_Datos_y_Limpieza.py", title="Datos y limpieza", icon="🧹"),
            st.Page("pages/0_EDA.py", title="Análisis exploratorio", icon="📈"),
            st.Page("pages/9_Spark_Particiones.py", title="Spark y particiones", icon="⚡"),
        ],
        "Textos similares": [
            st.Page("pages/4_Minhash_LSH.py", title="MinHash y LSH", icon="🔎"),
            st.Page("pages/5_Casos_de_Textos.py", title="Casos de textos", icon="📄"),
            st.Page("pages/6_ANN.py", title="Vecinos aproximados (ANN)", icon="🧭"),
        ],
        "Flujos con poca memoria": [
            st.Page("pages/1_Bloom_Filter.py", title="Bloom Filter", icon="🌸"),
            st.Page("pages/2_Count_Min_Sketch.py", title="Count-Min Sketch", icon="🔢"),
            st.Page("pages/3_DGIM.py", title="DGIM", icon="⏱️"),
        ],
        "Reglas de asociación": [
            st.Page("pages/8_Apriori_FPGrowth.py", title="Apriori y FP-Growth", icon="🧺"),
            st.Page("pages/7_Reglas_Asociacion.py", title="Reglas", icon="🔗"),
        ],
        "Cierre": [
            st.Page("pages/10_Discusion_Critica.py", title="Discusión crítica", icon="⚖️"),
        ],
    }
)
pagina.run()
