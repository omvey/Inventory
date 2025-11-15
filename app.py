# app.py
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Aplikasi Pembukuan", layout="wide")

st.title("📊 Aplikasi Pembukuan Usaha")

# Input form
with st.form("input_transaksi"):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tanggal = st.date_input("Tanggal", datetime.date.today())
    with col2:
        keterangan = st.text_input("Keterangan")
    with col3:
        jenis = st.selectbox("Jenis", ["Pemasukan", "Pengeluaran"])
    with col4:
        jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    
    submitted = st.form_submit_button("Tambah Transaksi")

# Tampilkan data
if 'transaksi' not in st.session_state:
    st.session_state.transaksi = []

if submitted and keterangan:
    st.session_state.transaksi.append({
        'tanggal': tanggal,
        'keterangan': keterangan,
        'jenis': jenis,
        'jumlah': jumlah
    })
    st.success("Transaksi berhasil ditambahkan!")

if st.session_state.transaksi:
    df = pd.DataFrame(st.session_state.transaksi)
    
    # Summary
    pemasukan = df[df['jenis'] == 'Pemasukan']['jumlah'].sum()
    pengeluaran = df[df['jenis'] == 'Pengeluaran']['jumlah'].sum()
    saldo = pemasukan - pengeluaran
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pemasukan", f"Rp {pemasukan:,}")
    col2.metric("Total Pengeluaran", f"Rp {pengeluaran:,}")
    col3.metric("Saldo", f"Rp {saldo:,}")
    
    # Tabel transaksi
    st.dataframe(df, use_container_width=True)
    
    # Export
    if st.button("Export ke Excel"):
        df.to_excel("pembukuan.xlsx", index=False)
        st.success("Data berhasil diexport!")