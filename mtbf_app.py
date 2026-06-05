import streamlit as st
import pandas as pd
import plotly.express as px
st.write("Plotly test")
# ----------------------------------
# CONFIG
# ----------------------------------

st.set_page_config(
    page_title="SAP MTBF Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SAP PM MTBF Analytics")
st.markdown(
    """
    Cargue un archivo CSV exportado desde SAP IW28/IW29
    para calcular automáticamente MTBF por equipo.
    """
)

# ----------------------------------
# FILE UPLOAD
# ----------------------------------

uploaded_file = st.file_uploader(
    "Cargar archivo CSV",
    type=["csv"]
)

if uploaded_file is not None:

    # ----------------------------------
    # READ FILE
    # ----------------------------------

    try:
        df = pd.read_csv(
            uploaded_file,
            sep=";",
            encoding="latin1"
        )
    except:
        df = pd.read_csv(uploaded_file)

    st.subheader("Vista previa de datos")

    st.dataframe(
        df.head(),
        use_container_width=True
    )

    # ----------------------------------
    # COLUMN VALIDATION
    # ----------------------------------

    required_columns = [
        "Equipo",
        "Fecha de aviso"
    ]

    missing_columns = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing_columns:

        st.error(
            f"Columnas faltantes: {missing_columns}"
        )

        st.stop()

    # ----------------------------------
    # DATE FORMAT
    # ----------------------------------

    df["Fecha de aviso"] = pd.to_datetime(
        df["Fecha de aviso"],
        errors="coerce",
        dayfirst=True
    )

    df = df.dropna(
        subset=["Fecha de aviso"]
    )

    # ----------------------------------
    # MTBF CALCULATION
    # ----------------------------------

    mtbf_results = []

    equipos = (
        df["Equipo"]
        .dropna()
        .unique()
    )

    for equipo in equipos:

        temp = (
            df[df["Equipo"] == equipo]
            .sort_values("Fecha de aviso")
            .copy()
        )

        temp["TBF"] = (
            temp["Fecha de aviso"]
            .diff()
            .dt.days
        )

        mtbf = temp["TBF"].mean()

        mtbf_results.append(
            {
                "Equipo": equipo,
                "Eventos": len(temp),
                "MTBF_Dias": round(mtbf, 2)
                if pd.notnull(mtbf)
                else None
            }
        )

    result = pd.DataFrame(mtbf_results)

    result = result.dropna()

    if len(result) == 0:

        st.warning(
            "No existen suficientes eventos para calcular MTBF."
        )

        st.stop()

    # ----------------------------------
    # KPIs
    # ----------------------------------

    st.subheader("Indicadores")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Equipos",
        len(result)
    )

    col2.metric(
        "Avisos",
        len(df)
    )

    col3.metric(
        "MTBF Promedio",
        f"{round(result['MTBF_Dias'].mean(),1)} días"
    )

    # ----------------------------------
    # RANKING
    # ----------------------------------

    st.subheader("Ranking MTBF")

    ranking = result.sort_values(
        "MTBF_Dias",
        ascending=False
    )

    st.dataframe(
        ranking,
        use_container_width=True
    )

    # ----------------------------------
    # SCATTER PLOT
    # ----------------------------------

    st.subheader(
        "MTBF vs Número de Eventos"
    )

    fig_scatter = px.scatter(
        ranking,
        x="Eventos",
        y="MTBF_Dias",
        hover_name="Equipo",
        trendline="ols"
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )

    # ----------------------------------
    # PARETO
    # ----------------------------------

    st.subheader(
        "Pareto de Equipos"
    )

    pareto = (
        ranking
        .sort_values(
            "Eventos",
            ascending=False
        )
        .head(15)
    )

    fig_bar = px.bar(
        pareto,
        x="Equipo",
        y="Eventos"
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )

    # ----------------------------------
    # EQUIPO CRÍTICO
    # ----------------------------------

    critical = result.loc[
        result["MTBF_Dias"].idxmin()
    ]

    st.subheader(
        "Equipo Crítico"
    )

    st.warning(
        f"""
        Equipo: {critical['Equipo']}

        MTBF: {critical['MTBF_Dias']} días

        Eventos: {critical['Eventos']}
        """
    )

    # ----------------------------------
    # CONCLUSIÓN AUTOMÁTICA
    # ----------------------------------

    avg_mtbf = result["MTBF_Dias"].mean()

    if avg_mtbf > 180:

        conclusion = """
        Los activos presentan una
        confiabilidad adecuada.

        El MTBF promedio es superior
        a 180 días.

        Se recomienda mantener la
        estrategia actual.
        """

    elif avg_mtbf > 90:

        conclusion = """
        La confiabilidad es moderada.

        Existen oportunidades para
        optimizar los planes de
        mantenimiento.
        """

    else:

        conclusion = """
        La frecuencia de fallas es alta.

        Se recomienda realizar análisis
        de causa raíz y revisión de
        estrategias de mantenimiento.
        """

    st.subheader(
        "Conclusión Automática"
    )

    st.success(conclusion)

    # ----------------------------------
    # DOWNLOAD
    # ----------------------------------

    csv_download = ranking.to_csv(
        index=False
    )

    st.download_button(
        "Descargar Ranking MTBF",
        csv_download,
        "ranking_mtbf.csv",
        "text/csv"
    )