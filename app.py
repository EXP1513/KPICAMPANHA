import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha", page_icon="🚀"Gera Campanha"🚀", layout="centered")

# ---------- ESTILO ADAPTATIVO AUTOMÁTICO PARA LIGHT/DARK MODE ----------
st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', sans-serif;
        background-color: var(--background-color, #f4f6f8);
        color: var(--text-color, #000);
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    .titulo-principal {
        background-color: var(--primary-color, #004aad);
        color: var(--on-primary-color, #fff);
        padding: 18px;
        border-radius: 8px;
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    div.stDownloadButton > button, div.stFileUploader > div > button {
        background-color: #ffb703cc;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 16px;
        border: none;
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
        background-color: #fb850099;
        color: white;
    }
    .stSuccess {
        background-color: var(--success-bg, #e6f4ea);
        color: var(--success-text, #000);
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    .manual-popup {
        background-color: var(--warning-bg, #fff3cdcc);
        border-left: 6px solid #ff9800cc;
        padding: 15px;
        border-radius: 6px;
        font-size: 1.05em;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-top: 20px;
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }
    @media (prefers-color-scheme: dark) {
        body, .titulo-principal, .stSuccess, .manual-popup {
            color: #f0f0f0 !important;
        }
        .titulo-principal {
            background-color: #1c1c1c !important;
            box-shadow: 0 4px 8px rgba(255, 255, 255, 0.2) !important;
        }
        .manual-popup {
            background-color: #3a3a3a !important;
            border-left-color: #ffa726 !important;
            box-shadow: 0 4px 8px rgba(255, 165, 0, 0.5) !important;
        }
        div.stDownloadButton > button, div.stFileUploader > div > button {
            background-color: #ffa726 !important;
            color: #000 !important;
        }
        div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
            background-color: #ffb74d !important;
            color: #000 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------- TÍTULO ----------
st.markdown("<div class='titulo-principal'>🚀🇧🇷🚀 Gera Campanha</div>", unsafe_allow_html=True)

# ---------- MANUAL NA TELA PRINCIPAL ----------
st.markdown(
    """
    <div style='background-color:#e0f7fa; border-left: 5px solid #00796b;
                padding: 15px; margin-bottom: 20px; border-radius: 5px;'>
        <strong>PARA GERAR A BASE CAMPANHA É NECESSÁRIO IR ANTES NA ROBBU E...</strong><br>
        1️⃣ Gere o relatório de <b>KPI de Eventos</b>, selecionando o período desejado.<br>
        2️⃣ Ainda na <strong>Robbu</strong>, gere o relatório de <b>Contatos Fidelizados</b>.<br>
        3️⃣ Aqui no <strong>aplicativo de geração de base</strong>, faça o upload do arquivo de KPI no campo <em>"📂 Importar base KPI"</em>.<br>
        4️⃣ Faça também o upload do arquivo de Fidelizados no campo <em>"📂 Importar base FIDELIZADOS"</em>.<br>
        5️⃣ O sistema processará os dados e gerará a base final automaticamente, pronta para importação na Robbu.<br>
    </div>
    """, 
    unsafe_allow_html=True
)

# ---------- FUNÇÃO PARA LEITURA E FILTRO ----------
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

# ---------- UPLOAD ----------
file_kpi = st.file_uploader("📂 Importar base **KPI**", type=["xlsx", "csv"])
file_fid = st.file_uploader("📂 Importar base **FIDELIZADOS**", type=["xlsx", "csv"])

if file_kpi and file_fid:
    df_kpi = read_file(file_kpi)
    df_fid = read_file(file_fid)

    col_whatsapp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
    col_whatsapp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)

    if not col_whatsapp_kpi or not col_whatsapp_fid:
        st.error("❌ Coluna 'WhatsApp Principal' não encontrada.")
    else:
        df_kpi[col_whatsapp_kpi] = df_kpi[col_whatsapp_kpi].astype(str).str.strip()
        df_kpi[col_whatsapp_kpi] = df_kpi[col_whatsapp_kpi].apply(
            lambda x: re.sub(r'^0+', '', x) if re.match(r'^0', x) else x
        )

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
            def processar_contato(valor):
                texto_original = str(valor).strip()
                if not texto_original or texto_original.lower() == "nan":
                    return "Candidato"
                primeira_palavra = texto_original.split(" ")[0].capitalize()
                if len(primeira_palavra) <= 3:
                    return "Candidato"
                return primeira_palavra
            base_pronta[col_contato] = base_pronta[col_contato].apply(processar_contato)

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

        # Mensagem de sucesso
        st.success(f"✅ Base de campanha gerada para importação! {len(base_importacao)} registros.")

        # Botão de download
        output = BytesIO()
        base_importacao.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button(
            label="⬇️ DOWNLOAD CAMPANHA (formato .csv)",
            data=output,
            file_name=nome_arquivo,
            mime="text/csv"
        )

        # Manual logo abaixo da mensagem
        st.markdown(
            f"""
            <div class='manual-popup'>
                <h4>📤 Próximos passos – Importar na Robbu</h4>
                <p><strong>Agora:</strong> baixe o arquivo gerado acima (<em>{nome_arquivo}</em>).</p>
                <ol>
                    <li>Na <strong>Robbu</strong>, vá na opção <strong>"Público"</strong> e clique em <strong>"Importar Público"</strong>.</li>
                    <li>Na <strong>descrição</strong>, escreva <b>"Abandono"</b> junto com a data do arquivo.</li>
                    <li>Selecione o segmento <strong>"Distribuição Manual"</strong>.</li>
                    <li>Faça o upload do arquivo gerado.</li>
                    <li>Marque a opção: <strong>"Minha empresa possui autorização para processamento e comunicação com o público"</strong>.</li>
                    <li>Selecione o tipo de autorização como <strong>"Consentimento"</strong>.</li>
                    <li>Marque <strong>"Manter apenas neste segmento"</strong>.</li>
                    <li>Clique em <strong>Importar</strong> e aguarde até a confirmação de sucesso.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Prévia da Base
        st.markdown("## Prévia da Base")
        st.dataframe(base_importacao)



