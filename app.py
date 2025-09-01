import pandas as pd
import streamlit as st
import chardet
import re
import base64

# CSS para título principal
css = '''
<style>
.titulo-principal {
    color: #0066cc;
    font-size: 30px;
    font-weight: 700;
    text-align: center;
    padding-top: 20px;
    padding-bottom: 10px;
}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

def detect_separator_and_encoding(uploaded_file):
    content = uploaded_file.read()
    uploaded_file.seek(0)
    result = chardet.detect(content)
    encoding = result['encoding']
    sample = content.decode(encoding, errors='ignore').splitlines()
    separators = [',', ';', '\t', '|']
    counts = {sep: sum(line.count(sep) for line in sample[:10]) for sep in separators}
    separator = max(counts, key=counts.get)
    return separator, encoding

def read_file(uploaded_file):
    if uploaded_file.name.lower().endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        sep, encoding = detect_separator_and_encoding(uploaded_file)
        return pd.read_csv(uploaded_file, sep=sep, encoding=encoding)

def rename_columns_to_standard(df, standard_columns):
    mapping = {}
    lower_standard = [c.lower().strip() for c in standard_columns]
    for col in df.columns:
        col_check = col.lower().strip()
        if col_check in lower_standard:
            idx = lower_standard.index(col_check)
            mapping[col] = standard_columns[idx]
    return df.rename(columns=mapping)

def process_phone_number(num):
    num_str = str(num).strip()
    num_str = re.sub(r'^0+', '', num_str)  # remove leading zeros
    num_str = re.sub(r'\D', '', num_str)   # remove non-digit chars
    return num_str

def process_contact_name(name):
    if pd.isna(name):
        return name
    name_str = str(name)
    if name_str.lower().startswith('me'):
        return 'Cliente Abandono'
    return name_str

def app():
    st.title("Relatório Campanha de Abandono")

    # Standard columns for KPI and Fidelizados based on the attached files
    kpi_columns = [
        "Data Evento", "Descrição Evento", "Tipo Evento", "Evento Finalizador", "Contato",
        "Identificação", "Código Contato", "Hashtag", "Usuário", "Número Protocolo",
        "Data Hora Geração Protocolo", "Observação", "SMS Principal", "Whatsapp Principal",
        "Email Principal", "Canal", "Carteiras", "Carteira do Evento", "Valor da oportunidade",
        "Identificador da chamada Voz"
    ]

    fidelizados_columns = [
        "Usuário Fidelizado", "Contato", "Identificação", "Código", "Canal",
        "Último Contato", "Qtd. Mensagens Pendentes", "SMS Principal", "Whatsapp Principal",
        "Email Principal", "Segmentos vinculados pessoa", "Agendado",
        "Data Hora Agendamento", "Ultimo Evento", "Ultimo Evento Finalizador"
    ]

    st.markdown('<div class="titulo-principal">Importar Bases</div>', unsafe_allow_html=True)

    kpi_file = st.file_uploader("Arquivo KPI", type=["csv", "xlsx"], key="kpi")
    fid_file = st.file_uploader("Arquivo Fidelizados", type=["csv", "xlsx"], key="fid")

    if kpi_file and fid_file:
        df_kpi = read_file(kpi_file)
        df_fid = read_file(fid_file)

        # Rename columns to exact standard names
        df_kpi = rename_columns_to_standard(df_kpi, kpi_columns)
        df_fid = rename_columns_to_standard(df_fid, fidelizados_columns)

        # Find required columns by name
        kpi_wpp_col = [c for c in df_kpi.columns if "Whatsapp Principal" in c][0]
        kpi_obs_col = [c for c in df_kpi.columns if "Observação" in c][0]
        kpi_contato_col = [c for c in df_kpi.columns if c == "Contato"][0]

        fid_wpp_col = [c for c in df_fid.columns if "Whatsapp Principal" in c][0]

        # Normalize phone numbers removing leading zeros and non-digit chars
        df_kpi[kpi_wpp_col] = df_kpi[kpi_wpp_col].apply(process_phone_number)
        df_fid[fid_wpp_col] = df_fid[fid_wpp_col].apply(process_phone_number)

        # Filter KPI records that are NOT in Fidelizados (phone number)
        df_filtered = df_kpi[~df_kpi[kpi_wpp_col].isin(df_fid[fid_wpp_col])]

        # Keep only customers with schooling "Médio" or "Fundamental" in the observation column
        df_filtered = df_filtered[df_filtered[kpi_obs_col].astype(str).str.contains("médio|fundamental", case=False, na=False)]

        # Optional: exclude certain 'Carteiras' if exists - uncomment and adjust if needed
        # if 'Carteiras' in df_filtered.columns:
        #     df_filtered = df_filtered[~df_filtered['Carteiras'].isin(['SAC - Pós Venda', 'Secretaria'])]

        # Process contact names: replace if name starts with "Me"
        df_filtered[kpi_contato_col] = df_filtered[kpi_contato_col].apply(process_contact_name)

        # Prepare final dataframe with columns renamed
        df_final = df_filtered[[kpi_contato_col, kpi_wpp_col]].copy()
        df_final = df_final.rename(columns={kpi_contato_col: "Nome", kpi_wpp_col: "Número"})
        df_final = df_final.drop_duplicates(subset=["Número"]).reset_index(drop=True)

        st.subheader(f"Clientes para campanha de abandono ({len(df_final)})")
        st.dataframe(df_final)

        # Prepare CSV for download
        csv = df_final.to_csv(index=False, encoding="utf-8")
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="campanha_abandono.csv">📥 Baixar arquivo CSV</a>'
        st.markdown(href, unsafe_allow_html=True)


if __name__ == "__main__":
    app()
