# ============================================================
# SISTEMA DE ALERTA TEMPRANA - RÍO LA ESTRELLA
# V2 DEMOSTRATIVA
# Aplicación académica CATIE
#
# Los datos recientes se actualizan manualmente desde
# Google Earth Engine mediante Google Colab y luego se
# exportan a un CSV que consume Streamlit.
# ============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pydeck as pdk
import json

from pathlib import Path


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SAT Río La Estrella",
    page_icon="🌧️",
    layout="wide"
)


# ============================================================
# RUTAS DE ARCHIVOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ARCHIVO_CSV = (
    BASE_DIR /
    "SAT_Rio_La_Estrella_ACTUALIZADO.csv"
)

ARCHIVO_GEOJSON = (
    BASE_DIR /
    "cuenca_rio_la_estrella.geojson"
)


# ============================================================
# CARGAR DATOS DEL SAT
# ============================================================

@st.cache_data
def cargar_datos():

    if not ARCHIVO_CSV.exists():

        st.error(
            "No se encontró el archivo "
            "'SAT_Rio_La_Estrella_ACTUALIZADO.csv'."
        )

        st.write(
            "Archivos encontrados en el repositorio:"
        )

        st.write(
            [
                archivo.name
                for archivo in BASE_DIR.iterdir()
            ]
        )

        st.stop()

    df = pd.read_csv(
        ARCHIVO_CSV
    )

    # Convertir fecha
    df["fecha"] = pd.to_datetime(
        df["fecha"],
        errors="coerce"
    )

    # Columnas numéricas
    columnas_numericas = [
        "lluvia_mm",
        "lluvia_24h_mm",
        "lluvia_48h_mm",
        "lluvia_72h_mm",
        "humedad_superficial",
        "humedad_antecedente_3obs"
    ]

    for columna in columnas_numericas:

        if columna in df.columns:

            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            )

    # Limpiar tabla
    df = (
        df
        .dropna(
            subset=[
                "fecha",
                "lluvia_24h_mm",
                "humedad_superficial"
            ]
        )
        .sort_values("fecha")
        .drop_duplicates(
            subset="fecha",
            keep="last"
        )
        .reset_index(drop=True)
    )

    return df


df = cargar_datos()


# ============================================================
# PERIODO HISTÓRICO DE REFERENCIA
# ============================================================

df_historico = df[
    (
        df["fecha"] >=
        pd.Timestamp("2020-01-01")
    )
    &
    (
        df["fecha"] <=
        pd.Timestamp("2025-12-31")
    )
].copy()


if df_historico.empty:

    st.error(
        "No existen datos del periodo histórico "
        "2020–2025 para calcular los umbrales."
    )

    st.stop()


# ============================================================
# CALCULAR UMBRALES HISTÓRICOS
# ============================================================

P90_LLUVIA = (
    df_historico[
        "lluvia_24h_mm"
    ]
    .quantile(0.90)
)

P95_LLUVIA = (
    df_historico[
        "lluvia_24h_mm"
    ]
    .quantile(0.95)
)

P98_LLUVIA = (
    df_historico[
        "lluvia_24h_mm"
    ]
    .quantile(0.98)
)

P98_HUMEDAD = (
    df_historico[
        "humedad_superficial"
    ]
    .quantile(0.98)
)


# ============================================================
# FUNCIÓN DE CLASIFICACIÓN DEL SAT
# ============================================================

def clasificar_alerta(
    lluvia,
    humedad
):

    if (
        lluvia >= P98_LLUVIA
        and
        humedad >= P98_HUMEDAD
    ):

        return "Rojo"

    elif (
        lluvia >= P95_LLUVIA
        and
        humedad >= P98_HUMEDAD
    ):

        return "Naranja"

    elif (
        lluvia >= P90_LLUVIA
        and
        humedad >= P98_HUMEDAD
    ):

        return "Amarillo"

    else:

        return "Verde"


# Recalcular niveles desde los datos
df["alerta_app"] = df.apply(
    lambda fila: clasificar_alerta(
        fila["lluvia_24h_mm"],
        fila["humedad_superficial"]
    ),
    axis=1
)


# ============================================================
# FECHAS DISPONIBLES
# ============================================================

ultima_fecha = df[
    "fecha"
].max()

