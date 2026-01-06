import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
from datetime import datetime, date, timedelta
import os
from fpdf import FPDF

# Configuração da página e Estilo CSS para melhorar o Layout
st.set_page_config(page_title="Gestão Paroquial", layout="wide", page_icon="⛪")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1A5276; color: white; }
    .st-expander { border: 1px solid #d3d3d3; border-radius: 10px; background-color: white; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold; color: #1A5276; }
    </style>
    """, unsafe_allow_html=True)

ARQUIVO_CSV = "eventos_igreja.csv"

# --- FUNÇÕES DE APOIO (PÁSCOA E DADOS) ---
def calcular_pascoa(ano):
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    mes = (h + L - 7 * m + 114) // 31
    dia = ((h + L - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)

def obter_eventos_catolicos(ano):
    pascoa = calcular_pascoa(ano)
    eventos = [
        {"title": "⛪ Natal", "start": f"{ano}-12-25T00:00:00", "color": "#B03A2E"},
        {"title": "✨ N. Sra. das Dores (Padroeira)", "start": f"{ano}-09-15T00:00:00", "color": "#1A5276"},
        {"title": "⛪ N. Sra. Aparecida", "start": f"{ano}-10-12T00:00:00", "color": "#2E86C1"},
        {"title": "🟣 Quarta-feira de Cinzas", "start": (pascoa - timedelta(days=46)).isoformat() + "T08:00:00", "color": "#6C3483"},
        {"title": "🔴 Sexta-feira da Paixão", "start": (pascoa - timedelta(days=2)).isoformat() + "T15:00:00", "color": "#943126"},
        {"title": "⚪ Domingo de Páscoa", "start": pascoa.isoformat() + "T08:00:00", "color": "#F1C40F"},
        {"title": "⚪ Corpus Christi", "start": (pascoa + timedelta(days=60)).isoformat() + "T08:00:00", "color": "#F1C40F"},
    ]
    return eventos

def carregar_eventos_completos():
    if not os.path.exists(ARQUIVO_CSV):
        pd.DataFrame(columns=["title", "start", "end", "color", "categoria"]).to_csv(ARQUIVO_CSV, index=False)
    df = pd.read_csv(ARQUIVO_CSV)
    eventos_manuais = df.to_dict('records')
    ano = datetime.now().year
    return eventos_manuais + obter_eventos_catolicos(ano) + obter_eventos_catolicos(ano + 1)

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(eventos, mes_nome):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Agenda Paroquial - {mes_nome}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Data", 1)
    pdf.cell(110, 10, "Evento", 1)
    pdf.cell(40, 10, "Horário", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    # Ordenar eventos por data
    eventos_sorted = sorted(eventos, key=lambda x: x['start'])
    
    for ev in eventos_sorted:
        dt = datetime.fromisoformat(ev['start'])
        pdf.cell(40, 10, dt.strftime("%d/%m/%Y"), 1)
        pdf.cell(110, 10, ev['title'][:50], 1)
        pdf.cell(40, 10, dt.strftime("%H:%M"), 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.title("⛪ Gestão de Atividades Paroquiais")

todos_eventos = carregar_eventos_completos()

# Banner Próximo Evento
df_temp = pd.DataFrame(todos_eventos)
df_temp['start_dt'] = pd.to_datetime(df_temp['start'])
proximos = df_temp[df_temp['start_dt'] >= datetime.now()].sort_values('start_dt')

if not proximos.empty:
    p = proximos.iloc[0]
    st.info(f"🔔 **DESTAQUE:** {p['title']} em {p['start_dt'].strftime('%d/%m/%Y às %H:%M')}")

st.markdown("---")

# Colunas para Calendário e Ações
col_cal, col_info = st.columns([3, 1])

with col_cal:
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,listYear"},
        "initialView": "dayGridMonth",
        "locale": "pt-br",
    }
    calendar(events=todos_eventos, options=calendar_options)

with col_info:
    st.subheader("🖨️ Impressão")
    mes_relatorio = st.selectbox("Mês para o PDF", list(range(1, 13)), index=datetime.now().month - 1)
    
    # Filtrar eventos do mês selecionado para o PDF
    ev_mes = [e for e in todos_eventos if datetime.fromisoformat(e['start']).month == mes_relatorio]
    
    if st.button("Gerar Relatório Mensal PDF"):
        if ev_mes:
            pdf_bytes = gerar_pdf(ev_mes, f"Mês {mes_relatorio}")
            st.download_button("📥 Baixar PDF", data=pdf_bytes, file_name=f"agenda_mes_{mes_relatorio}.pdf", mime="application/pdf")
        else:
            st.warning("Sem eventos neste mês.")

    st.markdown("---")
    st.subheader("📝 Novo Evento")
    with st.container():
        t = st.text_input("Título")
        d = st.date_input("Data", format="DD/MM/YYYY")
        h = st.time_input("Hora")
        c = st.selectbox("Tipo", ["Missa", "Batizado", "Reunião", "Outros"])
        if st.button("Salvar Evento"):
            data_hora = datetime.combine(d, h).isoformat()
            cores = {"Missa": "#FF4B4B", "Batizado": "#7FB3D5", "Reunião": "#3D9DF3"}
            novo = {"title": f"[{c}] {t}", "start": data_hora, "end": data_hora, "color": cores.get(c, "#7D3C98"), "categoria": c}
            df_atual = pd.read_csv(ARQUIVO_CSV)
            pd.concat([df_atual, pd.DataFrame([novo])], ignore_index=True).to_csv(ARQUIVO_CSV, index=False)
            st.rerun()
