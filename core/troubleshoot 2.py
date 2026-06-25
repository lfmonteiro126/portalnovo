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
