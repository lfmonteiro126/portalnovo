import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import warnings
from auth import check_password

# Silencia warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*use_container_width.*')

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(
    page_title="Event Portal Pro",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if not check_password():
    st.stop()


# ==========================================
# VERIFICA STATUS DA IA
# ==========================================
def check_ai_status():
    """Testa conexão com IA local"""
    try:
        from core.ai_client import AIClient
        endpoint = st.session_state.get('ai_endpoint', 'http://localhost:11434')
        model = st.session_state.get('ai_model', 'llama3.2')
        
        if not endpoint:
            return False, "Não configurado", None
        
        client = AIClient(endpoint, model)
        success, models = client.test_connection()
        
        if success:
            if model in models:
                return True, f"Online · {model}", models
            else:
                return False, f"Modelo '{model}' não encontrado", models
        return False, "Sem conexão", models
    except Exception as e:
        return False, f"Erro: {str(e)[:30]}", None

# Inicializa status
if 'ai_status' not in st.session_state:
    is_online, status_msg, available_models = check_ai_status()
    st.session_state.ai_status = is_online
    st.session_state.ai_status_msg = status_msg
    st.session_state.ai_available_models = available_models or []

# ==========================================
# CSS CUSTOMIZADO - DESIGN MODERNO
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%); background-attachment: fixed; color: #e2e8f0; }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px !important; }
    .app-header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; background: linear-gradient(135deg, rgba(15,23,42,0.8), rgba(30,41,59,0.6)); backdrop-filter: blur(20px); border-radius: 16px; border: 1px solid rgba(148,163,184,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.3); margin-bottom: 2rem; transition: all 0.3s ease; }
    .app-header:hover { border-color: rgba(148,163,184,0.2); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }
    .app-title { font-size: 1.75rem; font-weight: 800; background: linear-gradient(135deg, #f1f5f9, #cbd5e1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.03em; margin: 0; }
    .app-subtitle { font-size: 0.875rem; color: #94a3b8; margin: 0.25rem 0 0 0; }
    .app-badge { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; cursor: help; box-shadow: 0 2px 8px rgba(0,0,0,0.2); transition: all 0.3s ease; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.7;transform:scale(1.1)} }
    .stat-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 1rem; margin-bottom: 2rem; }
    .stat-card { background: linear-gradient(135deg, rgba(15,23,42,0.6), rgba(30,41,59,0.4)); border: 1px solid rgba(148,163,184,0.1); border-radius: 12px; padding: 1.25rem 1.5rem; transition: all 0.3s cubic-bezier(0.4,0,0.2,1); position: relative; overflow: hidden; backdrop-filter: blur(10px); }
    .stat-card::before { content:''; position:absolute; top:0;left:0;right:0; height:3px; background:linear-gradient(90deg,#3b82f6,#8b5cf6); opacity:0; transition:opacity 0.3s; }
    .stat-card:hover::before { opacity:1; }
    .stat-card:hover { border-color: rgba(148,163,184,0.25); transform:translateY(-4px); box-shadow:0 12px 32px rgba(0,0,0,0.3); }
    .stat-label { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-bottom: 0.75rem; }
    .stat-value { font-size: 2rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.03em; line-height: 1; }
    .stat-value.critical { color:#f87171; text-shadow:0 0 20px rgba(248,113,113,0.4); }
    .stat-value.error { color:#fb7185; text-shadow:0 0 20px rgba(251,113,133,0.4); }
    .stat-value.warning { color:#fbbf24; text-shadow:0 0 20px rgba(251,191,36,0.4); }
    .stat-value.info { color:#60a5fa; text-shadow:0 0 20px rgba(96,165,250,0.4); }
    .level-badge { display:inline-flex; align-items:center; gap:0.4rem; padding:0.25rem 0.75rem; border-radius:6px; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; }
    .level-badge::before { content:''; width:6px;height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 8px currentColor; }
    .level-critical { background:linear-gradient(135deg,rgba(248,113,113,0.15),rgba(248,113,113,0.08)); color:#f87171; border:1px solid rgba(248,113,113,0.3); }
    .level-error { background:linear-gradient(135deg,rgba(251,113,133,0.15),rgba(251,113,133,0.08)); color:#fb7185; border:1px solid rgba(251,113,133,0.3); }
    .level-warning { background:linear-gradient(135deg,rgba(251,191,36,0.15),rgba(251,191,36,0.08)); color:#fbbf24; border:1px solid rgba(251,191,36,0.3); }
    .level-information { background:linear-gradient(135deg,rgba(96,165,250,0.15),rgba(96,165,250,0.08)); color:#60a5fa; border:1px solid rgba(96,165,250,0.3); }
    .level-verbose { background:linear-gradient(135deg,rgba(148,163,184,0.15),rgba(148,163,184,0.08)); color:#94a3b8; border:1px solid rgba(148,163,184,0.3); }
    .stButton>button { border-radius:8px!important; font-weight:600!important; font-size:0.875rem!important; padding:0.625rem 1.25rem!important; transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important; border:1px solid transparent!important; }
    .stButton>button[kind="primary"] { background:linear-gradient(135deg,#3b82f6,#2563eb)!important; box-shadow:0 4px 12px rgba(59,130,246,0.3)!important; }
    .stButton>button[kind="primary"]:hover { background:linear-gradient(135deg,#2563eb,#1d4ed8)!important; transform:translateY(-2px)!important; box-shadow:0 8px 20px rgba(59,130,246,0.4)!important; }
    .stButton>button:not([kind="primary"]) { background:rgba(30,41,59,0.5)!important; border:1px solid rgba(148,163,184,0.2)!important; }
    .stButton>button:not([kind="primary"]):hover { background:rgba(30,41,59,0.8)!important; border-color:rgba(148,163,184,0.4)!important; transform:translateY(-1px)!important; }
    section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0a0e1a,#0f172a)!important; border-right:1px solid rgba(148,163,184,0.1)!important; }
    section[data-testid="stSidebar"]>div { padding-top:2rem!important; }
    .sidebar-user { display:flex; align-items:center; gap:1rem; padding:1rem; background:linear-gradient(135deg,rgba(30,41,59,0.5),rgba(15,23,42,0.3)); border-radius:12px; margin-bottom:2rem; border:1px solid rgba(148,163,184,0.08); transition:all 0.3s; }
    .sidebar-user:hover { border-color:rgba(148,163,184,0.15); background:linear-gradient(135deg,rgba(30,41,59,0.7),rgba(15,23,42,0.5)); }
    .user-avatar { width:44px;height:44px; background:linear-gradient(135deg,#3b82f6,#8b5cf6,#ec4899); border-radius:12px; display:flex; align-items:center; justify-content:center; font-weight:700; color:white; font-size:1.1rem; box-shadow:0 4px 12px rgba(59,130,246,0.3); }
    [data-testid="stDialog"] { background:linear-gradient(135deg,#0f172a,#1e293b)!important; border:1px solid rgba(148,163,184,0.2)!important; border-radius:16px!important; box-shadow:0 25px 80px rgba(0,0,0,0.6)!important; backdrop-filter:blur(20px)!important; }
    .event-grid { display:grid; grid-template-columns:140px 1fr; gap:0.75rem 1.5rem; margin:1.5rem 0; }
    .event-key { color:#94a3b8; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; padding:0.5rem 0; }
    .event-val { color:#e2e8f0; font-size:0.875rem; padding:0.5rem 0.75rem; word-break:break-word; font-family:'JetBrains Mono',monospace; background:rgba(2,6,23,0.4); border-radius:6px; border-left:3px solid #3b82f6; }
    .msg-box { background:linear-gradient(135deg,#020617,#0f172a); border:1px solid rgba(148,163,184,0.15); border-radius:10px; padding:1.25rem; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#cbd5e1; line-height:1.7; max-height:300px; overflow-y:auto; white-space:pre-wrap; word-break:break-word; box-shadow:inset 0 2px 10px rgba(0,0,0,0.3); }
    .tip-panel { background:linear-gradient(135deg,rgba(139,92,246,0.1),rgba(59,130,246,0.05)); border:1px solid rgba(139,92,246,0.25); border-radius:12px; padding:1.5rem; margin:1.5rem 0; box-shadow:0 4px 20px rgba(139,92,246,0.1); }
    .tip-title { color:#c4b5fd; font-weight:700; font-size:1rem; margin-bottom:1rem; display:flex; align-items:center; gap:0.6rem; text-transform:uppercase; letter-spacing:0.05em; }
    .tip-cause { background:rgba(2,6,23,0.7); padding:1rem; border-radius:8px; border-left:4px solid #8b5cf6; margin:1rem 0; font-size:0.875rem; color:#cbd5e1; box-shadow:inset 0 2px 8px rgba(0,0,0,0.3); }
    .tip-steps { margin-top:1rem; padding-left:1.5rem; color:#cbd5e1; font-size:0.875rem; line-height:1.8; }
    .tip-steps li { margin-bottom:0.5rem; }
    .ai-response { background:linear-gradient(135deg,#020617,#0f172a); border:1px solid rgba(139,92,246,0.3); border-radius:12px; padding:1.25rem; font-size:0.875rem; color:#e2e8f0; line-height:1.8; max-height:450px; overflow-y:auto; white-space:pre-wrap; word-break:break-word; margin-top:1rem; box-shadow:0 4px 20px rgba(139,92,246,0.1); }
    .ai-header { display:flex; align-items:center; justify-content:space-between; padding:0.75rem 0; margin-bottom:1rem; }
    .ai-badge { display:inline-flex; align-items:center; gap:0.5rem; padding:0.375rem 0.75rem; background:linear-gradient(135deg,rgba(139,92,246,0.2),rgba(59,130,246,0.1)); border:1px solid rgba(139,92,246,0.4); border-radius:8px; font-size:0.75rem; color:#c4b5fd; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; box-shadow:0 2px 8px rgba(139,92,246,0.2); }
    .ai-timing { font-size:0.75rem; color:#64748b; font-family:'JetBrains Mono',monospace; }
    .section-title { font-size:0.8rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em; margin:2rem 0 1rem 0; display:flex; align-items:center; gap:0.75rem; }
    .section-title::before { content:''; width:4px;height:16px; background:linear-gradient(180deg,#3b82f6,#8b5cf6); border-radius:2px; box-shadow:0 0 10px rgba(59,130,246,0.5); }
    .stTabs [data-baseweb="tab-list"] { gap:4px; background:rgba(15,23,42,0.5); padding:4px; border-radius:12px; border:1px solid rgba(148,163,184,0.1); margin-bottom:1.5rem; }
    .stTabs [data-baseweb="tab"] { background:transparent; color:#94a3b8; padding:0.75rem 1.25rem!important; border-radius:8px; font-size:0.875rem; font-weight:600; transition:all 0.2s; }
    .stTabs [data-baseweb="tab"]:hover { background:rgba(30,41,59,0.5); color:#e2e8f0; }
    .stTabs [aria-selected="true"] { background:linear-gradient(135deg,#1e293b,#334155)!important; color:#f1f5f9!important; box-shadow:0 2px 8px rgba(0,0,0,0.2); }
    ::-webkit-scrollbar { width:10px; height:10px; }
    ::-webkit-scrollbar-track { background:rgba(15,23,42,0.5); border-radius:5px; }
    ::-webkit-scrollbar-thumb { background:linear-gradient(180deg,#475569,#334155); border-radius:5px; border:2px solid rgba(15,23,42,0.5); }
    ::-webkit-scrollbar-thumb:hover { background:linear-gradient(180deg,#64748b,#475569); }
    .stTextInput>div>div>input,.stSelectbox>div>div>select,.stMultiSelect>div>div { background:rgba(2,6,23,0.6)!important; border:1px solid rgba(148,163,184,0.15)!important; border-radius:8px!important; color:#e2e8f0!important; transition:all 0.2s!important; }
    .stTextInput>div>div>input:focus,.stSelectbox>div>div>select:focus,.stMultiSelect>div>div:focus-within { border-color:#3b82f6!important; box-shadow:0 0 0 3px rgba(59,130,246,0.1)!important; }
    .streamlit-expanderHeader { background:rgba(30,41,59,0.3)!important; border:1px solid rgba(148,163,184,0.1)!important; border-radius:8px!important; transition:all 0.2s!important; }
    .streamlit-expanderHeader:hover { background:rgba(30,41,59,0.5)!important; border-color:rgba(148,163,184,0.2)!important; }
    footer { visibility:hidden; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
    .main>div:first-child { animation:fadeIn 0.5s ease-out; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER COM BADGE DINÂMICO
# ==========================================
is_online = st.session_state.get('ai_status', False)
status_msg = st.session_state.get('ai_status_msg', 'Verificando...')

# Constrói badge como string
if is_online:
    badge_style = "background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981;"
    dot_style = "background: #10b981; box-shadow: 0 0 8px #10b981;"
    badge_text = "Local AI Ready"
    title_attr = ""
else:
    badge_style = "background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444;"
    dot_style = "background: #ef4444; box-shadow: none;"
    badge_text = "AI Offline"
    title_attr = f' title="{status_msg}"'

header_html = f"""
<div class="app-header">
    <div>
        <h1 class="app-title">🖥️ Event Portal Pro</h1>
        <p class="app-subtitle">Windows Server Troubleshooting Intelligence</p>
    </div>
    <div class="app-badge" style="{badge_style}"{title_attr}>
        <span class="status-dot" style="{dot_style}"></span>
        {badge_text}
    </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    user = st.session_state.get('user', 'admin')
    st.markdown(f"""
    <div class="sidebar-user">
        <div class="user-avatar">{user[0].upper()}</div>
        <div>
            <div style="color: #f1f5f9; font-weight: 600; font-size: 0.9rem;">{user}</div>
            <div style="color: #64748b; font-size: 0.75rem;">Administrator</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # CONFIGURAÇÃO DA IA
    # ==========================================
    st.markdown("#### 🤖 IA Local")
    
    ai_online = st.session_state.get('ai_status', False)
    ai_msg = st.session_state.get('ai_status_msg', '')
    
    if ai_online:
        st.success(f"✅ {ai_msg}")
    else:
        st.error(f"❌ {ai_msg}")
    
    with st.expander("⚙️ Configurar", expanded=not ai_online):
        ai_endpoint = st.text_input(
            "Endpoint",
            value=st.session_state.get('ai_endpoint', 'http://localhost:11434'),
            placeholder="http://localhost:11434"
        )
        
        available = st.session_state.get('ai_available_models', [])
        if available:
            default_model = st.session_state.get('ai_model', 'llama3.2')
            if default_model not in available:
                default_model = available[0]
            ai_model = st.selectbox(
                "Modelo",
                options=available,
                index=available.index(default_model) if default_model in available else 0
            )
        else:
            ai_model = st.text_input(
                "Modelo",
                value=st.session_state.get('ai_model', 'llama3.2'),
                placeholder="llama3.2"
            )
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Salvar", use_container_width=True):
                st.session_state.ai_endpoint = ai_endpoint
                st.session_state.ai_model = ai_model
                st.success("Salvo!")
                st.rerun()
        with c2:
            if st.button("🔄 Testar", use_container_width=True):
                st.session_state.ai_endpoint = ai_endpoint
                st.session_state.ai_model = ai_model
                with st.spinner("Testando..."):
                    is_ok, msg, models = check_ai_status()
                    st.session_state.ai_status = is_ok
                    st.session_state.ai_status_msg = msg
                    st.session_state.ai_available_models = models or []
                st.rerun()
    
    st.markdown("---")
    
    # ==========================================
    # IMPORT DE LOGS (COM PROTEÇÃO)
    # ==========================================
    st.markdown("#### 📂 Import")
    uploaded_files = st.file_uploader(
        "Event Viewer logs",
        type=['csv', 'xml', 'tsv', 'txt'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        for f in uploaded_files:
            st.caption(f"📎 `{f.name}` · {f.size/1024:.1f} KB")
        
        # Flag para evitar processamento duplicado
        processing_key = f"processing_{hash(tuple(f.name for f in uploaded_files))}"
        
        if not st.session_state.get(processing_key, False):
            if st.button("Processar arquivos", type="primary", use_container_width=True):
                st.session_state[processing_key] = True
                
                try:
                    from core.parser import parse_logs
                    all_logs = []
                    errors = []
                    
                    for file in uploaded_files:
                        try:
                            # CRÍTICO: Cria cópia em memória
                            file.seek(0)
                            file_copy = io.BytesIO(file.read())
                            file_copy.name = file.name
                            file_copy.seek(0)
                            
                            df_p = parse_logs(file_copy)
                            
                            # Verifica se retornou DataFrame válido
                            if df_p is None:
                                errors.append(f"{file.name}: Parser retornou None")
                                continue
                            
                            if not df_p.empty:
                                df_p['SourceFile'] = file.name
                                all_logs.append(df_p)
                                st.success(f"✓ {file.name}: {len(df_p)} eventos")
                            else:
                                errors.append(f"{file.name}: Nenhum evento válido")
                        except Exception as e:
                            errors.append(f"{file.name}: {e}")
                            st.error(f"✗ {file.name}: {e}")
                    
                    if all_logs:
                        combined = pd.concat(all_logs, ignore_index=True)
                        st.session_state.logs = combined
                        st.success(f"✅ Total: {len(combined)} eventos")
                        
                        if errors:
                            with st.expander(f"⚠️ {len(errors)} arquivo(s) com problema"):
                                for err in errors:
                                    st.warning(err)
                        
                        # Reseta flag
                        if processing_key in st.session_state:
                            del st.session_state[processing_key]
                        
                        import time
                        time.sleep(1.5)
                        st.rerun()
                    elif errors:
                        st.error(f"❌ Nenhum evento válido. {len(errors)} arquivo(s) com erro.")
                        if processing_key in st.session_state:
                            del st.session_state[processing_key]
                except Exception as e:
                    st.error(f"Erro crítico: {e}")
                    if processing_key in st.session_state:
                        del st.session_state[processing_key]
        else:
            st.info("⏳ Processamento em andamento...")
    
    if 'logs' in st.session_state and not st.session_state.logs.empty:
        df_side = st.session_state.logs
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Eventos", f"{len(df_side):,}")
        c2.metric("Fontes", df_side['Source'].nunique())
        
        if st.button("Limpar dados", use_container_width=True):
            st.session_state.logs = pd.DataFrame()
            if '_last_filtered_events' in st.session_state:
                del st.session_state['_last_filtered_events']
            st.rerun()
    
    st.markdown("---")
    if st.button("Sair", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ==========================================
# MODAL DE DETALHES
# ==========================================
@st.dialog("Detalhes do Evento", width="large")
def event_detail_dialog(idx):
    df = st.session_state.logs
    if idx >= len(df):
        st.error("Evento não encontrado")
        return
    
    row = df.iloc[idx]
    level = row['Level']
    lc = level.lower() if level.lower() in ['critical','error','warning','information','verbose'] else 'information'
    ts = row['TimeCreated'].strftime('%d/%m/%Y %H:%M:%S') if pd.notna(row['TimeCreated']) else '—'
    msg = str(row['Message']) if pd.notna(row['Message']) else '(sem mensagem)'
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
        <span class="level-badge level-{lc}">{level}</span>
        <span style="color: #94a3b8; font-size: 0.85rem;">Event ID</span>
        <span style="font-family: monospace; color: #60a5fa; font-weight: 600;">{row['EventId']}</span>
        <span style="color: #334155;">·</span>
        <span style="color: #94a3b8; font-size: 0.85rem;">{ts}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="event-grid">
        <div class="event-key">Fonte</div><div class="event-val">{row['Source']}</div>
        <div class="event-key">Log</div><div class="event-val">{row.get('LogName', '—')}</div>
        <div class="event-key">Arquivo</div><div class="event-val">{row.get('SourceFile', '—')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Mensagem</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg-box">{msg}</div>', unsafe_allow_html=True)
    
    # Troubleshooting
    try:
        from core.troubleshoot import TroubleshootDB
        tip = TroubleshootDB().get_tip(row['EventId'])
        if tip:
            steps_html = ''.join(f'<li>{s}</li>' for s in tip['steps'])
            doc_html = f'<a href="{tip["doc"]}" target="_blank" style="color:#60a5fa; font-size:0.8rem;">📖 Documentação Microsoft →</a>' if tip.get('doc') else ''
            st.markdown(f"""
            <div class="tip-panel">
                <div class="tip-title">🧠 {tip['title']}</div>
                <span class="level-badge level-warning">Severidade: {tip['severity']}</span>
                <div class="tip-cause">
                    <strong style="color:#c4b5fd;">Causa provável:</strong><br>
                    {tip['cause']}
                </div>
                <strong style="color:#c4b5fd; font-size:0.85rem;">Passos de resolução:</strong>
                <ol class="tip-steps">{steps_html}</ol>
                <div style="margin-top:0.75rem;">{doc_html}</div>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass
    
    # IA LOCAL
    st.markdown('<div class="section-title">Análise com IA</div>', unsafe_allow_html=True)
    
    ai_online = st.session_state.get('ai_status', False)
    
    if not ai_online:
        st.warning("⚠️ IA Local não configurada ou offline. Configure na barra lateral.")
    else:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown('<div style="color:#94a3b8; font-size:0.85rem;">Use seu modelo local para analisar este evento</div>', unsafe_allow_html=True)
        with c2:
            ask_ai = st.button("🤖 Analisar", key=f"ai_{idx}")
        
        if ask_ai:
            try:
                from core.ai_client import AIClient
                endpoint = st.session_state.get('ai_endpoint', 'http://localhost:11434')
                model = st.session_state.get('ai_model', 'llama3.2')
                client = AIClient(endpoint, model)
                
                with st.spinner("Processando..."):
                    import time
                    t0 = time.time()
                    response = client.explain_event(row['EventId'], row['Source'], msg)
                    elapsed = time.time() - t0
                
                st.markdown(f"""
                <div class="ai-header">
                    <span class="ai-badge">🤖 {model}</span>
                    <span class="ai-timing">⏱ {elapsed:.1f}s</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Erro: {e}")
    
    st.markdown("---")
    if st.button("Fechar", key=f"close_{idx}", use_container_width=True):
        st.rerun()

# ==========================================
# EMPTY STATE
# ==========================================
if 'logs' not in st.session_state or st.session_state.logs.empty:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.4;">📭</div>
        <h2 style="color: #cbd5e1; font-weight: 600; margin: 0;">Nenhum log carregado</h2>
        <p style="color: #64748b; margin-top: 0.5rem;">Importe logs do Event Viewer na barra lateral</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Como começar</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, (icon, title, desc) in zip([c1, c2, c3], [
        ("①", "Exportar", "Event Viewer → Save As → CSV"),
        ("②", "Importar", "Upload na barra lateral"),
        ("③", "Analisar", "Clique em qualquer evento")
    ]):
        with col:
            st.markdown(f"""
            <div style="background: rgba(15,23,42,0.4); border: 1px solid rgba(148,163,184,0.08); border-radius: 8px; padding: 1rem;">
                <div style="font-size: 1.25rem; color: #3b82f6; margin-bottom: 0.5rem;">{icon}</div>
                <div style="color: #f1f5f9; font-weight: 600; font-size: 0.9rem;">{title}</div>
                <div style="color: #64748b; font-size: 0.8rem; margin-top: 0.25rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# DASHBOARD
# ==========================================
df = st.session_state.logs.copy()

n_total = len(df)
n_crit = len(df[df['Level'].str.contains('Critical', case=False, na=False)])
n_err = len(df[df['Level'].str.contains('Error', case=False, na=False)])
n_warn = len(df[df['Level'].str.contains('Warning', case=False, na=False)])
n_src = df['Source'].nunique() if 'Source' in df.columns else 0

st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card"><div class="stat-label">Total</div><div class="stat-value">{n_total:,}</div></div>
    <div class="stat-card"><div class="stat-label">Críticos</div><div class="stat-value critical">{n_crit}</div></div>
    <div class="stat-card"><div class="stat-label">Erros</div><div class="stat-value error">{n_err}</div></div>
    <div class="stat-card"><div class="stat-label">Alertas</div><div class="stat-value warning">{n_warn}</div></div>
    <div class="stat-card"><div class="stat-label">Fontes</div><div class="stat-value info">{n_src}</div></div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📋 Eventos", "📈 Timeline", "📊 Insights"])

with tab1:
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search = st.text_input("🔍", placeholder="Buscar mensagem, fonte, ID...", label_visibility="collapsed")
    with c2:
        levels = ["Todos"] + sorted(df['Level'].unique().tolist())
        level_f = st.selectbox("N", levels, label_visibility="collapsed")
    with c3:
        sources = ["Todas"] + sorted(df['Source'].unique().tolist())
        source_f = st.selectbox("S", sources, label_visibility="collapsed")
    
    filt = df.copy()
    if level_f != "Todos":
        filt = filt[filt['Level'] == level_f]
    if source_f != "Todas":
        filt = filt[filt['Source'] == source_f]
    if search:
        s = search.lower()
        filt = filt[
            filt['Message'].str.lower().str.contains(s, na=False) |
            filt['Source'].str.lower().str.contains(s, na=False) |
            filt['EventId'].astype(str).str.contains(search, na=False)
        ]
    
    st.caption(f"{len(filt):,} de {len(df):,} eventos")
    
    if filt.empty:
        st.info("Nenhum evento corresponde aos filtros")
    else:
        display = filt.head(500).copy()
        display['Data'] = display['TimeCreated'].apply(
            lambda x: x.strftime('%d/%m %H:%M:%S') if pd.notna(x) else '—'
        )
        
        event = st.dataframe(
            display[['Data', 'Level', 'EventId', 'Source', 'Message']],
            use_container_width=True,
            height=500,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="event_table"
        )
        
        selected_rows = event.selection.rows if event.selection else []
        if selected_rows:
            real_idx = display.index[selected_rows[0]]
            event_detail_dialog(real_idx)
        
        if len(filt) > 500:
            st.caption(f"Mostrando 500 de {len(filt):,}.")

with tab2:
    valid = df[df['TimeCreated'].notna()].copy()
    if valid.empty:
        st.warning("Sem eventos com data válida")
    else:
        c1, c2 = st.columns(2)
        with c1:
            gran = st.selectbox("Granularidade", ["Hora", "Dia", "Semana"], index=1)
        with c2:
            lvs = st.multiselect("Níveis", valid['Level'].unique().tolist(), default=valid['Level'].unique().tolist())
        
        v2 = valid[valid['Level'].isin(lvs)].copy()
        if not v2.empty:
            v2['P'] = v2['TimeCreated'].dt.floor({'Hora':'h','Dia':'D','Semana':'W'}[gran])
            counts = v2.groupby(['P','Level']).size().reset_index(name='n')
            cmap = {'Critical':'#f87171','Error':'#fb7185','Warning':'#fbbf24','Information':'#60a5fa','Verbose':'#94a3b8'}
            fig = px.bar(counts, x='P', y='n', color='Level', color_discrete_map=cmap, barmode='stack')
            fig.update_layout(
                plot_bgcolor='rgba(15,23,42,0.4)', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0', height=450,
                xaxis=dict(showgrid=True, gridcolor='rgba(148,163,184,0.08)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(148,163,184,0.08)')
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown('<div class="section-title">Top 10 Fontes</div>', unsafe_allow_html=True)
        for src, cnt in df['Source'].value_counts().head(10).items():
            pct = cnt / len(df) * 100
            st.markdown(f"""
            <div style="margin-bottom:0.6rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.2rem;">
                    <span style="color:#e2e8f0;">{src}</span>
                    <span style="color:#64748b; font-family:monospace;">{cnt:,} ({pct:.1f}%)</span>
                </div>
                <div style="background:rgba(15,23,42,0.5); height:4px; border-radius:2px; overflow:hidden;">
                    <div style="background:linear-gradient(90deg,#3b82f6,#8b5cf6); height:100%; width:{pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with c2:
        st.markdown('<div class="section-title">Distribuição por Nível</div>', unsafe_allow_html=True)
        lc = df['Level'].value_counts()
        fig = go.Figure([go.Pie(
            labels=lc.index, values=lc.values, hole=0.65,
            marker=dict(colors=['#f87171','#fb7185','#fbbf24','#60a5fa','#94a3b8'][:len(lc)])
        )])
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e2e8f0', height=380, showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Exportar CSV",
        csv,
        f"events_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True
    )

# ==========================================
# SEÇÃO DE EVENTOS FILTRADOS (DEBUG)
# ==========================================
if 'logs' in st.session_state and not st.session_state.logs.empty:
    st.markdown("---")
    filtered = st.session_state.get('_last_filtered_events', [])
    
    with st.expander(f"🗑️ Eventos Filtrados ({len(filtered)})", expanded=False):
        if not filtered:
            st.info("✅ Nenhum evento foi filtrado - todos passaram nas validações!")
        else:
            st.caption("Estes eventos foram descartados pelo parser. Se algum for importante, ajuste as regras de filtragem.")
            
            for i, evt in enumerate(filtered, 1):
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        st.markdown(f"**#{i}**")
                        st.caption(f"Linha {evt.get('row_idx', '?')}")
                    
                    with col2:
                        st.error(f"Motivo: {evt.get('reason', 'Desconhecido')}")
                        
                        if 'level' in evt:
                            st.markdown(f"""
                            - **Level:** `{evt.get('level', '—')}`
                            - **Source:** `{evt.get('source', '—')}`
                            - **Time:** `{evt.get('time', '—')}`
                            - **Message:** `{evt.get('message_preview', '—')[:200]}`
                            """)
                        else:
                            st.code(evt.get('raw', '(sem dados)')[:300])
                    
                    st.markdown("---")