import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Monitoramento", page_icon="📊", layout="wide")

# ============================================================
# CONFIGURAÇÃO
# Esses valores NÃO ficam escritos aqui no código.
# Eles vêm do arquivo secreto .streamlit/secrets.toml (local)
# ou da área "Secrets" do Streamlit Community Cloud (produção).
# ============================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]  # senha única da equipe, definida por vocês

# 👇 TROQUE aqui pelo nome real da sua tabela no Supabase
TABLE_NAME = "clippings"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ============================================================
# TELA DE LOGIN (senha simples, comparada aqui mesmo no servidor)
# O código roda no servidor do Streamlit, então a senha e a chave
# nunca chegam a aparecer no navegador da pessoa que está usando.
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Acesso Restrito")
    st.caption("Ferramenta interna de monitoramento — uso exclusivo da equipe.")
    senha = st.text_input("Senha", type="password")
    entrar = st.button("Entrar")

    if entrar:
        if senha == APP_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Senha incorreta. Tente novamente.")

    st.stop()  # não deixa o resto da página carregar sem login

# ============================================================
# FERRAMENTA DE BUSCA (só aparece depois do login)
# ============================================================
st.title("📊 Monitoramento de Clientes")

col1, col2, col3 = st.columns(3)
with col1:
    cliente = st.text_input("Cliente")
with col2:
    data_inicio = st.date_input("Data início", value=None)
with col3:
    data_fim = st.date_input("Data fim", value=None)

col4, col5, col6 = st.columns(3)
with col4:
    sentimento = st.selectbox("Sentimento", ["Todos", "Positivo", "Neutro", "Negativo"])
with col5:
    tipo_veiculo = st.text_input("Tipo de Veículo")
with col6:
    localizacao = st.text_input("Localização (cidade)")

tier = st.text_input("Tier / IDM")

buscar = st.button("🔍 Buscar", type="primary")

if buscar:
    query = supabase.table(TABLE_NAME).select("*")

    if cliente:
        query = query.ilike("Cliente", f"%{cliente}%")
    if data_inicio:
        query = query.gte("Data", str(data_inicio))
    if data_fim:
        query = query.lte("Data", str(data_fim))
    if sentimento != "Todos":
        query = query.eq("Sentimento", sentimento)
    if tipo_veiculo:
        query = query.ilike("Tipo de Veículo", f"%{tipo_veiculo}%")
    if localizacao:
        query = query.ilike("Localização", f"%{localizacao}%")
    if tier:
        query = query.ilike("Tier", f"%{tier}%")

    with st.spinner("Buscando..."):
        resultado = query.execute()
        dados = resultado.data

    if dados:
        st.success(f"{len(dados)} resultado(s) encontrado(s)")
        st.dataframe(dados, use_container_width=True)
    else:
        st.warning("Nenhum resultado encontrado com esses filtros.")

# Botão de logout (opcional, no rodapé da barra lateral)
with st.sidebar:
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()
