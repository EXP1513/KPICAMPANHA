import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# ---------- CSS e HTML: gradiente igual ao layout do anexo ----------
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(90deg, #068569 0%, #38e195 30%, #ffe255 100%) !important;
    color: #fff !important;
    min-height: 100vh;
}
section[data-testid="stSidebar"] {
    background-color: #004aad !important;
    color: #fff !important;
}
.titulo-principal {
    background: linear-gradient(90deg, #068569 0%, #ffe055 100%);
    color: #fff;
    padding: 28px 0 20px 0;
    border-radius: 12px;
    text-align: center;
    font-size: 2.4em;
    font-weight: bold;
    margin-bottom: 20px;
    letter-spacing: 1px;
    box-shadow: 0 2px 14px rgba(0,0,0,0.04);
}
.manual-popup, .manual-inicio {
    background: #fff;
    color: #222;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    padding: 22px;
    width: 100%;
    max-width: 540px;
    margin: 0 auto 30px auto;
    border-left: 7px solid #068569;
    font-size: 1.10em;
}
.stDownloadButton > button, .stFileUploader > div > button {
    background-color: #38e195;
    color: #222;
    font-weight: bold;
    border-radius: 5px;
    padding: 10px 30px;
    border: none;
    font-size: 1.15em;
    margin-top: 10px;
}
.stDownloadButton > button:hover, .stFileUploader > div > button:hover {
    background-color: #068569;
    color: #fff;
}
.stDataFrame, .stTable {
    background: #fff;
    border-radius: 8px;
    color: #111;
}
</style>
""", unsafe_allow_html=True)

# ---------- MENU LATERAL COM EMOJIS ----------
st.sidebar.title("📋 Selecione o tipo de campanha")
opcao = st.sidebar.radio(
    "",
    ["👋🏚️ Abandono", "🛒 Carrinho Abandonado"]
)

# ---------- Funções padrão ----------
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
    nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', '', texto_original)
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo).strip()
    if not nome_limpo:
        return "Candidato"
    return nome_limpo.title()

# ---------- Conteúdo principal ----------
if opcao == "👋🏚️ Abandono":
    st.markdown("<div class='titulo-principal'>👋🚀🇧🇷🚀 Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>PARA GERAR A BASE DE CAMPANHA É NECESSÁRIO:</strong><br>
            1️⃣ Gerar o relatório de <b>KPI de Eventos</b> para o período.<br>
            2️⃣ Gerar o relatório de <b>Contatos Fidelizados</b>.<br>
            3️⃣ Importar o arquivo de <b>KPI</b> abaixo.<br>
            4️⃣ Importar o arquivo de <b>Fidelizados</b> abaixo.<br>
            5️⃣ O sistema irá processar e gerar a base final automaticamente.<br>
        </div>
    """, unsafe_allow_html=True)

    file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx", "csv"])
    file_fid = st.file_uploader("📂 Importar base Fidelizados", type=["xlsx", "csv"])

    if file_kpi and file_fid:
        df_kpi = read_file(file_kpi)
        df_fid = read_file(file_fid)
        kpi_valido = identificar_base_kpi(df_kpi)
        fid_valido = identificar_base_fidelizados(df_fid)
        kpi_invertido = identificar_base_kpi(df_fid)
        fid_invertido = identificar_base_fidelizados(df_kpi)

        if (not kpi_valido and not fid_valido) and (not kpi_invertido and not fid_invertido):
            st.error("❌ Bases incorretas. Verifique os arquivos importados.")
        elif kpi_invertido and fid_invertido:
            st.error("⚠️ As bases estão invertidas. Recarregue corretamente.")
        elif not kpi_valido or not fid_valido:
            st.error("❌ Um dos arquivos não corresponde ao tipo esperado (KPI ou Fidelizados).")
        else:
            col_wpp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
            col_wpp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)
            if not col_wpp_kpi or not col_wpp_fid:
                st.error("❌ Coluna 'WhatsApp Principal' não encontrada.")
            else:
                df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip()
                df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].apply(lambda x: re.sub(r'^0+', '', x))

                nome_arquivo = "Abandono.csv"
                col_data_evento = next((c for c in df_kpi.columns if str(c).strip().lower() == "data evento"), None)
                if col_data_evento:
                    df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
                    datas_validas = df_kpi[col_data_evento].dropna().dt.date
                    if not datas_validas.empty:
                        di, dfinal = min(datas_validas), max(datas_validas)
                        nome_arquivo = f"Abandono_{di.strftime('%d.%m')}" + (f"_a_{dfinal.strftime('%d.%m')}.csv" if di != dfinal else ".csv")

                df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]
                col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
                filtro = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]
                base_pronta = filtro.copy()

                col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
                if col_carteiras:
                    base_pronta = base_pronta[~base_pronta[col_carteiras].isin(["SAC - Pós Venda", "Secretaria"])]

                col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
                if col_contato:
                    base_pronta[col_contato] = base_pronta[col_contato].apply(processar_nome)

                mapping = {col_contato: "Nome", col_wpp_kpi: "Numero", col_obs: "Tipo"}
                base_pronta = base_pronta.rename(columns=mapping)[["Nome", "Numero", "Tipo"]]
                base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")

                layout = ["TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE",
                          "CPFCNPJ","CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3",
                          "CORINGA4","CORINGA5","PRIORIDADE"]
                base_importacao = pd.DataFrame(columns=layout)
                base_importacao["VALOR_DO_REGISTRO"] = base_pronta["Numero"]
                base_importacao["NOME_CLIENTE"] = base_pronta["Nome"]
                base_importacao["TIPO_DE_REGISTRO"] = "TELEFONE"
                base_importacao = base_importacao[layout]

                base_importacao["VALOR_DO_REGISTRO"] = base_importacao["VALOR_DO_REGISTRO"].apply(lambda n: "55" + re.sub(r"\D", "", str(n)).lstrip("0"))

                st.success(f"✅ Base de campanha pronta! {len(base_importacao)} registros.")
                output = BytesIO()
                base_importacao.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
                output.seek(0)
                st.download_button("⬇️ Baixar campanha (.csv)", output, file_name=nome_arquivo, mime="text/csv")

                st.markdown(
                    f"""
                    <div class='manual-popup'>
                        <h4>📤 Próximos passos – Importar na Robbu</h4>
                        <p><strong>Agora:</strong> baixe o arquivo gerado acima (<em>{nome_arquivo}</em>).</p>
                        <ol>
                            <li>No Robbu, vá em <strong>"Público"</strong> e clique <strong>"Importar Público"</strong>.</li>
                            <li>Na descrição, escreva <b>"Abandono"</b> com a data do arquivo.</li>
                            <li>Escolha o segmento <strong>"Distribuição Manual"</strong>.</li>
                            <li>Importe o arquivo gerado.</li>
                            <li>Marque: <strong>"Autorização para processamento e comunicação"</strong>.</li>
                            <li>Selecione tipo de autorização <strong>"Consentimento"</strong>.</li>
                            <li>Marque <strong>"Manter apenas neste segmento"</strong>.</li>
                            <li>Clique <strong>Importar</strong> e aguarde a confirmação.</li>
                        </ol>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Preview
    st.markdown("<h4 style='color:#fff; margin-top:20px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
    if 'base_importacao' in locals():
        st.dataframe(base_importacao)

elif opcao == "🛒 Carrinho Abandonado":
    st.markdown("<div class='titulo-principal'>🛒 Carrinho Abandonado</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='manual-popup' style='text-align:center;'>
            🚧 Em construção... Em breve será possível gerar a base de Carrinho Abandonado.
        </div>
        """,
        unsafe_allow_html=True
    )
