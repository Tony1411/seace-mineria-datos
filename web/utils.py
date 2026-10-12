from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


@st.cache_data
def cargar_csv(*partes):
    ruta = ARTIFACTS_DIR.joinpath(*partes)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el artefacto: {ruta}"
        )

    return pd.read_csv(ruta)

import json


@st.cache_data
def cargar_json(*partes):
    ruta = PROJECT_ROOT / "web_artefactos"

    for parte in partes:
        ruta = ruta / parte

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró: {ruta}"
        )

    with ruta.open("r", encoding="utf-8") as f:
        return json.load(f)


def encabezado(pregunta, respuesta):
    """Cuadro de arriba de cada página: qué queremos resolver y la respuesta corta."""
    with st.container(border=True):
        st.markdown(f"**Qué queremos resolver:** {pregunta}")
        st.markdown(f"**Respuesta corta:** {respuesta}")


def siguiente(ruta, etiqueta):
    """Enlace de abajo de cada página hacia la siguiente del recorrido."""
    st.divider()
    st.page_link(ruta, label=f"Siguiente: {etiqueta} →")