primera_fecha = df[
    "fecha"
].min()


# ============================================================
# ENCABEZADO
# ============================================================

st.title(
    "🌧️ Sistema de Alerta Temprana"
)

st.markdown(
    "### Cuenca del río La Estrella, Costa Rica"
)

st.caption(
    "Ejercicio académico desarrollado para el curso del CATIE"
)

st.info(
    """
    Este Sistema de Alerta Temprana constituye un prototipo
    demostrativo.

    Los datos recientes son obtenidos mediante Google Earth
    Engine desde Google Colab y posteriormente incorporados
    manualmente a la aplicación.

    Los niveles mostrados no representan alertas oficiales.
    """
)


# ============================================================
# BARRA LATERAL
# ============================================================

st.sidebar.header(
    "⚙️ Configuración"
)

st.sidebar.markdown(
    """
    **Fuentes**

    🌧️ CHIRPS Daily

    💧 SMAP Nivel 3

    **Periodo histórico de referencia**

    2020–2025
    """
)

st.sidebar.success(
    f"""
    Último dato disponible

    **{ultima_fecha.strftime('%d/%m/%Y')}**
    """
)


# ============================================================
# MODO DE CONSULTA
# ============================================================

modo = st.sidebar.radio(
    "Modo de consulta",
    [
        "Último dato disponible",
        "Consultar histórico"
    ]
)


# ============================================================
# SELECCIONAR REGISTRO
# ============================================================

if modo == "Último dato disponible":

    fecha_consulta = (
        ultima_fecha.date()
    )

    registro = df[
        df["fecha"] ==
        ultima_fecha
    ]

else:

    fecha_consulta = st.sidebar.date_input(
        "Seleccione una fecha",
        value=ultima_fecha.date(),
        min_value=primera_fecha.date(),
        max_value=ultima_fecha.date()
    )

    registro = df[
        df["fecha"].dt.date ==
        fecha_consulta
    ]


# ============================================================
# CREAR PESTAÑAS
# ============================================================

tab_estado, tab_mapa, tab_historial, tab_umbrales, tab_metodologia = st.tabs(
    [
        "🚨 Estado del SAT",
        "🗺️ Mapa",
        "📊 Historial",
        "🎯 Umbrales",
        "ℹ️ Metodología"
    ]
)


# ============================================================
# TAB 1 — ESTADO DEL SAT
# ============================================================

