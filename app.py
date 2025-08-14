import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Gera Campanha🚀", layout="centered")

# CSS (mantido igual, omitido aqui para brevidade)

def try_read_excel_or_csv(file):
    # Lê arquivo Excel ou CSV com tentativas múltiplas de encoding
    bytes_data = file.read()
    buffer = BytesIO(bytes_data)
    try:
        if file.name.lower().endswith('.xlsx') or file.name.lower().endswith('.xls'):
            return pd.read_excel(buffer)
        else:
            # Tentativa UTF-8
            try:
                return pd.read_csv(buffer, engine='python', encoding='utf-8')
            except Exception:
                buffer.seek(0)  # Voltar ao início
                # Tentativa latin1 (windows-1252)
                return pd.read_csv(buffer, engine='python', encoding='latin1')
    except Exception as e:
        st.error(f"Erro lendo arquivo {file.name}: {e}")
        return None

def localizar_coluna(df, nomes_possiveis):
    for nome in nomes_possiveis:
        for col in df.columns:
            if str(col).strip().lower() == nome.lower():
                return col
    return None

def tratar_nome(nome, numero):
    primeiro = str(nome).strip().split(' ')[0]
    limpo = re.sub(r'[^A-Za-zÀ-ÿ]', '', primeiro)
    if (not limpo) or (len(limpo) <=3 and str(numero).strip()):
        return "Candidato"
    return limpo.title()

def tratar_numero(num):
    nu = re.sub(r'\D','',str(num))
    return '55' + nu.lstrip('0') if nu else ''

def tratar_email(email):
    return str(email).strip().lower()

def export_layout_robbu(df, col_nome='nome', col_num='Numero'):
    cols = ['TIPO_DE_REGISTRO','VALOR_DO_REGISTRO','MENSAGEM','NOME_CLIENTE',
            'CPFCNPJ','CODCLIENTE','TAG','CORINGA1','CORINGA2','CORINGA3',
            'CORINGA4','CORINGA5','PRIORIDADE']
    res = pd.DataFrame(columns=cols)
    res['VALOR_DO_REGISTRO'] = df[col_num]
    res['NOME_CLIENTE'] = df[col_nome]
    res['TIPO_DE_REGISTRO'] = 'TELEFONE'
    return res[cols]

def gerar_nome_abandono(df, col_data_evento):
    try:
        df[col_data_evento] = pd.to_datetime(df[col_data_evento], errors='coerce', dayfirst=True)
        datas = df[col_data_evento].dropna().dt.date.unique()
        if len(datas) == 1:
            return f"Abandono_{datas[0].strftime('%d.%m')}.csv"
        elif len(datas) > 1:
            return f"Abandono_{min(datas).strftime('%d.%m')}_a_{max(datas).strftime('%d.%m')}.csv"
    except:
        pass
    return "Abandono.csv"

def gerar_nome_carinho():
    hoje = datetime.now()
    if hoje.weekday() == 0:
        sab = hoje - timedelta(days=2)
        dom = hoje - timedelta(days=1)
        return f"Carinho_Abandonado_{sab.strftime('%d.%m')}_{dom.strftime('%d.%m')}.csv"
    else:
        ante = hoje - timedelta(days=1)
        return f"Carinho_Abandonado_{ante.strftime('%d.%m')}.csv"


# --- Interface ---
st.sidebar.title("📋 Selecione a campanha")
opcao = st.sidebar.radio("", ["❌🚪 Abandono", "🛒👋 Carrinho Abandonado"])

if opcao == "❌🚪 Abandono":
    st.markdown("<h1 style='text-align:center;color:#066f46;'>Gerador de Campanha - Abandono</h1>", unsafe_allow_html=True)
    st.markdown("### Instruções:\n1) Importe o arquivo KPI.\n2) Importe o arquivo Fidelizados.\n3) O sistema processará e exibirá a base.\n", unsafe_allow_html=True)
    kpi_file = st.file_uploader("Importar arquivo KPI (xlsx/csv)", type=["xlsx", "csv"], key="kpi")
    fid_file = st.file_uploader("Importar arquivo Fidelizados (xlsx/csv)", type=["xlsx", "csv"], key="fid")
    if kpi_file and fid_file:
        df_kpi = try_read_excel_or_csv(kpi_file)
        df_fid = try_read_excel_or_csv(fid_file)
        if df_kpi is None or df_fid is None:
            st.error("Erro ao ler algum dos arquivos, verifique o formato e tente novamente.")
        else:
            wk_kpi = localizar_coluna(df_kpi, ['whatsapp principal'])
            wk_fid = localizar_coluna(df_fid, ['whatsapp principal'])
            w_obs = localizar_coluna(df_kpi, ['observação'])
            w_carteira = localizar_coluna(df_kpi, ['carteiras'])
            w_contato = localizar_coluna(df_kpi, ['contato','nome'])
            w_data = localizar_coluna(df_kpi, ['data evento'])
            obrigatorios = {'WhatsApp KPI': wk_kpi, 'WhatsApp Fidelizados': wk_fid, 'Observação': w_obs, 'Carteiras': w_carteira, 'Contato': w_contato}
            for nome, col in obrigatorios.items():
                if col is None:
                    st.error(f"Coluna obrigatória '{nome}' não encontrada.")
                    st.stop()

            df_kpi[wk_kpi] = df_kpi[wk_kpi].astype(str).str.strip().str.lstrip('0')
            df_kpi = df_kpi[~df_kpi[wk_kpi].isin(df_fid[wk_fid])]
            df_kpi = df_kpi[df_kpi[w_obs].str.contains('Médio|Fundamental', case=False, na=False)]

            if w_carteira:
                df_kpi = df_kpi[~df_kpi[w_carteira].str.strip().isin(['SAC - Pós Venda','Secretaria'])]

            df_kpi[w_contato] = [tratar_nome(n, t) for n, t in zip(df_kpi[w_contato], df_kpi[wk_kpi])]

            base_final = df_kpi.rename(columns={wk_kpi: 'Numero', w_contato:'nome'})
            final_df = base_final[['nome', 'Numero']].drop_duplicates(subset=['Numero'])

            export_df = export_layout_robbu(final_df, 'nome', 'Numero')
            nome_arquivo = gerar_nome_abandono(df_kpi, w_data)

            st.success(f"Base pronta com {len(export_df)} registros.")
            csv_data = export_df.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("Baixar CSV", data=csv_data, file_name=nome_arquivo, mime='text/csv')
            st.dataframe(export_df)

