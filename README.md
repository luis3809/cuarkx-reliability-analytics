# SAP MTBF Analytics

Aplicación desarrollada en Python y Streamlit para calcular automáticamente el MTBF a partir de exportaciones SAP PM (IW28 / IW29).

## Funcionalidades

- Carga de archivos CSV SAP
- Cálculo automático MTBF
- Ranking de equipos
- Gráfico de dispersión
- Pareto de equipos
- Identificación de equipo crítico
- Conclusión automática

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run mtbf_app.py
```