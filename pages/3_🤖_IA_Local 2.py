import streamlit as st
from core.ai_client import AIClient

st.set_page_config(page_title="IA Local", page_icon="🤖", layout="wide")
st.header("🤖 IA Local")

col1, col2 = st.columns(2)
with col1:
    endpoint = st.text_input("Endpoint", value="http://localhost:11434")
with col2:
    model = st.text_input("Modelo", value="llama3.2")

if st.button("🔍 Testar Conexão"):
    client = AIClient(endpoint, model)
    success, result = client.test_connection()
    if success:
        st.success(f"✅ Conectado! {len(result)} modelos disponíveis")
    else:
        st.error(f"❌ Erro: {result}")

st.divider()

prompt = st.text_area("Prompt", value="Explique EventID 4625 em PT-BR", height=100)
if st.button("▶️ Executar", type="primary"):
    client = AIClient(endpoint, model)
    with st.spinner("Processando..."):
        response = client.ask(prompt)
    st.markdown(response)
