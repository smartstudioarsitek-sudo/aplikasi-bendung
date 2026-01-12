import streamlit as st
import math

# Konfigurasi Halaman
st.set_page_config(page_title="Kalkulator Desain Bendung & Bangunan Air", layout="wide")

st.title("🌊 Aplikasi Desain Hidrolis: Bendung, Intake & Terjun")
st.markdown("Berdasarkan Referensi: *Laporan Penunjang Buku II (DI Tambah Luhur)*")

# Sidebar untuk Navigasi
menu = st.sidebar.selectbox("Pilih Modul Perhitungan", 
                            ["1. Hidrolika Bendung", "2. Intake & Bagi Sadap", "3. Bangunan Terjun"])

# --- MODUL 1: HIDROLIKA BENDUNG ---
if menu == "1. Hidrolika Bendung":
    st.header("1. Perhitungan Hidrolika Mercu Bendung")
    st.info("Rumus Dasar: Q = Cd * 2/3 * sqrt(2/3 * g) * Beff * He^1.5")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Data Dimensi")
        # Default value diambil dari PDF Hal 3 [cite: 68]
        Bn = st.number_input("Lebar Total Bendung (B) [m]", value=11.0)
        n_pilar = st.number_input("Jumlah Pilar (n)", value=1, step=1)
        t_pilar = st.number_input("Tebal Pilar (t) [m]", value=0.5)
        b_bilas = st.number_input("Lebar Pintu Pembilas [m]", value=1.0)
        
        st.subheader("Koefisien & Debit")
        # Default value dari PDF Hal 3 [cite: 68, 110]
        Ka = st.number_input("Koef. Kontraksi Pangkal (Ka)", value=0.10)
        Kp = st.number_input("Koef. Kontraksi Pilar (Kp)", value=0.01)
        Cd = st.number_input("Koef. Debit (Cd) - Asumsi Awal", value=1.45)
        Q_banjir = st.number_input("Debit Banjir Rencana (Q50) [m3/s]", value=39.59)
        g = 9.81

    with col2:
        st.subheader("Hasil Perhitungan")
        
        # 1. Hitung Lebar Efektif (Beff) - Rumus Hal 3 [cite: 68]
        # Beff = Bn - 2(n.Kp + Ka)Ho - (n.t) - b_bilas
        # Catatan: Di PDF rumus bergantung pada Ho, ini pendekatan iteratif. 
        # Di sini kita pakai pendekatan input Ho asumsi dulu untuk Beff.
        Ho_asumsi = st.number_input("Tinggi Energi Asumsi (Ho) untuk koreksi lebar [m]", value=1.0)
        
        koreksi_lebar = 2 * (n_pilar * Kp + Ka) * Ho_asumsi
        lebar_pilar_total = n_pilar * t_pilar
        
        # Menghitung lebar bersih (B_net) dikurangi pilar dan pintu bilas
        B_net = Bn - lebar_pilar_total - b_bilas
        Beff = B_net - koreksi_lebar
        
        st.metric("Lebar Efektif (Beff)", f"{Beff:.3f} m")
        
        if Beff <= 0:
            st.error("Nilai Beff negatif! Cek input lebar bendung dan pilar.")
        else:
            # 2. Hitung Tinggi Muka Air (He) dibalik dari rumus Q
            # Q = Cd * 1.704 * Beff * He^1.5 (dimana 1.704 adalah konstanta 2/3 * sqrt(2/3*g))
            const_g = (2/3) * math.sqrt((2/3) * g) # Sekitar 1.704
            
            # Q = Cd * const_g * Beff * He^1.5
            # He^1.5 = Q / (Cd * const_g * Beff)
            try:
                He_pow = Q_banjir / (Cd * const_g * Beff)
                He = math.pow(He_pow, (1/1.5))
                
                st.success(f"Tinggi Energi di Atas Mercu (He): **{He:.3f} m**")
                
                st.latex(r"Q = C_d \times \frac{2}{3} \sqrt{\frac{2}{3}g} \times B_{eff} \times H_e^{1.5}")
                st.write(f"Kontrol Q Hitung: {Cd * const_g * Beff * math.pow(He, 1.5):.2f} m3/s")
                
            except Exception as e:
                st.error("Terjadi kesalahan perhitungan. Cek nilai input.")

