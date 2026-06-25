#!/bin/bash

# ============================================
# Event Portal Pro - Setup Automático
# Para macOS
# ============================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funções de output
print_step() { echo -e "${BLUE}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# Banner
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════╗"
echo "║     🖥️  Event Portal Pro - Setup Script      ║"
echo "║        Troubleshooting Inteligente           ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não encontrado!"
    print_info "Instale com: brew install python3"
    exit 1
fi

print_success "Python $(python3 --version) detectado"

# Pergunta o nome do projeto
read -p "$(echo -e ${CYAN}Nome da pasta do projeto [event_portal]: ${NC})" PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-event_portal}

# Verifica se a pasta já existe
if [ -d "$PROJECT_NAME" ]; then
    print_warning "Pasta '$PROJECT_NAME' já existe!"
    read -p "Deseja continuar mesmo assim? (s/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Operação cancelada"
        exit 1
    fi
fi

# Cria estrutura de pastas
print_step "Criando estrutura de pastas..."
mkdir -p "$PROJECT_NAME"/{core,pages,data,.vscode}
print_success "Estrutura criada"

cd "$PROJECT_NAME" || exit

# Cria ambiente virtual
print_step "Criando ambiente virtual..."
python3 -m venv venv
print_success "Ambiente virtual criado"

# Ativa o ambiente
print_step "Ativando ambiente virtual..."
source venv/bin/activate
print_success "Ambiente ativado"

# Atualiza pip
print_step "Atualizando pip..."
pip install --upgrade pip -q

# Instala dependências
print_step "Instalando dependências..."
pip install -q \
    streamlit==1.38.0 \
    pandas==2.2.2 \
    plotly==5.24.0 \
    requests==2.32.3 \
    python-dateutil==2.9.0

print_success "Dependências instaladas"

# Salva requirements
pip freeze > requirements.txt
print_success "requirements.txt criado"

# ============================================
# Cria arquivos do projeto
# ============================================

print_step "Criando arquivos do projeto..."

# app.py
cat > app.py << 'EOF'
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
EOF

# core/__init__.py
cat > core/__init__.py << 'EOF'
# Core modules
EOF

# core/parser.py
cat > core/parser.py << 'EOF'
import pandas as pd
import re
import xml.etree.ElementTree as ET
from io import StringIO

def normalize_key(key):
    if not key:
        return ''
    return re.sub(r'[^a-z0-9]', '', str(key).lower().encode('ascii', 'ignore').decode())

def extract_message(row):
    """Extrai mensagem com fallback robusto"""
    # Prioridade: __parsed_extra
    if '__parsed_extra' in row:
        extra = row['__parsed_extra']
        if isinstance(extra, str) and len(extra) > 5 and extra != 'None':
            return extra.strip()
        if isinstance(extra, list):
            joined = ' '.join(str(v) for v in extra if v and v != 'None')
            if len(joined) > 5:
                return joined.strip()
    
    # Aliases conhecidos
    message_keys = ['message', 'mensagem', 'description', 'descricao', 'task category', 
                    'categoria', 'details', 'detalhes']
    
    for key in message_keys:
        for k, v in row.items():
            if normalize_key(k) == normalize_key(key) and v and v != 'None' and len(str(v)) > 5:
                return str(v).strip()
    
    # Fallback: maior string não-metadado
    exclude = {'level', 'eventid', 'source', 'log', 'date', 'time', 'user', 'computer', 'task'}
    candidates = [
        (k, v) for k, v in row.items()
        if v and isinstance(v, str) and len(v) > 5 and v != 'None'
        and not any(e in normalize_key(k) for e in exclude)
    ]
    
    if candidates:
        candidates.sort(key=lambda x: len(x[1]), reverse=True)
        return candidates[0][1].strip()
    
    return '(sem mensagem)'

def smart_get(row, aliases):
    """Busca inteligente em múltiplas variações"""
    for alias in aliases:
        for k, v in row.items():
            if normalize_key(k) == normalize_key(alias) and v and v != 'None':
                return v
    return ''

