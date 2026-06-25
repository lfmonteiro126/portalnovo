import streamlit as st
import pandas as pd

st.set_page_config(page_title="Logs", page_icon="📋", layout="wide")
st.header("📋 Visualização de Logs")

if st.session_state.get('logs', pd.DataFrame()).empty:
    st.warning("Importe logs na página inicial")
else:
    df = st.session_state.logs
    
    col1, col2 = st.columns(2)
    with col1:
        level_filter = st.multiselect("Nível", df['Level'].unique(), default=df['Level'].unique())
    with col2:
        search = st.text_input("🔍 Buscar")
    
    filtered = df[df['Level'].isin(level_filter)]
    if search:
        filtered = filtered[filtered['Message'].str.contains(search, case=False, na=False)]
    
    st.dataframe(filtered, use_container_width=True, height=600)
    
    csv = filtered.to_csv(index=False)
    st.download_button("📤 Exportar", csv, "logs_filtrados.csv", "text/csv")