with tab_estado:

    if modo == "Último dato disponible":

        st.header(
            "Último estado disponible"
        )

    else:

        st.header(
            "Estado histórico del SAT"
        )


    if registro.empty:

        st.warning(
            "No existen datos disponibles "
            "para la fecha seleccionada."
        )

    else:

        fila = registro.iloc[0]

        lluvia_24 = fila[
            "lluvia_24h_mm"
        ]

        humedad = fila[
            "humedad_superficial"
        ]

        alerta = fila[
            "alerta_app"
        ]


        st.caption(
            f"Fecha del dato: "
            f"{fila['fecha'].strftime('%d/%m/%Y')}"
        )


        # ====================================================
        # PANEL DE ALERTA
        # ====================================================

        if alerta == "Rojo":

            st.error(
                """
                ## 🔴 ALERTA ROJA

                Se identifican simultáneamente condiciones
                extremas de precipitación y alta humedad
                superficial del suelo.
                """
            )

        elif alerta == "Naranja":

            st.warning(
                """
                ## 🟠 ALERTA NARANJA

                Se identifican condiciones muy elevadas de
                precipitación sobre un suelo con alta humedad.
                """
            )

        elif alerta == "Amarillo":

            st.warning(
                """
                ## 🟡 ALERTA AMARILLA

                Se identifican condiciones elevadas de lluvia
                y humedad que requieren seguimiento.
                """
            )

        else:

            st.success(
                """
                ## 🟢 CONDICIONES NORMALES

                No se identifican simultáneamente condiciones
                extremas de precipitación y humedad según los
                umbrales del SAT.
                """
            )


        # ====================================================
        # MÉTRICAS
        # ====================================================

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "🌧️ Precipitación 24 h",
            f"{fila['lluvia_24h_mm']:.1f} mm"
        )


        if (
            "lluvia_48h_mm" in fila.index
            and
            pd.notna(
                fila["lluvia_48h_mm"]
            )
        ):

            col2.metric(
                "🌧️ Precipitación 48 h",
                f"{fila['lluvia_48h_mm']:.1f} mm"
            )

        else:

            col2.metric(
                "🌧️ Precipitación 48 h",
                "Sin dato"
            )


        if (
            "lluvia_72h_mm" in fila.index
            and
            pd.notna(
                fila["lluvia_72h_mm"]
            )
        ):

            col3.metric(
                "🌧️ Precipitación 72 h",
                f"{fila['lluvia_72h_mm']:.1f} mm"
            )

        else:

            col3.metric(
                "🌧️ Precipitación 72 h",
                "Sin dato"
            )


        col4.metric(
            "💧 Humedad superficial",
            f"{fila['humedad_superficial']:.3f} m³/m³"
        )


        st.divider()


        # ====================================================
        # EXPLICACIÓN
        # ====================================================

        st.subheader(
            "¿Por qué se obtuvo este nivel?"
        )


        col1, col2 = st.columns(2)


        with col1:

            st.markdown(
                "#### 🌧️ Precipitación"
            )

            st.write(
                f"""
                **Valor observado:** {lluvia_24:.1f} mm

                **P90:** {P90_LLUVIA:.1f} mm

                **P95:** {P95_LLUVIA:.1f} mm

                **P98:** {P98_LLUVIA:.1f} mm
                """
            )


        with col2:

            st.markdown(
                "#### 💧 Humedad superficial"
            )

            st.write(
                f"""
                **Valor observado:** {humedad:.3f} m³/m³

                **P98 histórico:** {P98_HUMEDAD:.3f} m³/m³
                """
            )


        st.subheader(
            "Interpretación"
        )


        if alerta == "Rojo":

            st.write(
                """
                La precipitación acumulada en 24 horas
                alcanzó o superó el P98 histórico y la
                humedad superficial también alcanzó o
                superó su P98.

                La coincidencia de ambas condiciones genera
                una **Alerta Roja**.
                """
            )

        elif alerta == "Naranja":

            st.write(
                """
                La precipitación alcanzó o superó el P95
                histórico y la humedad superficial alcanzó
                o superó su P98.

                El sistema clasifica estas condiciones como
                **Alerta Naranja**.
                """
            )

        elif alerta == "Amarillo":

            st.write(
                """
                La precipitación alcanzó o superó el P90
                histórico y la humedad superficial alcanzó
                o superó su P98.

                El sistema clasifica estas condiciones como
                **Alerta Amarilla**.
                """
            )

        else:

            st.write(
                """
                Las condiciones de precipitación y humedad
                no alcanzan simultáneamente los umbrales
                necesarios para activar una alerta.

                El sistema clasifica esta fecha como
                **condición normal**.
                """
            )


# ============================================================
# TAB 2 — MAPA
# ============================================================

