import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Agência LK | Monitoramento", page_icon="📊", layout="wide")

# ============================================================
# CONFIGURAÇÃO
# ============================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

# 👇 confirme que esse é o nome real da sua tabela no Supabase
TABLE_NAME = "clippings"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ============================================================
# LOGIN (senha simples, comparada aqui no servidor)
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Acesso Restrito")
    st.caption("Ferramenta interna de monitoramento — uso exclusivo da equipe.")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == APP_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Senha incorreta. Tente novamente.")
    st.stop()

# ============================================================
# FUNÇÕES AUXILIARES (com cache pra não sobrecarregar o banco)
# ============================================================
@st.cache_data(ttl=300)
def get_opcoes(coluna):
    """Busca os valores únicos de uma coluna, pra preencher os filtros em lista."""
    try:
        resultado = supabase.table(TABLE_NAME).select(coluna).execute()
        valores = sorted(set(r[coluna] for r in resultado.data if r.get(coluna)))
        return valores
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_ultima_atualizacao(cliente):
    """Busca a data mais recente registrada para o cliente selecionado."""
    try:
        query = supabase.table(TABLE_NAME).select("Data").order("Data", desc=True).limit(1)
        if cliente != "Todos":
            query = query.eq("Cliente", cliente)
        resultado = query.execute()
        if resultado.data:
            data_str = resultado.data[0]["Data"]
            data_fmt = pd.to_datetime(data_str).strftime("%d/%m/%Y")
            return data_fmt
        return None
    except Exception:
        return None

# ============================================================
# CABEÇALHO (logo + título)
# ============================================================
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    try:
        st.image("logo.png", width=90)
    except Exception:
        st.write("")  # se ainda não tiver logo.png no repositório, só não mostra nada aqui
with col_titulo:
    st.title("Consulta de Monitoramento - Agência LK")

st.divider()

# ============================================================
# FILTROS
# ============================================================
clientes_disponiveis = ["Todos"] + get_opcoes("Cliente")
cliente = st.selectbox("Cliente", clientes_disponiveis)

# Aviso de última atualização, muda de acordo com o cliente escolhido
ultima_data = get_ultima_atualizacao(cliente)
if ultima_data:
    st.info(f"📅 Última atualização da base para **{cliente}**: {ultima_data}")
else:
    st.info("📅 Ainda não há registros de data para essa seleção.")

col1, col2, col3 = st.columns(3)
with col1:
    data_inicio = st.date_input("Data início", value=None, format="DD/MM/YYYY")
with col2:
    data_fim = st.date_input("Data fim", value=None, format="DD/MM/YYYY")
with col3:
    sentimento = st.selectbox("Sentimento", ["Todos", "Positivo", "Neutro", "Negativo"])

col4, col5 = st.columns(2)
with col4:
    tipos_veiculo_disponiveis = ["Todos"] + get_opcoes("Tipo de Veículo")
    tipo_veiculo = st.selectbox("Tipo de Veículo", tipos_veiculo_disponiveis)
with col5:
    estados_disponiveis = ["Todos"] + get_opcoes("Localização")
    estado = st.selectbox("Estado", estados_disponiveis)

tier = st.text_input("Tier / IDM")

buscar = st.button("🔍 Buscar", type="primary")

# ============================================================
# BUSCA E RESULTADOS
# ============================================================
if buscar:
    query = supabase.table(TABLE_NAME).select("*")

    if cliente != "Todos":
        query = query.eq("Cliente", cliente)
    if data_inicio:
        query = query.gte("Data", str(data_inicio))
    if data_fim:
        query = query.lte("Data", str(data_fim))
    if sentimento != "Todos":
        query = query.eq("Sentimento", sentimento)
    if tipo_veiculo != "Todos":
        query = query.eq("Tipo de Veículo", tipo_veiculo)
    if estado != "Todos":
        query = query.eq("Localização", estado)
    if tier:
        query = query.ilike("Tier", f"%{tier}%")

    try:
        with st.spinner("Buscando..."):
            resultado = query.execute()
            dados = resultado.data
    except Exception as e:
        # Mostra o erro real (isso resolve o problema do erro escondido)
        st.error(f"Erro ao buscar dados: {e}")
        dados = None

    if dados:
        df = pd.DataFrame(dados)
        st.success(f"{len(df)} resultado(s) encontrado(s)")

        # --- Cartões ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de menções", len(df))
        if "Audiência online" in df.columns:
            try:
                total_audiencia = pd.to_numeric(df["Audiência online"], errors="coerce").sum()
                c2.metric("Audiência total", f"{total_audiencia:,.0f}".replace(",", "."))
            except Exception:
                pass
        if "Sentimento" in df.columns and not df["Sentimento"].dropna().empty:
            c3.metric("Sentimento predominante", df["Sentimento"].mode()[0])

        # --- Gráficos ---
        g1, g2 = st.columns(2)
        with g1:
            if "Sentimento" in df.columns:
                fig_pizza = px.pie(
                    df, names="Sentimento", title="Distribuição por Sentimento",
                    color="Sentimento",
                    color_discrete_map={"Positivo": "#2ecc71", "Neutro": "#95a5a6", "Negativo": "#e74c3c"}
                )
                st.plotly_chart(fig_pizza, use_container_width=True)
        with g2:
            if "Tipo de Veículo" in df.columns:
                contagem = df["Tipo de Veículo"].value_counts().reset_index()
                contagem.columns = ["Tipo de Veículo", "Menções"]
                fig_barras = px.bar(contagem, x="Tipo de Veículo", y="Menções", title="Menções por Tipo de Veículo")
                st.plotly_chart(fig_barras, use_container_width=True)

        # --- Tabela completa ---
        st.dataframe(df, use_container_width=True)
    elif dados == []:
        st.warning("Nenhum resultado encontrado com esses filtros.")

with st.sidebar:
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()
