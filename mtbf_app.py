import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

uploaded_file = st.file_uploader("Cargar archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=";", encoding="latin1")
    except:
        df = pd.read_csv(uploaded_file)

    st.subheader("Vista previa de datos")
    st.dataframe(df.head(), use_container_width=True)

    required_columns = ["Equipo", "Fecha de aviso"]
    missing_columns = [c for c in required_columns if c not in df.columns]

    if missing_columns:
        st.error(f"Columnas faltantes: {missing_columns}")
        st.stop()

    df["Fecha de aviso"] = pd.to_datetime(df["Fecha de aviso"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Fecha de aviso"])

    mtbf_results = []
    equipos = df["Equipo"].dropna().unique()

    for equipo in equipos:
        temp = df[df["Equipo"] == equipo].sort_values("Fecha de aviso").copy()
        temp["TBF"] = temp["Fecha de aviso"].diff().dt.days
        if len(temp) > 1:
            mtbf = temp["TBF"].mean()
        else:
            mtbf = None
        mtbf_results.append({
            "Equipo": equipo,
            "Eventos": len(temp),
            "MTBF_Dias": round(mtbf, 2) if pd.notnull(mtbf) else None
        })

    result = pd.DataFrame(mtbf_results).dropna()

    if len(result) == 0:
        st.warning("No existen suficientes eventos para calcular MTBF.")
        st.stop()

    st.subheader("Indicadores")
    col1, col2, col3 = st.columns(3)
    col1.metric("Equipos", len(result))
    col2.metric("Avisos", len(df))
    col3.metric("MTBF Promedio", f"{round(result['MTBF_Dias'].mean(),1)} días")

    st.subheader("Ranking MTBF")
    ranking = result.sort_values("MTBF_Dias", ascending=False)
    st.dataframe(ranking, use_container_width=True)

    # SCATTER PLOT con Seaborn
    st.subheader("MTBF vs Número de Eventos")
    fig, ax = plt.subplots()
    sns.scatterplot(data=ranking, x="Eventos", y="MTBF_Dias", hue="Equipo", ax=ax)
    st.pyplot(fig)

    # PARETO con Matplotlib
    st.subheader("Pareto de Equipos")
    pareto = ranking.sort_values("Eventos", ascending=False).head(15)
    fig2, ax2 = plt.subplots()
    sns.barplot(data=pareto, x="Equipo", y="Eventos", ax=ax2)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha="right")
    st.pyplot(fig2)

    # Equipo crítico
    critical = result.loc[result["MTBF_Dias"].idxmin()]
    st.subheader("Equipo Crítico")
    st.warning(f"Equipo: {critical['Equipo']}\n\nMTBF: {critical['MTBF_Dias']} días\n\nEventos: {critical['Eventos']}")

    # Conclusión automática
    avg_mtbf = result["MTBF_Dias"].mean()
    if avg_mtbf > 180:
        conclusion = "Los activos presentan una confiabilidad adecuada. MTBF > 180 días."
    elif avg_mtbf > 90:
        conclusion = "La confiabilidad es moderada. Existen oportunidades de optimización."
    else:
        conclusion = "La frecuencia de fallas es alta. Se recomienda análisis de causa raíz."
    st.subheader("Conclusión Automática")
    st.success(conclusion)

    # Descarga
    csv_download = ranking.to_csv(index=False)
    st.download_button("Descargar Ranking MTBF", csv_download, "ranking_mtbf.csv", "text/csv")