elif opcao == "🛒👋 Carrinho Abandonado":
    st.markdown("<h1 style='text-align:center;color:#066f46;'>Gerador de Campanha - Carrinho Abandonado</h1>", unsafe_allow_html=True)
    st.markdown("### Importe as três bases:\n- Carrinho Abandonado (csv)\n- Não Pagos (xls/csv)\n- Pedidos (xls/csv)\n", unsafe_allow_html=True)
    c_file = st.file_uploader("Carrinho Abandonado (csv)", type=['csv'], key='carrinho')
    np_file = st.file_uploader("Não Pagos (excel/csv)", type=['csv','xlsx'], key='np')
    p_file = st.file_uploader("Pedidos (excel/csv)", type=['csv','xlsx'], key='peds')
    if c_file and np_file and p_file:
        try:
            df_c = pd.read_csv(c_file, encoding='utf-8')
            mapping_c = {'First-Name':'nome','Email':'E-mail','Phone':'Numero'}
            df_c = df_c[[col for col in mapping_c if col in df_c.columns]].rename(columns=mapping_c)
            df_c['nome'] = [tratar_nome(n,t) for n,t in zip(df_c['nome'], df_c['Numero'])]
            df_c['Numero'] = df_c['Numero'].apply(tratar_numero)
            df_c['E-mail'] = df_c['E-mail'].apply(tratar_email)

            if np_file.name.lower().endswith('csv'):
                df_np = pd.read_csv(np_file, encoding='utf-8')
            else:
                df_np = pd.read_excel(np_file)
            mapping_np = {'Nome completo (cobrança)':'nome','E-mail (cobrança)':'E-mail','Telefone (cobrança)':'Numero'}
            df_np = df_np[[col for col in mapping_np if col in df_np.columns]].rename(columns=mapping_np)
            df_np['nome'] = [tratar_nome(n,t) for n,t in zip(df_np['nome'], df_np['Numero'])]
            df_np['Numero'] = df_np['Numero'].apply(tratar_numero)
            df_np['E-mail'] = df_np['E-mail'].apply(tratar_email)

            df_ped = None
            if p_file.name.lower().endswith('csv'):
                df_ped = pd.read_csv(p_file, encoding='utf-8')
            else:
                df_ped = pd.read_excel(p_file)

            emails_col_candidates = [c for c in df_ped.columns if 'email' in c.lower()]
            emails_peds = set()
            if emails_col_candidates and len(emails_col_candidates) > 0:
                emails_peds = set(df_ped[emails_col_candidates[0]].dropna().astype(str).str.strip().str.lower())

            combined_df = pd.concat([df_c, df_np], ignore_index=True)
            combined_df = combined_df[~combined_df['E-mail'].isin(emails_peds)]
            combined_df = combined_df.drop_duplicates(subset=['Numero']).reset_index(drop=True)

            qtd_c = len(df_c)
            qtd_np = len(df_np)
            qtd_final = len(combined_df)

            export_df = export_layout_robbu(combined_df, 'nome', 'Numero')
            nome_arquivo = gerar_nome_carinho()

            st.markdown(f"""
                <div class="card-summary">
                    <h3>Resumo:</h3>
                    <p>Registros Carrinho: <b>{qtd_c}</b></p>
                    <p>Registros Não Pagos: <b>{qtd_np}</b></p>
                    <p>Total Final Após Filtros: <b>{qtd_final}</b></p>
                </div>
            """, unsafe_allow_html=True)

            st.dataframe(combined_df[['nome','E-mail','Numero']])

            csv_out = export_df.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("Baixar CSV", data=csv_out, file_name=nome_arquivo, mime='text/csv')

        except Exception as e:
            st.error(f"Erro no processamento: {e}")
