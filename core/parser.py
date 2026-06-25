"""
Parser para logs do Event Viewer
Versão conservadora: remove APENAS lixo óbvio
"""

import pandas as pd
import csv
from io import StringIO
import re
import warnings

warnings.filterwarnings('ignore')


def parse_datetime_safe(value):
    """Parser de datas simples"""
    if not value or str(value).strip() in ['', 'None', '—', '-']:
        return pd.NaT
    
    val = str(value).strip()
    val = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', val)
    
    try:
        return pd.to_datetime(val, format='%m/%d/%Y %I:%M:%S %p')
    except:
        pass
    
    try:
        return pd.to_datetime(val, errors='coerce')
    except:
        return pd.NaT


def is_definitely_junk(source, message):
    """
    Remove APENAS lixo óbvio. Conservador ao máximo.
    Retorna True apenas se for CERTAMENTE lixo.
    """
    if not message:
        return False
    
    # ÚNICO filtro: ESENT com "Internal Timing Sequence"
    # Esses são logs de performance interna do banco ESE, inúteis para troubleshooting
    if source and source.upper() == 'ESENT':
        if 'Internal Timing Sequence' in message:
            return True
    
    # Nada mais é filtrado!
    # Eventos SPP com [(?)(?)(?)] são VÁLIDOS (status de licenciamento)
    # Crash dumps do WER são VÁLIDOS (informações de erro)
    # Eventos com data e Event ID são VÁLIDOS
    
    return False


def parse_logs(uploaded_file):
    """
    Parser conservador para CSV do Event Viewer.
    Formato: Level,DateTime,Source,EventID,TaskCategory,Message
    """
    try:
        content_bytes = uploaded_file.read()
        content = content_bytes.decode('utf-8-sig')
        
        print(f"\n🔍 Processando: {uploaded_file.name}")
        print(f"📄 Tamanho: {len(content):,} caracteres")
        
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        
        if len(rows) < 2:
            raise ValueError("CSV vazio ou só com cabeçalho")
        
        header = rows[0]
        data_rows = rows[1:]
        
        print(f"📋 Cabeçalho: {header}")
        print(f"📊 Linhas de dados: {len(data_rows)}")
        
        events = []
        filtered_junk = 0
        
        for idx, row in enumerate(data_rows):
            if len(row) < 5:
                filtered_junk += 1
                continue
            
            level = row[0].strip()
            datetime_str = row[1].strip()
            source = row[2].strip()
            event_id_str = row[3].strip()
            task_category = row[4].strip() if len(row) > 4 else ''
            message = row[5].strip() if len(row) > 5 else ''
            
            if not level or not datetime_str:
                filtered_junk += 1
                continue
            
            parsed_time = parse_datetime_safe(datetime_str)
            
            if pd.isna(parsed_time):
                filtered_junk += 1
                continue
            
            try:
                event_id = int(event_id_str) if event_id_str.isdigit() else 0
            except:
                event_id = 0
            
            # FILTRO CONSERVADOR: só remove lixo óbvio
            if is_definitely_junk(source, message):
                filtered_junk += 1
                if filtered_junk <= 3:
                    print(f"  🗑️ Filtrado: {source} (ID:{event_id}) - ESENT timing")
                continue
            
            # Debug primeiras 3 linhas válidas
            if len(events) < 3:
                print(f"\n  ✅ [{idx}] Level: {level}")
                print(f"       Time: {parsed_time}")
                print(f"       Source: {source}")
                print(f"       ID: {event_id}")
                print(f"       Message: {message[:80]}...")
            
            events.append({
                'TimeCreated': parsed_time,
                'Level': level,
                'EventId': event_id,
                'Source': source if source else uploaded_file.name,
                'LogName': uploaded_file.name,
                'Message': message if message else '(sem mensagem)'
            })
        
        if not events:
            raise ValueError(f"Nenhum evento válido de {len(data_rows)} linhas")
        
        df = pd.DataFrame(events)
        
        total = len(df)
        valid_dates = df['TimeCreated'].notna().sum()
        valid_ids = (df['EventId'] > 0).sum()
        
        print(f"\n✅ RESULTADO:")
        print(f"   📊 Eventos válidos: {total}")
        print(f"   📅 Com data: {valid_dates}/{total}")
        print(f"   🎯 Com ID: {valid_ids}/{total}")
        print(f"   🗑️ Lixo filtrado: {filtered_junk}")
        
        df = df.sort_values('TimeCreated', ascending=False, na_position='last')
        
        return df
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=[
            'TimeCreated', 'Level', 'EventId', 'Source', 'LogName', 'Message'
        ])