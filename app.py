import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta
import csv

# Lista das colunas esperadas na base KPI
kpi_columns = [
    "Data Evento",
    "Descrição Evento",
    "Tipo de Evento",
    "Evento Finalizador",
    "Contato",
    "Identificação",
    "Código Contato",
    "Hashtag",
    "Usuário",
    "Número Protocolo",
    "Data Hora Geração Protocolo",
    "Observação",
    "SMS Principal",
    "Whatsapp Principal",
    "Email Principal",
    "Canal",
    "Carteiras",
    "Carteira do Evento",
    "Valor da oportunidade",
    "Identificador da chamada de Voz"
]

# Lista das colunas esperadas na base Fidelizados
fidelizados_columns = [
    "Usuário Fidelizado",
    "Contato",
    "Identificação",
    "Código",
    "Canal",
    "Último Contato",
    "Qtd. Mensagens Pendentes",
    "SMS Principal",
    "WhatsApp Principal",
    "Email Principal",
    "Segmentos vinculados a pessoa",
    "Agendado",
    "Data Hora Agendamento",
    "Ultimo Evento",
    "Ultimo Evento Finalizador"
]

def read_file(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    sep = ','  
    if f.name.lower().endswith(".csv"):
        try:
            sample = bytes_data[:1024].decode("utf-8", errors="ignore")
            try:
                dialect = csv.Sniffer().sniff(sample)
                sep = dialect.delimiter
            except Exception:
                sep = ',' if ',' in sample else ';'
            data_io.seek(0)
            try:
                return pd.read_csv(
                    data_io,
                    encoding="utf-8",
                    sep=sep,
                    on_bad_lines='warn'
                )
            except pd.errors.ParserError as e:
                st.error(f"Erro ao ler o CSV: {e}. Verifique se o arquivo está bem formatado.")
                st.stop()
        except UnicodeDecodeError:
            data_io.seek(0)
            try:
                return pd.read_csv(
                    data_io,
                    encoding="ISO-8859-1",
                    sep=sep,
                    on_bad_lines='warn'
                )
            except pd.errors.ParserError as e:
                st.error(f"Erro ao ler o CSV com encoding ISO: {e}. Verifique se o arquivo está bem formatado.")
                st.stop()
    else:
        return pd.read_excel(data_io)

def localizar_colunas(df, col_names):
    found_cols = {}
    for col_name in col_names:
        for c in df.columns:
            if str(c).strip().lower() == col_name.lower():
                found_cols[col_name] = c
                break
    return found_cols

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

def carregar_fidelizados_tratado(file_fid):
    df_fid = read_file(file_fid)
    cols_fid = localizar_colunas(df_fid, fidelizados_columns)

    # Validar colunas essenciais - Whatsapp Principal e Contato
    col_wpp_fid = cols_fid.get("WhatsApp Principal")
    col_contato_fid = cols_fid.get("Contato")
    if not all([col_wpp_fid, col_contato_fid]):
        st.error("❌ Colunas obrigatórias da base Fidelizados não encontradas.")
        st.stop()

    # Selecionar apenas as colunas encontradas para trabalhar
    df_fid = df_fid[list(cols_fid.values())]

    return df_fid, cols_fid

def localizar_coluna(df, nome):
    return next((c for c in df.columns if str(c).strip().lower() == nome.lower()), None)

def aba_abandono():
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    file_kpi = st.file_uploader("📂 Base KPI", type=["xlsx","csv"], key="kpi_file")
    file_fid = st.file_uploader("📂 Base Fidelizados", type=["xlsx","csv"], key="fid_file")

    if file_kpi and file_fid:
        df_kpi = read_file(file_kpi)
        df_fid, cols_fid = carregar_fidelizados_tratado(file_fid)

        # Localizar colunas KPI conforme lista específica
        kpi_cols = localizar_colunas(df_kpi, kpi_columns)

        # Validar colunas essenciais na KPI
        col_wpp_kpi = kpi_cols.get("Whatsapp Principal")
        col_obs = kpi_cols.get("Observação")
        col_contato = kpi_cols.get("Contato")
        col_carteiras = kpi_cols.get("Carteiras")
        col_data_evento = kpi_cols.get("Data Evento")

        if not all([col_wpp_kpi, col_obs, col_contato]):
            st.error("❌ Colunas obrigatórias da base KPI não encontradas.")
            st.stop()

        # Colunas essenciais na base fidelizados (já validadas no carregar_fidelizados_tratado)
        col_wpp_fid = cols_fid.get("WhatsApp Principal")

        # Limpeza e filtros na base KPI
        df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip().apply(lambda x: re.sub(r'^0+', '', x))

        # Remove contatos que já estão na base fidelizados
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
