import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
from datetime import datetime, date, timedelta
import os

# Configuração da página
st.set_page_config(page_title="Gestão Paroquial", layout="wide", page_icon="⛪")

ARQUIVO_CSV = "eventos_igreja.csv"

# --- LÓGICA DE DATAS CATÓLICAS AUTOMÁTICAS ---
def calcular_pascoa(ano):
    """Algoritmo para calcular o domingo de Páscoa"""
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
    quarta_cinzas = pascoa - timedelta(days=46)
    sexta_paixao = pascoa - timedelta(days=2)
    corpus_christi = pascoa + timedelta(days=60)
    
    eventos = [
        {"title": "⛪ Natal", "start": f"{ano}-12-25T00:00:00", "color": "#B03A2E"},
        {"title": "⛪ Véspera de Natal", "start": f"{ano}-12-24T19:00:00", "color": "#B03A2E"},
        {"title": "⛪ N. Sra. Aparecida", "start": f"{ano}-10-12T00:00:00", "color": "#2E86C1"},
        
        # --- DATA DA PADROEIRA ADICIONADA ---
        {"title": "✨ N. Sra. das Dores (Padroeira)", "start": f"{ano}-09-15T00:00:00", "color": "#1A5276"},
        
        {"title": "⛪ Dia de Reis", "start": f"{ano}-01-06T00:00:00", "color": "#7D3C98"},
        {"title": "🟣 Quarta-feira de Cinzas", "start": quarta_cinzas.isoformat() + "T08:00:00", "color": "#6C3483"},
        {"title": "🔴 Sexta-feira da Paixão", "start": sexta_paixao.isoformat() + "T15:00:00", "color": "#943126"},
        {"title": "⚪ Domingo de Páscoa", "start": pascoa.isoformat() + "T08:00:00", "color": "#F1C40F"},
        {"title": "⚪ Corpus Christi", "start": corpus_christi.isoformat() + "T08:00:00", "color": "#F1C40F"},
    ]
    return eventos

# --- GESTÃO DE DADOS ---
def inicializar_csv():
    if not os.path.exists(ARQUIVO_CSV):
        pd.DataFrame(columns=["title", "start", "end", "color", "categoria"]).to_csv(ARQUIVO_CSV, index=False)

def carregar_eventos_completos():
    inicializar_csv()
    try:
        df = pd.read_csv(ARQUIVO_CSV)
        eventos_manuais = df.to_dict('records')
    except:
        eventos_manuais = []
    
    ano_atual = datetime.now().year
    # Gera eventos para o ano atual e o próximo para garantir transição suave
    eventos_auto = obter_eventos_catolicos(ano_atual) + obter_eventos_catolicos(ano_atual + 1)
    return eventos_manuais + eventos_auto

def salvar_novo_evento(titulo, data, hora, categoria):
    data_hora = datetime.combine(data, hora).isoformat()
    cores = {"Culto/Missa": "#FF4B4B", "Reunião": "#3D9DF3", "Ensaio": "#FFA500", "Social": "#28a745", "Batizado": "#7FB3D5", "Outros": "#7D3C98"}
    
    novo_evento = {
        "title": f"[{categoria}] {titulo}",
        "start": data_hora, 
        "end": data_hora,
        "color": cores.get(categoria, "#3D9DF3"), 
        "categoria": categoria
    }
    df_atual = pd.read_csv(ARQUIVO_CSV)
    df_novo = pd.concat([df_atual, pd.DataFrame([novo_evento])], ignore_index=True)
    df_novo.to_csv(ARQUIVO_CSV, index=False)

# --- INTERFACE ---
st.title("⛪ Dashboard de Gestão Paroquial")

# 1. Carregar todos os dados
todos_eventos = carregar_eventos_completos()

# 2. Banner de Próximo Evento (Destaque)
if todos_eventos:
    df_temp = pd.DataFrame(todos_eventos)
    df_temp['start_dt'] = pd.to_datetime(df_temp['start'])
    agora = datetime.now()
    
    # Filtra o que é de hoje em diante e ordena
    eventos_futuros = df_temp[df_temp['start_dt'] >= agora].sort_values(by='start_dt')
    
    if not eventos_futuros.empty:
        proximo = eventos_futuros.iloc[0]
        data_f = proximo['start_dt'].strftime('%d/%m/%Y às %H:%M')
        st.info(f"🔔 **PRÓXIMO EVENTO:** {proximo['title']} | 📅 {data_f}")
    else:
        st.write("Nenhum evento futuro encontrado.")

st.markdown("---")

# 3. Barra Lateral com formulário
with st.sidebar:
    st.header("📝 Agendar Atividade")
    with st.form("form_evento", clear_on_submit=True):
        titulo = st.text_input("Nome do Evento (ex: Batizado)")
        # Formato dd/mm/aaaa
        data_evento = st.date_input("Data", format="DD/MM/YYYY")
        hora_evento = st.time_input("Horário")
        cat_evento = st.selectbox("Categoria", ["Culto/Missa", "Batizado", "Reunião", "Ensaio", "Social", "Outros"])
        
        if st.form_submit_button("Confirmar Agendamento"):
            if titulo:
                salvar_novo_evento(titulo, data_evento, hora_evento, cat_evento)
                st.success("Evento salvo!")
                st.rerun()
            else:
                st.error("Por favor, dê um nome ao evento.")

# 4. Calendário Principal
calendar_options = {
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,listYear",
    },
    "initialView": "dayGridMonth", # Default mensal
    "locale": "pt-br",
    "buttonText": {
        "today": "Hoje", 
        "month": "Mês", 
        "week": "Semana", 
        "list": "Lista Anual"
    }
}

st.subheader("📅 Cronograma Geral")
calendar(events=todos_eventos, options=calendar_options)

# 5. Painel Administrativo
st.markdown("---")
with st.expander("🛠️ Administração (Excluir Eventos Manuais)"):
    df_admin = pd.read_csv(ARQUIVO_CSV)
    if not df_admin.empty:
        st.write("Lista de eventos cadastrados pela secretaria:")
        st.dataframe(df_admin, use_container_width=True)
        if st.button("🚨 APAGAR TODOS OS EVENTOS MANUAIS"):
            os.remove(ARQUIVO_CSV)
            st.rerun()
    else:
        st.write("Nenhum evento manual cadastrado.")
