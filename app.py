# ============================================================
# SISTEMA DE ALERTA TEMPRANA - RÍO LA ESTRELLA
# Aplicación académica CATIE
# ============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SAT Río La Estrella",
    page_icon="🌧️",
    layout="wide"
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
        df["fecha"],
        errors="coerce"
    )

    # Convertir variables numéricas
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
        .reset_index(drop=True)
    )

    return df


df = cargar_datos()


# ============================================================
# CALCULAR UMBRALES
# ============================================================

P90_LLUVIA = df[
    "lluvia_24h_mm"
].quantile(0.90)

P95_LLUVIA = df[
    "lluvia_24h_mm"
].quantile(0.95)

P98_LLUVIA = df[
    "lluvia_24h_mm"
].quantile(0.98)

P98_HUMEDAD = df[
    "humedad_superficial"
].quantile(0.98)


# ============================================================
# FUNCIÓN DEL SAT
# ============================================================

def clasificar_alerta(lluvia, humedad):

    # ALERTA ROJA
    if (
        lluvia >= P98_LLUVIA
        and humedad >= P98_HUMEDAD
    ):
        return "Rojo"

    # ALERTA NARANJA
    elif (
        lluvia >= P95_LLUVIA
        and humedad >= P98_HUMEDAD
    ):
        return "Naranja"

    # ALERTA AMARILLA
    elif (
        lluvia >= P90_LLUVIA
        and humedad >= P98_HUMEDAD
    ):
        return "Amarillo"

    # CONDICIONES NORMALES
    else:
        return "Verde"


# Recalcular alertas directamente en la aplicación

