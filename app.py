import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Gera Campanha - Abandono & Carrinho", layout="centered")

# CSS (copiado do seu código para visual harmônico)
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
    font-size:2.7em;
    font-weight:700;
    margin:40px auto 18px auto;
}
.manual-inicio, .card-importacao {
    background:#fff;
    color:#222;
    border-radius:22px;
    box-shadow:0 4px 28px rgba(0,0,0,0.07);
    padding:28px 24px 18px 24px;
    width:100%;
    max-width:630px;
    margin:0 auto 28px auto;
    border-left:9px solid #018a62;
    font-size:1.07em;
}
.card-importacao h5 {
    color:#018a62;
    font-size:1.18em;
    font-weight:bold;
    text-align:center;
    margin-bottom:14px;
    margin-top:0;
}
.stDownloadButton > button, .stFileUploader > div > button {
    background-color:#3be291;
    color:#06643b;
    font-weight:bold;
    border-radius:7px;
    padding:10px 36px;
    border:none;
    font-size:1.09em;
    margin-top:12px;
}
.stDownloadButton > button:hover, .stFileUploader > div > button:hover {
    background-color:#018a62;
    color:#fff;
}
.stDataFrame, .stTable {
    background:#fff;
    border-radius:16px;
    color:#222;
    box-shadow:0 2px 12px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# Sidebar menu
aba = st.sidebar.selectbox("Selecione uma aba", ["Campanha de Abandono", "Carrinho Abandonado"])

# Funções comuns ----------------------------
def read_file(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    if f.name.lower().endswith(".csv"):
        try:
            return pd.read_csv(data_io, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            data_io.seek(0)
            return pd.read_csv(data_io, encoding="ISO-8859-1", sep=None, engine="python")
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
    if pd.isna(num):
        return ''
    num_str = re.sub(r'\D', '', str(num))
    num_str = num_str.lstrip('0')
    return '55' + num_str if num_str else ''

def limpar_nome_carrinho(nome):
    nome_limpo = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ\s]', '', str(nome))
    return nome_limpo

def tratar_nome_carrinho(row):
    nome = row['Nome'].strip()
    if len(nome) in [0,1,2,3] and pd.notna(row['Numero']) and str(row['Numero']).strip() != '':
        return "Candidato"
    else:
        return nome.title()

def importar_excel_tratamento_carrinho(df):
    # filtra colunas e trata nome
    cols = ['First-Name', 'Email', 'Phone']
    df = df[[c for c in cols if c in df.columns]]
    if 'First-Name' in df.columns:
        df['First-Name'] = df['First-Name'].str.split(' ').str[0]
    df = df.rename(columns={'First-Name': 'Nome', 'Email': 'e-mail', 'Phone': 'Numero'})
    df = df[['Nome','Numero','e-mail']]

    # limpezas no nome e telefone
    df['Nome'] = df['Nome'].apply(limpar_nome_carrinho)
    df['Nome'] = df.apply(tratar_nome_carrinho, axis=1)
    df['Numero'] = df['Numero'].apply(tratar_numero_telefone)
    return df

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
    df = df[['Nome','Numero','e-mail']]
    df['Nome'] = df['Nome'].apply(limpar_nome_carrinho)
    df['Nome'] = df.apply(tratar_nome_carrinho, axis=1)
    df['Numero'] = df['Numero'].apply(tratar_numero_telefone)
    return df

def gerar_nome_arquivo_carrinho():
    hoje = datetime.now()
    dia_semana = hoje.weekday()  # segunda=0, terça=1... domingo=6
    if dia_semana == 0: # segunda
        sexta = hoje - timedelta(days=3)
        domingo = hoje - timedelta(days=1)
        return f"Carrinho Abandonado_{sexta.strftime('%d.%m')}_{domingo.strftime('%d.%m')}.csv"
    else:
        dia_anterior = hoje - timedelta(days=1)
        return f"Carrinho Abandonado_{dia_anterior.strftime('%d.%m')}.csv"

def gerar_nome_arquivo_abandono(df_kpi, col_data_evento):
    nome_arquivo = "Abandono.csv"
    if col_data_evento and col_data_evento in df_kpi.columns:
        try:
            df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
            datas_validas = df_kpi[col_data_evento].dropna().dt.date
            if not datas_validas.empty:
                di, dfinal = min(datas_validas), max(datas_validas)
                if di == dfinal:
                    nome_arquivo = f"Abandono_{di.strftime('%d.%m')}.csv"
                else:
                    nome_arquivo = f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"
        except:
            pass
    return nome_arquivo

# === ABA: Campanha de Abandono ===
def aba_abandono():
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>PARA GERAR A BASE DE CAMPANHA É NECESSÁRIO:</strong><br>
            1️⃣ Gerar o relatório de KPI de Eventos para o período.<br>
            2️⃣ Gerar o relatório de Contatos Fidelizados.<br>
            3️⃣ Importe os arquivos abaixo.<br>
            4️⃣ O sistema irá processar e gerar a base final automaticamente.<br>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='card-importacao'><h5>Importe as bases aqui</h5></div>", unsafe_allow_html=True)

    file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx", "csv"], key="abandono_kpi")
    file_fid = st.file_uploader("📂 Importar base Fidelizados", type=["xlsx", "csv"], key="abandono_fid")

    if file_kpi and file_fid:
        df_kpi = read_file(file_kpi)
        df_fid = read_file(file_fid)

        # Localiza colunas relevantes
        col_wpp_kpi = localizar_coluna(df_kpi, "whatsapp principal")
        col_wpp_fid = localizar_coluna(df_fid, "whatsapp principal")
        col_obs = localizar_coluna(df_kpi, "observação")
        col_carteiras = localizar_coluna(df_kpi, "carteiras")
        col_contato = localizar_coluna(df_kpi, "contato")
        col_data_evento = localizar_coluna(df_kpi, "data evento")

        # Validação colunas obrigatórias
        if not all([col_wpp_kpi, col_wpp_fid, col_obs, col_contato]):
            st.error("❌ Colunas obrigatórias não encontradas nas bases.")
            st.stop()

        # Limpeza
        df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip()
        df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].apply(lambda x: re.sub(r'^0+', '', x))

        # Remove já fidelizados
        df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]

        # Filtro por observação (níveis de ensino)
        df_kpi = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]

        # Remove carteiras indesejadas
        if col_carteiras:
            df_kpi = df_kpi[~df_kpi[col_carteiras].isin(["SAC - Pós Venda", "Secretaria"])]

        # Tratamento nomes
        df_kpi[col_contato] = df_kpi[col_contato].apply(processar_nome_abandono)

        # Monta base para exportação
        mapping = {col_contato:"Nome", col_wpp_kpi:"Numero", col_obs:"Tipo"}
        base_pronta = df_kpi.rename(columns=mapping)[["Nome","Numero","Tipo"]]
        base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")

        # Layout Robbu
        layout = ["TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE",
                  "CPFCNPJ","CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3",
                  "CORINGA4","CORINGA5","PRIORIDADE"]
        base_export = pd.DataFrame(columns=layout)
        base_export["VALOR_DO_REGISTRO"] = base_pronta["Numero"].apply(tratar_numero_telefone)
        base_export["NOME_CLIENTE"] = base_pronta["Nome"]
        base_export["TIPO_DE_REGISTRO"] = "TELEFONE"
        base_export = base_export[layout]

        nome_arquivo = gerar_nome_arquivo_abandono(df_kpi, col_data_evento)

        st.success(f"✅ Base de campanha pronta! {len(base_export)} registros.")
        output = BytesIO()
        base_export.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar campanha (.csv)", output, file_name=nome_arquivo, mime="text/csv")

        st.markdown("<h4 style='color:#077339; margin-top:20px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
        st.dataframe(base_export)


# === ABA: Carrinho Abandonado ===
def aba_carrinho():
    st.markdown("<div class='titulo-principal'>Carrinho Abandonado - Unificado</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>PARA GERAR A BASE DE CARRINHO ABANDONADO É NECESSÁRIO:</strong><br>
            1️⃣ Importar os arquivos abaixo:<br>
            - Carrinho Abandonado<br>
            - Não Pagos<br>
            - Pedidos<br>
            2️⃣ O sistema fará a união, limpeza, filtragem e geração da base final.<br>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='card-importacao'><h5>Importe as bases aqui</h5></div>", unsafe_allow_html=True)

    file_carrinho = st.file_uploader("📂 Importar Carrinho Abandonado", type=["xlsx","csv"], key="carrinho_aband")
    file_nao_pagos = st.file_uploader("📂 Importar Não Pagos", type=["xlsx","csv"], key="nao_pagos")
    file_pedidos = st.file_uploader("📂 Importar Pedidos", type=["xlsx","csv"], key="pedidos")

    if file_carrinho and file_nao_pagos and file_pedidos:
        df_carrinho = read_file(file_carrinho)
        df_nao_pagos = read_file(file_nao_pagos)
        df_pedidos = read_file(file_pedidos)

        # Processa carrinho
        df_carrinho = importar_excel_tratamento_carrinho(df_carrinho)

        # Processa não pagos
        df_nao_pagos = importar_excel_tratamento_nao_pagos(df_nao_pagos)

        # Unifica
        df_unificado = pd.concat([df_carrinho, df_nao_pagos], ignore_index=True)

        # Remove duplicados de emails presentes em pedidos
        if 'E-mail (cobrança)' in df_pedidos.columns:
            emails_unificado = df_unificado['e-mail'].str.strip().str.lower()
            emails_pedidos = df_pedidos['E-mail (cobrança)'].astype(str).str.strip().str.lower()
            df_unificado = df_unificado[~emails_unificado.isin(emails_pedidos)]

        # Limpa e trata nomes
        df_unificado['Nome'] = df_unificado['Nome'].astype(str).apply(limpar_nome_carrinho)
        def tratar_nome_condicional(row):
            nome = row['Nome'].strip()
            if len(nome) in [0,1,2,3] and pd.notna(row['Numero']) and str(row['Numero']).strip() != '':
                return "Candidato"
            else:
                return nome.title()
        df_unificado['Nome'] = df_unificado.apply(tratar_nome_condicional, axis=1)

        # Trata telefones
        def tratar_numero(num):
            if pd.isna(num):
                return ''
            num_str = re.sub(r'\D', '', str(num))
            num_str = num_str.lstrip('0')
            return '55' + num_str if num_str else ''
        df_unificado['Numero'] = df_unificado['Numero'].apply(tratar_numero)

        # Mantém somente colunas necessárias
        df_unificado = df_unificado[['Nome','Numero']]

        # Monta layout final
        layout_cols = [
            "TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE", "CPFCNPJ",
            "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3", "CORINGA4", "CORINGA5", "PRIORIDADE"
        ]
        df_saida = pd.DataFrame(columns=layout_cols)
        df_saida["VALOR_DO_REGISTRO"] = df_unificado["Numero"]
        df_saida["NOME_CLIENTE"] = df_unificado["Nome"]
        df_saida["TIPO_DE_REGISTRO"] = df_saida["VALOR_DO_REGISTRO"].apply(
            lambda x: "TELEFONE" if pd.notna(x) and str(x).strip() != "" else ""
        )

        nome_arquivo = gerar_nome_arquivo_carrinho()

        st.success(f"✅ Base Carrinho Abandonado pronta! {len(df_saida)} registros.")
        output = BytesIO()
        df_saida.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar campanha (.csv)", output, file_name=nome_arquivo, mime="text/csv")

        st.markdown("<h4 style='color:#077339; margin-top:20px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
        st.dataframe(df_saida)


# Exibe a aba selecionada
if aba == "Campanha de Abandono":
    aba_abandono()
elif aba == "Carrinho Abandonado":
    aba_carrinho()
