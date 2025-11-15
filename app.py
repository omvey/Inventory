import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import datetime as dt
import json
import io

# Konfigurasi halaman
st.set_page_config(
    page_title="Pembukuan Usaha Online",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan lebih baik
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
    .positive {
        color: #00aa00;
        font-weight: bold;
    }
    .negative {
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi database
def init_database():
    conn = sqlite3.connect('pembukuan.db')
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
    return sqlite3.connect('pembukuan.db')

# Inisialisasi database
init_database()

# Sidebar untuk navigasi
st.sidebar.title("📊 Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Menu:",
    ["🏠 Dashboard", "➕ Tambah Transaksi", "📋 Lihat Transaksi", "📈 Laporan", "⚙️ Export Data"]
)

# Header utama
st.markdown('<div class="main-header">💼 Pembukuan Usaha Online</div>', unsafe_allow_html=True)

# Session state untuk menyimpan data sementara
if 'transaksi_df' not in st.session_state:
    conn = get_connection()
    st.session_state.transaksi_df = pd.read_sql('SELECT * FROM transaksi ORDER BY tanggal DESC', conn)
    conn.close()

# Fungsi untuk refresh data
def refresh_data():
    conn = get_connection()
    st.session_state.transaksi_df = pd.read_sql('SELECT * FROM transaksi ORDER BY tanggal DESC', conn)
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
            st.metric("Saldo", f"Rp {saldo:,}", delta=f"Rp {saldo:,}" if saldo >= 0 else f"-Rp {abs(saldo):,}")
        with col4:
            st.metric("Total Transaksi", total_transaksi)
        
        # Chart bulanan
        st.subheader("📈 Trend Bulanan")
        
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df['bulan_tahun'] = df['tanggal'].dt.to_period('M')
        
        monthly_data = df.groupby(['bulan_tahun', 'jenis'])['jumlah'].sum().unstack(fill_value=0)
        monthly_data = monthly_data.reset_index()
        monthly_data['bulan_tahun'] = monthly_data['bulan_tahun'].astype(str)
        
        if not monthly_data.empty:
            st.line_chart(monthly_data.set_index('bulan_tahun'))
        
        # Transaksi terbaru
        st.subheader("🆕 Transaksi Terbaru")
        st.dataframe(
            df.head(10)[['tanggal', 'keterangan', 'kategori', 'jenis', 'jumlah']],
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
                
                c.execute('''
                    INSERT INTO transaksi (tanggal, keterangan, kategori, jenis, jumlah)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tanggal.strftime("%Y-%m-%d"), keterangan, kategori, jenis, jumlah))
                
                conn.commit()
                conn.close()
                
                refresh_data()
                st.success(f"✅ Transaksi berhasil ditambahkan!")
                st.balloons()

# 3. LIHAT TRANSAKSI
elif menu == "📋 Lihat Transaksi":
    st.header("📋 Daftar Semua Transaksi")
    
    if st.session_state.transaksi_df.empty:
        st.info("Belum ada transaksi.")
    else:
        df = st.session_state.transaksi_df
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_jenis = st.selectbox("Filter Jenis", ["Semua", "Pemasukan", "Pengeluaran"])
        with col2:
            start_date = st.date_input("Dari Tanggal", 
                                     value=df['tanggal'].min() if not df.empty else datetime.date.today())
        with col3:
            end_date = st.date_input("Sampai Tanggal", 
                                   value=df['tanggal'].max() if not df.empty else datetime.date.today())
        
        # Apply filters
        filtered_df = df.copy()
        filtered_df['tanggal'] = pd.to_datetime(filtered_df['tanggal'])
        
        if filter_jenis != "Semua":
            filtered_df = filtered_df[filtered_df['jenis'] == filter_jenis]
        
        filtered_df = filtered_df[
            (filtered_df['tanggal'].dt.date >= start_date) & 
            (filtered_df['tanggal'].dt.date <= end_date)
        ]
        
        st.subheader(f"📊 {len(filtered_df)} Transaksi Ditemukan")
        
        # Tampilkan data
        st.dataframe(
            filtered_df[['tanggal', 'keterangan', 'kategori', 'jenis', 'jumlah']],
            use_container_width=True
        )
        
        # Summary filtered
        if not filtered_df.empty:
            total_filtered_pemasukan = filtered_df[filtered_df['jenis'] == 'Pemasukan']['jumlah'].sum()
            total_filtered_pengeluaran = filtered_df[filtered_df['jenis'] == 'Pengeluaran']['jumlah'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Total Pemasukan:** Rp {total_filtered_pemasukan:,}")
            with col2:
                st.info(f"**Total Pengeluaran:** Rp {total_filtered_pengeluaran:,}")

# 4. LAPORAN
elif menu == "📈 Laporan":
    st.header("📈 Laporan Keuangan")
    
    if st.session_state.transaksi_df.empty:
        st.info("Belum ada data untuk laporan.")
    else:
        df = st.session_state.transaksi_df
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        
        # Pilihan periode
        col1, col2 = st.columns(2)
        with col1:
            tahun = st.selectbox("Pilih Tahun", sorted(df['tanggal'].dt.year.unique(), reverse=True))
        with col2:
            bulan = st.selectbox("Pilih Bulan", [
                "Semua", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                "Juli", "Agustus", "September", "Oktober", "November", "Desember"
            ])
        
        # Filter data berdasarkan pilihan
        filtered_df = df[df['tanggal'].dt.year == tahun]
        
        if bulan != "Semua":
            bulan_num = [
                "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                "Juli", "Agustus", "September", "Oktober", "November", "Desember"
            ].index(bulan) + 1
            filtered_df = filtered_df[filtered_df['tanggal'].dt.month == bulan_num]
        
        if not filtered_df.empty:
            # Ringkasan
            st.subheader("📋 Ringkasan")
            
            pemasukan = filtered_df[filtered_df['jenis'] == 'Pemasukan']['jumlah'].sum()
            pengeluaran = filtered_df[filtered_df['jenis'] == 'Pengeluaran']['jumlah'].sum()
            saldo = pemasukan - pengeluaran
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Pemasukan", f"Rp {pemasukan:,}")
            col2.metric("Total Pengeluaran", f"Rp {pengeluaran:,}")
            col3.metric("Saldo", f"Rp {saldo:,}")
            
            # Chart by kategori
            st.subheader("📊 Breakdown by Kategori")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pemasukan_by_kategori = filtered_df[filtered_df['jenis'] == 'Pemasukan'].groupby('kategori')['jumlah'].sum()
                if not pemasukan_by_kategori.empty:
                    st.write("**Pemasukan by Kategori:**")
                    st.dataframe(pemasukan_by_kategori)
            
            with col2:
                pengeluaran_by_kategori = filtered_df[filtered_df['jenis'] == 'Pengeluaran'].groupby('kategori')['jumlah'].sum()
                if not pengeluaran_by_kategori.empty:
                    st.write("**Pengeluaran by Kategori:**")
                    st.dataframe(pengeluaran_by_kategori)

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
                    
                    # Auto-adjust columns' width
                    worksheet = writer.sheets['Transaksi']
                    for i, col in enumerate(df.columns):
                        column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                        worksheet.set_column(i, i, column_len)
                
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
        
        # Backup JSON
        st.subheader("🔄 Backup Data")
        if st.button("💾 Generate Backup"):
            backup_data = df.to_dict('records')
            st.download_button(
                label="⬇️ Download Backup JSON",
                data=json.dumps(backup_data, indent=2),
                file_name=f"backup_pembukuan_{dt.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

# Footer
st.markdown("---")
st.markdown(
    "**Pembukuan Usaha Online** - Dibuat dengan Streamlit • "
    "Deployed di Railway • "
    "© 2024"
)