import streamlit as st
import math

# Konfigurasi Halaman
st.set_page_config(page_title="Kalkulator Desain Bendung Lengkap", layout="wide")

st.title("🌊 Aplikasi Desain Hidrolis & Rembesan Air")
st.markdown("Referensi: *Laporan Penunjang Buku II (DI Tambah Luhur)*")

# Sidebar
menu = st.sidebar.selectbox("Pilih Modul Perhitungan", 
                            ["1. Hidrolika Bendung", 
                             "2. Kontrol Rembesan (Lane's Method)",
                             "3. Intake & Bagi Sadap", 
                             "4. Bangunan Terjun & Peredam Energi"])

# --- MODUL 1: HIDROLIKA BENDUNG ---
if menu == "1. Hidrolika Bendung":
    st.header("1. Perhitungan Hidrolika Mercu Bendung")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Data Dimensi")
        Bn = st.number_input("Lebar Total Bendung (B) [m]", value=11.0)
        n_pilar = st.number_input("Jumlah Pilar (n)", value=1.0)
        t_pilar = st.number_input("Tebal Pilar (t) [m]", value=0.5)
        b_bilas = st.number_input("Lebar Pintu Pembilas [m]", value=1.0)
        
        st.subheader("Koefisien & Debit")
        Ka = st.number_input("Koef. Kontraksi Pangkal (Ka)", value=0.10)
        Kp = st.number_input("Koef. Kontraksi Pilar (Kp)", value=0.01)
        Cd = st.number_input("Koef. Debit (Cd)", value=1.45)
        Q_banjir = st.number_input("Debit Banjir (Q50) [m3/s]", value=39.59)
        g = 9.81

    with col2:
        st.subheader("Hasil Perhitungan")
        Ho_asumsi = st.number_input("Tinggi Energi Asumsi (Ho) [m]", value=1.0)
        
        koreksi_lebar = 2 * (n_pilar * Kp + Ka) * Ho_asumsi
        lebar_pilar_total = n_pilar * t_pilar
        B_net = Bn - lebar_pilar_total - b_bilas
        Beff = B_net - koreksi_lebar
        
        st.metric("Lebar Efektif (Beff)", f"{Beff:.3f} m")
        
        if Beff > 0:
            const_g = (2/3) * math.sqrt((2/3) * g)
            try:
                He_pow = Q_banjir / (Cd * const_g * Beff)
                He = math.pow(He_pow, (1/1.5))
                st.success(f"Tinggi Energi (He): **{He:.3f} m**")
                st.info(f"Elevasi Muka Air Banjir = Elevasi Mercu + {He:.3f} m")
            except:
                st.error("Cek inputan debit/dimensi")

# --- MODUL 2: KONTROL REMBESAN (BARU) ---
elif menu == "2. Kontrol Rembesan (Lane's Method)":
    st.header("2. Kontrol Rembesan (Weighted Creep Line)")
    st.info("Sesuai PDF Halaman 4: Pemeriksaan panjang lantai udik & hilir terhadap piping.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Jalur Rayapan")
        # Default value dari PDF Hal 4 (Lv=12.6, Lh=17.0)
        Lv = st.number_input("Total Panjang Vertikal (Lv) [m]", value=12.6)
        Lh = st.number_input("Total Panjang Horizontal (Lh) [m]", value=17.0) # PDF text says 16.6 in calculation but 17.0 in list
        
        st.subheader("Beda Tinggi & Tanah")
        Delta_H = st.number_input("Beda Tinggi Muka Air (ΔH) [m]", value=2.516)
        C_lane = st.number_input("Koefisien Lane (C) [Lempung Lunak=4, Pasir Halus=7]", value=4.0)

    with col2:
        st.subheader("Hasil Kontrol Safety")
        
        # Hitung Panjang Rayapan (L_weighted)
        # Rumus: L = Lv + (1/3 * Lh)
        L_weighted = Lv + (1/3 * Lh)
        
        # Hitung Panjang Minimum yang Dibutuhkan
        L_min = C_lane * Delta_H
        
        st.metric("Panjang Rayapan Terhitung (L)", f"{L_weighted:.3f} m")
        st.metric("Panjang Minimum Diperlukan (L min)", f"{L_min:.3f} m")
        
        st.markdown("---")
        if L_weighted >= L_min:
            st.success("✅ **AMAN TERHADAP PIPING**")
            st.write(f"Karena $L_{{hitung}} ({L_weighted:.2f}) > L_{{min}} ({L_min:.2f})$")
        else:
            st.error("❌ **TIDAK AMAN (BAHAYA PIPING)**")
            st.write("Perpanjang lantai muka (apron) atau tambah kedalaman pondasi (koperan).")
            
        st.latex(r"L_{creep} = \Sigma L_v + \frac{1}{3}\Sigma L_h \geq C \cdot \Delta H")

