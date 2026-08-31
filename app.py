import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
import re
from datetime import datetime, timedelta
import plotly.express as px

from dicionario_tiers import DICIONARIO_VEICULOS

st.set_page_config(page_title="Consulta de Monitoramento - Agência LK", page_icon="logo.png", layout="wide")

# ============================================================
# ESTILO (tema claro, colorido e elegante)
# ============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    header[data-testid="stHeader"] { background-color: transparent !important; }
    footer[data-testid="stFooter"] { display: none !important; }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background-color: #FAFAFF !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        color: #2D2A4A !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
    }

    .terminal-label {
        color: #6C5CE7;
        font-family: 'Poppins', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 700;
        display: block;
        margin-bottom: 6px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #ECEBFA !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 16px rgba(108, 92, 231, 0.06) !important;
        padding: 1.5rem !important;
    }

    div[data-testid="stMetric"] {
        margin: 0 auto;
        padding: 10px 0 !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
    }

    [data-testid="stMetricLabel"] {
        font-family: 'Poppins', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #8B87A8 !important;
        text-align: center !important;
        justify-content: center !important;
        margin-bottom: 8px !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'Poppins', sans-serif !important;
        font-size: clamp(16px, 2.5vw, 28px) !important;
        font-weight: 700 !important;
        color: #6C5CE7 !important;
        text-align: center !important;
        justify-content: center !important;
        word-break: break-word !important;
        line-height: 1.2 !important;
    }

    .stTextInput div[data-baseweb="input"], .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E4E2F7 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }

    .stTextInput input {
        color: #2D2A4A !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        background-color: transparent !important;
    }

    .stTextInput div[data-baseweb="input"]:focus-within, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #6C5CE7 !important;
        box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.15) !important;
    }

    label[data-testid="stWidgetLabel"] p {
        font-family: 'Poppins', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #8B87A8 !important;
    }

    .stButton > button {
        font-family: 'Poppins', sans-serif !important;
        background-color: #FFFFFF !important;
        color: #6C5CE7 !important;
        border: 1.5px solid #E4E2F7 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #F4F3FF !important;
        color: #6C5CE7 !important;
        border-color: #6C5CE7 !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5b4bd6 0%, #8f87f0 100%) !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
    }

    hr { border-color: #ECEBFA !important; }

    .custom-footer {
        text-align: center;
        margin-top: 60px;
        padding-bottom: 20px;
        color: #B5B2CC;
        font-size: 11px;
        font-family: 'Inter', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN
# ============================================================
def check_password():
    try:
        SENHA_CORRETA = st.secrets["APP_PASSWORD"]
    except KeyError:
        st.error("⚠️ Erro de configuração: Senha não encontrada nos secrets.")
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    c_img1, c_img2, c_img3 = st.columns([3, 1, 3])
    with c_img2:
        try:
            st.image("logo.png", width="stretch")
        except Exception:
            pass

    st.markdown("<h2 style='text-align: center; font-weight: 700;'><span class='terminal-label'>Security</span>Acesso Restrito</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            senha = st.text_input("Senha:", type="password")
            c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
            with c_btn2:
                submit = st.form_submit_button("ENTRAR", type="primary", width="stretch")
            if submit:
                if senha == SENHA_CORRETA:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
    return False

if not check_password():
    st.stop()

# ============================================================
# FUNÇÕES AUXILIARES (mesma lógica do sistema original)
# ============================================================
def safe_float(val):
    try:
        v = float(val)
        return 0.0 if pd.isna(v) else v
    except:
        return 0.0

def limpar_valor_numerico(valor):
    if pd.isna(valor) or valor == "": return 0.0
    texto = str(valor).lower().replace("r$", "").strip()
    try:
        if "." in texto and "," in texto: texto = texto.replace(".", "").replace(",", ".")
        elif "," in texto: texto = texto.replace(",", ".")
        texto_limpo = re.sub(r"[^\d\.-]", "", texto)
        return float(texto_limpo)
    except: return 0.0

def extrair_valoracao_real(valor_str, sentimento_str):
    v = limpar_valor_numerico(valor_str)
    s = str(sentimento_str).strip().lower()
    if s in ['negativo', 'negativa']:
        return -abs(v)
    return abs(v)

def formatar_audiencia(valor):
    valor = safe_float(valor)
    if valor >= 1_000_000: return f"{valor/1_000_000:.1f} mi"
    if valor >= 1_000: return f"{valor/1_000:.1f} mil"
    return f"{valor:.0f}"

def formatar_moeda(valor):
    valor = safe_float(valor)
    sinal = "-" if valor < 0 else ""
    v_abs = abs(valor)
    if v_abs >= 1_000_000:
        return f"{sinal}R$ {v_abs/1_000_000:.1f} mi"
    return f"{sinal}R$ {v_abs:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def padronizar_canal(c_str):
    if pd.isna(c_str): return "Portal de Notícias"
    c_str = str(c_str).strip()
    c_lower = c_str.lower()
    if c_lower in ["online", "web", "internet", "portal correio", "portal a tarde", "ibahia", "bnews", "portal", "site"]: return "Portal de Notícias"
    if c_lower in ["mídia impressa", "impresso", "jornal", "jornal impresso", "revista"]: return "Impresso"
    if c_lower in ["televisão", "tv", "televisao", "telejornal", "band", "record", "globo"]: return "TV"
    if c_lower in ["radio", "rádio", "fm", "am"]: return "Rádio"
    if c_lower in ["x", "twitter", "x/twitter", "x / twitter"]: return "X / Twitter"
    return c_str.title() if c_str else "Portal de Notícias"

def inferir_estado(cliente, veiculo, localizacao):
    if pd.notna(veiculo) and str(veiculo).strip() != "":
        veiculo_limpo = str(veiculo).lower().strip()
        if cliente != "Ambev":
            dic = DICIONARIO_VEICULOS.get(cliente, {})
            for v, dados in dic.items():
                if v.lower().strip() in veiculo_limpo or veiculo_limpo in v.lower().strip():
                    return dados.get("Estado", "Nacional")

    if pd.notna(localizacao) and str(localizacao).strip() != "":
        loc = str(localizacao).lower().strip()
        estados_br = {
            'acre': 'AC', 'alagoas': 'AL', 'amapá': 'AP', 'amapa': 'AP', 'amazonas': 'AM',
            'bahia': 'BA', 'salvador': 'BA', 'ceará': 'CE', 'ceara': 'CE', 'fortaleza': 'CE',
            'distrito federal': 'DF', 'brasília': 'DF', 'brasilia': 'DF',
            'espírito santo': 'ES', 'espirito santo': 'ES', 'vitória': 'ES', 'vitoria': 'ES',
            'goiás': 'GO', 'goias': 'GO', 'goiânia': 'GO', 'goiania': 'GO',
            'maranhão': 'MA', 'maranhao': 'MA', 'são luís': 'MA', 'sao luis': 'MA',
            'mato grosso do sul': 'MS', 'mato grosso': 'MT', 'cuiabá': 'MT', 'cuiaba': 'MT',
            'minas gerais': 'MG', 'belo horizonte': 'MG', 'pará': 'PA', 'para': 'PA', 'belém': 'PA', 'belem': 'PA',
            'paraíba': 'PB', 'paraiba': 'PB', 'joão pessoa': 'PB', 'joao pessoa': 'PB',
            'paraná': 'PR', 'parana': 'PR', 'curitiba': 'PR',
            'pernambuco': 'PE', 'recife': 'PE', 'piauí': 'PI', 'piaui': 'PI', 'teresina': 'PI',
            'rio de janeiro': 'RJ', 'rio grande do norte': 'RN', 'natal': 'RN',
            'rio grande do sul': 'RS', 'porto alegre': 'RS',
            'rondônia': 'RO', 'rondonia': 'RO', 'roraima': 'RR', 'boa vista': 'RR',
            'santa catarina': 'SC', 'florianópolis': 'SC', 'florianopolis': 'SC',
            'são paulo': 'SP', 'sao paulo': 'SP', 'sergipe': 'SE', 'aracaju': 'SE', 'tocantins': 'TO', 'palmas': 'TO'
        }
        if loc in ["nacional", "brasil", "nacional, brasil"]: return "Nacional"
        if len(loc) == 2 and loc.upper() in estados_br.values(): return loc.upper()
        for nome, sigla in estados_br.items():
            if nome in loc: return sigla
        if "brasil" in loc: return "Nacional"
        return "Internacional"
    return "Nacional"

def converter_df_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy') as writer:
        df.to_excel(writer, index=False, sheet_name='Clipping')
        workbook = writer.book
        worksheet = writer.sheets['Clipping']
        workbook.formats[0].set_font_name('Calibri')
        format_aud = workbook.add_format({'num_format': '#,##0', 'font_name': 'Calibri'})
        format_moeda = workbook.add_format({'num_format': 'R$ #,##0.00', 'font_name': 'Calibri'})
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 50)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 18, format_aud)
        worksheet.set_column('I:I', 20, format_moeda)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 12)
        worksheet.set_column('L:L', 60)
    return output.getvalue()

