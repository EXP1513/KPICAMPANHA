import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# ---------- CSS COM SUPORTE A MODO ESCURO ----------
st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', sans-serif;
    }
    .titulo-principal {
        background-color: #004aad;
        color: #fff;
        padding: 18px;
        border-radius: 8px;
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 20px;
    }
    div.stDownloadButton > button, div.stFileUploader > div > button {
        background-color: #ffb703cc;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 16px;
        border: none;
    }
    div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
        background-color: #fb850099;
        color: white;
    }
    .manual-popup {
        background-color: #fff3cdcc;
        border-left: 6px solid #ff9800cc;
        padding: 15px;
        border-radius: 6px;
        font-size: 1.05em;
        margin-top: 20px;
        color: black;
    }

    /* ===== Ajustes para modo escuro ===== */
    @media (prefers-color-scheme: dark) {
        body, .manual-popup, .stMarkdown, .stText, .stDataFrame, .stTable {
            color: white !important;
        }
        div.stDownloadButton > button, div.stFileUploader > div > button {
            color: white !important;
            background-color: #ffb703cc !important;
        }
        div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
            background-color: #fb850099 !important;
            color: white !important;
        }
        .manual-popup {
            background-color: rgba(255, 243, 205, 0.1) !important;
            border-left: 6px solid rgba(255, 152, 0, 0.8);
            color: white !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------- MENU NA SIDEBAR ----------
st.sidebar.title("📋 Selecione o tipo de campanha")
opcao = st.sidebar.radio("", ["Abandono", "Carrinho Abandonado"])


# ---------- FUNÇÕES COMUNS ----------
def read_file(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    if f.name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(data_io, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            data_io.seek(0)
            df = pd.read_csv(data_io, encoding="ISO-8859-1", sep=None, engine="python")
    else:
        df = pd.read_excel(data_io)
    col_carteiras = next((c for c in df.columns if str(c).strip().lower() == "carteiras"), None)
    if col_carteiras:
        valores_permitidos = ["SAC", "Distribuição Manual"]
        df = df[df[col_carteiras].astype(str).str.strip().isin(valores_permitidos)]
    return df

def identificar_base_kpi(df):
    return any("data evento" == str(c).strip().lower() for c in df.columns)

def identificar_base_fidelizados(df):
    return any(str(c).strip().lower() in ["nome cliente","contato","nome"] for c in df.columns)

def processar_nome(valor):
    texto_original = str(valor).strip()
    nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', '', texto_original)  # mantém letras, números e espaços
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo).strip()
    if not nome_limpo:
        return "Candidato"
    return nome_limpo.title()


# ---------- CONTEÚDO DAS PÁGINAS ----------
if opcao == "Abandono":
    st.markdown("<div class='titulo-principal'>🚀🇧🇷🚀 Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background-color:#e0f7fa; border-left: 5px solid #00796b;
                    padding: 15px; margin-bottom: 20px; border-radius: 5px;'>
            <strong>PARA GERAR A BASE CAMPANHA É NECESSÁRIO IR ANTES NA ROBBU E...</strong><br>
            1️⃣ Gere o relatório de <b>KPI de Eventos</b>, selecionando o período desejado.<br>
            2️⃣ Gere o relatório de <b>Contatos Fidelizados</b>.<br>
            3️⃣ Faça o upload de <b>KPI</b> no campo correspondente.<br>
            4️⃣ Faça o upload de <b>Fidelizados</b> no campo correspondente.<br>
            5️⃣ O sistema processará e gerará a base final automaticamente.<br>
        </div>
        """, unsafe_allow_html=True)

    file_kpi = st.file_uploader("📂 Importar base **KPI**", type=["xlsx", "csv"])
    file_fid = st.file_uploader("📂 Importar base **FIDELIZADOS**", type=["xlsx", "csv"])

    if file_kpi and file_fid:
        df_kpi = read_file(file_kpi)
        df_fid = read_file(file_fid)
        kpi_valido = identificar_base_kpi(df_kpi)
        fid_valido = identificar_base_fidelizados(df_fid)
        kpi_invertido = identificar_base_kpi(df_fid)
        fid_invertido = identificar_base_fidelizados(df_kpi)

        if (not kpi_valido and not fid_valido) and (not kpi_invertido and not fid_invertido):
            st.error("❌ Bases incorretas foram importadas. Verifique os arquivos.")
        elif kpi_invertido and fid_invertido:
            st.error("⚠️ As bases parecem estar invertidas. Verifique e recarregue corretamente.")
        elif not kpi_valido or not fid_valido:
            st.error("❌ Um dos arquivos não corresponde ao tipo esperado (KPI ou Fidelizados).")
        else:
            col_whatsapp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
            col_whatsapp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)
            if not col_whatsapp_kpi or not col_whatsapp_fid:
                st.error("❌ Coluna 'WhatsApp Principal' não encontrada.")
            else:
                df_kpi[col_whatsapp_kpi] = df_kpi[col_whatsapp_kpi].astype(str).str.strip()
                df_kpi[col_whatsapp_kpi] = df_kpi[col_whatsapp_kpi].apply(lambda x: re.sub(r'^0+', '', x) if re.match(r'^0', x) else x)

                nome_arquivo = "Abandono.csv"
                col_data_evento = next((c for c in df_kpi.columns if str(c).strip().lower() == "data evento"), None)
                if col_data_evento:
                    try:
                        df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
                        datas_validas = df_kpi[col_data_evento].dropna().dt.date
                        if not datas_validas.empty:
                            data_inicial = min(datas_validas)
                            data_final = max(datas_validas)
                            if data_inicial == data_final:
                                nome_arquivo = f"Abandono_{data_inicial.strftime('%d.%m')}.csv"
                            else:
                                nome_arquivo = f"Abandono_{data_inicial.strftime('%d.%m')}_a_{data_final.strftime('%d.%m')}.csv"
                    except Exception as e:
                        st.warning(f"⚠️ Não foi possível processar as datas: {e}")

                df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]
                col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
                filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
                filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
                base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)
                col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
                if col_carteiras:
                    termos_excluir = ["SAC - Pós Venda", "Secretaria"]
                    base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]
                col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
                if col_contato:
                    base_pronta[col_contato] = base_pronta[col_contato].apply(processar_nome)
                mapping = {col_contato: "Nome", col_whatsapp_kpi: "Numero", col_obs: "Tipo"}
                base_pronta = base_pronta.rename(columns=mapping)[["Nome", "Numero", "Tipo"]]
                base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")

                layout_colunas = [
                    "TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE",
                    "CPFCNPJ", "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3",
                    "CORINGA4", "CORINGA5", "PRIORIDADE"
                ]
                base_importacao = pd.DataFrame(columns=layout_colunas)
                base_importacao["VALOR_DO_REGISTRO"] = base_pronta["Numero"].values
                base_importacao["NOME_CLIENTE"] = base_pronta["Nome"].values
                base_importacao["TIPO_DE_REGISTRO"] = "TELEFONE"
                base_importacao = base_importacao[layout_colunas]

                def limpar_numero_final(num):
                    num_limpo = re.sub(r"\D", "", str(num))
                    num_limpo = num_limpo.lstrip("0")
                    return "55" + num_limpo
                base_importacao["VALOR_DO_REGISTRO"] = base_importacao["VALOR_DO_REGISTRO"].apply(limpar_numero_final)

                st.success(f"✅ Base de campanha gerada para importação! {len(base_importacao)} registros.")

                output = BytesIO()
                base_importacao.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
                output.seek(0)
                st.download_button(
                    label="⬇️ DOWNLOAD CAMPANHA (formato .csv)",
                    data=output,
                    file_name=nome_arquivo,
                    mime="text/csv"
                )

elif opcao == "Carrinho Abandonado":
    st.markdown("<div class='titulo-principal'>🛒 Carrinho Abandonado</div>", unsafe_allow_html=True)
    st.info("🚧 Em construção... Em breve você poderá gerar a base de Carrinho Abandonado aqui!")
