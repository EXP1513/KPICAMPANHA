import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Gera Campanha - Abandono & Carrinho", layout="centered")

##--- CSS personalizado ---
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(90deg,#018a62 0%,#3be291 35%,#fee042 100%)!important;
    min-height: 100vh;
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

##--- Função robusta para leitura de arquivos ---
def read_file(f):
    try:
        bytes_data = f.read()
        data_io = BytesIO(bytes_data)
        data_io.seek(0)
        if f.name.lower().endswith('.csv'):
            try:
                return pd.read_csv(data_io, sep=';', encoding='ISO-8859-1', on_bad_lines='warn', engine='python')
            except Exception:
                data_io.seek(0)
                return pd.read_csv(data_io, sep=';', encoding='utf-8', on_bad_lines='warn', engine='python')
        elif f.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(data_io)
        else:
            st.error("Formato de arquivo não suportado. Use CSV ou Excel.")
            return None
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

def localizar_coluna(df, nome):
    return next((c for c in df.columns if str(c).strip().lower() == nome.lower()), None)

##--- Funções de tratamento ---
def processar_nome_abandono(valor):
    texto_original = str(valor).strip()
    primeiro_nome = texto_original.split(' ')[0]
    nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
    return nome_limpo.title() if len(nome_limpo) > 3 else "Candidato"

def tratar_numero_telefone(num):
    if pd.isna(num): return ''
    num_str = re.sub(r'\D', '', str(num)).lstrip('0')
    return '55' + num_str if num_str else ''

def limpar_nome_carrinho(nome):
    return re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ\s]', '', str(nome))

def tratar_nome_carrinho(row):
    nome = str(row['Nome']).strip()
    return "Candidato" if len(nome) in [0,1,2,3] and pd.notna(row['Numero']) and str(row['Numero']).strip() else nome.title()

##--- Importar Carrinho com validação rigorosa ---
def importar_excel_tratamento_carrinho(df):
    required = {'First-Name', 'Email', 'Phone'}
    atual = set(df.columns)
    faltando = required - atual
    if faltando:
        st.error(f"O arquivo Carrinho Abandonado está faltando as colunas: {', '.join(faltando)}")
        st.stop()
    df = df[list(required)]
    df['First-Name'] = df['First-Name'].astype(str).str.split(' ').str[0]
    df.rename(columns={'First-Name': 'Nome', 'Email': 'e-mail', 'Phone': 'Numero'}, inplace=True)
    df['Nome'] = df['Nome'].apply(limpar_nome_carrinho)
    df['Nome'] = df.apply(tratar_nome_carrinho, axis=1)
    df['Numero'] = df['Numero'].apply(tratar_numero_telefone)
    return df[['Nome', 'Numero', 'e-mail']]

##--- Importar Não Pagos com validação rigorosa ---
def importar_excel_tratamento_nao_pagos(df):
    required = {'Nome completo (cobrança)', 'Telefone (cobrança)', 'E-mail (cobrança)'}
    atual = set(df.columns)
    faltando = required - atual
    if faltando:
        st.error(f"O arquivo Não Pagos está faltando as colunas: {', '.join(faltando)}")
        st.stop()
    df = df[list(required)]
    df['Nome completo (cobrança)'] = df['Nome completo (cobrança)'].astype(str).str.split(' ').str[0]
    df.rename(columns={
        'Nome completo (cobrança)': 'Nome',
        'Telefone (cobrança)': 'Numero',
        'E-mail (cobrança)': 'e-mail'
    }, inplace=True)
    df['Nome'] = df['Nome'].apply(limpar_nome_carrinho)
    df['Nome'] = df.apply(tratar_nome_carrinho, axis=1)
    df['Numero'] = df['Numero'].apply(tratar_numero_telefone)
    return df[['Nome', 'Numero', 'e-mail']]