# ============================================================
# CONEXÃO COM O BANCO (via Supabase Client, com anon key + RLS)
# ============================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
except Exception:
    st.error("❌ Erro: SUPABASE_URL ou SUPABASE_ANON_KEY não encontrados nos Secrets.")
    st.stop()

@st.cache_resource
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase = get_client()

@st.cache_data(ttl=600)
def carregar_dados_banco(cliente):
    query = supabase.table("clippings").select("*")
    if cliente != "Todos os Clientes":
        query = query.eq("cliente", cliente)
    resultado = query.order("data_publicacao", desc=True).execute()
    return pd.DataFrame(resultado.data)

CLIENTES = [
    "2GB Entretenimento", "99 City Launches", "99 Food", "99 Metrô", "Ambev", "ACEC", "Camarote LEM", "CCBB Salvador", "Clínica Sim",
    "Crema Gelato", "Faculdade Baiana de Direito e Gestão", "Feed Experience Hub",
    "Grupo Loro", "Grupo Raymundo da Fonte", "JBS Alimentos", "Konecta", "Mercado Pago", "Nestlé",
    "Pepsico", "Villa Global Education", "XP Investimentos"
]

# ============================================================
# CABEÇALHO E LOGOUT
# ============================================================
with st.sidebar:
    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo_lk.png", width="stretch")
        except:
            pass
    st.markdown("---")
    if st.button("Sair", width="stretch"):
        st.session_state["authenticated"] = False
        st.rerun()

