import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Timeline", page_icon="📈", layout="wide")
st.header("📈 Timeline de Eventos")

if st.session_state.get('logs', pd.DataFrame()).empty:
    st.warning("Importe logs na página inicial")
else:
    df = st.session_state.logs.dropna(subset=['TimeCreated'])
    
    if not df.empty:
        df['Hour'] = df['TimeCreated'].dt.floor('h')
        counts = df.groupby(['Hour', 'Level']).size().reset_index(name='count')
        
        fig = px.bar(counts, x='Hour', y='count', color='Level',
                    title='Eventos por Hora',
                    color_discrete_map={
                        'Critical': '#ff4d4d', 'Error': '#ef4444',
                        'Warning': '#f59e0b', 'Information': '#3b82f6'
                    })
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem eventos com timestamp válido")