df["alerta_app"] = df.apply(
    lambda fila: clasificar_alerta(
        fila["lluvia_24h_mm"],
        fila["humedad_superficial"]
    ),
    axis=1
)


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
    Este Sistema de Alerta Temprana constituye un ejercicio
    académico demostrativo.

    Los niveles de alerta no representan alertas oficiales
    ni han sido calibrados con niveles del río, caudales,
    daños históricos o estaciones hidrometeorológicas.
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
    **Periodo histórico**

    2020–2025

    **Predictores**

    🌧️ Precipitación CHIRPS

    💧 Humedad superficial SMAP L3
    """
)


# ============================================================
# SELECTOR DE FECHA
# ============================================================

fecha_seleccionada = st.sidebar.date_input(
    "Seleccione una fecha",
    value=df["fecha"].max().date(),
    min_value=df["fecha"].min().date(),
    max_value=df["fecha"].max().date()
)


registro = df[
    df["fecha"].dt.date
    == fecha_seleccionada
]


# ============================================================
# CREAR PESTAÑAS
# ============================================================

tab_estado, tab_historial, tab_umbrales, tab_metodologia = st.tabs(
    [
        "🚨 Estado del SAT",
        "📊 Historial",
        "🎯 Umbrales",
        "ℹ️ Metodología"
    ]
)


# ============================================================
# TAB 1 — ESTADO DEL SAT
# ============================================================

with tab_estado:

    st.header(
        "Estado del SAT"
    )

    if registro.empty:

        st.warning(
            "No existen datos disponibles para la fecha seleccionada."
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


        # ====================================================
        # PANEL PRINCIPAL DE ALERTA
        # ====================================================

        if alerta == "Rojo":

            st.error(
                """
                ## 🔴 ALERTA ROJA

                Se identifican condiciones extremas de
                precipitación y elevada humedad superficial
                del suelo.
                """
            )


        elif alerta == "Naranja":

            st.warning(
                """
                ## 🟠 ALERTA NARANJA

                Se identifican condiciones muy elevadas
                de precipitación y humedad del suelo.
                """
            )


        elif alerta == "Amarillo":

            st.warning(
                """
                ## 🟡 ALERTA AMARILLA

                Se identifican condiciones elevadas que
                requieren seguimiento.
                """
            )


        else:

            st.success(
                """
                ## 🟢 CONDICIONES NORMALES

                No se identifican condiciones extremas según
                los umbrales estadísticos utilizados por
                este SAT académico.
                """
            )


        # ====================================================
        # MÉTRICAS PRINCIPALES
        # ====================================================

        col1, col2, col3, col4 = st.columns(4)


        col1.metric(
            "🌧️ Precipitación 24 h",
            f"{fila['lluvia_24h_mm']:.1f} mm"
        )


        if "lluvia_48h_mm" in df.columns:

            col2.metric(
                "🌧️ Precipitación 48 h",
                f"{fila['lluvia_48h_mm']:.1f} mm"
            )

        else:

            col2.metric(
                "🌧️ Precipitación 48 h",
                "Sin dato"
            )


        if "lluvia_72h_mm" in df.columns:

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
        # EXPLICACIÓN DE LA ALERTA
        # ====================================================

        st.subheader(
            "¿Por qué se generó esta condición?"
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
                "#### 💧 Humedad del suelo"
            )

            st.write(
                f"""
                **Valor observado:** {humedad:.3f} m³/m³

                **P98:** {P98_HUMEDAD:.3f} m³/m³
                """
            )


        # ====================================================
        # INTERPRETACIÓN AUTOMÁTICA
        # ====================================================

        st.subheader(
            "Interpretación"
        )


        if alerta == "Rojo":

            st.write(
                """
                La precipitación acumulada en 24 horas
                alcanzó o superó el percentil P98 y la
                humedad superficial del suelo también
                alcanzó o superó su percentil P98.

                La coincidencia entre lluvia extrema y
                condiciones de alta humedad determina la
                clasificación como **Alerta Roja**.
                """
            )


        elif alerta == "Naranja":

            st.write(
                """
                La precipitación acumulada en 24 horas
                alcanzó o superó el percentil P95 y la
                humedad superficial del suelo alcanzó el
                umbral de alta humedad.

                Estas condiciones corresponden a una
                **Alerta Naranja**.
                """
            )


        elif alerta == "Amarillo":

            st.write(
                """
                La precipitación acumulada en 24 horas
                alcanzó o superó el percentil P90 y el
                suelo presenta condiciones elevadas de
                humedad.

                Estas condiciones corresponden a una
                **Alerta Amarilla**.
                """
            )


        else:

            st.write(
                """
                La combinación de precipitación y humedad
                del suelo no supera simultáneamente los
                umbrales definidos para los niveles de
                alerta.

                El sistema clasifica la fecha seleccionada
                como **condición normal**.
                """
            )


# ============================================================
# PREPARAR DATOS MENSUALES
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
# TAB 2 — HISTORIAL
# ============================================================

with tab_historial:

    st.header(
        "Historial hidrometeorológico"
    )


    # ========================================================
    # FILTRO POR AÑO
    # ========================================================

    años = sorted(
        df["fecha"].dt.year.unique()
    )


    años_seleccionados = st.multiselect(
        "Seleccione los años que desea visualizar",
        options=años,
        default=años
    )


    mensual_filtrado = mensual[
        mensual["Año"].isin(
            años_seleccionados
        )
    ]


    # ========================================================
    # GRÁFICOS EN DOS COLUMNAS
    # ========================================================

    col1, col2 = st.columns(2)


    # --------------------------------------------------------
    # PRECIPITACIÓN MENSUAL
    # --------------------------------------------------------

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
            mdates.DateFormatter("%Y")
        )

        ax.grid(
            axis="y",
            alpha=0.3
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        st.pyplot(fig)


    # --------------------------------------------------------
    # HUMEDAD MENSUAL
    # --------------------------------------------------------

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
            mdates.DateFormatter("%Y")
        )

        ax.grid(
            axis="y",
            alpha=0.3
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        st.pyplot(fig)


    st.divider()


    # ========================================================
    # EVENTOS HISTÓRICOS DE ALERTA
    # ========================================================

    st.subheader(
        "🚨 Eventos históricos de alerta"
    )


    eventos = df[
        df["alerta_app"]
        != "Verde"
    ][
        [
            "fecha",
            "lluvia_24h_mm",
            "lluvia_48h_mm",
            "lluvia_72h_mm",
            "humedad_superficial",
            "alerta_app"
        ]
    ].copy()


    eventos = eventos.rename(
        columns={
            "fecha": "Fecha",
            "lluvia_24h_mm": "Lluvia 24 h (mm)",
            "lluvia_48h_mm": "Lluvia 48 h (mm)",
            "lluvia_72h_mm": "Lluvia 72 h (mm)",
            "humedad_superficial": "Humedad (m³/m³)",
            "alerta_app": "Nivel de alerta"
        }
    )


    st.dataframe(
        eventos,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 3 — UMBRALES
# ============================================================

with tab_umbrales:

    st.header(
        "Umbrales estadísticos del SAT"
    )


    # ========================================================
    # MÉTRICAS
    # ========================================================

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


    # ========================================================
    # GRÁFICOS DE DISTRIBUCIÓN
    # ========================================================

    col1, col2 = st.columns(2)


    # --------------------------------------------------------
    # DISTRIBUCIÓN PRECIPITACIÓN
    # --------------------------------------------------------

    with col1:

        st.subheader(
            "Distribución de precipitación"
        )


        fig, ax = plt.subplots(
            figsize=(8, 5)
        )


        ax.hist(
            df[
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
            "Precipitación acumulada 24 h (mm)"
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


        st.pyplot(fig)


    # --------------------------------------------------------
    # DISTRIBUCIÓN HUMEDAD
    # --------------------------------------------------------

    with col2:

        st.subheader(
            "Distribución de humedad"
        )


        fig, ax = plt.subplots(
            figsize=(8, 5)
        )


        ax.hist(
            df[
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


        st.pyplot(fig)


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
                "Sin condición crítica",
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
# TAB 4 — METODOLOGÍA
# ============================================================

with tab_metodologia:

    st.header(
        "Metodología"
    )


    st.markdown(
        """
        ### Objetivo

        El Sistema de Alerta Temprana fue desarrollado como
        un ejercicio académico para identificar condiciones
        hidrometeorológicas potencialmente favorables para
        inundaciones en la cuenca del río La Estrella.

        El análisis utiliza información correspondiente al
        periodo **2020–2025**.


        ### 🌧️ Precipitación

        La precipitación se obtuvo a partir del producto
        satelital **CHIRPS Daily**.

        A partir de la precipitación diaria media sobre la
        cuenca se calcularon acumulados de:

        - 24 horas
        - 48 horas
        - 72 horas

        La precipitación acumulada de **24 horas** es la
        variable utilizada para definir los niveles de alerta.


        ### 💧 Humedad superficial del suelo

        La humedad superficial se obtuvo mediante el producto
        **SMAP Nivel 3**.

        La variable representa el contenido volumétrico de
        agua en la capa superficial del suelo.


        ### 🎯 Definición de umbrales

        Los umbrales fueron calculados utilizando la
        distribución histórica de las observaciones diarias
        disponibles entre 2020 y 2025.

        Para la precipitación se utilizaron:

        - **P90:** condición elevada
        - **P95:** condición muy elevada
        - **P98:** condición extrema

        Para la humedad superficial se utilizó:

        - **P98:** condición de alta humedad del suelo


        ### 🚨 Funcionamiento del SAT

        El sistema evalúa simultáneamente dos variables:

        1. Precipitación acumulada en 24 horas.
        2. Humedad superficial del suelo.

        Una alerta se activa solamente cuando la precipitación
        supera el umbral correspondiente **y**, simultáneamente,
        la humedad superficial alcanza o supera su P98.

        Esto representa de forma simplificada el principio
        hidrológico de que una lluvia intensa puede producir
        una mayor respuesta de escorrentía cuando ocurre sobre
        un suelo previamente húmedo.


        ### ⚠️ Limitaciones

        Este SAT es exclusivamente un ejercicio académico.

        Los umbrales:

        - no han sido calibrados con niveles del río;
        - no utilizan caudales observados;
        - no utilizan estaciones meteorológicas locales;
        - no han sido validados con registros históricos
          completos de inundaciones;
        - no deben interpretarse como alertas oficiales.

        El sistema demuestra una metodología para combinar
        precipitación y humedad del suelo mediante umbrales
        estadísticos.
        """
    )


# ============================================================
# PIE DE PÁGINA
# ============================================================

st.divider()

st.caption(
    """
    Sistema de Alerta Temprana — Cuenca del río La Estrella |
    Ejercicio académico CATIE |
    Datos: CHIRPS y SMAP L3
    """
)
