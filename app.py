import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# -------------------- CSS Visual --------------------
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(90deg,#018a62 0%,#3be291 35%,#fee042 100%)!important;
    min-height: 100vh;
    color: #222!important;
    font-family: 'Segoe UI','Montserrat','Arial',sans-serif!important;
}
section[data-testid="stSidebar"] {background-color:#004aad!important;color:#fff!important;}
.titulo-principal {background: rgba(255,255,255,0.55);color:#06643b;padding:28px 0 12px 0;border-radius:16px;text-align:center;font-size:2.7em;font-weight:700;margin:40px auto 18px auto;}
.manual-popup,.manual-inicio,.card-importacao,.card-tabela,.card-summary {
    background:#fff;color:#222;border-radius:22px;box-shadow:0 4px 28px rgba(0,0,0,0.07);
    padding:28px 24px 18px 24px;width:100%;max-width:630px;
    margin:0 auto 28px auto;border-left:9px solid #018a62;font-size:1.07em;
}
.card-importacao h5,.card-tabela h5,.card-summary h5 {color:#018a62;font-size:1.18em;font-weight:bold;text-align:center;margin-bottom:14px;margin-top:0;}
.stDownloadButton > button,.stFileUploader > div > button {background-color:#3be291;color:#06643b;font-weight:bold;border-radius:7px;padding:10px 36px;border:none;font-size:1.09em;margin-top:12px;}
.stDownloadButton > button:hover,.stFileUploader > div > button:hover {background-color:#018a62;color:#fff;}
button[title="Browse files"] > div > p {visibility:hidden;}
button[title="Browse files"]::after {content:"Selecionar Arquivos";color:#06643b;font-size:1.1em;font-weight:bold;}
[data-testid="stFileUploadDropzoneInstructions"] {visibility:hidden;position:relative;}
[data-testid="stFileUploadDropzoneInstructions"]::after {content:"Arraste e solte o arquivo aqui\\nLimite de 200 MB por arquivo • XLSX, CSV";position:absolute;left:16px;top:6px;color:#06643b;font-size:1.05em;font-weight:bold;white-space:pre-line;}
</style>
""", unsafe_allow_html=True)

# -------------------- Menu Lateral --------------------
st.sidebar.title("📋 Selecione o tipo de campanha")
opcao = st.sidebar.radio("", ["❌👋 Abandono", "🛒👋 Carrinho Abandonado"])

# -------------------- Funções Auxiliares --------------------
def tratar_nome(nome, numero):
    primeiro_nome = str(nome).strip().split(' ')[0]
    nome_limpos = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
    if len(nome_limpos) <= 3 and str(numero).strip():
        return "Candidato"
    if not nome_limpos:
        return "Candidato"
    return nome_limpos.title()

def tratar_numero(numero):
    num = re.sub(r"\\D", "", str(numero))
    return "55" + num.lstrip("0") if num else ""

def tratar_email(email):
    return str(email).strip().lower()

def exportar_layout_robbu(df, col_nome="nome", col_numero="Numero"):
    layout_colunas = [
        "TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE",
        "CPFCNPJ","CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3",
        "CORINGA4","CORINGA5","PRIORIDADE"
    ]
    export_df = pd.DataFrame(columns=layout_colunas)
    export_df["VALOR_DO_REGISTRO"] = df[col_numero]
    export_df["NOME_CLIENTE"] = df[col_nome]
    export_df["TIPO_DE_REGISTRO"] = "TELEFONE"
    return export_df[layout_colunas]

def localizar_coluna(df, nomes_possiveis):
    return next((c for c in df.columns if str(c).strip().lower() in [n.lower() for n in nomes_possiveis]), None)

def gerar_nome_abandono(df_kpi, col_data_evento):
    try:
        df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
        datas_validas = df_kpi[col_data_evento].dropna().dt.date
        if datas_validas.empty:
            return "Abandono.csv"
        di, dfinal = min(datas_validas), max(datas_validas)
        if di == dfinal:
            return f"Abandono_{di.strftime('%d.%m')}.csv"
        else:
            return f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"
    except:
        return "Abandono.csv"

def gerar_nome_carinho():
    hoje = datetime.now()
    if hoje.weekday() == 0: # segunda
        sab = hoje - timedelta(days=2)
        dom = hoje - timedelta(days=1)
        return f"Carinho_Abandonado_{sab.strftime('%d.%m')}_{dom.strftime('%d.%m')}.csv"
    else:
        ont = hoje - timedelta(days=1)
        return f"Carinho_Abandonado_{ont.strftime('%d.%m')}.csv"

# -------------------- ABA ABANDONO --------------------
if opcao == "❌👋 Abandono":
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)
    file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx","csv"])
    file_fid = st.file_uploader("📂 Importar base Fidelizados", type=["xlsx","csv"])
    if file_kpi and file_fid:
        try:
            df_kpi = pd.read_excel(file_kpi) if file_kpi.name.lower().endswith(".xlsx") else pd.read_csv(file_kpi, sep=None, engine="python", encoding="utf-8")
            df_fid = pd.read_excel(file_fid) if file_fid.name.lower().endswith(".xlsx") else pd.read_csv(file_fid, sep=None, engine="python", encoding="utf-8")
            col_wpp_kpi = localizar_coluna(df_kpi, ['whatsapp principal'])
            col_wpp_fid = localizar_coluna(df_fid, ['whatsapp principal'])
            col_obs = localizar_coluna(df_kpi, ['observação'])
            col_carteiras = localizar_coluna(df_kpi, ['carteiras'])
            col_contato = localizar_coluna(df_kpi, ['contato','nome cliente'])
            col_data_evento = localizar_coluna(df_kpi, ['data evento'])
            # validação
            if not all([col_wpp_kpi,col_wpp_fid,col_obs,col_contato]):
                st.error("❌ Colunas obrigatórias não encontradas.")
                st.stop()
            df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip().apply(lambda x: re.sub(r'^0+','',x))
            df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]
            df_kpi = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]
            if col_carteiras:
                df_kpi = df_kpi[~df_kpi[col_carteiras].isin(["SAC - Pós Venda","Secretaria"])]
            df_kpi[col_contato] = [tratar_nome(n, t) for n,t in zip(df_kpi[col_contato], df_kpi[col_wpp_kpi])]
            base_final = df_kpi.rename(columns={col_contato:"nome", col_wpp_kpi:"Numero"})[["nome","Numero"]].drop_duplicates(subset=["Numero"])
            export_df = exportar_layout_robbu(base_final,"nome","Numero")
            nome_arquivo = gerar_nome_abandono(df_kpi,col_data_evento)
            st.success(f"✅ Base gerada com {len(export_df)} registros.")
            output = BytesIO()
            export_df.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
            output.seek(0)
            st.download_button("⬇️ Baixar base Abandono", output, file_name=nome_arquivo, mime="text/csv")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

# -------------------- ABA CARINHO ABANDONADO --------------------
elif opcao == "🛒👋 Carrinho Abandonado":
    st.markdown("<div class='titulo-principal'>Carinho Abandonado</div>", unsafe_allow_html=True)
    file_carinho = st.file_uploader("📥 Carrinho Abandonado", type=["csv"], key="carinho")
    file_naopago = st.file_uploader("📥 Não Pagos", type=["xlsx","csv"], key="naopago")
    file_pedidos = st.file_uploader("📥 Pedidos", type=["xlsx","csv"], key="pedidos")
    if file_carinho and file_naopago and file_pedidos:
        try:
            # Carrinho
            df1 = pd.read_csv(file_carinho, sep=',', encoding='utf-8')
            col_map1 = {"First-Name": "nome", "Email": "E-mail", "Phone": "Numero"}
            df1 = df1[[c for c in col_map1 if c in df1.columns]].rename(columns=col_map1)
            df1['nome'] = [tratar_nome(n,num) for n,num in zip(df1['nome'], df1['Numero'])]
            df1['Numero'] = df1['Numero'].apply(tratar_numero)
            df1['E-mail'] = df1['E-mail'].apply(tratar_email)
            # Não pagos
            if file_naopago.name.lower().endswith(".csv"):
                df2 = pd.read_csv(file_naopago, encoding="utf-8")
            else:
                df2 = pd.read_excel(file_naopago)
            col_map2 = {"Nome completo (cobrança)": "nome", "E-mail (cobrança)": "E-mail", "Telefone (cobrança)": "Numero"}
            df2 = df2[[c for c in col_map2 if c in df2.columns]].rename(columns=col_map2)
            df2['nome'] = [tratar_nome(n,num) for n,num in zip(df2['nome'], df2['Numero'])]
            df2['Numero'] = df2['Numero'].apply(tratar_numero)
            df2['E-mail'] = df2['E-mail'].apply(tratar_email)
            qtd_carinho = len(df1)
            qtd_naopag = len(df2)
            # Unifica
            base_total = pd.concat([df1, df2], ignore_index=True)
            # Pedidos
            if file_pedidos.name.lower().endswith(".csv"):
                df_ped = pd.read_csv(file_pedidos, encoding="utf-8")
            else:
                df_ped = pd.read_excel(file_pedidos)
            possiveis = [c for c in df_ped.columns if 'email' in c.lower()]
            emails_pedidos = set(df_ped[possiveis[0]].astype(str).str.strip().str.lower()) if possiveis else set()
            base_filtrada = base_total[~base_total['E-mail'].isin(emails_pedidos)].copy()
            base_filtrada = base_filtrada.drop_duplicates(subset=['Numero'], keep="first").reset_index(drop=True)
            qtd_final = len(base_filtrada)
            # Export
            export_df = exportar_layout_robbu(base_filtrada, "nome", "Numero")
            nome_arquivo = gerar_nome_carinho()
            st.success(f"✅ Base gerada com {qtd_final} registros. (Carrinho: {qtd_carinho} | Não pagos: {qtd_naopag})")
            output = BytesIO()
            export_df.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
            output.seek(0)
            st.download_button("⬇️ Baixar base Carinho Abandonado", output, file_name=nome_arquivo, mime="text/csv")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
