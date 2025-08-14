import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# --- CSS visual, tradução, layout ---
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(90deg, #018a62 0%, #3be291 35%, #fee042 100%) !important;
    min-height: 100vh;
    color: #222 !important;
    font-family: 'Segoe UI', 'Montserrat', 'Arial', sans-serif !important;
}
section[data-testid="stSidebar"] {
    background-color: #004aad !important;
    color: #fff !important;
}
.titulo-principal {
    background: rgba(255,255,255,0.55);
    color: #06643b;
    padding: 28px 0 12px 0;
    border-radius: 16px;
    text-align: center;
    font-size: 2.7em;
    font-weight: 700;
    margin: 40px auto 18px auto;
}
.manual-popup, .manual-inicio, .card-importacao, .card-tabela, .card-summary {
    background: #fff;
    color: #222;
    border-radius: 22px;
    box-shadow: 0 4px 28px rgba(0,0,0,0.07);
    padding: 28px 24px 18px 24px;
    width: 100%;
    max-width: 630px;
    margin: 0 auto 28px auto;
    border-left: 9px solid #018a62;
    font-size: 1.07em;
}
.card-importacao h5, .card-tabela h5, .card-summary h5 {
    color: #018a62;
    font-size: 1.18em;
    font-weight: bold;
    text-align: center;
    margin-bottom: 14px;
    margin-top: 0;
    letter-spacing: 0.5px;
}
.stDownloadButton > button, .stFileUploader > div > button {
    background-color: #3be291;
    color: #06643b;
    font-weight: bold;
    border-radius: 7px;
    padding: 10px 36px;
    border: none;
    font-size: 1.09em;
    margin-top: 12px;
}
.stDownloadButton > button:hover, .stFileUploader > div > button:hover {
    background-color: #018a62;
    color: #fff;
}
.stDataFrame, .stTable {
    background: #fff;
    border-radius: 16px;
    color: #222;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
button[title="Browse files"] > div > p {
    visibility: hidden;
}
button[title="Browse files"]::after {
    content: "Selecionar Arquivos";
    color: #06643b;
    font-size: 1.1em;
    font-weight: bold;
}
[data-testid="stFileUploadDropzoneInstructions"] {
    visibility: hidden;
    position: relative;
}
[data-testid="stFileUploadDropzoneInstructions"]::after {
    content: "Arraste e solte o arquivo aqui\nLimite de 200 MB por arquivo • XLSX, CSV";
    position: absolute;
    left: 16px;
    top: 6px;
    color: #06643b;
    font-size: 1.05em;
    font-weight: bold;
    white-space: pre-line;
}
.summary-num {
    font-size: 1.34em;
    color: #018a62;
    font-weight: bold;
}
.summary-label {
    font-size: 1.10em;
    color: #06643b;
    margin-bottom: 6px;
}
@media (max-width: 700px) {
    .titulo-principal, .manual-popup, .manual-inicio, .card-importacao,
    .card-tabela, .card-summary {
        max-width: 95vw;
        padding: 18px 8vw 14px 8vw;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Menu lateral ---
st.sidebar.title("📋 Selecione o tipo de campanha")
opcao = st.sidebar.radio(
    "",
    ["❌👋 Abandono", "🛒👋 Carrinho Abandonado"]
)

# --- Funções auxiliares ---
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

def localizar_coluna(df, nomes_possiveis):
    # Busca coluna por lista de nomes possíveis (case insensitive)
    cols = [c for c in df.columns if str(c).strip().lower() in [n.lower() for n in nomes_possiveis]]
    return cols[0] if cols else None

def gerar_nome_arquivo_abandono(df_kpi, col_data_evento):
    try:
        df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
        datas_validas = df_kpi[col_data_evento].dropna().dt.date
        if len(datas_validas) == 0:
            return "Abandono.csv"
        di, dfinal = min(datas_validas), max(datas_validas)
        if di == dfinal:
            return f"Abandono_{di.strftime('%d.%m')}.csv"
        else:
            return f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"
    except Exception:
        return "Abandono.csv"

def gerar_nome_arquivo_carinho():
    hoje = datetime.now()
    if hoje.weekday() == 0:  # segunda-feira
        sab = hoje - timedelta(days=2)
        dom = hoje - timedelta(days=1)
        return f"Carinho_Abandonado_{sab.strftime('%d.%m')}_{dom.strftime('%d.%m')}.csv"
    else:  # terça a sexta
        ont = hoje - timedelta(days=1)
        return f"Carinho_Abandonado_{ont.strftime('%d.%m')}.csv"

def exportar_layout_robbu(df, nome_coluna_nome="nome", nome_coluna_numero="Numero"):
    layout_colunas = [
        "TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE",
        "CPFCNPJ", "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3",
        "CORINGA4", "CORINGA5", "PRIORIDADE"
    ]
    export_df = pd.DataFrame(columns=layout_colunas)
    export_df["VALOR_DO_REGISTRO"] = df[nome_coluna_numero]
    export_df["NOME_CLIENTE"] = df[nome_coluna_nome]
    export_df["TIPO_DE_REGISTRO"] = "TELEFONE"
    return export_df[layout_colunas]

# --- Aba Carrinho Abandonado ---
if opcao == "🛒👋 Carrinho Abandonado":
    st.markdown("<div class='titulo-principal'>Carinho Abandonado</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>Como funciona?</strong><br>
            1️⃣ Importe as três bases abaixo:<br>
            • Carrinho Abandonado (CSV, campos First-Name, Email, Phone)<br>
            • Não Pagos (XLSX/CSV, campos 'Nome completo (cobrança)', 'E-mail (cobrança)', 'Telefone (cobrança)')<br>
            • Pedidos (XLSX/CSV, campo E-mail)<br>
            O sistema irá: padronizar nomes/números, unificar bases, remover registros cujo e-mail existe na base Pedidos, retirar duplicatas e exportar.
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='card-importacao'><h5>Importe as três bases aqui</h5></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        file_carinho = st.file_uploader("📥 Carrinho Abandonado", type=["csv"], key="carinho")
    with col2:
        file_naopago = st.file_uploader("📥 Não Pagos", type=["xlsx", "csv"], key="naopago")
    with col3:
        file_pedidos = st.file_uploader("📥 Pedidos", type=["xlsx", "csv"], key="pedidos")

    if file_carinho and file_naopago and file_pedidos:
        try:
            # Carinho
            df_carinho = pd.read_csv(file_carinho, sep=',', encoding='utf-8')
            col_map1 = {"First-Name": "nome", "Email": "E-mail", "Phone": "Numero"}
            cols1 = [c for c in col_map1 if c in df_carinho.columns]
            df1 = df_carinho[cols1].rename(columns=col_map1)
            df1['nome'] = [tratar_nome(n, num) for n, num in zip(df1['nome'], df1['Numero'])]
            df1['Numero'] = df1['Numero'].apply(tratar_numero)
            df1['E-mail'] = df1['E-mail'].apply(tratar_email)

            # Não Pagos
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

            qtd_carinho = len(df1)
            qtd_naopag = len(df2)

            # Unificação
            base_total = pd.concat([df1, df2], ignore_index=True)

            # Pedidos
            if file_pedidos.name.lower().endswith(".csv"):
                df_ped = pd.read_csv(file_pedidos, encoding="utf-8")
            else:
                df_ped = pd.read_excel(file_pedidos)
            possiveis = [c for c in df_ped.columns if 'email' in c.lower()]
            emails_pedidos = set(df_ped[possiveis[0]].astype(str).str.strip().str.lower()) if possiveis else set()

            # Remove registros cujo e-mail está nos pedidos
            base_filtrada = base_total[~base_total['E-mail'].isin(emails_pedidos)].copy()

            # Remove duplicatas de telefone
            base_filtrada = base_filtrada.drop_duplicates(subset=['Numero'], keep="first").reset_index(drop=True)

            qtd_final = len(base_filtrada)

            # Exportação no layout robbu
            export_df = exportar_layout_robbu(base_filtrada, "nome", "Numero")
            nome_arquivo = gerar_nome_arquivo_carinho()

            # Card resumo
            st.markdown(f"""
              <div class='card-summary'>
                <h5>Resumo da Base Gerada – Carinho Abandonado</h5>
                <div class='summary-label'>Registros da base Carrinho Abandonado:</div>
                <div class='summary-num'>{qtd_carinho}</div>
                <div class='summary-label' style="margin-top:12px;">Registros da base Não Pagos:</div>
                <div class='summary-num'>{qtd_naopag}</div>
                <div class='summary-label' style="margin-top:12px;">Quantidade total após filtros e remoção de duplicatas:</div>
                <div class='summary-num'>{qtd_final}</div>
              </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='card-tabela'><h5>Pré-visualização da base final</h5></div>", unsafe_allow_html=True)
            st.dataframe(base_filtrada[["nome", "E-mail", "Numero"]])

            output = BytesIO()
            export_df.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
            output.seek(0)
            st.download_button("⬇️ Baixar base Carinho Abandonado (.csv)", data=output, file_name=nome_arquivo, mime="text/csv")

        except Exception as e:
            st.error(f"❌ Erro ao processar as bases: {e}")

# --- Aba Abandono ---
elif opcao == "❌👋 Abandono":
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='manual-inicio'>
            <strong>PARA GERAR A BASE DE CAMPANHA É NECESSÁRIO:</strong><br>
            1️⃣ Gerar o relatório de KPI de Eventos para o período;<br>
            2️⃣ Gerar o relatório de Contatos Fidelizados;<br>
            3️⃣ Importe os arquivos abaixo;<br>
            4️⃣ O sistema irá processar e gerar a base final automaticamente.<br>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='card-importacao'><h5>Importe as bases aqui</h5></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        file_kpi = st.file_uploader("📥 Base KPI", type=["xlsx", "csv"], key="KPI")
    with col2:
        file_fid = st.file_uploader("📥 Base Fidelizados", type=["xlsx", "csv"], key="FID")

    if file_kpi and file_fid:
        try:
            # Ler arquivos com flexibilidade e detectar colunas
            if file_kpi.name.lower().endswith("xlsx"):
                df_kpi = pd.read_excel(file_kpi)
            else:
                df_kpi = pd.read_csv(file_kpi, sep=None, engine="python", encoding="utf-8")

            if file_fid.name.lower().endswith("xlsx"):
                df_fid = pd.read_excel(file_fid)
            else:
                df_fid = pd.read_csv(file_fid, sep=None, engine="python", encoding="utf-8")

            # localizar colunas essenciais
            col_wpp_kpi = localizar_coluna(df_kpi, ['whatsapp principal'])
            col_wpp_fid = localizar_coluna(df_fid, ['whatsapp principal'])
            col_obs = localizar_coluna(df_kpi, ['observação'])
            col_carteiras = localizar_coluna(df_kpi, ['carteiras'])
            col_contato = localizar_coluna(df_kpi, ['contato'])
            col_data_evento = localizar_coluna(df_kpi, ['data evento'])

            for nome_col, col in [('WhatsApp Principal (KPI)', col_wpp_kpi), ('WhatsApp Principal (Fidelizados)', col_wpp_fid), 
                                ('Observação', col_obs), ('Carteiras', col_carteiras), ('Contato', col_contato)]:
                if col is None:
                    st.error(f"❌ Coluna obrigatória não encontrada: {nome_col}")
                    st.stop()

            # Limpar telefones e filtrar
            df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip().apply(lambda x: re.sub(r'^0+', '', x))
            df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]
            df_kpi = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]

            if col_carteiras:
                df_kpi = df_kpi[~df_kpi[col_carteiras].astype(str).str.strip().isin(["SAC - Pós Venda", "Secretaria"])]

            if col_contato:
                df_kpi[col_contato] = [tratar_nome(nome, numero) for nome, numero in zip(df_kpi[col_contato], df_kpi[col_wpp_kpi])]

            mapping = {col_contato: "Nome", col_wpp_kpi: "Numero", col_obs: "Tipo"}
            base_pronta = df_kpi.rename(columns=mapping)[["Nome", "Numero", "Tipo"]].drop_duplicates(subset=["Numero"], keep="first")

            export_df = exportar_layout_robbu(base_pronta, "Nome", "Numero")
            nome_arquivo = gerar_nome_arquivo_abandono(df_kpi, col_data_evento)

            st.success(f"✅ Base de campanha pronta! {len(export_df)} registros.")
            output = BytesIO()
            export_df.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
            output.seek(0)
            st.download_button("⬇️ Baixar campanha (.csv)", data=output, file_name=nome_arquivo, mime="text/csv")

            st.markdown("""
                <div class='manual-popup'>
                    <h4>📤 Próximos passos – Importar na Robbu</h4>
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
            st.markdown("<h4 style='color:#077339; margin-top:24px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
            st.dataframe(export_df)
        except Exception as e:
            st.error(f"❌ Erro ao processar bases Abandono: {e}")
