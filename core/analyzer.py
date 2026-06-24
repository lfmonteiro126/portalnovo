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
