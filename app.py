import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Gera Campanha - Abandono🚀", layout="centered")

# -------------------- CSS Visual --------------------
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

# -------------------- Menu --------------------
st.sidebar.title("📋 Campanha")
st.sidebar.markdown("Apenas fluxo de Abandono")
opcao = "❌👋 Abandono"

# -------------------- Funções --------------------
def read_file(f):
    from io import BytesIO
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

def processar_nome(valor):
    texto_original = str(valor).strip()
    primeiro_nome = texto_original.split(' ')[0]
    nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
    if len(nome_limpo) <= 3:
        return "Candidato"
    return nome_limpo.title()

# -------------------- Aba Abandono --------------------
if opcao == "❌👋 Abandono":
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

    file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx", "csv"])
    file_fid = st.file_uploader("📂 Importar base Fidelizados", type=["xlsx", "csv"])

    if file_kpi and file_fid:
        df_kpi = read_file(file_kpi)
        df_fid = read_file(file_fid)

        col_wpp_kpi = localizar_coluna(df_kpi, "whatsapp principal")
        col_wpp_fid = localizar_coluna(df_fid, "whatsapp principal")
        col_obs = localizar_coluna(df_kpi, "observação")
        col_carteiras = localizar_coluna(df_kpi, "carteiras")
        col_contato = localizar_coluna(df_kpi, "contato")
        col_data_evento = localizar_coluna(df_kpi, "data evento")

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

        # Tratamento de nomes
        df_kpi[col_contato] = [processar_nome(v) for v in df_kpi[col_contato]]

        # Monta base para exportação
        mapping = {col_contato: "Nome", col_wpp_kpi: "Numero", col_obs: "Tipo"}
        base_pronta = df_kpi.rename(columns=mapping)[["Nome", "Numero", "Tipo"]]
        base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")

        # Layout Robbu
        layout = ["TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE",
                  "CPFCNPJ", "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3",
                  "CORINGA4", "CORINGA5", "PRIORIDADE"]
        base_export = pd.DataFrame(columns=layout)
        base_export["VALOR_DO_REGISTRO"] = base_pronta["Numero"].apply(lambda n: "55" + re.sub(r"\D", "", str(n)).lstrip("0"))
        base_export["NOME_CLIENTE"] = base_pronta["Nome"]
        base_export["TIPO_DE_REGISTRO"] = "TELEFONE"
        base_export = base_export[layout]

        # Nome do arquivo
        nome_arquivo = "Abandono.csv"
        if col_data_evento:
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

        st.success(f"✅ Base de campanha pronta! {len(base_export)} registros.")
        output = BytesIO()
        base_export.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar campanha (.csv)", output, file_name=nome_arquivo, mime="text/csv")

        st.markdown("<h4 style='color:#077339; margin-top:20px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
        st.dataframe(base_export)
