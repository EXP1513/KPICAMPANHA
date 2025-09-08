import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
import csv

st.set_page_config(page_title="Gera Campanha - Abandono & Carrinho", layout="centered")

# ======== CSS visual ========
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(90deg,#018a62 0%,#3be291 35%,#fee042 100%)!important;
    min-height: 100vh;
    color: #222!important;
    font-family: 'Segoe UI','Montserrat','Arial',sans-serif!important;
}
section[data-testid="stSidebar"] {
    background-color:#004aad!important;
    color:#fff!important;
}
.titulo-principal {
    background: rgba(255,255,255,0.55);
    color:#06643b;
    padding:28px 0 12px 0;
    border-radius:16px;
    text-align:center;
    font-size:2.4em;
    font-weight:700;
    margin:30px auto 18px auto;
}
.manual-inicio, .card-importacao {
    background:#fff;
    color:#222;
    border-radius:22px;
    box-shadow:0 4px 28px rgba(0,0,0,0.07);
    padding:20px;
    width:100%;
    max-width:640px;
    margin:0 auto 22px auto;
    border-left:9px solid #018a62;
    font-size:1.07em;
}
.card-importacao h5 {
    color:#018a62;
    font-size:1.18em;
    font-weight:bold;
    text-align:center;
    margin-bottom:14px;
}
.stDownloadButton > button, .stFileUploader > div > button {
    background-color:#3be291;
    color:#06643b !important;
    font-weight:bold;
    border-radius:7px;
    padding:10px 36px;
    border:none;
    font-size:1.09em;
    margin-top:12px;
}
.stDownloadButton > button:hover, .stFileUploader > div > button:hover {
    background-color:#018a62;
    color:#fff !important;
}
.stDataFrame, .stTable {
    background:#fff;
    border-radius:16px;
    color:#222;
    box-shadow:0 2px 12px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# Função robusta para ler arquivos CSV detectando o separador e tratando erros
def read_file(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    
    if f.name.lower().endswith(".csv"):
        sep = ';'  # separador correto do seu CSV
        encoding = "ISO-8859-1"  # encoding correto para acentos
        data_io.seek(0)
        try:
            return pd.read_csv(
                data_io,
                sep=sep,
                encoding=encoding,
                on_bad_lines='warn',
                engine='python'
            )
        except pd.errors.ParserError as e:
            print(f"Erro ao ler o CSV: {e}. Verifique se o arquivo está bem formatado.")
            return None
    else:
        return pd.read_excel(data_io)

def localizar_coluna(df, nome):
    return next((c for c in df.columns if str(c).strip().lower() == nome.lower()), None)

def processar_nome_abandono(valor):
    texto_original = str(valor).strip()
    primeiro_nome = texto_original.split(' ')[0]
    nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
    if len(nome_limpo) <= 3:
        return "Candidato"
    return nome_limpo.title()

def tratar_numero_telefone(num):
    if pd.isna(num): return ''
    num_str = re.sub(r'\D', '', str(num)).lstrip('0')
    return '55' + num_str if num_str else ''

def limpar_nome_carrinho(nome):
    return re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ\s]', '', str(nome))

def tratar_nome_carrinho(row):
    nome = row['Nome'].strip()
    if len(nome) in [0,1,2,3] and pd.notna(row['Numero']) and str(row['Numero']).strip() != '':
        return "Candidato"
    else:
        return nome.title()

def importar_excel_tratamento_carrinho(df):
    cols = ['First-Name', 'Email', 'Phone']
    df = df[[c for c in cols if c in df.columns]]
    if 'First-Name' in df.columns:
        df['First-Name'] = df['First-Name'].str.split(' ').str[0]
    df = df.rename(columns={'First-Name': 'Nome', 'Email': 'e-mail', 'Phone': 'Numero'})
    df['Nome'] = df['Nome'].apply(limpar_nome_carrinho)
    df['Nome'] = df.apply(tratar_nome_carrinho, axis=1)
    df['Numero'] = df['Numero'].apply(tratar_numero_telefone)
    return df[['Nome','Numero','e-mail']]

def importar_excel_tratamento_nao_pagos(df):
    cols = ['Nome completo (cobrança)', 'Telefone (cobrança)', 'E-mail (cobrança)']
    df = df[[c for c in cols if c in df.columns]]
    if 'Nome completo (cobrança)' in df.columns:
        df['Nome completo (cobrança)'] = df['Nome completo (cobrança)'].str.split(' ').str[0]
    df = df.rename(columns={
        'Nome completo (cobrança)': 'Nome',
        'Telefone (cobrança)': 'Numero',
        'E-mail (cobrança)': 'e-mail'
    })
    df['Nome'] = df['Nome'].apply(limpar_nome_carrinho)
    df['Nome'] = df.apply(tratar_nome_carrinho, axis=1)
    df['Numero'] = df['Numero'].apply(tratar_numero_telefone)
    return df[['Nome','Numero','e-mail']]

def gerar_nome_arquivo_carrinho():
    hoje = datetime.now()
    dia_semana = hoje.weekday()
    prefixo = "Carinho_Nãopagos"
    if dia_semana == 0:  # segunda-feira
        sexta = hoje - timedelta(days=3)
        domingo = hoje - timedelta(days=1)
        return f"{prefixo}_{sexta.strftime('%d.%m')}_{domingo.strftime('%d.%m')}.csv"
    else:
        dia_anterior = hoje - timedelta(days=1)
        return f"{prefixo}_{dia_anterior.strftime('%d.%m')}.csv"

def gerar_nome_arquivo_abandono(df_kpi, col_data_evento):
    if col_data_evento and col_data_evento in df_kpi.columns:
        try:
            df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
            datas_validas = df_kpi[col_data_evento].dropna().dt.date
            if not datas_validas.empty:
                di, dfinal = min(datas_validas), max(datas_validas)
                if di == dfinal:
                    return f"Abandono_{di.strftime('%d.%m')}.csv"
                else:
                    return f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"
        except:
            pass
    return "Abandono.csv"

# Padronizar colunas para base KPI conforme arquivo "kpi-1.csv"
colunas_kpi_base = [
    'Data Evento', 'Descrição Evento', 'Tipo de Evento', 'Evento Finalizador', 'Contato', 'Identificação', 
    'Código Contato', 'Hashtag', 'Usuário', 'Número Protocolo', 'Data Hora Geração Protocolo', 'Observação', 
    'SMS Principal', 'Whatsapp Principal', 'Email Principal', 'Canal', 'Carteiras', 'Carteira do Evento', 
    'Valor da oportunidade', 'Identificador da chamada de Voz'
]

def padronizar_colunas_kpi(df):
    col_mapping = {}
    for col in colunas_kpi_base:
        col_lower = col.lower().strip()
        for c in df.columns:
            if c.lower().strip() == col_lower:
                col_mapping[c] = col
                break
    df = df.rename(columns=col_mapping)
    df = df[[col for col in colunas_kpi_base if col in df.columns]]
    return df

# Padronizar colunas para base Fidelizados conforme arquivo "fidelizados.csv"
colunas_fid_base = [
    'Usuário Fidelizado', 'Contato', 'Identificação', 'Código', 'Canal', 'Último Contato', 'Qtd. Mensagens Pendentes', 
    'SMS Principal', 'WhatsApp Principal', 'Email Principal', 'Segmentos vinculados a pessoa', 'Agendado', 
    'Data Hora Agendamento', 'Ultimo Evento', 'Ultimo Evento Finalizador'
]

def padronizar_colunas_fid(df):
    col_mapping = {}
    for col in colunas_fid_base:
        col_lower = col.lower().strip()
        for c in df.columns:
            if c.lower().strip() == col_lower:
                col_mapping[c] = col
                break
    df = df.rename(columns=col_mapping)
    df = df[[col for col in colunas_fid_base if col in df.columns]]
    return df

# ===== Aba Abandono =====
def aba_abandono():
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    file_kpi = st.file_uploader("📂 Base KPI", type=["xlsx","csv"], key="kpi_file")
    file_fid = st.file_uploader("📂 Base Fidelizados", type=["xlsx","csv"], key="fid_file")
    if file_kpi and file_fid:
        df_kpi = read_file(file_kpi)
        df_fid = read_file(file_fid)

        # Padronizar colunas para correspondência exata às bases anexadas
        df_kpi = padronizar_colunas_kpi(df_kpi)
        df_fid = padronizar_colunas_fid(df_fid)

        col_wpp_kpi = localizar_coluna(df_kpi, "Whatsapp Principal")
        col_wpp_fid = localizar_coluna(df_fid, "WhatsApp Principal")
        col_obs = localizar_coluna(df_kpi, "Observação")
        col_carteiras = localizar_coluna(df_kpi, "Carteiras")
        col_contato = localizar_coluna(df_kpi, "Contato")
        col_data_evento = localizar_coluna(df_kpi, "Data Evento")

        if not all([col_wpp_kpi, col_wpp_fid, col_obs, col_contato]):
            st.error("❌ Colunas obrigatórias não encontradas.")
            st.stop()

        # Limpeza e filtros
        df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip().apply(lambda x: re.sub(r'^0+', '', x))
        df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]
        df_kpi = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]
        if col_carteiras:
            df_kpi = df_kpi[~df_kpi[col_carteiras].isin(["SAC - Pós Venda", "Secretaria"])]
        df_kpi[col_contato] = df_kpi[col_contato].apply(processar_nome_abandono)

        base_pronta = df_kpi.rename(columns={col_contato: "Nome", col_wpp_kpi: "Numero"}).drop_duplicates(subset=["Numero"], keep="first")

        layout = ["TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE","CPFCNPJ","CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3","CORINGA4","CORINGA5","PRIORIDADE"]
        base_export = pd.DataFrame(columns=layout)
        base_export["VALOR_DO_REGISTRO"] = base_pronta["Numero"].apply(tratar_numero_telefone)
        base_export["NOME_CLIENTE"] = base_pronta["Nome"].astype(str).str.strip().str.lower().str.capitalize()
        base_export["TIPO_DE_REGISTRO"] = "TELEFONE"

        # Bloqueio de contatos específicos
        email_bloqueado = "ederaldosalustianodasilvaresta@gmail.com"
        numeros_bloqueados = {re.sub(r'\D', '', "(21) 96999-9549"), "5521969999549"}
        base_export = base_export[
            ~(base_export["VALOR_DO_REGISTRO"].isin(numeros_bloqueados)) &
            ~(base_export["NOME_CLIENTE"].str.lower() == email_bloqueado.lower())
        ]

        # Remove duplicatas e vazios
        base_export = base_export.drop_duplicates(subset=["VALOR_DO_REGISTRO"], keep="first")
        base_export = base_export[base_export["VALOR_DO_REGISTRO"].astype(str).str.strip() != ""]
        total_leads = len(base_export)
        nome_arquivo = gerar_nome_arquivo_abandono(df_kpi, col_data_evento)
        st.success(f"✅ Base de abandono pronta! Total de Leads Gerados: {total_leads}")

        output = BytesIO()
        base_export.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar (.csv)", output, file_name=nome_arquivo, mime="text/csv")
        st.dataframe(base_export)

