import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# --- CSS: mantido como nas etapas anteriores ---

st.markdown("""
<style>
body, .stApp { background: linear-gradient(90deg, #018a62 0%, #3be291 35%, #fee042 100%) !important; min-height: 100vh; color: #222 !important; font-family: 'Segoe UI', 'Montserrat', 'Arial', sans-serif !important; }
section[data-testid="stSidebar"] { background-color: #004aad !important; color: #fff !important; font-family: 'Segoe UI', 'Montserrat', 'Arial', sans-serif !important; }
.titulo-principal { background: rgba(255,255,255,0.55); color: #06643b; padding: 28px 0 12px 0; border-radius: 16px; text-align: center; font-size: 2.7em; font-weight: 700; margin: 40px auto 18px auto; letter-spacing: 1.2px; box-shadow: 0 2px 14px rgba(0,0,0,0.07); width: 95%; max-width: 750px; font-family: 'Montserrat', 'Segoe UI', Arial, sans-serif; }
.manual-popup, .manual-inicio, .card-importacao { background: #fff; color: #222; border-radius: 22px; box-shadow: 0 4px 28px rgba(0,0,0,0.07); padding: 32px 28px 20px 28px; width: 100%; max-width: 630px; margin: 0 auto 32px auto; border-left: 9px solid #018a62; font-size: 1.08em; font-family: 'Segoe UI', 'Montserrat', Arial, sans-serif; }
.card-importacao h5 { color: #018a62; font-size: 1.35em; font-weight: bold; text-align: center; margin-bottom: 14px; margin-top: 0; font-family: 'Segoe UI', 'Montserrat', Arial, sans-serif; }
.stDownloadButton > button, .stFileUploader > div > button { background-color: #3be291; color: #06643b; font-weight: bold; border-radius: 7px; padding: 10px 36px; border: none; font-size: 1.17em; margin-top: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); transition: background 0.18s; }
.stDownloadButton > button:hover, .stFileUploader > div > button:hover { background-color: #018a62; color: #fff; }
.stDataFrame, .stTable { background: #fff; border-radius: 16px; color: #222; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
@media (max-width: 700px){ .titulo-principal, .manual-popup, .manual-inicio, .card-importacao {max-width:95vw; padding:18px 8vw 14px 8vw;} }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📋 Selecione o tipo de campanha")
opcao = st.sidebar.radio("", ["👋 Abandono", "🛒👋 Carrinho Abandonado"])

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
        df = df[df[col_carteiras].astype(str).str.strip().isin(["SAC", "Distribuição Manual"])]
    return df

def identificar_base_kpi(df):
    return any("data evento" == str(c).strip().lower() for c in df.columns)

def identificar_base_fidelizados(df):
    return any(str(c).strip().lower() in ["nome cliente", "contato", "nome"] for c in df.columns)

def processar_nome(valor, numero):
    texto_original = str(valor).strip()
    # Só pega até o primeiro espaço (primeira palavra)
    primeiro_nome = texto_original.split(' ')[0]
    # Remove caracteres especiais
    nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
    # Se tamanho entre 0...3 e tem telefone, vira Candidato
    if len(nome_limpo) <= 3 and str(numero).strip():
        return "Candidato"
    if not nome_limpo:
        return "Candidato"
    return nome_limpo.title()

def limpar_numero_final(num):
    num_limpo = re.sub(r"\D", "", str(num))
    num_limpo = num_limpo.lstrip("0")
    return "55" + num_limpo

if opcao == "🏚️ Abandono":
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>PARA GERAR A BASE DE CAMPANHA É NECESSÁRIO:</strong><br>
            1️⃣ Gerar o relatório de <b>KPI de Eventos</b> para o período.<br>
            2️⃣ Gerar o relatório de <b>Contatos Fidelizados</b>.<br>
            3️⃣ Importe os arquivos abaixo.<br>
            4️⃣ O sistema irá processar e gerar a base final automaticamente.<br>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class='card-importacao'>
            <h5>Importe as bases aqui</h5>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        file_kpi = st.file_uploader("📥 Base KPI", type=["xlsx", "csv"], key="KPI")
    with col2:
        file_fid = st.file_uploader("📥 Base Fidelizados", type=["xlsx", "csv"], key="FID")
    st.markdown("</div>", unsafe_allow_html=True)
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
                    try:
                        df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
                        datas_validas = df_kpi[col_data_evento].dropna().dt.date
                        if not datas_validas.empty:
                            di, dfinal = min(datas_validas), max(datas_validas)
                            if di == dfinal:
                                nome_arquivo = f"Abandono_{di.strftime('%d.%m')}.csv"
                            else:
                                nome_arquivo = f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"
                    except Exception as e:
                        st.warning(f"⚠️ Não foi possível processar datas: {e}")
                df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]
                col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
                base_pronta = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]
                col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
                if col_carteiras:
                    base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(["SAC - Pós Venda", "Secretaria"])]
                col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
                if col_contato:
                    base_pronta[col_contato] = [
                        processar_nome(nome, numero)
                        for nome, numero in zip(base_pronta[col_contato], base_pronta[col_wpp_kpi])
                    ]
                mapping = {col_contato: "Nome", col_wpp_kpi: "Numero", col_obs: "Tipo"}
                base_pronta = base_pronta.rename(columns=mapping)[["Nome", "Numero", "Tipo"]]
                base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")
                layout = ["TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE",
                          "CPFCNPJ", "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3",
                          "CORINGA4", "CORINGA5", "PRIORIDADE"]
                base_importacao = pd.DataFrame(columns=layout)
                base_importacao["VALOR_DO_REGISTRO"] = base_pronta["Numero"].apply(limpar_numero_final)
                base_importacao["NOME_CLIENTE"] = base_pronta["Nome"]
                base_importacao["TIPO_DE_REGISTRO"] = "TELEFONE"
                base_importacao = base_importacao[layout]
                st.success(f"✅ Base de campanha pronta! {len(base_importacao)} registros.")
                output = BytesIO()
                base_importacao.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
                output.seek(0)
                st.download_button("⬇️ Baixar campanha (.csv)", output, file_name=nome_arquivo, mime="text/csv")
                st.markdown(f"""
                    <div class='manual-popup'>
                        <h4>📤 Próximos passos – Importar na Robbu</h4>
                        <p><strong>Baixe o arquivo gerado acima (<em>{nome_arquivo}</em>) e siga:</strong></p>
                        <ol>
                            <li>No Robbu, vá em <strong>Público</strong> e clique <strong>Importar Público</strong></li>
                            <li>Na descrição, informe <strong>Abandono</strong> e a data</li>
                            <li>Escolha o segmento <strong>Distribuição Manual</strong></li>
                            <li>Importe o arquivo gerado</li>
                            <li>Marque autorização de processamento/comunicação</li>
                            <li>Tipo de autorização: <strong>Consentimento</strong></li>
                            <li>Marque <strong>Manter apenas neste segmento</strong></li>
                            <li>Clique <strong>Importar</strong> e aguarde a confirmação</li>
                        </ol>
                    </div>
                """, unsafe_allow_html=True)
    st.markdown("<h4 style='color:#077339; margin-top:28px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
    if 'base_importacao' in locals():
        st.dataframe(base_importacao)
elif opcao == "🛒👋 Carrinho Abandonado":
    st.markdown("<div class='titulo-principal'>Carrinho Abandonado</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-popup' style='text-align:center;'>
            🚧 Em construção... Em breve será possível gerar a base de Carrinho Abandonado.
        </div>
    """, unsafe_allow_html=True)


