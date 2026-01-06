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
    # Limpa dados nulos que causam erro de JSON
    df = df.dropna(subset=['title', 'start'])
    df['categoria'] = df['categoria'].fillna('Geral')
    df['local'] = df['local'].fillna(LOCAL_PADRAO)
    df['id'] = df['id'].fillna(0).astype(str)
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
    ano_ref = datetime.now().year
    if eventos:
        try: ano_ref = datetime.fromisoformat(str(eventos[0]['start'])).year
        except: pass

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(190, 8, "Agenda Paróquia Nossa Senhora das Dores", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(190, 6, "Dorândia - Barra do Piraí/RJ", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 10, f"Programação Mensal: {mes_nome} / {ano_ref}", align="L", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 10, "DATA", border=1, align='C', fill=True)
    pdf.cell(20, 10, "HORA", border=1, align='C', fill=True)
    pdf.cell(70, 10, "EVENTO", border=1, align='L', fill=True)
    pdf.cell(70, 10, "LOCAL", border=1, align='L', fill=True, new_x="LMARGIN", new_y="NEXT")
    
    for ev in sorted(eventos, key=lambda x: str(x['start'])):
        dt = datetime.fromisoformat(str(ev['start']))
        pdf.set_font("helvetica", "", 9)
        pdf.cell(30, 8, dt.strftime("%d/%m/%Y"), border=1, align='C')
        pdf.cell(20, 8, dt.strftime("%H:%M"), border=1, align='C')
        pdf.cell(70, 8, str(ev['title'])[:40], border=1, align='L')
        pdf.cell(70, 8, str(ev.get('local', LOCAL_PADRAO))[:40], border=1, align='L', new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())

def gerar_pdf_bingo(quantidade, festa, data_b, hora_b, premio, obs):
    pdf = FPDF()
    for _ in range(quantidade):
        pdf.add_page()
        serie = random.randint(100000, 999999)
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(190, 10, festa.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(190, 8, f"PRÊMIO: {premio.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(190, 7, "Paróquia Nossa Senhora das Dores - Dorândia", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(190, 7, f"Sorteio: {data_b.strftime('%d/%m/%Y')} às {hora_b.strftime('%H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        pdf.set_x(17.5)
        pdf.set_font("helvetica", "B", 40)
        for letra in "BINGO":
            pdf.cell(35, 20, letra, border=1, align='C')
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
        
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(190, 10, f"Obs: {obs}", align="C", new_x="LMARGIN", new_y="NEXT")

        qr_data = f"Dorandia Bingo | Serie: {serie} | Festa: {festa}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        tmp_img = BytesIO()
        img_qr.save(tmp_img)
        tmp_img.seek(0)
        
        pdf.image(tmp_img, x=160, y=215, w=30)
        pdf.set_y(245)
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(190, 10, f"Autenticidade Série: {serie}", align="R")
    return bytes(pdf.output())

# --- INTERFACE ---
df_ev = carregar_eventos_manuais()
eventos_cal = df_ev.to_dict('records') + obter_eventos_catolicos(datetime.now().year)

st.title("⛪ Paróquia Nossa Senhora das Dores")
st.caption("📍 Dorândia, Barra do Piraí/RJ")

tab_cal, tab_bingo, tab_admin = st.tabs(["📅 Agenda", "🎲 Bingo", "🛠️ Administração"])

with tab_cal:
    c1, c2 = st.columns([2, 1])
    with c1:
        state = calendar(events=eventos_cal, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"}, "locale": "pt-br"}, key="cal_dor")
    with c2:
        if state.get("eventClick"):
            eid = state["eventClick"]["event"]["id"]
            if not str(eid).startswith('c'):
                ev_sel = df_ev[df_ev['id'].astype(str) == str(eid)].iloc[0]
                with st.form("edit"):
                    nt = st.text_input("Nome", value=ev_sel['title'])
                    nd = st.date_input("Data", value=datetime.fromisoformat(ev_sel['start']).date(), format="DD/MM/YYYY")
                    nh = st.time_input("Hora", value=datetime.fromisoformat(ev_sel['start']).time())
                    nl = st.text_input("Local", value=ev_sel.get('local', LOCAL_PADRAO))
                    c_sim, c_del = st.columns(2)
                    if c_sim.form_submit_button("Confirmar Alteração"):
                        iso = datetime.combine(nd, nh).isoformat()
                        df_ev.loc[df_ev['id'].astype(str) == str(eid), ['title', 'start', 'end', 'local']] = [nt, iso, iso, nl]
                        df_ev.to_csv(ARQUIVO_CSV, index=False); st.rerun()
                    if c_del.form_submit_button("Excluir"):
                        df_ev[df_ev['id'].astype(str) != str(eid)].to_csv(ARQUIVO_CSV, index=False); st.rerun()
        else:
            with st.form("novo"):
                nt = st.text_input("Evento")
                nd = st.date_input("Data", format="DD/MM/YYYY")
                nh = st.time_input("Hora")
                nl = st.text_input("Local", value=LOCAL_PADRAO)
                nc = st.selectbox("Categoria", ["Missa", "Batizado", "Reunião", "Social"])
                if st.form_submit_button("Cadastrar") and nt:
                    iso = datetime.combine(nd, nh).isoformat()
                    nid = str(random.randint(1000, 9999))
                    nr = pd.DataFrame([{"id": nid, "title": nt, "start": iso, "end": iso, "color": "#3D9DF3", "categoria": nc, "local": nl}])
                    pd.concat([df_ev, nr], ignore_index=True).to_csv(ARQUIVO_CSV, index=False); st.rerun()

with tab_bingo:
    st.header("🎲 Bingo Autenticado")
    with st.expander("Configurar Sorteio", expanded=True):
        col1, col2 = st.columns(2)
        f_b = col1.text_input("Título", "Festa da Padroeira")
        p_b = col1.text_input("Prêmio", "Cesta de Café")
        d_b = col1.date_input("Data do Bingo", format="DD/MM/YYYY")
        q_b = col2.number_input("Qtd Cartelas", 1, 500, 20)
        o_b = col2.text_input("Observação", "Leve sua caneta!")
        h_b = col2.time_input("Hora")
    if st.button("🚀 Gerar Cartelas"):
        pdf_b = gerar_pdf_bingo(q_b, f_b, d_b, h_b, p_b, o_b)
        st.download_button("📥 Baixar Bingo", data=pdf_b, file_name="bingo.pdf", mime="application/pdf")

with tab_admin:
    st.subheader("🖨️ Relatório Mensal")
    m_s = st.selectbox("Mês", list(MESES_NOMES.keys()), index=datetime.now().month-1)
    if st.button("Gerar Agenda PDF"):
        ev_m = [e for e in eventos_cal if datetime.fromisoformat(str(e['start'])).month == MESES_NOMES[m_s]]
        if ev_m: st.download_button(f"Baixar {m_s}", data=gerar_pdf_agenda(ev_m, m_s), file_name="agenda.pdf", mime="application/pdf")
    st.markdown("---")
    st.dataframe(df_ev, width="stretch")
    if st.button("🚨 LIMPAR TODOS OS DADOS"):
        if os.path.exists(ARQUIVO_CSV): os.remove(ARQUIVO_CSV); st.rerun()
