import streamlit as st
from streamlit_calendar import calendar
import pandas as pd
from datetime import datetime, date, timedelta
import os
from fpdf import FPDF
import random
import qrcode
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Paroquial - Dorândia", layout="wide", page_icon="⛪")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stButton > button:first-child { border-radius: 8px; font-weight: bold; height: 3em; }
    .btn-salvar button { background-color: #28a745 !important; color: white !important; }
    .btn-excluir button { background-color: #dc3545 !important; color: white !important; }
    .btn-geral button { background-color: #1A5276 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

ARQUIVO_CSV = "eventos_igreja.csv"
LOCAL_PADRAO = "Paróquia Nossa Senhora das Dores"
MESES_NOMES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
    "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
}

# --- FUNÇÕES DE APOIO ---
def carregar_eventos_manuais():
    if not os.path.exists(ARQUIVO_CSV):
        pd.DataFrame(columns=["id", "title", "start", "end", "color", "categoria", "local"]).to_csv(ARQUIVO_CSV, index=False)
    df = pd.read_csv(ARQUIVO_CSV)
    if 'id' not in df.columns: df['id'] = range(len(df))
    if 'local' not in df.columns: df['local'] = LOCAL_PADRAO
    return df

def obter_eventos_catolicos(ano):
    return [
        {"id": f"c1-{ano}", "title": "Natal", "start": f"{ano}-12-25T00:00:00", "color": "#B03A2E", "local": LOCAL_PADRAO},
        {"id": f"c2-{ano}", "title": "N. Sra. das Dores", "start": f"{ano}-09-15T19:00:00", "color": "#1A5276", "local": LOCAL_PADRAO},
    ]

# --- GERAÇÃO DE PDF ---
def gerar_pdf_agenda(eventos, mes_nome):
    pdf = FPDF()
    pdf.add_page()
    ano_referencia = datetime.now().year
    if eventos:
        try: ano_referencia = datetime.fromisoformat(str(eventos[0]['start'])).year
        except: pass

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(190, 8, "Agenda Paróquia Nossa Senhora das Dores", align="C")
    pdf.ln(8)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(190, 6, "Dorândia - Barra do Piraí/RJ", align="C")
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 10, f"Programação Mensal: {mes_nome} / {ano_referencia}", align="L")
    pdf.ln(12)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    for label, width in [("DATA", 30), ("HORA", 20), ("EVENTO", 70), ("LOCAL", 70)]:
        pdf.cell(width, 10, label, border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    for ev in sorted(eventos, key=lambda x: str(x['start'])):
        dt = datetime.fromisoformat(str(ev['start']))
        pdf.cell(30, 8, dt.strftime("%d/%m/%Y"), border=1, align='C')
        pdf.cell(20, 8, dt.strftime("%H:%M"), border=1, align='C')
        pdf.cell(70, 8, str(ev['title'])[:40], border=1, align='L')
        pdf.cell(70, 8, str(ev.get('local', LOCAL_PADRAO))[:40], border=1, align='L')
        pdf.ln()
    return bytes(pdf.output())

def gerar_pdf_bingo(quantidade, festa, data_b, hora_b, premio, obs):
    pdf = FPDF()
    for _ in range(quantidade):
        pdf.add_page()
        serie = random.randint(100000, 999999)
        
        # Cabeçalho
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(190, 10, festa.upper(), align="C")
        pdf.ln(10)
        
        # Prêmio (Destaque)
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(200, 0, 0) # Cor vermelha para o prêmio
        pdf.cell(190, 8, f"PRÊMIO: {premio.upper()}", align="C")
        pdf.set_text_color(0, 0, 0) # Volta para preto
        pdf.ln(8)

        pdf.set_font("helvetica", "B", 11)
        pdf.cell(190, 7, "Paróquia Nossa Senhora das Dores - Dorândia", align="C")
        pdf.ln(6)
        pdf.cell(190, 7, f"Sorteio: {data_b.strftime('%d/%m/%Y')} às {hora_b.strftime('%H:%M')}", align="C")
        pdf.ln(12)
        
        # Grade BINGO
        pdf.set_font("helvetica", "B", 40)
        pdf.set_x(17.5)
        for letra in "BINGO":
            pdf.cell(35, 22, letra, border=1, align='C')
        pdf.ln()
        
        faixas = {'B': range(1,16), 'I': range(16,31), 'N': range(31,46), 'G': range(46,61), 'O': range(61,76)}
        nums = {l: random.sample(f, 5) for l, f in faixas.items()}
        for i in range(5):
            pdf.set_x(17.5)
            for letra in "BINGO":
                if i == 2 and letra == 'N':
                    pdf.set_font("helvetica", "B", 10); pdf.cell(35, 25, "LIVRE", border=1, align='C')
                else:
                    pdf.set_font("helvetica", "B", 30); pdf.cell(35, 25, str(nums[letra][i]), border=1, align='C')
            pdf.ln()
        
        # Observação do Usuário
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(190, 10, f"Obs: {obs}", align="C")

        # QR Code e Autenticação
        qr_data = f"Festa: {festa} | Premio: {premio} | Serie: {serie}"
        qr = qrcode.make(qr_data)
        img_buf = BytesIO()
        qr.save(img_buf, format="PNG")
        img_buf.seek(0)
        
        pdf.image(img_buf, x=160, y=210, w=30)
        pdf.set_y(240)
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(190, 10, f"Autenticidade: {serie}", align="R")
        
    return bytes(pdf.output())

# --- INTERFACE ---
df_ev = carregar_eventos_manuais()
eventos_cal = df_ev.to_dict('records') + obter_eventos_catolicos(datetime.now().year)

st.title("⛪ Paróquia Nossa Senhora das Dores")
st.caption("📍 Dorândia, Barra do Piraí/RJ")

tab_cal, tab_bingo, tab_admin = st.tabs(["📅 Agenda", "🎲 Bingo com Prêmios", "🛠️ Administração"])

with tab_cal:
    col_calendar, col_edit = st.columns([2, 1])
    with col_calendar:
        state = calendar(events=eventos_cal, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"}, "locale": "pt-br"}, key="cal_dorandia")
    with col_edit:
        if state.get("eventClick"):
            eid = state["eventClick"]["event"]["id"]
            if not str(eid).startswith('c'):
                ev_data = df_ev[df_ev['id'].astype(str) == str(eid)].iloc[0]
                with st.form("edit_form"):
                    novo_t = st.text_input("Nome", value=ev_data['title'])
                    nova_d = st.date_input("Data", value=datetime.fromisoformat(ev_data['start']).date(), format="DD/MM/YYYY")
                    nova_h = st.time_input("Hora", value=datetime.fromisoformat(ev_data['start']).time())
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Salvar"):
                        iso = datetime.combine(nova_d, nova_h).isoformat()
                        df_ev.loc[df_ev['id'].astype(str) == str(eid), ['title', 'start', 'end']] = [novo_t, iso, iso]
                        df_ev.to_csv(ARQUIVO_CSV, index=False); st.rerun()
                    if c2.form_submit_button("Excluir"):
                        df_ev[df_ev['id'].astype(str) != str(eid)].to_csv(ARQUIVO_CSV, index=False); st.rerun()
        else:
            with st.form("novo_form"):
                nt = st.text_input("Novo Evento")
                nd = st.date_input("Data", format="DD/MM/YYYY")
                nh = st.time_input("Hora")
                if st.form_submit_button("Cadastrar") and nt:
                    iso = datetime.combine(nd, nh).isoformat()
                    new_row = pd.DataFrame([{"id": str(random.randint(1000, 9999)), "title": nt, "start": iso, "end": iso, "color": "#3D9DF3"}])
                    pd.concat([df_ev, new_row], ignore_index=True).to_csv(ARQUIVO_CSV, index=False); st.rerun()

with tab_bingo:
    st.header("🎲 Configurar Sorteio")
    with st.expander("Informações do Bingo", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            f_bingo = st.text_input("Título do Evento", "Festa de Nossa Senhora")
            p_bingo = st.text_input("Prêmio Principal", "Um Garrote")
            d_bingo = st.date_input("Data do Bingo", format="DD/MM/YYYY")
        with c2:
            q_bingo = st.number_input("Qtd de Cartelas", 1, 500, 50)
            o_bingo = st.text_input("Observação na Cartela", "Não esqueça de levar a caneta!")
            h_bingo = st.time_input("Hora do Sorteio")
    
    if st.button("🚀 Gerar Cartelas Personalizadas"):
        pdf_b = gerar_pdf_bingo(q_bingo, f_bingo, d_bingo, h_bingo, p_bingo, o_bingo)
        st.download_button("📥 Baixar PDF do Bingo", data=pdf_b, file_name="bingo_paroquia.pdf", mime="application/pdf")

with tab_admin:
    st.subheader("🖨️ Agenda")
    m_sel = st.selectbox("Mês", list(MESES_NOMES.keys()), index=datetime.now().month-1)
    if st.button("Gerar Agenda PDF"):
        ev_m = [e for e in eventos_cal if datetime.fromisoformat(str(e['start'])).month == MESES_NOMES[m_sel]]
        if ev_m: st.download_button(f"Baixar {m_sel}", data=gerar_pdf_agenda(ev_m, m_sel), file_name=f"agenda_{m_sel.lower()}.pdf", mime="application/pdf")
    st.markdown("---")
    st.dataframe(df_ev, width="stretch")
    if st.button("🚨 LIMPAR TUDO"):
        if os.path.exists(ARQUIVO_CSV): os.remove(ARQUIVO_CSV); st.rerun()