def parse_csv(uploaded_file):
    """Parser CSV robusto"""
    content = uploaded_file.read().decode('utf-8-sig')
    lines = content.split('\n')
    
    # Detecta cabeçalho
    header_line = 0
    for i, line in enumerate(lines[:10]):
        if not line.strip():
            continue
        normalized = normalize_key(line)
        has_keywords = any(kw in normalized for kw in ['nivel', 'level', 'data', 'date', 'source', 'event'])
        comma_count = line.count(',')
        if has_keywords and comma_count >= 3:
            header_line = i
            break
    
    clean_content = '\n'.join(lines[header_line:])
    df = pd.read_csv(StringIO(clean_content), dtype=str, keep_default_na=False)
    
    processed = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        processed.append({
            'TimeCreated': smart_get(row_dict, ['date and time', 'timecreated', 'data/hora', 'date', 'data']),
            'Level': smart_get(row_dict, ['level', 'leveldisplayname', 'nivel']) or 'Information',
            'EventId': int(smart_get(row_dict, ['event id', 'eventid', 'id']) or 0),
            'Source': smart_get(row_dict, ['source', 'origem', 'provider']) or '',
            'LogName': smart_get(row_dict, ['log name', 'log', 'canal']) or uploaded_file.name,
            'Message': extract_message(row_dict)
        })
    
    result_df = pd.DataFrame(processed)
    result_df['TimeCreated'] = pd.to_datetime(result_df['TimeCreated'], errors='coerce')
    return result_df

def parse_xml(uploaded_file):
    """Parser XML do Event Viewer"""
    content = uploaded_file.read().decode('utf-8-sig')
    root = ET.fromstring(content)
    
    events = []
    for event in root.findall('.//Event'):
        system = event.find('System')
        if system is None:
            continue
        
        time_created = system.find('TimeCreated')
        level = system.find('Level')
        event_id = system.find('EventID')
        provider = system.find('Provider')
        channel = system.find('Channel')
        
        level_map = {1: 'Critical', 2: 'Error', 3: 'Warning', 4: 'Information', 5: 'Verbose'}
        level_num = int(level.text) if level is not None and level.text else 4
        
        events.append({
            'TimeCreated': time_created.get('SystemTime', '').split('.')[0] if time_created is not None else '',
            'Level': level_map.get(level_num, 'Information'),
            'EventId': int(event_id.text) if event_id is not None and event_id.text else 0,
            'Source': provider.get('Name', '') if provider is not None else '',
            'LogName': channel.text if channel is not None else uploaded_file.name,
            'Message': '(XML - detalhes disponíveis)'
        })
    
    result_df = pd.DataFrame(events)
    result_df['TimeCreated'] = pd.to_datetime(result_df['TimeCreated'], errors='coerce')
    return result_df

def parse_logs(uploaded_file):
    """Parser principal"""
    filename = uploaded_file.name.lower()
    if filename.endswith('.csv'):
        return parse_csv(uploaded_file)
    elif filename.endswith('.xml'):
        return parse_xml(uploaded_file)
    else:
        raise ValueError(f"Formato não suportado: {filename}")
EOF

# core/analyzer.py
cat > core/analyzer.py << 'EOF'
import pandas as pd
from datetime import timedelta

def detect_patterns(df):
    """Detecta padrões suspeitos"""
    alerts = []
    if df.empty:
        return alerts
    
    # Brute force: 5+ EventID 4625 em 2 min
    e4625 = df[df['EventId'] == 4625].dropna(subset=['TimeCreated']).copy()
    if len(e4625) >= 5:
        e4625 = e4625.sort_values('TimeCreated')
        for i in range(len(e4625)):
            window = e4625[
                (e4625['TimeCreated'] >= e4625.iloc[i]['TimeCreated']) &
                (e4625['TimeCreated'] <= e4625.iloc[i]['TimeCreated'] + timedelta(minutes=2))
            ]
            if len(window) >= 5:
                alerts.append({
                    'type': 'critical',
                    'title': 'Possível ataque de força bruta',
                    'desc': f"{len(window)} falhas de logon em 2 minutos"
                })
                break
    
    # Log clear
    e1102 = df[df['EventId'] == 1102]
    if len(e1102) > 0:
        alerts.append({
            'type': 'critical',
            'title': '⚠️ Log de segurança limpo',
            'desc': f"Detectado em {e1102.iloc[0]['TimeCreated']}"
        })
    
    return alerts
