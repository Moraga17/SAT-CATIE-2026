
# ============================================================
# SISTEMA DE ALERTA TEMPRANA - RÍO LA ESTRELLA
# Aplicación académica CATIE
# ============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# CONFIGURACIÓN DE LA APP
# ============================================================

st.set_page_config(
    page_title="SAT Río La Estrella",
    page_icon="🌧️",
    layout="wide"
)


# ============================================================
# TÍTULO
# ============================================================

st.title("🌧️ Sistema de Alerta Temprana")
st.subheader("Cuenca del río La Estrella, Costa Rica")

st.info(
    """
    Este SAT constituye un ejercicio académico desarrollado para el curso
    del CATIE. Los niveles de alerta son demostrativos y no representan
    un sistema oficial u operativo de alerta por inundaciones.
    """
)


# ============================================================
# CARGAR DATOS
# ============================================================

@st.cache_data
def cargar_datos():

    df = pd.read_csv(
        "SAT_Rio_La_Estrella_2020_2025.csv"
    )

    df["fecha"] = pd.to_datetime(
        df["fecha"]
    )

    return df


df = cargar_datos()


# ============================================================
# CALCULAR PERCENTILES
# ============================================================

# Precipitación
P90_LLUVIA = df[
    "lluvia_24h_mm"
].quantile(0.90)

P95_LLUVIA = df[
    "lluvia_24h_mm"
].quantile(0.95)

P98_LLUVIA = df[
    "lluvia_24h_mm"
].quantile(0.98)


# Humedad superficial
P98_HUMEDAD = df[
    "humedad_superficial"
].quantile(0.98)


# ============================================================
# FUNCIÓN DEL SAT
# ============================================================

def clasificar_alerta(lluvia, humedad):

    # ROJO
    if (
        lluvia >= P98_LLUVIA
        and humedad >= P98_HUMEDAD
    ):
        return "🔴 Rojo"

    # NARANJA
    elif (
        lluvia >= P95_LLUVIA
        and humedad >= P98_HUMEDAD
    ):
        return "🟠 Naranja"

    # AMARILLO
    elif (
        lluvia >= P90_LLUVIA
        and humedad >= P98_HUMEDAD
    ):
        return "🟡 Amarillo"

    # VERDE
    else:
        return "🟢 Verde"


# Recalcular alerta
df["alerta_app"] = df.apply(
    lambda fila: clasificar_alerta(
        fila["lluvia_24h_mm"],
        fila["humedad_superficial"]
    ),
    axis=1
)


# ============================================================
# BARRA LATERAL
# ============================================================

st.sidebar.title(
    "Configuración"
)

st.sidebar.markdown(
    """
    **Periodo de análisis**

    2020–2025

    **Predictores**

    - Precipitación CHIRPS
    - Humedad superficial SMAP L3
    """
)


# Selector de fecha

fecha_seleccionada = st.sidebar.date_input(
    "Seleccione una fecha",
    value=df["fecha"].max().date(),
    min_value=df["fecha"].min().date(),
    max_value=df["fecha"].max().date()
)


# ============================================================
# REGISTRO SELECCIONADO
# ============================================================

registro = df[
    df["fecha"].dt.date
    == fecha_seleccionada
]


st.header(
    "Estado del SAT"
)


if not registro.empty:

    fila = registro.iloc[0]

    lluvia = fila[
        "lluvia_24h_mm"
    ]

    humedad = fila[
        "humedad_superficial"
    ]

    alerta = fila[
        "alerta_app"
    ]


    col1, col2, col3 = st.columns(3)


    col1.metric(
        "Precipitación 24 h",
        f"{lluvia:.1f} mm"
    )


    col2.metric(
        "Humedad superficial",
        f"{humedad:.3f} m³/m³"
    )


    col3.metric(
        "Nivel de alerta",
        alerta
    )


else:

    st.warning(
        "No existen datos disponibles para esta fecha."
    )


# ============================================================
# UMBRALES DEL SAT
# ============================================================

st.header(
    "Umbrales del SAT"
)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "P90 lluvia",
    f"{P90_LLUVIA:.1f} mm"
)


col2.metric(
    "P95 lluvia",
    f"{P95_LLUVIA:.1f} mm"
)


col3.metric(
    "P98 lluvia",
    f"{P98_LLUVIA:.1f} mm"
)


col4.metric(
    "P98 humedad",
    f"{P98_HUMEDAD:.3f} m³/m³"
)


st.markdown(
    """
    ### Interpretación

    🟢 **Verde**
    Condiciones normales.

    🟡 **Amarillo**
    Precipitación ≥ P90 y humedad ≥ P98.

    🟠 **Naranja**
    Precipitación ≥ P95 y humedad ≥ P98.

    🔴 **Rojo**
    Precipitación ≥ P98 y humedad ≥ P98.
    """
)


