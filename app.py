import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import datetime as dt
import json
import io
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="Pembukuan Usaha Online",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .summary-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi database - FIXED untuk Railway
def init_database():
    # Gunakan path absolute untuk database
    db_path = os.path.join(os.getcwd(), 'pembukuan.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            keterangan TEXT NOT NULL,
            kategori TEXT NOT NULL,
            jenis TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    db_path = os.path.join(os.getcwd(), 'pembukuan.db')
    return sqlite3.connect(db_path, check_same_thread=False)

# Inisialisasi database
init_database()

# Sidebar navigation
st.sidebar.title("📊 Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Menu:",
    ["🏠 Dashboard", "➕ Tambah Transaksi", "📋 Lihat Transaksi", "📈 Laporan", "⚙️ Export Data"]
)

# Header
st.markdown('<div class="main-header">💼 Pembukuan Usaha Online</div>', unsafe_allow_html=True)

# Session state
if 'transaksi_df' not in st.session_state:
    conn = get_connection()
    try:
        st.session_state.transaksi_df = pd.read_sql('SELECT * FROM transaksi ORDER BY tanggal DESC', conn)
    except:
        st.session_state.transaksi_df = pd.DataFrame()
    finally:
        conn.close()

def refresh_data():
    conn = get_connection()
    try:
        st.session_state.transaksi_df = pd.read_sql('SELECT * FROM transaksi ORDER BY tanggal DESC', conn)
    except:
        st.session_state.transaksi_df = pd.DataFrame()
    finally:
        conn.close()

# 1. DASHBOARD
if menu == "🏠 Dashboard":
    st.header("📊 Dashboard Keuangan")
    
    if st.session_state.transaksi_df.empty:
        st.info("📝 Belum ada transaksi. Mulai dengan menambah transaksi di menu 'Tambah Transaksi'.")
    else:
        df = st.session_state.transaksi_df
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        
        total_pemasukan = df[df['jenis'] == 'Pemasukan']['jumlah'].sum()
        total_pengeluaran = df[df['jenis'] == 'Pengeluaran']['jumlah'].sum()
        saldo = total_pemasukan - total_pengeluaran
        total_transaksi = len(df)
        
        with col1:
            st.metric("Total Pemasukan", f"Rp {total_pemasukan:,}")
        with col2:
            st.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,}")
        with col3:
            st.metric("Saldo", f"Rp {saldo:,}")
        with col4:
            st.metric("Total Transaksi", total_transaksi)
        
        # Transaksi terbaru
        st.subheader("🆕 5 Transaksi Terbaru")
        st.dataframe(
            df.head(5)[['tanggal', 'keterangan', 'kategori', 'jenis', 'jumlah']],
            use_container_width=True
        )

# 2. TAMBAH TRANSAKSI
elif menu == "➕ Tambah Transaksi":
    st.header("➕ Tambah Transaksi Baru")
    
    with st.form("tambah_transaksi_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tanggal = st.date_input("Tanggal Transaksi", datetime.date.today())
            keterangan = st.text_input("Keterangan Transaksi", placeholder="Contoh: Penjualan Harian")
            
            kategori_pemasukan = ["Penjualan", "Investasi", "Lainnya"]
            kategori_pengeluaran = ["Bahan Baku", "Operasional", "Gaji", "Transportasi", "Lainnya"]
            
            jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
        
        with col2:
            if jenis == "Pemasukan":
                kategori = st.selectbox("Kategori", kategori_pemasukan)
            else:
                kategori = st.selectbox("Kategori", kategori_pengeluaran)
            
            jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000, value=0)
        
        submitted = st.form_submit_button("💾 Simpan Transaksi")
        
        if submitted:
            if keterangan.strip() == "":
                st.error("❌ Keterangan transaksi harus diisi!")
            elif jumlah == 0:
                st.error("❌ Jumlah transaksi harus lebih dari 0!")
            else:
                conn = get_connection()
                c = conn.cursor()
                
                try:
                    c.execute('''
                        INSERT INTO transaksi (tanggal, keterangan, kategori, jenis, jumlah)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tanggal.strftime("%Y-%m-%d"), keterangan, kategori, jenis, jumlah))
                    
                    conn.commit()
                    refresh_data()
                    st.success(f"✅ Transaksi berhasil ditambahkan!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                finally:
                    conn.close()

# 3. LIHAT TRANSAKSI
elif menu == "📋 Lihat Transaksi":
    st.header("📋 Daftar Semua Transaksi")
    
    if st.session_state.transaksi_df.empty:
        st.info("Belum ada transaksi.")
    else:
        df = st.session_state.transaksi_df
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            filter_jenis = st.selectbox("Filter Jenis", ["Semua", "Pemasukan", "Pengeluaran"])
        
        # Apply filters
        filtered_df = df.copy()
        
        if filter_jenis != "Semua":
            filtered_df = filtered_df[filtered_df['jenis'] == filter_jenis]
        
        st.subheader(f"📊 {len(filtered_df)} Transaksi Ditemukan")
        
        # Tampilkan data
        st.dataframe(
            filtered_df[['tanggal', 'keterangan', 'kategori', 'jenis', 'jumlah']],
            use_container_width=True
        )

# 4. LAPORAN
elif menu == "📈 Laporan":
    st.header("📈 Laporan Keuangan")
    
    if st.session_state.transaksi_df.empty:
        st.info("Belum ada data untuk laporan.")
    else:
        df = st.session_state.transaksi_df
        
        # Ringkasan
        st.subheader("📋 Ringkasan")
        
        pemasukan = df[df['jenis'] == 'Pemasukan']['jumlah'].sum()
        pengeluaran = df[df['jenis'] == 'Pengeluaran']['jumlah'].sum()
        saldo = pemasukan - pengeluaran
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pemasukan", f"Rp {pemasukan:,}")
        col2.metric("Total Pengeluaran", f"Rp {pengeluaran:,}")
        col3.metric("Saldo", f"Rp {saldo:,}")

# 5. EXPORT DATA
elif menu == "⚙️ Export Data":
    st.header("⚙️ Export Data")
    
    if st.session_state.transaksi_df.empty:
        st.info("Belum ada data untuk di-export.")
    else:
        df = st.session_state.transaksi_df
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export to Excel
            if st.button("📊 Export ke Excel"):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Transaksi', index=False)
                
                st.download_button(
                    label="⬇️ Download Excel File",
                    data=buffer.getvalue(),
                    file_name=f"pembukuan_{dt.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
        
        with col2:
            # Export to CSV
            if st.button("📄 Export ke CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV File",
                    data=csv,
                    file_name=f"pembukuan_{dt.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )

# Footer
st.markdown("---")
st.markdown(
    "**Pembukuan Usaha Online** - Dibuat dengan Streamlit • "
    "Deployed di Railway • "
    "© 2024"
)