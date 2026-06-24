import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Event Portal Pro",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🖥️ Event Portal Pro")
st.markdown("### Troubleshooting Inteligente para Windows Server")

with st.sidebar:
    st.header("📂 Importar Logs")
    uploaded_files = st.file_uploader(
        "Selecione CSV ou XML",
        type=['csv', 'xml'],
        accept_multiple_files=True
    )

if 'logs' not in st.session_state:
    st.info("👈 Importe logs do Event Viewer na barra lateral")
    
    st.markdown("### 📖 Como exportar logs:")
    st.markdown("""
    1. Abra **Event Viewer** (`eventvwr.msc`)
    2. Botão direito no log → **Save All Events As...**
    3. Salve como **CSV** ou **XML**
    4. Importe aqui
    """)
else:
    df = st.session_state.logs
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(df))
    col2.metric("Erros", len(df[df['Level'].str.contains('Error|Critical', case=False, na=False)]))
    col3.metric("Fontes", df['Source'].nunique() if 'Source' in df.columns else 0)
    
    st.dataframe(df, use_container_width=True, height=600)