col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    try:
        st.image("logo_lk.png", width=90)
    except Exception:
        pass
with col_titulo:
    st.markdown("<h2 style='margin-top: 8px;'>Consulta de Monitoramento - Agência LK</h2>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# FILTROS
# ============================================================
cli_sel = st.selectbox("Cliente:", ["Todos os Clientes"] + CLIENTES)

df_view = carregar_dados_banco(cli_sel).copy()

if not df_view.empty:
    df_view['data_upload'] = pd.to_datetime(df_view.get('data_upload', pd.Series()), errors='coerce')
    if 'data_publicacao' in df_view.columns:
        df_view['data_publicacao'] = pd.to_datetime(df_view['data_publicacao'], errors='coerce')
        df_view['data_publicacao'] = df_view['data_publicacao'].fillna(df_view['data_upload']).fillna(pd.Timestamp.now())
    else:
        df_view['data_publicacao'] = df_view['data_upload'].fillna(pd.Timestamp.now())

    df_view['estado'] = df_view.apply(lambda r: inferir_estado(cli_sel, r['veiculo_nome'], r['localizacao']), axis=1)

    # Aviso de última atualização
    ultima_att = df_view['data_upload'].max()
    if pd.notna(ultima_att):
        st.info(f"📅 Última atualização da base para **{cli_sel}**: {ultima_att.strftime('%d/%m/%Y')}")

    st.write("<span class='terminal-label' style='margin-top: 15px;'>Query Filters</span>", unsafe_allow_html=True)

    c_filt1, c_filt2 = st.columns([1, 1.5])
    with c_filt2:
        ano_vigente = datetime.now().year
        padrao_inicio = datetime(ano_vigente, 1, 1).date()
        padrao_fim = datetime(ano_vigente, 12, 31).date()
        c_de, c_ate = st.columns(2)
        with c_de: data_inicio = st.date_input("Data Inicial:", value=padrao_inicio, format="DD/MM/YYYY", key=f"di_{cli_sel}")
        with c_ate: data_fim = st.date_input("Data Final:", value=padrao_fim, format="DD/MM/YYYY", key=f"df_{cli_sel}")

    if data_inicio and data_fim:
        mask_data = (df_view['data_publicacao'].dt.date >= data_inicio) & (df_view['data_publicacao'].dt.date <= data_fim)
        df_view_filtrado_data = df_view[mask_data]
    else:
        df_view_filtrado_data = df_view

    with c_filt1:
        temas_disponiveis = sorted([t for t in df_view_filtrado_data['release_tema'].unique() if pd.notna(t) and t != ""])
        filtro_tema = st.multiselect("Filtrar Tema:", temas_disponiveis)

    if filtro_tema:
        df_view_filtrado_data = df_view_filtrado_data[df_view_filtrado_data['release_tema'].isin(filtro_tema)]

    c_veic, c_est, c_mid = st.columns([2, 1, 1])
    with c_veic:
        filtro_veiculo = st.text_input("Filtrar Veículo:", placeholder="Ex: Folha, G1, @...")
    with c_est:
        estados_disp = sorted([e for e in df_view_filtrado_data['estado'].unique() if pd.notna(e) and e != ""])
        filtro_estado = st.multiselect("Filtrar Estado:", estados_disp)
    with c_mid:
        midias_disp = sorted([m for m in df_view_filtrado_data['canal'].unique() if pd.notna(m) and m != ""])
        filtro_midia = st.multiselect("Tipo de Mídia:", midias_disp)

    if filtro_veiculo:
        df_view_filtrado_data = df_view_filtrado_data[df_view_filtrado_data['veiculo_nome'].astype(str).str.contains(filtro_veiculo, case=False, na=False)]
    if filtro_estado:
        df_view_filtrado_data = df_view_filtrado_data[df_view_filtrado_data['estado'].isin(filtro_estado)]
    if filtro_midia:
        df_view_filtrado_data = df_view_filtrado_data[df_view_filtrado_data['canal'].isin(filtro_midia)]

    url_busca = st.text_input("Checagem de Duplicidade (URL):", placeholder="Cole o link exato aqui...")
    if url_busca:
        df_view_final = df_view_filtrado_data[df_view_filtrado_data['link'].astype(str).str.contains(url_busca, case=False, na=False)]
    else:
        df_view_final = df_view_filtrado_data

    if filtro_tema:
        st.markdown(f"<p style='color: #8B87A8; font-family: \"Inter\", sans-serif; font-size: 12px; margin-top: 5px;'>↳ Você está vendo o preview do tema: <span style='color: #6C5CE7; font-weight: 700;'>{', '.join(filtro_tema)}</span></p>", unsafe_allow_html=True)

    # ============================================================
    # RESUMO (cartões)
    # ============================================================
    st.markdown("<span class='terminal-label'>Overview</span><h4>Resumo</h4>", unsafe_allow_html=True)
    with st.container(border=True):
        total_materias = len(df_view_final)
        aud_total = safe_float(df_view_final['audiencia'].apply(limpar_valor_numerico).sum())
        val_total = safe_float(df_view_final.apply(lambda r: extrair_valoracao_real(r['valoracao'], r['sentimento']), axis=1).sum())

        st.metric("Total de Matérias", total_materias)
        k1, k2 = st.columns(2)
        k1.metric("Audiência Est.", formatar_audiencia(aud_total))
        k2.metric("Valor Editorial", formatar_moeda(val_total))
        st.markdown("---")

        st.markdown("<span class='terminal-label'>Distribution</span>", unsafe_allow_html=True)
        contagem = df_view_final['canal'].value_counts().to_dict()
        canais_presentes = {}
        for nome_canal, qtd in contagem.items():
            if qtd > 0:
                n = padronizar_canal(nome_canal)
                canais_presentes[n] = canais_presentes.get(n, 0) + qtd
        canais_ordenados = dict(sorted(canais_presentes.items(), key=lambda item: item[1], reverse=True))
        if canais_ordenados:
            cols = st.columns(3)
            i = 0
            for c_nome, c_qtd in canais_ordenados.items():
                cols[i % 3].metric(c_nome, c_qtd)
                i += 1

        st.markdown("---")
        if cli_sel == "Ambev":
            st.markdown("<span class='terminal-label'>Classificação</span>", unsafe_allow_html=True)
            qtd_idm = len(df_view_final[df_view_final['check_idm'].astype(str).str.strip() == "IDM"])
            qtd_sem_idm = total_materias - qtd_idm
            c_idm1, c_idm2 = st.columns(2)
            c_idm1.metric("IDM", qtd_idm)
            c_idm2.metric("Sem IDM", qtd_sem_idm)
        elif "tier" in df_view_final.columns:
            st.markdown("<span class='terminal-label'>Classificação</span>", unsafe_allow_html=True)
            qtd_tier1 = len(df_view_final[df_view_final['tier'].astype(str).str.strip() == "Tier 1"])
            qtd_tier2 = len(df_view_final[df_view_final['tier'].astype(str).str.strip() == "Tier 2"])
            c_t1, c_t2 = st.columns(2)
            c_t1.metric("Tier 1", qtd_tier1)
            c_t2.metric("Tier 2", qtd_tier2)

    # ============================================================
    # GRÁFICOS
    # ============================================================
    if total_materias > 0:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("<span class='terminal-label'>Breakdown</span><h4>Tipo de Mídia</h4>", unsafe_allow_html=True)
            df_canal_padrao = df_view_final['canal'].apply(padronizar_canal)
            df_pizza = df_canal_padrao.value_counts().reset_index()
            df_pizza.columns = ['Canal', 'Quantidade']
            fig_pizza = px.pie(df_pizza, names='Canal', values='Quantidade')
            fig_pizza.update_traces(textposition='inside', textinfo='percent', hoverinfo='label+percent')
            fig_pizza.update_layout(margin=dict(t=10, b=10, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pizza, width="stretch")
        with g2:
            st.markdown("<span class='terminal-label'>Geomapping</span><h4>Publicações por Estado</h4>", unsafe_allow_html=True)
            df_barras = df_view_final['estado'].value_counts().reset_index()
            df_barras.columns = ['Estado', 'Quantidade']
            fig_barras = px.bar(df_barras, x='Estado', y='Quantidade', text_auto=True)
            fig_barras.update_traces(marker_color='#4ade80')
            fig_barras.update_layout(xaxis_title="", yaxis_title="Publicações", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig_barras, width="stretch")

    st.markdown("---")

    # ============================================================
    # TABELA E EXPORTAÇÃO
    # ============================================================
    df_preview = df_view_final.copy()
    df_preview['data_formatada'] = df_preview['data_publicacao'].dt.tz_localize(None)
    df_preview['audiencia'] = df_preview['audiencia'].apply(limpar_valor_numerico)
    df_preview['valoracao'] = df_preview.apply(lambda r: extrair_valoracao_real(r['valoracao'], r['sentimento']), axis=1)

    colunas_map = {
        'data_formatada': 'Data',
        'cliente': 'Cliente',
        'release_tema': 'Tema',
        'titulo': 'Título',
        'veiculo_nome': 'Veículo',
        'canal': 'Tipo de Veículo',
        'sentimento': 'Sentimento',
        'audiencia': 'Audiência online',
        'valoracao': 'Valoração',
        'localizacao': 'Localização'
    }
    if cli_sel == "Ambev":
        colunas_map['check_idm'] = 'IDM'
    else:
        colunas_map['tier'] = 'Tier'
    colunas_map['link'] = 'Link'

    for col_db in colunas_map.keys():
        if col_db not in df_preview.columns: df_preview[col_db] = ""

    df_final_preview = df_preview[list(colunas_map.keys())].rename(columns=colunas_map)
    df_final_preview = df_final_preview.sort_values(by='Data', ascending=False)

    c_titulo, c_botao = st.columns([3, 1])
    with c_titulo:
        st.markdown("<span class='terminal-label'>Output</span><h4>Preview da Exportação</h4>", unsafe_allow_html=True)
    with c_botao:
        df_final_export = df_final_preview.sort_values(by='Data', ascending=True)
        excel_data = converter_df_para_excel(df_final_export)
        nome_arq = f"Consulta de Monitoramento — {cli_sel} {data_inicio.strftime('%d-%m')} a {data_fim.strftime('%d-%m')} | LK.xlsx"
        st.download_button(label="EXPORTAR EXCEL", data=excel_data, file_name=nome_arq,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           width="stretch")

    st.dataframe(
        df_final_preview,
        width="stretch",
        height=500,
        hide_index=True,
        column_config={
            "Data": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY"),
            "Audiência online": st.column_config.NumberColumn("Audiência online", format="%d"),
            "Valoração": st.column_config.NumberColumn("Valoração", format="R$ %.2f"),
            "Link": st.column_config.LinkColumn("Link"),
        }
    )
else:
    st.info("Nenhum registro encontrado no banco de dados.")

st.markdown("""
    <div class="custom-footer">
        <p>© 2026 Agência LK. Todos os direitos reservados.</p>
    </div>
""", unsafe_allow_html=True)
