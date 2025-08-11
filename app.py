import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha", page_icon="📢", layout="centered")

# ======= CSS =======
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
    * { font-family: 'Poppins', sans-serif; }
    body { background-color: #f4f6f8; }
    .titulo-principal {
        background-color: #004aad;
        color: white;
        padding: 18px;
        border-radius: 8px;
        text-align: center;
        font-size: 2em;
        font-weight: 600;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    div.stDownloadButton > button, div.stFileUploader > div > button {
        background-color: #ffb703;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 16px;
        border: none;
    }
    div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
        background-color: #fb8500;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='titulo-principal'>📢 Gera Campanha</div>", unsafe_allow_html=True)

# ======= Função leitura de arquivos =======
def read_kpi_all_sheets(f):
    """Lê TODAS as abas do Excel KPI, une e remove duplicatas por WhatsApp Principal"""
    xls = pd.ExcelFile(f)
    df_list = []
    for sheet in xls.sheet_names:
        df_sheet = pd.read_excel(xls, sheet_name=sheet)
        df_list.append(df_sheet)
    df_total = pd.concat(df_list, ignore_index=True)

    # Localiza coluna de telefone
    col_tel = next((c for c in df_total.columns if str(c).strip().lower() == "whatsapp principal"), None)
    if col_tel:
        df_total = df_total.drop_duplicates(subset=[col_tel], keep="first")

    return df_total

def read_file_generic(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    if f.name.lower().endswith(".csv"):
        try:
            return pd.read_csv(data_io, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            data_io.seek(0)
            return pd.read_csv(data_io, encoding="ISO-8859-1", sep=None, engine="python")
    else:
        return read_kpi_all_sheets(data_io)

# ======= Upload =======
file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx", "csv"])
file_fid = st.file_uploader("📂 Importar base FIDELIZADOS", type=["xlsx", "csv"])

if file_kpi and file_fid:
    df_kpi = read_file_generic(file_kpi)
    df_fid = read_file_generic(file_fid)  # Fidelizados normalmente vem de uma aba só

    col_whatsapp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
    col_whatsapp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)

    # Coleta datas para nome do arquivo
    col_data_evento = next((c for c in df_kpi.columns if str(c).strip().lower() == "data evento"), None)
    data_inicial_str = data_final_str = ""
    if col_data_evento:
        datas = pd.to_datetime(df_kpi[col_data_evento], errors='coerce').dropna()
        if not datas.empty:
            dmin, dmax = datas.min(), datas.max()
            if dmin == dmax:
                data_inicial_str = dmin.strftime("%d.%m.%Y")
            else:
                data_inicial_str = dmin.strftime("%d.%m.%Y")
                data_final_str = dmax.strftime("%d.%m.%Y")

    if not col_whatsapp_kpi or not col_whatsapp_fid:
        st.error("❌ Coluna 'WhatsApp Principal' não encontrada.")
    else:
        # Remove números da KPI que estão na Fidelizados
        df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]

        # Filtra Observação
        col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
        filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
        filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
        base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

        # Remove carteiras indesejadas
        col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
        if col_carteiras:
            base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(["SAC - Pós Venda", "Secretaria"])]

        # Processa contato
        col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
        if col_contato:
            def processar_contato(valor):
                texto = str(valor).strip()
                if not texto:
                    return texto
                primeira = texto.split(" ")[0].capitalize()
                return "Candidato" if len(primeira) < 3 else primeira
            base_pronta[col_contato] = base_pronta[col_contato].apply(processar_contato)

        # Mantém colunas necessárias e renomeia
        mapping = {col_contato: "Nome", col_whatsapp_kpi: "Numero", col_obs: "Tipo"}
        base_pronta = base_pronta.rename(columns=mapping)
        base_pronta = base_pronta[["Nome", "Numero", "Tipo"]].drop_duplicates(subset=["Numero"], keep="first")

        # Trata números
        base_pronta["Numero"] = base_pronta["Numero"].astype(str).apply(lambda x: "55" + re.sub(r"\D", "", x))
        base_pronta = base_pronta[base_pronta["Numero"].str.len().between(12, 13)]

        # Monta layout final
        layout_cols = [
            "TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE","CPFCNPJ","CODCLIENTE",
            "TAG","CORINGA1","CORINGA2","CORINGA3","CORINGA4","CORINGA5","PRIORIDADE"
        ]
        base_importacao = pd.DataFrame(columns=layout_cols)
        base_importacao["VALOR_DO_REGISTRO"] = base_pronta["Numero"].values
        base_importacao["NOME_CLIENTE"] = base_pronta["Nome"].values
        base_importacao["TIPO_DE_REGISTRO"] = "TELEFONE"
        base_importacao = base_importacao[layout_cols]

        # Nome do arquivo
        if data_inicial_str and data_final_str:
            nome_arquivo = f"Abandono_{data_inicial_str}_{data_final_str}.csv"
        elif data_inicial_str:
            nome_arquivo = f"Abandono_{data_inicial_str}.csv"
        else:
            nome_arquivo = "Abandono.csv"

        st.success(f"✅ Base de campanha gerada ({len(base_importacao)} registros)")
        st.dataframe(base_importacao)

        # Download
        output = BytesIO()
        base_importacao.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button(
            label=f"⬇️ Baixar {nome_arquivo}",
            data=output,
            file_name=nome_arquivo,
            mime="text/csv"
        )

