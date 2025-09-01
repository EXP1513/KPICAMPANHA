import pandas as pd
import streamlit as st
import chardet
import re
import base64

def detect_separator_and_encoding(uploaded_file):
    content = uploaded_file.read()
    uploaded_file.seek(0)
    detected = chardet.detect(content)
    encoding = detected['encoding']
    sample = content.decode(encoding, errors='ignore').splitlines()
    separators = [',', ';', '\t', '|']
    counts = {sep: sum(line.count(sep) for line in sample[:10]) for sep in separators}
    sep = max(counts, key=counts.get)
    return sep, encoding

def read_file(uploaded_file):
    if uploaded_file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        sep, encoding = detect_separator_and_encoding(uploaded_file)
        return pd.read_csv(uploaded_file, sep=sep, encoding=encoding)

def rename_columns(df, standard_columns):
    mapping = {}
    lower_std_cols = [c.lower() for c in standard_columns]
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in lower_std_cols:
            mapping[col] = standard_columns[lower_std_cols.index(col_lower)]
    return df.rename(columns=mapping)

def clean_phone(phone):
    phone = str(phone).strip()
    phone = re.sub(r'^0+', '', phone)
    phone = re.sub(r'\D', '', phone)
    return phone

def clean_name(name):
    if pd.isna(name):
        return name
    if str(name).lower().startswith('me'):
        return 'Cliente Abandono'
    return name

def main():
    st.markdown(\"\"\"<style>
    .titulo-principal {
        color: #0066cc;
        font-size: 30px;
        font-weight: 700;
        text-align: center;
        padding-top: 20px;
        padding-bottom: 10px;
    }
    </style>\"\"\", unsafe_allow_html=True)

    st.markdown('<div class=\"titulo-principal\">Campanha de Abandono - Importar Arquivos</div>', unsafe_allow_html=True)

    kpi_file = st.file_uploader('Enviar arquivo KPI (.csv ou .xlsx)', type=['csv','xlsx'])
    fid_file = st.file_uploader('Enviar arquivo Fidelizados (.csv ou .xlsx)', type=['csv','xlsx'])

    if not kpi_file or not fid_file:
        st.info('Por favor, envie ambos os arquivos para processar.')
        return

    # Colunas padrão (idênticas ao arquivo anexado)
    kpi_columns = [
        'Data Evento', 'Descrição Evento', 'Tipo', 'Evento Finalizador', 'Contato',
        'Identificação', 'Código Contato', 'Hashtag', 'Usuário', 'Número Protocolo',
        'Data Hora Geração Protocolo', 'Observação', 'SMS Principal', 'Whatsapp Principal',
        'Email Principal', 'Canal', 'Carteiras', 'Carteira do Evento',
        'Valor da oportunidade', 'Identificador da chamada Voz'
    ]

    fid_columns = [
        'Usuário Fidelizado', 'Contato', 'Identificação', 'Código', 'Canal', 'Último Contato',
        'Qtd. Mensagens Pendentes', 'SMS Principal', 'Whatsapp Principal',
        'Email Principal', 'Segmentos vinculados pessoa', 'Agendado',
        'Data Hora Agendamento', 'Ultimo Evento', 'Ultimo Evento Finalizador'
    ]

    df_kpi = read_file(kpi_file)
    df_fid = read_file(fid_file)

    df_kpi = rename_columns(df_kpi, kpi_columns)
    df_fid = rename_columns(df_fid, fid_columns)

    # Validar colunas obrigatórias
    required_kpi_cols = ['Contato', 'Whatsapp Principal', 'Observação']
    required_fid_cols = ['Whatsapp Principal']

    missing_kpi = [c for c in required_kpi_cols if c not in df_kpi.columns]
    missing_fid = [c for c in required_fid_cols if c not in df_fid.columns]

    if missing_kpi:
        st.error(f'Colunas obrigatórias da KPI ausentes: {missing_kpi}')
        return
    if missing_fid:
        st.error(f'Colunas obrigatórias da Fidelizados ausentes: {missing_fid}')
        return

    # Limpar telefone
    df_kpi['Whatsapp Principal'] = df_kpi['Whatsapp Principal'].apply(clean_phone)
    df_fid['Whatsapp Principal'] = df_fid['Whatsapp Principal'].apply(clean_phone)

    # Selecionar clientes não fidelizados
    df_abandon = df_kpi[~df_kpi['Whatsapp Principal'].isin(df_fid['Whatsapp Principal'])]

    # Filtrar escolaridade na observação
    df_abandon = df_abandon[df_abandon['Observação'].str.contains('médio|fundamental', case=False, na=False)]

    # Excluir carteiras indesejadas caso exista a coluna
    if 'Carteiras' in df_abandon.columns:
        df_abandon = df_abandon[~df_abandon['Carteiras'].isin(['SAC - Pós Venda', 'Secretaria'])]

    # Ajustar nomes para abandono
    df_abandon['Contato'] = df_abandon['Contato'].apply(clean_name)

    # Gerar dataframe final com colunas renomeadas para Exportar
    df_final = df_abandon[['Contato', 'Whatsapp Principal']].copy()
    df_final.rename(columns={'Contato': 'Nome', 'Whatsapp Principal': 'Número'}, inplace=True)
    df_final.drop_duplicates(subset=['Número'], inplace=True)
    df_final.reset_index(drop=True, inplace=True)

    st.subheader(f'Total de clientes para campanha de abandono: {len(df_final)}')
    st.dataframe(df_final)

    # Link download CSV
    csv = df_final.to_csv(index=False, encoding='utf-8')
    b64 = base64.b64encode(csv.encode()).decode()
    st.markdown(f'<a href=\"data:file/csv;base64,{b64}\" download=\"campanha_abandono.csv\">📥 Baixar CSV</a>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()
