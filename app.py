import streamlit as st
import pandas as pd
from io import BytesIO
import re

# ==============================
# CONFIG E CSS PROFISSIONAL
# ==============================
st.set_page_config(page_title="Gera Campanha", page_icon="📢", layout="centered")

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

# ==============================
# LEITURA DE ARQUIVOS
# ==============================
def read_excel_all_sheets(f):
    xls = pd.ExcelFile(f)
    all_sheets = [pd.read_excel(xls, sheet) for sheet in xls.sheet_names]
    df = pd.concat(all_sheets, ignore_index=True)
    col_tel = next((c for c in df.columns if str(c).strip().lower() == "whatsapp principal"), None)
    if col_tel:
        df = df.drop_duplicates(subset=[col_tel], keep="first")
    return df

def read_file(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    if f.name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(data_io, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            data_io.seek(0)
            df = pd.read_csv(data_io, encoding="ISO-8859-1", sep=None, engine="python")
        col_tel = next((c for c in df.columns if str(c).strip().lower() == "whatsapp principal"), None)
        if col_tel:
            df = df.drop_duplicates(subset=[col_tel], keep="first")
        return df
    else:
        return read_excel_all_sheets(data_io)

# ==============================
# UPLOAD DE ARQUIVOS
# ==============================
file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx","csv"])
file_fid = st.file_uploader("📂 Importar base FIDELIZADOS", type=["xlsx","csv"])

if file_kpi and file_fid:
    df_kpi = read_file(file_kpi)
    df_fid = read_file(file_fid)

    # Colunas de telefone
    col_whatsapp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
    col_whatsapp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)

    # Datas para nome do arquivo
    col_data_evt = next((c for c in df_kpi.columns if str(c).strip().lower() == "data evento"), None)
    data_ini_str, data_fim_str = "", ""
    if col_data_evt:
        datas = pd.to_datetime(df_kpi[col_data_evt], errors="coerce").dropna()
        if not datas.empty:
            dmin, dmax = datas.min(), datas.max()
            if dmin == dmax:
                data_ini_str = dmin.strftime("%d.%m")
            else:
                data_ini_str = dmin.strftime("%d.%m")
                data_fim_str = dmax.strftime("%d.%m")

    if not col_whatsapp_kpi or not col_whatsapp_fid:
        st.error("❌ Coluna 'WhatsApp Principal' não encontrada.")
    else:
        # Remove da KPI os que estão na Fidelizados
        df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]

        # Filtros por Observação
        col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
        filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
        filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
        base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

        # Remove carteiras específicas
        col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
        if col_carteiras:
            base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(["SAC - Pós Venda", "Secretaria"])]

        # Processa coluna contato
        col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
        if col_contato:
            def processa_nome(valor):
                texto = str(valor).strip()
                if not texto:
                    return texto
                primeira = texto.split(" ")[0].capitalize()
                return "Candidato" if len(primeira) < 3 else primeira
            base_pronta[col_contato] = base_pronta[col_contato].apply(processa_nome)

        # Mantém e renomeia
        mapping = {col_contato: "Nome", col_whatsapp_kpi: "Numero", col_obs: "Tipo"}
        base_pronta = base_pronta.rename(columns=mapping)
        base_pronta = base_pronta[["Nome", "Numero", "Tipo"]].drop_duplicates(subset=["Numero"], keep="first")

        # Trata números: só dígitos + 55
        base_pronta["Numero"] = base_pronta["Numero"].astype(str).apply(lambda x: "55" + re.sub(r"\D", "", x))
        base_pronta = base_pronta[base_pronta["Numero"].str.len().between(12, 13)]

        # Layout final de campanha
        layout_cols = [
            "TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE","CPFCNPJ","CODCLIENTE",
            "TAG","CORINGA1","CORINGA2","CORINGA3","CORINGA4","CORINGA5","PRIORIDADE"
        ]
        base_campanha = pd.DataFrame(columns=layout_cols)
        base_campanha["VALOR_DO_REGISTRO"] = base_pronta["Numero"].values
        base_campanha["NOME_CLIENTE"] = base_pronta["Nome"].values
        base_campanha["TIPO_DE_REGISTRO"] = "TELEFONE"
        base_campanha = base_campanha[layout_cols]

        # Nome do arquivo final
        if data_ini_str and data_fim_str:
            nome_arquivo = f"Abandono_{data_ini_str}_{data_fim_str}.csv"
        elif data_ini_str:
            nome_arquivo = f"Abandono_{data_ini_str}.csv"
        else:
            nome_arquivo = "Abandono.csv"

        # Resultado
        st.success(f"✅ Base de campanha gerada ({len(base_campanha)} registros).")
        st.dataframe(base_campanha)

        # Download
        out = BytesIO()
        base_campanha.to_csv(out, sep=";", index=False, encoding="utf-8-sig")