# ============================================================
# DATOS MENSUALES
# ============================================================

df["Año"] = df[
    "fecha"
].dt.year

df["Mes"] = df[
    "fecha"
].dt.month


mensual = (
    df
    .groupby(
        ["Año", "Mes"],
        as_index=False
    )
    .agg(
        precipitacion_mensual=(
            "lluvia_mm",
            "sum"
        ),

        humedad_media=(
            "humedad_superficial",
            "mean"
        )
    )
)


mensual["Fecha"] = pd.to_datetime(
    dict(
        year=mensual["Año"],
        month=mensual["Mes"],
        day=1
    )
)


# ============================================================
# PRECIPITACIÓN MENSUAL
# ============================================================

st.header(
    "Precipitación mensual"
)


fig, ax = plt.subplots(
    figsize=(14, 5)
)


ax.bar(
    mensual["Fecha"],
    mensual[
        "precipitacion_mensual"
    ],
    width=20
)


ax.set_title(
    "Precipitación acumulada mensual CHIRPS"
)


ax.set_ylabel(
    "Precipitación (mm)"
)


ax.set_xlabel(
    "Fecha"
)


ax.grid(
    axis="y",
    alpha=0.3
)


plt.tight_layout()


st.pyplot(fig)


# ============================================================
# HUMEDAD MENSUAL
# ============================================================

st.header(
    "Humedad superficial mensual"
)


fig, ax = plt.subplots(
    figsize=(14, 5)
)


ax.bar(
    mensual["Fecha"],
    mensual[
        "humedad_media"
    ],
    width=20
)


ax.set_title(
    "Humedad superficial media mensual SMAP L3"
)


ax.set_ylabel(
    "Humedad superficial (m³/m³)"
)


ax.set_xlabel(
    "Fecha"
)


ax.grid(
    axis="y",
    alpha=0.3
)


plt.tight_layout()


st.pyplot(fig)


# ============================================================
# DISTRIBUCIÓN DE PRECIPITACIÓN
# ============================================================

st.header(
    "Distribución de precipitación"
)


fig, ax = plt.subplots(
    figsize=(10, 5)
)


ax.hist(
    df["lluvia_24h_mm"],
    bins=40
)


ax.axvline(
    P90_LLUVIA,
    linestyle="--",
    label=f"P90 = {P90_LLUVIA:.1f} mm"
)


ax.axvline(
    P95_LLUVIA,
    linestyle="--",
    label=f"P95 = {P95_LLUVIA:.1f} mm"
)


ax.axvline(
    P98_LLUVIA,
    linestyle="--",
    label=f"P98 = {P98_LLUVIA:.1f} mm"
)


ax.set_xlabel(
    "Precipitación 24 h (mm)"
)


ax.set_ylabel(
    "Frecuencia"
)


ax.legend()


st.pyplot(fig)


# ============================================================
# DISTRIBUCIÓN DE HUMEDAD
# ============================================================

st.header(
    "Distribución de humedad del suelo"
)


fig, ax = plt.subplots(
    figsize=(10, 5)
)


ax.hist(
    df[
        "humedad_superficial"
    ],
    bins=40
)


ax.axvline(
    P98_HUMEDAD,
    linestyle="--",
    label=(
        f"P98 = "
        f"{P98_HUMEDAD:.3f}"
    )
)


ax.set_xlabel(
    "Humedad superficial (m³/m³)"
)


ax.set_ylabel(
    "Frecuencia"
)


ax.legend()


st.pyplot(fig)


# ============================================================
# EVENTOS DE ALERTA
# ============================================================

st.header(
    "Eventos históricos de alerta"
)


eventos = df[
    df["alerta_app"]
    != "🟢 Verde"
][
    [
        "fecha",
        "lluvia_24h_mm",
        "humedad_superficial",
        "alerta_app"
    ]
]


st.dataframe(
    eventos,
    use_container_width=True
)


# ============================================================
# METODOLOGÍA
# ============================================================

st.header(
    "Metodología"
)


st.markdown(
    """
    El sistema utiliza dos variables predictoras:

    **1. Precipitación**

    Datos diarios CHIRPS para el periodo 2020–2025.

    **2. Humedad superficial del suelo**

    Producto SMAP Nivel 3.

    Los percentiles históricos de las series fueron utilizados
    como umbrales estadísticos.

    El nivel de alerta se determina a partir de la combinación
    simultánea entre precipitación intensa y elevada humedad
    superficial del suelo.

    Este SAT corresponde exclusivamente a un ejercicio académico
    y no ha sido calibrado con registros históricos de inundación,
    caudales o niveles del río.
    """
)
