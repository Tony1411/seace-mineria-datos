"""Lectura de los artefactos del Proyecto 2 (carpeta web_artefactos/p2). Solo lee archivos ya calculados."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

P2_DIR = Path(__file__).resolve().parents[1] / "web_artefactos" / "p2"


@st.cache_data
def csv_p2(nombre):
    ruta = P2_DIR / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")
    return pd.read_csv(ruta)


@st.cache_data
def json_p2(nombre):
    ruta = P2_DIR / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")
    with ruta.open("r", encoding="utf-8") as f:
        return json.load(f)