with tab_mapa:

    st.header(
        "🗺️ Cuenca del río La Estrella"
    )

    st.write(
        """
        El mapa muestra la delimitación de la cuenca
        hidrográfica utilizada como unidad espacial de
        análisis para calcular la precipitación CHIRPS
        y la humedad superficial SMAP.
        """
    )


    if not ARCHIVO_GEOJSON.exists():

        st.error(
            "No se encontró el archivo "
            "'cuenca_rio_la_estrella.geojson'."
        )

    else:

        # ====================================================
        # CARGAR GEOJSON
        # ====================================================

        with open(
            ARCHIVO_GEOJSON,
            "r",
            encoding="utf-8"
        ) as f:

            cuenca_geojson = json.load(f)


        # ====================================================
        # DETERMINAR COLOR SEGÚN ALERTA
        # ====================================================

        if not registro.empty:

            nivel_mapa = (
                registro.iloc[0][
                    "alerta_app"
                ]
            )

        else:

            nivel_mapa = "Verde"


        if nivel_mapa == "Rojo":

            color_relleno = [
                220,
                40,
                40,
                110
            ]

            color_linea = [
                160,
                0,
                0
            ]


        elif nivel_mapa == "Naranja":

            color_relleno = [
                255,
                140,
                0,
                110
            ]

            color_linea = [
                200,
                90,
                0
            ]


        elif nivel_mapa == "Amarillo":

            color_relleno = [
                255,
                210,
                0,
                110
            ]

            color_linea = [
                180,
                150,
                0
            ]


        else:

            color_relleno = [
                50,
                170,
                80,
                90
            ]

            color_linea = [
                0,
                110,
                40
            ]


        # ====================================================
        # CAPA GEOJSON
        # ====================================================

        capa_cuenca = pdk.Layer(
            "GeoJsonLayer",

            data=cuenca_geojson,

            stroked=True,

            filled=True,

            opacity=0.45,

            get_fill_color=color_relleno,

            get_line_color=color_linea,

            line_width_min_pixels=2,

            pickable=True
        )


        # ====================================================
        # VISTA
        # ====================================================

        vista = pdk.ViewState(
            latitude=9.72,
            longitude=-82.95,
            zoom=9.3,
            pitch=0,
            bearing=0
        )


        # ====================================================
        # MAPA
        # ====================================================

        mapa = pdk.Deck(
            layers=[
                capa_cuenca
            ],

            initial_view_state=vista,

            map_style=None,

            tooltip={
                "html":
                f"""
                <b>Cuenca del río La Estrella</b>
                <br>
                Nivel SAT: <b>{nivel_mapa}</b>
                """
            }
        )


        st.pydeck_chart(
            mapa,
            use_container_width=True,
            height=550
        )


        st.caption(
            """
            El color del polígono representa el nivel de
            alerta correspondiente a la fecha seleccionada.
            """
        )


        # ====================================================
        # CONDICIONES DE LA FECHA
        # ====================================================

        if not registro.empty:

            fila_mapa = registro.iloc[0]

            st.subheader(
                "Condiciones de la fecha seleccionada"
            )


            col1, col2, col3 = st.columns(3)


            col1.metric(
                "🌧️ Lluvia 24 h",
                f"{fila_mapa['lluvia_24h_mm']:.1f} mm"
            )


            col2.metric(
                "💧 Humedad superficial",
                f"{fila_mapa['humedad_superficial']:.3f} m³/m³"
            )


            col3.metric(
                "🚨 Nivel",
                fila_mapa["alerta_app"]
            )


# ============================================================
# PREPARAR DATOS MENSUALES
# ============================================================

df["Año"] = (
    df["fecha"]
    .dt.year
)

df["Mes"] = (
    df["fecha"]
    .dt.month
)


mensual = (
    df
    .groupby(
        [
            "Año",
            "Mes"
        ],
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
        year=mensual[
            "Año"
        ],

        month=mensual[
            "Mes"
        ],

        day=1
    )
)


# ============================================================
# TAB 3 — HISTORIAL
# ============================================================

