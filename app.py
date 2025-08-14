import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# --- CSS e Layout ---
st.markdown("""
<style>
body, .stApp {background: linear-gradient(90deg, #018a62 0%, #3be291 35%, #fee042 100%) !important; min-height: 100vh; color: #222 !important; font-family: 'Segoe UI', 'Montserrat', 'Arial', sans-serif !important;}
section[data-testid="stSidebar"] {background-color: #004aad !important; color: #fff !important;}
.titulo-principal {background: rgba(255,255,255,0.55); color: #06643b; padding: 28px 0 12px 0; border-radius: 16px; text-align: center; font-size: 2.7em; font-weight: 700; margin: 40px auto 18px auto;}
.manual-popup, .manual-inicio, .card-importacao, .card-tabela, .card-summary {
    background: #fff; color: #222; border-radius: 22px; box-shadow: 0 4px 28px rgba(0,0,0,0.07);
    padding: 28px 24px 18px 24px; width: 100%; max-width: 630px; margin: 0 auto 28px auto; border-left: 9px solid #018a62; font-size: 1.07em;
}
.card-importacao h5, .card-tabela h5, .card-summary h5 {
    color: #018a62; font-size: 1.18em; font-weight: bold; text-align: center; margin-bottom: 14px; margin-top: 0; letter-spacing: 0.5px;
}
.stDownloadButton > button, .stFileUploader > div > button {background-color: #3be291; color: #06643b; font-weight: bold; border-radius: 7px; padding: 10px 36px; border: none; font-size: 1.09em; margin-top: 12px;}
.stDownloadButton > button:hover, .stFileUploader > div > button:hover {background-color: #018a62;color: #fff;}
.stDataFrame, .stTable {background: #fff; border-radius: 16px; color: #222; box-shadow: 0 2px 12px rgba(0,0,0,0.05);}
button[title="Browse files"] > div > p { visibility: hidden; }
button[title="Browse files"]::after {content: "Selecionar Arquivos"; color: #06643b; font-size: 1.1em; font-weight: bold;}
[data-testid="stFileUploadDropzoneInstructions"] {visibility: hidden; position: relative;}
[data-testid="stFileUploadDropzoneInstructions"]::after {content: "Arraste e solte o arquivo aqui\nLimite de 200 MB por arquivo • XLSX, CSV"; position: absolute; left: 16px; top: 6px; color: #06643b; font-size: 1.05em; font-weight: bold; white-space: pre-line;}
.summary-num {font-size: 1.34em; color: #018a62; font-weight: bold;}
.summary-label {font-size: 1.10em; color: #06643b; margin-bottom: 6px;}
@media (max-width: 700px){ .titulo-principal, .manual-popup, .manual-inicio, .card-importacao, .card-tabela, .card-summary {max-width:95vw; padding:18px 8vw 14px 8vw;} }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📋 Selecione o tipo de campanha")
opcao = st.sidebar.radio(
    "",
    ["❌👋 Abandono", "🛒👋 Carrinho Abandonado"]
)

def tratar_nome(nome, numero):
    primeiro_nome = str(nome).strip().split(' ')[0]
    nome_letras = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
    if len(nome_letras) <= 3 and str(numero).strip():
        return "Candidato"
    if not nome_letras:
        return "Candidato"
    return nome_letras.title()

def tratar_numero(numero):
    num = re.sub(r"\D", "", str(numero))
    return "55" + num.lstrip("0") if num else ""

def tratar_email(email):
    return str(email).strip().lower()

if opcao == "🛒👋 Carrinho Abandonado":
    st.markdown("<div class='titulo-principal'>Carinho Abandonado</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>Como funciona?</strong><br>
            1️⃣ Importe as três bases abaixo:<br>
            <b>- Carrinho Abandonado</b>: CSV, separada por vírgula<br>
            <b>- Não Pagos</b>: XLSX/CSV<br>
            <b>- Pedidos</b>: XLSX/CSV<br>
            <br>
            O sistema irá:<br>
            • Padronizar nomes e números;<br>
            • Unificar bases;<br>
            • Remover registros cujo e-mail existe na base de Pedidos;<br>
            • Remover duplicatas pelo número de telefone;<br>
            • Gerar relatório para exportação.
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class='card-importacao'>
            <h5>Importe as três bases aqui</h5>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        file_carinho = st.file_uploader("📥 Carrinho Abandonado", type=["csv"], key="carinho")
    with col2:
        file_naopago = st.file_uploader("📥 Não Pagos", type=["xlsx", "csv"], key="naopago")
    with col3:
        file_pedidos = st.file_uploader("📥 Pedidos", type=["xlsx", "csv"], key="pedidos")
    st.markdown("</div>", unsafe_allow_html=True)

    if file_carinho and file_naopago and file_pedidos:
        try:
            # -- Carinho Abandonado --
            df_carinho = pd.read_csv(file_carinho, sep=',', encoding='utf-8')
            col_map1 = {"First-Name": "nome", "Email": "E-mail", "Phone": "Numero"}
            cols1 = [c for c in col_map1 if c in df_carinho.columns]
            df1 = df_carinho[cols1].rename(columns=col_map1)
            df1['nome'] = [tratar_nome(n, num) for n, num in zip(df1['nome'], df1['Numero'])]
            df1['Numero'] = df1['Numero'].apply(tratar_numero)
            df1['E-mail'] = df1['E-mail'].apply(tratar_email)

            # -- Não Pagos --
            if file_naopago.name.lower().endswith(".csv"):
                df_naopago = pd.read_csv(file_naopago, encoding="utf-8")
            else:
                df_naopago = pd.read_excel(file_naopago)
            col_map2 = {
                "Nome completo (cobrança)": "nome",
                "E-mail (cobrança)": "E-mail",
                "Telefone (cobrança)": "Numero"
            }
            cols2 = [c for c in col_map2 if c in df_naopago.columns]
            df2 = df_naopago[cols2].rename(columns=col_map2)
            df2['nome'] = [tratar_nome(n, num) for n, num in zip(df2['nome'], df2['Numero'])]
            df2['Numero'] = df2['Numero'].apply(tratar_numero)
            df2['E-mail'] = df2['E-mail'].apply(tratar_email)

            # -- Pedidos --
            if file_pedidos.name.lower().endswith(".csv"):
                df_ped = pd.read_csv(file_pedidos, encoding="utf-8")
            else:
                df_ped = pd.read_excel(file_pedidos)
            possiveis = [c for c in df_ped.columns if 'email' in c.lower()]
            emails_pedidos = set(df_ped[possiveis[0]].astype(str).str.strip().str.lower()) if possiveis else set()

            # Unifica
            qtd_carinho = len(df1)
            qtd_naopag = len(df2)
            base_total = pd.concat([df1, df2], ignore_index=True)

            # Remove pelo email da base Pedidos
            base_total = base_total[~base_total['E-mail'].isin(emails_pedidos)]
            qtd_final = len(base_total)

            # Remove duplicatas de Numero
            base_total = base_total.drop_duplicates(subset=['Numero'], keep="first").reset_index(drop=True)
            qtd_finaldedup = len(base_total)

            # --- CARD DE RESUMO
            st.markdown(f"""
              <div class='card-summary'>
                <h5>Resumo da Base Gerada - Carinho Abandonado</h5>
                <div class='summary-label'>Registros da base Carrinho Abandonado:</div>
                <div class='summary-num'>{qtd_carinho}</div>
                <div class='summary-label' style="margin-top:12px;">Registros da base Não Pagos:</div>
                <div class='summary-num'>{qtd_naopag}</div>
                <div class='summary-label' style="margin-top:12px;">Quantidade total após filtros e remoção de duplicatas:</div>
                <div class='summary-num'>{qtd_finaldedup}</div>
              </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class='card-tabela'>
                    <h5>Pré-visualização da base final</h5>
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(base_total[['nome', 'E-mail', 'Numero']])

            # Download
            output = BytesIO()
            base_total.to_csv(output, index=False, encoding="utf-8-sig", sep=";")
            output.seek(0)
            st.download_button("⬇️ Baixar base Carinho Abandonado (.csv)", output, file_name="Carinho_Abandonado.csv", mime="text/csv")
        except Exception as e:
            st.error("❌ Erro ao processar as bases. Confira os formatos e campos obrigatórios.")

elif opcao == "❌👋 Abandono":
    # ... (módulo Abandono mantido como antes, visual e funções já implementadas).
    pass