##--- Nome do arquivo gerado ---
def gerar_nome_arquivo_carrinho():
    hoje = datetime.now()
    dia_semana = hoje.weekday()
    prefixo = "Carinho_Nãopagos"
    if dia_semana == 0:
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
                return f"Abandono_{di.strftime('%d.%m')}.csv" if di == dfinal else f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"
        except Exception:
            pass
    return "Abandono.csv"

##--- Padronização de colunas para KPI/Fidelizados
colunas_kpi_base = [
    'Data Evento', 'Descrição Evento', 'Tipo de Evento', 'Evento Finalizador', 'Contato', 'Identificação', 
    'Código Contato', 'Hashtag', 'Usuário', 'Número Protocolo', 'Data Hora Geração Protocolo', 'Observação', 
    'SMS Principal', 'Whatsapp Principal', 'Email Principal', 'Canal', 'Carteiras', 'Carteira do Evento', 
    'Valor da oportunidade', 'Identificador da chamada de Voz'
]
def padronizar_colunas_kpi(df):
    col_mapping = {c: col for col in colunas_kpi_base for c in df.columns if c.lower().strip() == col.lower().strip()}
    df.rename(columns=col_mapping, inplace=True)
    return df[[col for col in colunas_kpi_base if col in df.columns]]

colunas_fid_base = [
    'Usuário Fidelizado', 'Contato', 'Identificação', 'Código', 'Canal', 'Último Contato', 'Qtd. Mensagens Pendentes', 
    'SMS Principal', 'WhatsApp Principal', 'Email Principal', 'Segmentos vinculados a pessoa', 'Agendado', 
    'Data Hora Agendamento', 'Ultimo Evento', 'Ultimo Evento Finalizador'
]
def padronizar_colunas_fid(df):
    col_mapping = {c: col for col in colunas_fid_base for c in df.columns if c.lower().strip() == col.lower().strip()}
    df.rename(columns=col_mapping, inplace=True)
    return df[[col for col in colunas_fid_base if col in df.columns]]

##--- Aba Abandono
def aba_abandono():
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    file_kpi = st.file_uploader("📂 Base KPI", type=["xlsx","csv"], key="kpi_file")
    file_fid = st.file_uploader("📂 Base Fidelizados", type=["xlsx","csv"], key="fid_file")

    if file_kpi and file_fid:
        df_kpi, df_fid = read_file(file_kpi), read_file(file_fid)
        if df_kpi is None or df_kpi.empty:
            st.error("Arquivo de KPI inválido ou está vazio.")
            return
        if df_fid is None or df_fid.empty:
            st.error("Arquivo de Fidelizados inválido ou está vazio.")
            return

        df_kpi, df_fid = padronizar_colunas_kpi(df_kpi), padronizar_colunas_fid(df_fid)
        col_wpp_kpi, col_wpp_fid = localizar_coluna(df_kpi, "Whatsapp Principal"), localizar_coluna(df_fid, "WhatsApp Principal")
        col_obs, col_carteiras = localizar_coluna(df_kpi, "Observação"), localizar_coluna(df_kpi, "Carteiras")
        col_contato, col_data_evento = localizar_coluna(df_kpi, "Contato"), localizar_coluna(df_kpi, "Data Evento")

        if not all([col_wpp_kpi, col_wpp_fid, col_obs, col_contato]):
            st.error("❌ Colunas obrigatórias não encontradas.")
            return

        # Processamento e filtros
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
        base_export["NOME_CLIENTE"] = base_pronta["Nome"].str.strip().str.lower().str.capitalize()
        base_export["TIPO_DE_REGISTRO"] = "TELEFONE"

        email_bloqueado = "ederaldosalustianodasilvaresta@gmail.com"
        numeros_bloqueados = {"5521969999549"}
        base_export = base_export[
            ~(base_export["VALOR_DO_REGISTRO"].isin(numeros_bloqueados)) &
            ~(base_export["NOME_CLIENTE"].str.lower() == email_bloqueado.lower())
        ]
        base_export = base_export.drop_duplicates(subset=["VALOR_DO_REGISTRO"], keep="first")
        base_export = base_export[base_export["VALOR_DO_REGISTRO"].astype(str).str.strip() != ""]
        total_leads, nome_arquivo = len(base_export), gerar_nome_arquivo_abandono(df_kpi, col_data_evento)
        st.success(f"✅ Base de abandono pronta! Total de Leads Gerados: {total_leads}")

        output = BytesIO()
        base_export.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar (.csv)", output, file_name=nome_arquivo, mime="text/csv")
        st.dataframe(base_export, width=750)