# --- MODUL 3: INTAKE ---
elif menu == "3. Intake & Bagi Sadap":
    st.header("3. Perhitungan Bukaan Pintu")
    col1, col2 = st.columns(2)
    with col1:
        Q_rencana = st.number_input("Debit (Q) [m3/s]", value=0.164)
        B_pintu = st.number_input("Lebar Pintu (B) [m]", value=0.60)
        h_kehilangan = st.number_input("Kehilangan Tinggi (h/z) [m]", value=0.20)
        C_intu = 0.80
        g = 9.81
    with col2:
        if st.button("Hitung a"):
            a = Q_rencana / (C_intu * B_pintu * math.sqrt(2 * g * h_kehilangan))
            st.metric("Bukaan Pintu (a)", f"{a:.3f} m")

# --- MODUL 4: TERJUN & PEREDAM ENERGI (UPDATED) ---
elif menu == "4. Bangunan Terjun & Peredam Energi":
    st.header("4. Desain Peredam Energi (Kolam Olak)")
    st.info("Termasuk perhitungan kedalaman kritis (hc), hilir (t), dan ambang.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parameter Hidrolis")
        Q_terjun = st.number_input("Debit Desain (Q) [m3/s]", value=0.049)
        b_terjun = st.number_input("Lebar Saluran (b) [m]", value=0.15)
        z_drop = st.number_input("Tinggi Terjun (z) [m]", value=2.40)
        g = 9.81
        
    with col2:
        st.subheader("Dimensi Kolam Olak")
        if b_terjun > 0:
            # 1. Kedalaman Kritis (hc)
            q = Q_terjun / b_terjun
            hc = math.pow((q**2)/g, 1/3)
            
            # 2. Kedalaman Hilir (t) - Rumus PDF Hal 16
            # t = 3.0 * hc + 0.1 * z
            t = (3.0 * hc) + (0.1 * z_drop)
            
            # 3. Tinggi Ambang Ujung (a) / Baffle - Rumus PDF Hal 16 & 17
            # a = 0.28 * hc * sqrt(hc/z)
            try:
                a_ambang = 0.28 * hc * math.sqrt(hc / z_drop)
            except:
                a_ambang = 0
            
            # 4. Estimasi Panjang Kolam (L)
            # Biasanya L = 1.5 * Ludik (PDF Hal 17 sebut Lsayap = 1.5 * Ludik)
            # Atau L kolam ~ 5-6 kali hc (pendekatan umum jika tidak ada rumus spesifik di PDF)
            # Kita tampilkan variabel kuncinya saja
            
            st.metric("Kedalaman Kritis (hc)", f"{hc:.3f} m")
            st.metric("Kedalaman Air Hilir (t)", f"{t:.3f} m")
            st.metric("Tinggi Ambang (a)", f"{a_ambang:.3f} m")
            st.write(f"Estimasi dimensi ambang: ~{a_ambang*100:.1f} cm")
            
            st.markdown("**Referensi Rumus (PDF Hal 16):**")
            st.latex(r"t = 3.0 h_c + 0.1 z")
            st.latex(r"a = 0.28 h_c \sqrt{\frac{h_c}{z}}")
        else:
            st.error("Lebar saluran 0")
