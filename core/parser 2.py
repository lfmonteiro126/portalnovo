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