# ===== Aba Carrinho Abandonado =====
def aba_carrinho():
    st.markdown("<div class='titulo-principal'>Carrinho Abandonado - Unificado</div>", unsafe_allow_html=True)
    file_carrinho = st.file_uploader("📂 Carrinho Abandonado", type=["xlsx","csv"], key="carrinho_file")
    file_nao_pagos = st.file_uploader("📂 Não Pagos", type=["xlsx","csv"], key="naopagos_file")
    file_pedidos = st.file_uploader("📂 Pedidos", type=["xlsx","csv"], key="pedidos_file")
    if file_carrinho and file_nao_pagos and file_pedidos:
        df_carrinho = importar_excel_tratamento_carrinho(read_file(file_carrinho))
        df_nao_pagos = importar_excel_tratamento_nao_pagos(read_file(file_nao_pagos))
        df_pedidos = read_file(file_pedidos)

        df_unificado = pd.concat([df_carrinho, df_nao_pagos], ignore_index=True)

        if 'E-mail (cobrança)' in df_pedidos.columns:
            emails_unif = df_unificado['e-mail'].str.strip().str.lower()
            emails_ped = df_pedidos['E-mail (cobrança)'].astype(str).str.strip().str.lower()
            df_unificado = df_unificado[~emails_unif.isin(emails_ped)]

        # Filtrar para colunas 'Nome' e 'Numero' somente
        df_unificado = df_unificado[['Nome','Numero']]

        # Layout de saída
        layout_cols = ["TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE","CPFCNPJ",
                       "CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3","CORINGA4","CORINGA5","PRIORIDADE"]
        df_saida = pd.DataFrame(columns=layout_cols)

        df_saida["VALOR_DO_REGISTRO"] = df_unificado["Numero"]
        df_saida["NOME_CLIENTE"] = df_unificado["Nome"].astype(str).str.strip().str.lower().str.capitalize()
        df_saida["TIPO_DE_REGISTRO"] = df_saida["VALOR_DO_REGISTRO"].apply(lambda x: "TELEFONE" if str(x).strip() != "" else "")

        # Bloqueio de contatos específicos
        email_bloqueado = "ederaldosalustianodasilvaresta@gmail.com"
        numeros_bloqueados = {re.sub(r'\D', '', "(21) 96999-9549"), "5521969999549"}
        df_saida = df_saida[
            ~(df_saida["VALOR_DO_REGISTRO"].isin(numeros_bloqueados)) &
            ~(df_saida["NOME_CLIENTE"].str.lower() == email_bloqueado.lower())
        ]

        # Remove duplicatas e vazios
        df_saida = df_saida.drop_duplicates(subset=["VALOR_DO_REGISTRO"], keep="first")
        df_saida = df_saida[df_saida["VALOR_DO_REGISTRO"].astype(str).str.strip() != ""]
        qtd_total_final = len(df_saida)

        nome_arquivo = gerar_nome_arquivo_carrinho()
        st.success(f"✅ Base Carrinho pronta! Total de Leads Gerados: {qtd_total_final}")

        output = BytesIO()
        df_saida.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)

        st.download_button("⬇️ Baixar (.csv)", output, file_name=nome_arquivo, mime="text/csv")
        st.dataframe(df_saida)

# ========= Menu ==========
aba = st.sidebar.selectbox("Selecione a campanha", ["Campanha de Abandono", "Carrinho Abandonado"])
if aba == "Campanha de Abandono":
    aba_abandono()
else:
    aba_carrinho()
