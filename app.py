import pandas as pd
import streamlit as st
import re
import base64

def read_file(uploaded_file):
    # For CSV, assume separator ';' and encoding 'utf-8'
    if uploaded_file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(uploaded_file)
    else:
        return pd.read_csv(uploaded_file, sep=';', encoding='utf-8')

def clean_phone(phone):
    phone = str(phone).strip()
    phone = re.sub(r'^0+', '', phone)  # remove zeros à esquerda
    phone = re.sub(r'\D', '', phone)   # remove tudo que não é dígito
    return phone

def clean_name(name):
    if pd.isna(name):
        return name
    if str(name).lower().startswith('me'):
        return 'Cliente Abandono'
    return name

def main():
    st.markdown("""
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
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="titulo-principal">Campanha de Abandono - Importar Arquivos</div>', unsafe_allow_html=True)

    kpi_file = st.file_uploader('Enviar arquivo KPI (.csv ou .xlsx)', type=['csv','xlsx'])
    fid_file = st.file_uploader('Enviar arquivo Fidelizados (.csv ou .xlsx)', type=['csv','xlsx'])

    if not kpi_file or not fid_file:
        st.info('Por favor, envie ambos os arquivos para processar.')
        return

    df_kpi = read_file(kpi_file)
    df_fid = read_file(fid_file)

    # Validar colunas necessárias
    required_columns_kpi = ['Contato', 'Whatsapp Principal', 'Observação', 'Carteiras']
    required_columns_fid = ['Whatsapp Principal']
    
    for col in required_columns_kpi[:-1]:  # Carteiras pode não existir, usar condicionado depois
        if col not in df_kpi.columns:
            st.error(f"Coluna '{col}' não encontrada no arquivo KPI.")
            return
    
    for col in required_columns_fid:
        if col not in df_fid.columns:
            st.error(f"Coluna '{col}' não encontrada no arquivo Fidelizados.")
            return

    # Limpar números Whatsapp
    df_kpi['Whatsapp Principal'] = df_kpi['Whatsapp Principal'].apply(clean_phone)
    df_fid['Whatsapp Principal'] = df_fid['Whatsapp Principal'].apply(clean_phone)

    # Selecionar clientes de KPI que não estão fidelizados
    df_abandon = df_kpi[~df_kpi['Whatsapp Principal'].isin(df_fid['Whatsapp Principal'])]

    # Filtrar por escolaridade na observação
    df_abandon = df_abandon[df_abandon['Observação'].str.contains('médio|fundamental', case=False, na=False)]

    # Excluir carteiras indesejadas (se existir coluna)
    if 'Carteiras' in df_abandon.columns:
        df_abandon = df_abandon[~df_abandon['Carteiras'].isin(['SAC - Pós Venda', 'Secretaria'])]

    # Ajustar nomes para abandono
    df_abandon['Contato'] = df_abandon['Contato'].apply(clean_name)

    # Preparar tabela final para exportar
    df_final = df_abandon[['Contato', 'Whatsapp Principal']].drop_duplicates()
    df_final.rename(columns={'Contato':'Nome', 'Whatsapp Principal':'Número'}, inplace=True)
    df_final.reset_index(drop=True, inplace=True)

    st.subheader(f"Total de clientes para campanha de abandono: {len(df_final)}")
    st.dataframe(df_final)

    csv = df_final.to_csv(index=False, encoding='utf-8')
    b64 = base64.b64encode(csv.encode()).decode()
    st.markdown(f'<a href="data:file/csv;base64,{b64}" download="campanha_abandono.csv">📥 Baixar CSV</a>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()
