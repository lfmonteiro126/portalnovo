import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Timeline", page_icon="📈", layout="wide")
st.header("📈 Timeline de Eventos")

if st.session_state.get('logs', pd.DataFrame()).empty:
    st.warning("⚠️ Importe logs na página inicial para ver a timeline")
    st.stop()

df = st.session_state.logs.copy()

# ============================================
# DIAGNÓSTICO DE DATAS
# ============================================
total_events = len(df)
valid_dates = df['TimeCreated'].notna().sum()
invalid_dates = total_events - valid_dates

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Eventos", f"{total_events:,}")
with col2:
    st.metric("✅ Datas Válidas", f"{valid_dates:,}", 
              delta=f"{valid_dates/total_events*100:.1f}%" if total_events > 0 else "0%")
with col3:
    st.metric("⚠️ Datas Inválidas", f"{invalid_dates:,}",
              delta=f"{invalid_dates/total_events*100:.1f}%" if total_events > 0 else "0%",
              delta_color="inverse")

# ============================================
# TRATAMENTO DE DATAS INVÁLIDAS
# ============================================
if valid_dates == 0:
    st.error("❌ **Nenhum evento com data válida!**")
    
    with st.expander("🔍 Diagnóstico - Amostras de datas brutas"):
        st.caption("Primeiras 10 datas encontradas no CSV (formato original):")
        
        if 'TimeCreated_Raw' in df.columns:
            samples = df['TimeCreated_Raw'].dropna().head(10).tolist()
            for i, sample in enumerate(samples, 1):
                st.code(f"{i}. {sample}")
        else:
            samples = df['TimeCreated'].head(10).tolist()
            for i, sample in enumerate(samples, 1):
                st.code(f"{i}. {sample}")
        
        st.info("""
        **Possíveis causas:**
        - Formato de data não reconhecido pelo parser
        - Coluna de data com nome diferente do esperado
        
        **Solução:** Envie uma amostra das datas para o desenvolvedor ajustar o parser.
        """)
    st.stop()

if invalid_dates > 0:
    st.warning(f"⚠️ {invalid_dates} evento(s) sem data válida foram excluídos da timeline")

# Filtra apenas eventos com datas válidas
df_valid = df[df['TimeCreated'].notna()].copy()

# ============================================
# CONTROLES DA TIMELINE
# ============================================
st.subheader("⚙️ Configurações")

col1, col2, col3 = st.columns(3)

with col1:
    granularity = st.selectbox(
        "📊 Granularidade",
        options=['Hora', 'Dia', 'Semana', 'Mês'],
        index=1
    )

with col2:
    # Filtro de nível
    available_levels = df_valid['Level'].unique().tolist()
    selected_levels = st.multiselect(
        "🎯 Níveis",
        options=available_levels,
        default=available_levels
    )

with col3:
    # Filtro de período
    min_date = df_valid['TimeCreated'].min().date()
    max_date = df_valid['TimeCreated'].max().date()
    
    date_range = st.date_input(
        "📅 Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Aplica filtros
df_filtered = df_valid[df_valid['Level'].isin(selected_levels)].copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered['TimeCreated'].dt.date >= start_date) &
        (df_filtered['TimeCreated'].dt.date <= end_date)
    ]

if df_filtered.empty:
    st.warning("⚠️ Nenhum evento corresponde aos filtros selecionados")
    st.stop()

# ============================================
# AGRUPAMENTO POR GRANULARIDADE
# ============================================
granularity_map = {
    'Hora': 'h',
    'Dia': 'D',
    'Semana': 'W',
    'Mês': 'M'
}

df_filtered['Period'] = df_filtered['TimeCreated'].dt.floor(granularity_map[granularity])

# Conta eventos por período e nível
counts = df_filtered.groupby(['Period', 'Level']).size().reset_index(name='count')

# ============================================
# GRÁFICO PRINCIPAL
# ============================================
st.subheader(f"📊 Eventos por {granularity}")

color_map = {
    'Critical': '#ff4d4d',
    'Error': '#ef4444',
    'Warning': '#f59e0b',
    'Information': '#3b82f6',
    'Verbose': '#94a3b8'
}

fig = px.bar(
    counts,
    x='Period',
    y='count',
    color='Level',
    title=f'Distribuição de Eventos por {granularity} ({len(df_filtered):,} eventos)',
    color_discrete_map=color_map,
    barmode='stack',
    labels={'Period': 'Período', 'count': 'Quantidade', 'Level': 'Nível'}
)

fig.update_layout(
    xaxis_title='Período',
    yaxis_title='Quantidade de Eventos',
    legend_title='Nível de Severidade',
    hovermode='x unified',
    height=500,
    showlegend=True
)

fig.update_xaxes(
    tickformat='%d/%m/%Y %H:%M' if granularity == 'Hora' else '%d/%m/%Y',
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ============================================
# ESTATÍSTICAS DETALHADAS
# ============================================
with st.expander("📊 Estatísticas Detalhadas"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Por Nível")
        level_stats = df_filtered['Level'].value_counts()
        for level, count in level_stats.items():
            pct = count / len(df_filtered) * 100
            color = color_map.get(level, '#666')
            st.markdown(f"<span style='color:{color}'>●</span> **{level}**: {count:,} ({pct:.1f}%)", 
                       unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Por Período (Top 5)")
        period_stats = counts.groupby('Period')['count'].sum().sort_values(ascending=False).head(5)
        for period, count in period_stats.items():
            st.write(f"📅 **{period.strftime('%d/%m/%Y %H:%M' if granularity == 'Hora' else '%d/%m/%Y')}**: {count:,} eventos")

# ============================================
# HEATMAP (se granularidade for Hora)
# ============================================
if granularity == 'Hora' and len(df_filtered) > 0:
    with st.expander("🔥 Heatmap por Hora do Dia"):
        df_filtered['Hour'] = df_filtered['TimeCreated'].dt.hour
        df_filtered['DayOfWeek'] = df_filtered['TimeCreated'].dt.day_name()
        
        heatmap_data = df_filtered.groupby(['DayOfWeek', 'Hour']).size().reset_index(name='count')
        
        # Ordena dias da semana
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_order_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        day_map = dict(zip(day_order, day_order_pt))
        heatmap_data['DayOfWeek_PT'] = heatmap_data['DayOfWeek'].map(day_map)
        
        heatmap_pivot = heatmap_data.pivot(
            index='DayOfWeek_PT',
            columns='Hour',
            values='count'
        ).fillna(0)
        
        # Reordena
        heatmap_pivot = heatmap_pivot.reindex(day_order_pt)
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=[f"{h:02d}h" for h in heatmap_pivot.columns],
            y=heatmap_pivot.index,
            colorscale='YlOrRd',
            colorbar=dict(title="Eventos")
        ))
        
        fig_heat.update_layout(
            title='Distribuição de Eventos por Dia da Semana e Hora',
            xaxis_title='Hora do Dia',
            yaxis_title='Dia da Semana',
            height=400
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)

# ============================================
# EXPORTAÇÃO
# ============================================
st.divider()
col1, col2 = st.columns(2)

with col1:
    csv_data = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv_data,
        file_name=f"timeline_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    if st.button("🔄 Limpar Filtros", use_container_width=True):
        st.rerun()