##--- Aba Carrinho Abandonado
def aba_carrinho():
    st.markdown("<div class='titulo-principal'>Carrinho Abandonado - Unificado</div>", unsafe_allow_html=True)
    file_carrinho = st.file_uploader("📂 Carrinho Abandonado", type=["xlsx","csv"], key="carrinho_file")
    file_nao_pagos = st.file_uploader("📂 Não Pagos", type=["xlsx","csv"], key="naopagos_file")
    file_pedidos = st.file_uploader("📂 Pedidos", type=["xlsx","csv"], key="pedidos_file")

    if file_carrinho and file_nao_pagos and file_pedidos:
        df_carrinho = read_file(file_carrinho)
        df_nao_pagos = read_file(file_nao_pagos)
        df_pedidos = read_file(file_pedidos)

        for nome, df in zip(
            ["Carrinho Abandonado", "Não Pagos", "Pedidos"], 
            [df_carrinho, df_nao_pagos, df_pedidos]
        ):
            if df is None or df.empty:
                st.error(f"Arquivo '{nome}' inválido ou está vazio.")
                return

        df_carrinho = importar_excel_tratamento_carrinho(df_carrinho)
        df_nao_pagos = importar_excel_tratamento_nao_pagos(df_nao_pagos)
        df_unificado = pd.concat([df_carrinho, df_nao_pagos], ignore_index=True)

        if 'E-mail (cobrança)' in df_pedidos.columns:
            emails_unif = df_unificado['e-mail'].str.strip().str.lower()
            emails_ped = df_pedidos['E-mail (cobrança)'].astype(str).str.strip().str.lower()
            df_unificado = df_unificado[~emails_unif.isin(emails_ped)]
        df_unificado = df_unificado[['Nome','Numero']]

        layout_cols = ["TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE","CPFCNPJ",
                       "CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3","CORINGA4","CORINGA5","PRIORIDADE"]
        df_saida = pd.DataFrame(columns=layout_cols)
        df_saida["VALOR_DO_REGISTRO"] = df_unificado["Numero"]
        df_saida["NOME_CLIENTE"] = df_unificado["Nome"].str.strip().str.lower().str.capitalize()
        df_saida["TIPO_DE_REGISTRO"] = df_saida["VALOR_DO_REGISTRO"].apply(lambda x: "TELEFONE" if str(x).strip() else "")

        email_bloqueado = "ederaldosalustianodasilvaresta@gmail.com"
        numeros_bloqueados = {"5521969999549"}
        df_saida = df_saida[
            ~(df_saida["VALOR_DO_REGISTRO"].isin(numeros_bloqueados)) &
            ~(df_saida["NOME_CLIENTE"].str.lower() == email_bloqueado.lower())
        ]
        df_saida = df_saida.drop_duplicates(subset=["VALOR_DO_REGISTRO"], keep="first")
        df_saida = df_saida[df_saida["VALOR_DO_REGISTRO"].astype(str).str.strip() != ""]
        qtd_total_final, nome_arquivo = len(df_saida), gerar_nome_arquivo_carrinho()
        st.success(f"✅ Base Carrinho pronta! Total de Leads Gerados: {qtd_total_final}")

        output = BytesIO()
        df_saida.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar (.csv)", output, file_name=nome_arquivo, mime="text/csv")
        st.dataframe(df_saida, width=750)

##--- Menu principal
aba = st.sidebar.selectbox("Selecione a campanha", ["Campanha de Abandono", "Carrinho Abandonado"])
if aba == "Campanha de Abandono":
    aba_abandono()
else:
    aba_carrinho()