with tab_historial:

    st.header(
        "Historial hidrometeorológico"
    )


    st.caption(
        f"Serie disponible: "
        f"{primera_fecha.strftime('%d/%m/%Y')} "
        f"– "
        f"{ultima_fecha.strftime('%d/%m/%Y')}"
    )


    años = sorted(
        df[
            "fecha"
        ]
        .dt.year
        .unique()
    )


    años_seleccionados = st.multiselect(
        "Seleccione los años que desea visualizar",
        options=años,
        default=años
    )


    mensual_filtrado = mensual[
        mensual[
            "Año"
        ]
        .isin(
            años_seleccionados
        )
    ]


    col1, col2 = st.columns(2)


    # ========================================================
    # PRECIPITACIÓN MENSUAL
    # ========================================================

    with col1:

        st.subheader(
            "🌧️ Precipitación mensual"
        )


        fig, ax = plt.subplots(
            figsize=(9, 5)
        )


        ax.bar(
            mensual_filtrado[
                "Fecha"
            ],

            mensual_filtrado[
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


        ax.xaxis.set_major_locator(
            mdates.YearLocator()
        )


        ax.xaxis.set_major_formatter(
            mdates.DateFormatter(
                "%Y"
            )
        )


        ax.grid(
            axis="y",
            alpha=0.3
        )


        plt.xticks(
            rotation=45
        )


        plt.tight_layout()


        st.pyplot(
            fig
        )


    # ========================================================
    # HUMEDAD MENSUAL
    # ========================================================

    with col2:

        st.subheader(
            "💧 Humedad superficial"
        )


        fig, ax = plt.subplots(
            figsize=(9, 5)
        )


        ax.bar(
            mensual_filtrado[
                "Fecha"
            ],

            mensual_filtrado[
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


        ax.xaxis.set_major_locator(
            mdates.YearLocator()
        )


        ax.xaxis.set_major_formatter(
            mdates.DateFormatter(
                "%Y"
            )
        )


        ax.grid(
            axis="y",
            alpha=0.3
        )


        plt.xticks(
            rotation=45
        )


        plt.tight_layout()


        st.pyplot(
            fig
        )


    st.divider()


    # ========================================================
    # EVENTOS DE ALERTA
    # ========================================================

    st.subheader(
        "🚨 Eventos clasificados con alerta"
    )


    columnas_eventos = [
        "fecha",
        "lluvia_24h_mm",
        "lluvia_48h_mm",
        "lluvia_72h_mm",
        "humedad_superficial",
        "alerta_app"
    ]


    columnas_eventos = [
        columna
        for columna in columnas_eventos
        if columna in df.columns
    ]


    eventos = df[
        df[
            "alerta_app"
        ]
        != "Verde"
    ][
        columnas_eventos
    ].copy()


    eventos = eventos.rename(
        columns={
            "fecha":
                "Fecha",

            "lluvia_24h_mm":
                "Lluvia 24 h (mm)",

            "lluvia_48h_mm":
                "Lluvia 48 h (mm)",

            "lluvia_72h_mm":
                "Lluvia 72 h (mm)",

            "humedad_superficial":
                "Humedad (m³/m³)",

            "alerta_app":
                "Nivel de alerta"
        }
    )


    st.dataframe(
        eventos,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 4 — UMBRALES
# ============================================================

with tab_umbrales:

    st.header(
        "Umbrales históricos del SAT"
    )


    st.info(
        """
        Los umbrales se calculan exclusivamente utilizando
        el periodo histórico 2020–2025.

        Los datos posteriores a 2025 se comparan contra
        estos valores, pero no modifican los percentiles.
        """
    )


    col1, col2, col3, col4 = st.columns(4)


    col1.metric(
        "🟡 P90 lluvia",
        f"{P90_LLUVIA:.1f} mm"
    )


    col2.metric(
        "🟠 P95 lluvia",
        f"{P95_LLUVIA:.1f} mm"
    )


    col3.metric(
        "🔴 P98 lluvia",
        f"{P98_LLUVIA:.1f} mm"
    )


    col4.metric(
        "💧 P98 humedad",
        f"{P98_HUMEDAD:.3f} m³/m³"
    )


    st.divider()


    col1, col2 = st.columns(2)


    # ========================================================
    # HISTOGRAMA PRECIPITACIÓN
    # ========================================================

    with col1:

        st.subheader(
            "Distribución histórica de precipitación"
        )


        fig, ax = plt.subplots(
            figsize=(8, 5)
        )


        ax.hist(
            df_historico[
                "lluvia_24h_mm"
            ].dropna(),

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


        ax.grid(
            axis="y",
            alpha=0.2
        )


        plt.tight_layout()


        st.pyplot(
            fig
        )


    # ========================================================
    # HISTOGRAMA HUMEDAD
    # ========================================================

    with col2:

        st.subheader(
            "Distribución histórica de humedad"
        )


        fig, ax = plt.subplots(
            figsize=(8, 5)
        )


        ax.hist(
            df_historico[
                "humedad_superficial"
            ].dropna(),

            bins=40
        )


        ax.axvline(
            P98_HUMEDAD,
            linestyle="--",
            label=(
                f"P98 = "
                f"{P98_HUMEDAD:.3f} m³/m³"
            )
        )


        ax.set_xlabel(
            "Humedad superficial (m³/m³)"
        )


        ax.set_ylabel(
            "Frecuencia"
        )


        ax.legend()


        ax.grid(
            axis="y",
            alpha=0.2
        )


        plt.tight_layout()


        st.pyplot(
            fig
        )


    # ========================================================
    # TABLA DE REGLAS
    # ========================================================

    st.subheader(
        "Reglas de clasificación"
    )


    tabla_reglas = pd.DataFrame(
        {
            "Nivel": [
                "🟢 Verde",
                "🟡 Amarillo",
                "🟠 Naranja",
                "🔴 Rojo"
            ],

            "Precipitación 24 h": [
                f"< {P90_LLUVIA:.1f} mm",
                f"≥ {P90_LLUVIA:.1f} mm",
                f"≥ {P95_LLUVIA:.1f} mm",
                f"≥ {P98_LLUVIA:.1f} mm"
            ],

            "Humedad superficial": [
                "No cumple ambos criterios",
                f"≥ {P98_HUMEDAD:.3f} m³/m³",
                f"≥ {P98_HUMEDAD:.3f} m³/m³",
                f"≥ {P98_HUMEDAD:.3f} m³/m³"
            ],

            "Interpretación": [
                "Condiciones normales",
                "Condiciones elevadas",
                "Condiciones muy elevadas",
                "Condiciones extremas"
            ]
        }
    )


    st.dataframe(
        tabla_reglas,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 5 — METODOLOGÍA
# ============================================================

with tab_metodologia:

    st.header(
        "Metodología"
    )


    st.markdown(
        """
        ### Objetivo

        El Sistema de Alerta Temprana fue desarrollado
        como un ejercicio académico para identificar
        condiciones hidrometeorológicas potencialmente
        favorables para inundaciones en la cuenca del
        río La Estrella.


        ### 📚 Periodo histórico de referencia

        Los umbrales fueron definidos utilizando
        exclusivamente el periodo **2020–2025**.

        Este periodo constituye la línea base histórica
        del SAT.


        ### 🌧️ Precipitación

        La precipitación se obtiene del producto
        **CHIRPS Daily** mediante Google Earth Engine.

        Se calculan acumulados de:

        - 24 horas
        - 48 horas
        - 72 horas

        La precipitación de **24 horas** es la variable
        utilizada para determinar el nivel de alerta.


        ### 💧 Humedad superficial

        La humedad superficial se obtiene del producto
        **SMAP Nivel 3**.

        Esta variable representa el contenido volumétrico
        de agua en la capa superficial del suelo.


        ### 🎯 Umbrales

        Para precipitación:

        - **P90:** condición elevada
        - **P95:** condición muy elevada
        - **P98:** condición extrema

        Para humedad:

        - **P98:** condición de alta humedad


        ### 🚨 Funcionamiento del SAT

        El sistema utiliza simultáneamente:

        1. precipitación acumulada en 24 horas;
        2. humedad superficial del suelo.

        **Amarillo**

        Precipitación ≥ P90  
        y humedad ≥ P98.

        **Naranja**

        Precipitación ≥ P95  
        y humedad ≥ P98.

        **Rojo**

        Precipitación ≥ P98  
        y humedad ≥ P98.


        ### 🔄 Actualización

        La aplicación no consulta Earth Engine
        directamente.

        Los datos recientes se actualizan mediante
        Google Colab.

        El flujo es:

        1. consultar CHIRPS y SMAP en Earth Engine;
        2. integrar los datos recientes;
        3. combinarlos con la base histórica;
        4. eliminar fechas duplicadas;
        5. recalcular los niveles de alerta;
        6. exportar un CSV actualizado;
        7. cargar el CSV en GitHub;
        8. Streamlit actualiza el dashboard.


        ### 🗺️ Unidad espacial

        La cuenca del río La Estrella constituye la
        unidad espacial de análisis.

        Tanto la precipitación CHIRPS como la humedad
        SMAP corresponden a valores medios calculados
        sobre esta geometría.


        ### ⚠️ Limitaciones

        Este SAT constituye exclusivamente un ejercicio
        académico.

        Los umbrales:

        - no han sido calibrados con niveles del río;
        - no utilizan caudales observados;
        - no incorporan estaciones meteorológicas locales;
        - no han sido validados contra un inventario
          completo de inundaciones;
        - no deben interpretarse como alertas oficiales.

        La fecha mostrada corresponde al último dato
        simultáneamente disponible de CHIRPS y SMAP.
        """
    )


# ============================================================
# PIE DE PÁGINA
# ============================================================

st.divider()


st.caption(
    f"""
    Sistema de Alerta Temprana — Cuenca del río La Estrella |
    Ejercicio académico CATIE |
    CHIRPS + SMAP L3 |
    Último dato disponible:
    {ultima_fecha.strftime('%d/%m/%Y')}
    """
)
