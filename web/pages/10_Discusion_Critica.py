import re

import pandas as pd
import streamlit as st

from utils import PROJECT_ROOT, encabezado
from preguntas import PREGUNTAS


RUTA_TEXTO = PROJECT_ROOT / "web_artefactos" / "discusion" / "discusion_critica.md"

st.title("Análisis y discusión crítica")

encabezado(
    '¿Cuánto vale aproximar y cuánto cuesta en precisión, y cuándo conviene cada técnica?',
    'Las respuestas a las cinco preguntas están en la tabla de abajo. El detalle de pérdida, Spark, escala y límites está en las pestañas.',
)

st.caption(
    "Parte VI. Cada cifra sale de los notebooks y artefactos del proyecto. "
    "Las marcas (medido), (estimado) e (hipótesis) indican cuánto respaldo tiene cada dato."
)

if not RUTA_TEXTO.exists():
    st.error(f"No se encontró el texto: {RUTA_TEXTO}")
    st.stop()

texto = RUTA_TEXTO.read_text(encoding="utf-8")

# El archivo tiene un título (#) y secciones que empiezan con "## ".
# La introducción es lo que va antes de la primera sección.
partes = re.split(r"^## ", texto, flags=re.MULTILINE)
introduccion = partes[0].split("\n", 1)[1] if "\n" in partes[0] else ""
secciones = []
for p in partes[1:]:
    titulo, _, cuerpo = p.partition("\n")
    secciones.append((titulo.strip(), cuerpo.strip()))

st.markdown(introduccion)

st.subheader("Las cinco preguntas y sus respuestas")
st.table(pd.DataFrame([
    {"Pregunta": p["titulo"], "Respuesta": p["respuesta"],
     "Dónde se ve": ", ".join(e for _, e in p["links"])}
    for p in PREGUNTAS
]))

# Nombres cortos para las pestañas (si cambia el número de secciones, usa los títulos completos)
nombres_pestanas = [
    "1. Valor", "2. Pérdida", "3. Spark", "4. Escala",
    "5. Implicancias", "6. Limitaciones", "7. Guía de decisión",
]
if len(nombres_pestanas) != len(secciones):
    nombres_pestanas = [t for t, _ in secciones]

pestanas = st.tabs(nombres_pestanas)
for pestana, (titulo, cuerpo) in zip(pestanas, secciones):
    with pestana:
        st.subheader(titulo)
        st.markdown(cuerpo)