EOF

# core/ai_client.py
cat > core/ai_client.py << 'EOF'
import requests

class AIClient:
    def __init__(self, endpoint="http://localhost:11434", model="llama3.2"):
        self.endpoint = endpoint.rstrip('/')
        self.model = model
    
    def test_connection(self):
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            if response.ok:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return True, models
            return False, []
        except Exception as e:
            return False, [str(e)]
    
    def ask(self, prompt):
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            if response.ok:
                return response.json().get('response', '(sem resposta)')
            return f"Erro HTTP {response.status_code}"
        except Exception as e:
            return f"Erro: {str(e)}"
    
    def explain_event(self, event_id, source, message):
        prompt = f"""Especialista em Windows Server. Analise:
Event ID: {event_id}
Fonte: {source}
Mensagem: {message}

Forneça: 1) Causa, 2) Passos (3-5), 3) Comandos. PT-BR."""
        return self.ask(prompt)
EOF

# core/troubleshoot.py
cat > core/troubleshoot.py << 'EOF'
import json
from pathlib import Path

DEFAULT_TIPS = {
    4625: {
        "title": "Falha de Logon",
        "severity": "Alta",
        "cause": "Credenciais inválidas ou conta bloqueada.",
        "steps": ["Verificar conta em AD", "Checar w32tm", "Analisar Workstation"],
        "doc": "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-4625"
    },
    1102: {
        "title": "Log Limpo",
        "severity": "Crítica",
        "cause": "⚠️ Possível encobrimento de intrusão.",
        "steps": ["Investigar usuário", "Preservar evidências"],
        "doc": "https://learn.microsoft.com/windows/security/threat-protection/auditing/event-1102"
    }
}

class TroubleshootDB:
    def __init__(self):
        self.tips = DEFAULT_TIPS.copy()
    
    def get_tip(self, event_id):
        return self.tips.get(int(event_id))
EOF

# Pages
cat > pages/1_📋_Logs.py << 'EOF'
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
EOF

cat > pages/2_📈_Timeline.py << 'EOF'
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
EOF

cat > pages/3_🤖_IA_Local.py << 'EOF'
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
EOF

# .vscode/settings.json
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "ms-python.black-formatter"
    }
}
EOF

# .vscode/launch.json
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit",
            "type": "debugpy",
            "request": "launch",
            "module": "streamlit",
            "args": ["run", "app.py"],
            "console": "integratedTerminal"
        }
    ]
}
EOF

# .gitignore
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
.env
*.log
data/*.csv
.DS_Store
EOF

# Script para rodar
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run app.py
EOF
chmod +x run.sh

print_success "Todos os arquivos criados"

# Inicializa Git
if command -v git &> /dev/null; then
    print_step "Inicializando Git..."
    git init -q
    git add .
    git commit -m "🎉 Initial commit - Event Portal Pro" -q
    print_success "Git inicializado"
else
    print_warning "Git não encontrado (instale com: brew install git)"
fi

# Final
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 SETUP CONCLUÍDO COM SUCESSO!           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
print_info "Próximos passos:"
echo ""
echo -e "  ${CYAN}1. Abra o projeto no VS Code:${NC}"
echo -e "     ${YELLOW}cd $PROJECT_NAME && code .${NC}"
echo ""
echo -e "  ${CYAN}2. Rode o app:${NC}"
echo -e "     ${YELLOW}./run.sh${NC}"
echo ""
echo -e "  ${CYAN}3. Ou use o VS Code:${NC}"
echo -e "     Pressione ${YELLOW}F5${NC} para debug"
echo ""
echo -e "  ${CYAN}4. Acesse:${NC}"
echo -e "     ${YELLOW}http://localhost:8501${NC}"
echo ""
echo -e "${PURPLE}Bom trabalho! 🚀${NC}"
echo ""