# --- MODUL 2: INTAKE & BAGI SADAP ---
elif menu == "2. Intake & Bagi Sadap":
    st.header("2. Perhitungan Bukaan Pintu (Intake/Sadap)")
    st.info("Digunakan untuk menghitung bukaan pintu (a) pada Intake S.TL.1, S.TL.2, dll.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Data Pintu")
        nama_bangunan = st.text_input("Nama Bangunan (Cth: Intake S.TL.1)", "Intake S.TL.1")
        # Data default dari Hal 13 
        Q_rencana = st.number_input("Debit Rencana (Q) [m3/s]", value=0.164, format="%.4f")
        B_pintu = st.number_input("Lebar Pintu (B) [m]", value=0.60)
        h_kehilangan = st.number_input("Kehilangan Tinggi Energi (z atau h) [m]", value=0.20)
        C_intu = st.number_input("Koefisien Debit Pintu (C)", value=0.80)
        g = 9.81

    with col2:
        st.subheader("Hasil Bukaan Pintu (a)")
        
        if st.button("Hitung Bukaan"):
            # Rumus dari Hal 13 
            # Q = C * B * a * sqrt(2 * g * h)
            # a = Q / (C * B * sqrt(2 * g * h))
            
            try:
                root_val = math.sqrt(2 * g * h_kehilangan)
                a = Q_rencana / (C_intu * B_pintu * root_val)
                
                st.metric("Tinggi Bukaan Pintu (a)", f"{a:.3f} m")
                st.write(f"Atau sekitar **{a*100:.1f} cm**")
                
                st.latex(r"a = \frac{Q}{C \cdot B \cdot \sqrt{2gh}}")
                st.write(f"Perhitungan: {Q_rencana} / ({C_intu} * {B_pintu} * {root_val:.2f})")
                
            except ZeroDivisionError:
                st.error("Nilai pembagi 0. Pastikan Lebar Pintu dan Tinggi Energi > 0")

# --- MODUL 3: BANGUNAN TERJUN ---
elif menu == "3. Bangunan Terjun":
    st.header("3. Hidrolika Bangunan Terjun")
    st.info("Menghitung kedalaman kritis (hc) dan kebutuhan peredam energi.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Data")
        # Data default dari Hal 16 [cite: 567-573]
        Q_terjun = st.number_input("Debit (Q) [m3/s]", value=0.049, format="%.4f")
        b_terjun = st.number_input("Lebar Saluran/Terjun (b) [m]", value=0.15)
        z_drop = st.number_input("Tinggi Terjun (z) [m]", value=2.40)
        g = 9.81
        
    with col2:
        st.subheader("Analisis Hidrolis")
        
        # 1. Hitung Debit per lebar (q)
        # q = Q / b
        if b_terjun > 0:
            q = Q_terjun / b_terjun
            
            # 2. Hitung Kedalaman Kritis (hc) - Hal 5 [cite: 185] & Hal 16 [cite: 575]
            # hc = (q^2 / g)^(1/3)
            hc = math.pow((q**2)/g, 1/3)
            
            st.metric("Kedalaman Kritis (hc)", f"{hc:.3f} m")
            
            # 3. Cek Aliran
            # Input h hulu biasanya kecil, kita asumsikan h < hc (Superkritis)
            st.write(f"Unit Discharge (q): {q:.3f} m3/s/m")
            
            # 4. Hitung Kedalaman Hilir (t) untuk kolam olak - Hal 16 [cite: 579]
            # Rumus empiris dari PDF: t = 3.0 * hc + 0.1 * z (bisa bervariasi tergantung tipe)
            # Di PDF Hal 16 tertulis: t = 3.0 hc + 0.1 z = 0.9 m
            
            t_hitung = (3.0 * hc) + (0.1 * z_drop)
            
            st.metric("Kedalaman Air Hilir / Kolam Olak (t)", f"{t_hitung:.3f} m")
            st.latex(r"t \approx 3.0 h_c + 0.1 z")
            
            # 5. Panjang Kolam (L) - Opsional, biasanya L = 1.5 * Ludik atau rumus lain
            # Di PDF Hal 4 rumus panjang lantai: L >= C * deltaH (Lane)
            st.info("Catatan: Pastikan panjang lantai kolam olak dicek terhadap angka rembesan (Lane/Bligh) jika struktur berada di tanah permeabel.")
            
        else:
            st.error("Lebar saluran harus > 0")

st.markdown("---")
st.caption("Dikembangkan dengan Python Streamlit untuk Engineering Calculation.")