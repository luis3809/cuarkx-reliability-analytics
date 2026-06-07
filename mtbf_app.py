import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis MTBF", layout="wide")
st.title("📊 Análisis MTBF - SAP PM (IW28/IW29)")

# 1. Cargar archivo
file = st.file_uploader("Cargar archivo IW28/IW29 (CSV)", type=["csv"])
if file:
    df = pd.read_csv(file, sep=";", encoding="latin1")

    # Convertir fechas
    df["Fecha de aviso"] = pd.to_datetime(df["Fecha de aviso"], dayfirst=True, errors="coerce")
    df["Inicio avería"] = pd.to_datetime(df["Inicio avería"], dayfirst=True, errors="coerce")
    df["Fin de avería"] = pd.to_datetime(df["Fin de avería"], dayfirst=True, errors="coerce")

    # Duración parada a numérico
    df["Duración parada"] = df["Duración parada"].astype(str).str.replace(",", ".").astype(float)

    st.subheader("Vista previa de datos")
    st.dataframe(df.head())

    # 2. Selección de periodo
    min_date, max_date = df["Fecha de aviso"].min(), df["Fecha de aviso"].max()
    start, end = st.date_input("Seleccionar periodo de evaluación", [min_date, max_date])
    df_periodo = df[(df["Fecha de aviso"] >= pd.to_datetime(start)) & 
                    (df["Fecha de aviso"] <= pd.to_datetime(end))]

    # Filtrar solo avisos de tipo M2 (fallas)
    df_periodo = df_periodo[df_periodo["Clase de aviso"] == "M2"]

    # 3. Agrupación por equipo (Denominación2)
    resultados = []
    for equipo, temp in df_periodo.groupby("Denominación2"):
        temp = temp.sort_values("Fecha de aviso")
        temp["TBF"] = temp["Fecha de aviso"].diff().dt.total_seconds() / 3600  # horas
        mtbf = temp["TBF"].mean() if len(temp) > 1 else None
        resultados.append({
            "Equipo": equipo,
            "Fallas (M2)": len(temp),
            "Tiempo_Detencion_Total (h)": temp["Duración parada"].sum(),
            "MTBF_Horas": round(mtbf,2) if pd.notnull(mtbf) else None
        })

    result = pd.DataFrame(resultados)

    st.subheader("Resultados consolidados por equipo")
    st.dataframe(result)

    # 4. Visualizaciones
    col1, col2, col3 = st.columns(3)

    with col1:
        fig_mtbf = px.bar(result, x="Equipo", y="MTBF_Horas",
                          title="MTBF por equipo (horas)", text_auto=True)
        st.plotly_chart(fig_mtbf, use_container_width=True)

    with col2:
        fig_pareto = px.bar(result.sort_values("Fallas (M2)", ascending=False),
                            x="Equipo", y="Fallas (M2)",
                            title="Pareto de fallas por equipo", text_auto=True)
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col3:
        fig_detencion = px.bar(result.sort_values("Tiempo_Detencion_Total (h)", ascending=False),
                               x="Equipo", y="Tiempo_Detencion_Total (h)",
                               title="Tiempo total de detención por equipo", text_auto=True)
        st.plotly_chart(fig_detencion, use_container_width=True)

    # 5. Conclusión automática
    avg_mtbf = result["MTBF_Horas"].mean()
    if avg_mtbf > 4000:
        conclusion = "✅ Alta confiabilidad (MTBF > 4000 horas)."
    elif avg_mtbf > 2000:
        conclusion = "⚠️ Confiabilidad moderada, existen oportunidades de mejora."
    else:
        conclusion = "❌ Frecuencia de fallas alta, se recomienda análisis de causa raíz."
    st.success(conclusion)