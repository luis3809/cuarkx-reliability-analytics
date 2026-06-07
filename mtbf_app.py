import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

st.set_page_config(page_title="Análisis MTBF", layout="wide")
st.title("📊 Análisis MTBF - SAP PM (IW28/IW29)")

# Función para quitar acentos
def quitar_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c)
    )

# 1. Cargar archivo
file = st.file_uploader("Cargar archivo IW28/IW29 (CSV)", type=["csv"])
if file:
    df = pd.read_csv(file, sep=";", encoding="latin1")

    # Normalizar nombres de columnas
    df.columns = (
        df.columns.str.strip()
                  .map(quitar_acentos)   # elimina acentos
                  .str.replace(" ", "_") # reemplaza espacios por _
                  .str.lower()           # pasa a minúsculas
    )

    # Renombrar a nombres simples
    df.rename(columns={
        "denominacion2": "Equipo",
        "fecha_de_aviso": "FechaAviso",
        "inicio_averia": "InicioAveria",
        "fin_de_averia": "FinAveria",
        "duracion_parada": "DuracionParada",
        "clase_de_aviso": "ClaseAviso"
    }, inplace=True)

      # Convertir fechas
    df["FechaAviso"] = pd.to_datetime(df["FechaAviso"], dayfirst=True, errors="coerce")
    if "InicioAveria" in df.columns:
        df["InicioAveria"] = pd.to_datetime(df["InicioAveria"], dayfirst=True, errors="coerce")
    if "FinAveria" in df.columns:
        df["FinAveria"] = pd.to_datetime(df["FinAveria"], dayfirst=True, errors="coerce")

    # Duración parada a numérico
    df["DuracionParada"] = df["DuracionParada"].astype(str).str.replace(",", ".").astype(float)

    # 2. Selección de periodo
    st.write("### Selección de periodo de evaluación")
    min_date, max_date = df["FechaAviso"].min(), df["FechaAviso"].max()
    start, end = st.date_input("Seleccionar periodo de evaluación", [min_date, max_date])

    # Calcular horas totales del periodo
    horas_periodo = (pd.to_datetime(end) - pd.to_datetime(start)).days * 24

    df_periodo = df[(df["FechaAviso"] >= pd.to_datetime(start)) & 
                    (df["FechaAviso"] <= pd.to_datetime(end))]

    # Filtrar solo avisos de tipo M2 (fallas)
    if "ClaseAviso" in df.columns:
        df_periodo = df_periodo[df_periodo["ClaseAviso"] == "M2"]

    # 3. Agrupación por equipo
    resultados = []
    for equipo, temp in df_periodo.groupby("Equipo"):
        n_fallas = len(temp)
        tiempo_detencion = temp["DuracionParada"].sum()
        tiempo_operacion = horas_periodo - tiempo_detencion
        mtbf = tiempo_operacion / n_fallas if n_fallas > 0 else None

        resultados.append({
            "Equipo": equipo,
            "Fallas (M2)": n_fallas,
            "Tiempo_Detencion_Total (h)": tiempo_detencion,
            "Tiempo_Operacion (h)": tiempo_operacion,
            "MTBF_Horas": round(mtbf, 2) if mtbf else None
        })

    result = pd.DataFrame(resultados)

    st.subheader("Resultados consolidados por equipo")
    st.dataframe(result)

   # 📊 Evolución temporal (fila completa arriba)
st.subheader("Evolución temporal de MTBF")
fig_mtbf = px.scatter(df_periodo, 
                      x="FechaAviso", 
                      y="DuracionParada", 
                      color="Equipo",
                      title="MTBF por equipo en el tiempo",
                      labels={"FechaAviso":"Fecha de aviso", "DuracionParada":"MTBF (horas)"})
fig_mtbf.update_traces(mode="lines+markers", line=dict(shape="linear"))
st.plotly_chart(fig_mtbf, use_container_width=True)

# 📊 Segunda fila: Pareto y Detención en columnas
st.subheader("Análisis comparativo de fallas y detenciones")
col2, col3 = st.columns(2)

with col2:
    df_pareto = result.sort_values("Fallas (M2)", ascending=False)
    fig_pareto = px.bar(df_pareto, x="Equipo", y="Fallas (M2)",
                        title="Pareto de fallas por equipo", text_auto=True)
    st.plotly_chart(fig_pareto, use_container_width=True)

with col3:
    df_detencion = result.sort_values("Tiempo_Detencion_Total (h)", ascending=False)
    fig_detencion = px.bar(df_detencion, x="Equipo", y="Tiempo_Detencion_Total (h)",
                           title="Tiempo total de detención por equipo", text_auto=True)
    st.plotly_chart(fig_detencion, use_container_width=True)

# 📊 Tercera fila: Matriz de disponibilidad
st.subheader("Matriz de Disponibilidad")
fig_heat = px.density_heatmap(result, x="Equipo", y="Fallas (M2)", z="Disponibilidad",
                              color_continuous_scale="RdYlGn",
                              title="Disponibilidad (%) por equipo")
st.plotly_chart(fig_heat, use_container_width=True)

# 📊 Cuarta fila: Clustering
st.subheader("Clustering de Equipos por Confiabilidad")
X = result[["MTBF_Horas","MTTR_Horas","Fallas (M2)"]].dropna()
kmeans = KMeans(n_clusters=3, random_state=42)
result["Cluster"] = kmeans.fit_predict(X)

fig_cluster = px.scatter(result, x="MTBF_Horas", y="MTTR_Horas", color="Cluster",
                         size="Tiempo_Detencion_Total (h)",
                         hover_data=["Equipo","Disponibilidad"],
                         title="Segmentación de Equipos")
st.plotly_chart(fig_cluster, use_container_width=True)