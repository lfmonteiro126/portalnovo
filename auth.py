# auth.py
import streamlit as st
import hashlib

def check_password():
    """Retorna True se autenticado, False caso contrário"""
    
    # Se já está autenticado nesta sessão, libera direto
    if st.session_state.get("authenticated", False):
        return True

    def login_callback():
        user = st.session_state.get("username", "")
        pwd = st.session_state.get("password", "")
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()

        # Tenta ler secrets
        try:
            passwords = st.secrets.get("passwords", {})
        except Exception:
            passwords = {}

        if user in passwords and passwords[user] == pwd_hash:
            st.session_state.authenticated = True
            st.session_state.user = user
            # ❌ REMOVIDO: st.rerun() - Streamlit já faz isso automaticamente
        else:
            st.error("😕 Usuário ou senha incorretos")

    # Tela de Login
    st.title("🔐 Login - Event Portal Pro")
    st.markdown("### Acesse com suas credenciais")
    st.text_input("👤 Usuário", key="username")
    st.text_input("🔑 Senha", type="password", key="password")
    st.button("Entrar", on_click=login_callback, use_container_width=True)
    
    return False