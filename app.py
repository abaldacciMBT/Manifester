
import streamlit as st
import pandas as pd
import re
import pdfplumber

st.title("Manifest Data Extractor SaaS (MVP)")

def parse_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name=0)
    return df

def parse_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    st.info("PDF parsing is basic. Excel works better for now.")
    return pd.DataFrame({'Raw PDF Text': [text]})

def extract_consignee_info(raw_text):
    lines = str(raw_text).strip().split('\n')
    name = lines[0] if lines else ''
    email, phone = '', ''
    for line in lines[1:]:
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', line)
        phone_match = re.search(r'\+?\d[\d\s-]{7,}', line)
        if email_match: email = email_match.group(0)
        if phone_match: phone = phone_match.group(0)
    return pd.Series([name, email, phone])

uploaded_file = st.file_uploader("Upload Excel or PDF manifest", type=["xlsx", "xls", "pdf"])
if uploaded_file:
    if uploaded_file.name.endswith('.pdf'):
        df = parse_pdf(uploaded_file)
        st.write(df)
    else:
        df = parse_excel(uploaded_file)
        st.success("Excel file loaded.")

        st.write("Preview:", df.head())

        if "LOADING PORT" in df.columns:
            port_breakdown = df['LOADING PORT'].value_counts().reset_index()
            port_breakdown.columns = ['Loading Port', 'Number of Shipments']
            st.subheader("Shipments by Loading Port")
            st.dataframe(port_breakdown)

        if "CONSIGNEE" in df.columns:
            consignees = df['CONSIGNEE'].dropna().unique()
            consignees_df = pd.DataFrame(consignees, columns=['Raw Consignee'])
            consignees_df[['Name', 'Email', 'Phone']] = consignees_df['Raw Consignee'].apply(extract_consignee_info)
            st.subheader("Consignee Contacts")
            st.dataframe(consignees_df[['Name', 'Email', 'Phone']])

        st.subheader("Find BOL for Consignee")
        name_search = st.text_input("Enter consignee name to search BOL")
        if name_search:
            matches = df[df['CONSIGNEE'].str.contains(name_search, case=False, na=False)]
            if not matches.empty:
                st.dataframe(matches[['B/L NUMBER', 'CONSIGNEE']])
            else:
                st.info("No matches found.")
