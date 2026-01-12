import streamlit as st
import math
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Desain Irigasi Terpadu", layout="wide", initial_sidebar_state="expanded")

# --- HEADER APLIKASI ---
st.title("🏗️ Sistem Desain Irigasi Terpadu")
st.markdown("""
**Referensi Desain:** Laporan Penunjang Buku II (DI Tambah Luhur)
*Mencakup: Hidrolika Bendung, Stabilitas, Bangunan Bagi Sadap, dan Terjunan.*
""")
st.markdown("---")

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.header("🗂️ Menu Navigasi")
    pilihan_modul = st.radio(
        "Pilih Modul Perhitungan:",
        [
            "1. Hidrolika Bendung & Rembesan",
            "2. Cek Stabilitas Bendung",
            "3. Bangunan Bagi Sadap",
            "4. Bangunan Terjun (Drop Structure)"
        ]
    )
    st.info("Gunakan menu di atas untuk berpindah antar modul perhitungan.")

# ==============================================================================
# MODUL 1: HIDROLIKA BENDUNG & REMBESAN
# ==============================================================================
if pilihan_modul == "1. Hidrolika Bendung & Rembesan":
    st.header("1. Hidrolika Bendung & Kontrol Rembesan")
    
    tab1, tab2 = st.tabs(["Hidrolika Mercu", "Kontrol Rembesan (Lane)"])
    
    with tab1:
        st.subheader("A. Dimensi & Debit (Ref: Hal 3)")
        col1, col2 = st.columns(2)
        with col1:
            Bn = st.number_input("Lebar Total Bendung (B) [m]", value=11.0)
            n_pilar = st.number_input("Jumlah Pilar", value=1.0)
            t_pilar = st.number_input("Tebal Pilar [m]", value=0.5)
            Q_banjir = st.number_input("Debit Banjir (Q50) [m3/s]", value=39.59)
        with col2:
            Cd = st.number_input("Koefisien Debit (Cd)", value=1.45)
            Ho_asumsi = st.number_input("Tinggi Energi Asumsi (Ho) [m]", value=1.0)
            Kp = 0.01
            Ka = 0.10
            
        if st.button("Hitung Hidrolika"):
            beff = Bn - (n_pilar * t_pilar) - 1.0 - (2 * (n_pilar * Kp + Ka) * Ho_asumsi)
            st.metric("Lebar Efektif (Beff)", f"{beff:.3f} m")
            
            # Rumus Q = Cd * 2/3 * sqrt(2/3g) * Beff * He^1.5
            g = 9.81
            const = (2/3) * math.sqrt((2/3)*g)
            try:
                He = (Q_banjir / (Cd * const * beff))**(2/3)
                st.success(f"Tinggi Muka Air Banjir (He): {He:.3f} m")
                st.latex(r"Q = C_d \times \frac{2}{3}\sqrt{\frac{2}{3}g} \times B_{eff} \times H_e^{1.5}")
            except:
                st.error("Cek input dimensi")

    with tab2:
        st.subheader("B. Kontrol Rembesan (Ref: Hal 4)")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            Lv = st.number_input("Total Rayapan Vertikal (Lv) [m]", value=12.6)
            Lh = st.number_input("Total Rayapan Horizontal (Lh) [m]", value=17.0)
            DeltaH = st.number_input("Beda Tinggi Air (ΔH) [m]", value=2.516)
        with col_r2:
            C_lane = st.number_input("Angka Rembesan Lane (C)", value=4.0, help="Lempung Lunak=4, Pasir=7")
            
        L_weighted = Lv + (1/3 * Lh)
        L_min = C_lane * DeltaH
        
        st.metric("Panjang Rayapan (L weighted)", f"{L_weighted:.2f} m")
        st.metric("Syarat Minimum (C * ΔH)", f"{L_min:.2f} m")
        
        if L_weighted > L_min:
            st.success("✅ AMAN Terhadap Piping")
        else:
            st.error("❌ TIDAK AMAN (Perbesar lantai muka)")

# ==============================================================================
# MODUL 2: STABILITAS BENDUNG
# ==============================================================================
elif pilihan_modul == "2. Cek Stabilitas Bendung":
    st.header("2. Analisis Stabilitas Tubuh Bendung")
    st.markdown("Analisis Guling, Geser, Eksentrisitas, dan Daya Dukung (Ref: Hal 6-10).")
    
    col_input, col_hasil = st.columns([1, 2])
    
    with col_input:
        st.subheader("Input Gaya Rekapitulasi")
        kondisi = st.selectbox("Kondisi", ["Air Normal (M.A.N)", "Banjir (M.A.B)"])
        
        # Default value conditional logic
        def_V = 36.37 if kondisi == "Air Normal (M.A.N)" else 40.47
        def_U = 4.19 if kondisi == "Air Normal (M.A.N)" else 10.38
        def_H = 10.28 if kondisi == "Air Normal (M.A.N)" else 7.69
        def_Mt = 65.76 if kondisi == "Air Normal (M.A.N)" else 99.94
        def_Mg = 41.77 if kondisi == "Air Normal (M.A.N)" else 61.68
        
        V_tahan = st.number_input("ΣV Penahan (Berat) [ton]", value=def_V)
        V_angkat = st.number_input("ΣV Angkat (Uplift) [ton]", value=def_U)
        H_dorong = st.number_input("ΣH Dorong Total [ton]", value=def_H)
        M_tahan = st.number_input("Σ Momen Tahan [tm]", value=def_Mt)
        M_guling = st.number_input("Σ Momen Guling [tm]", value=def_Mg)
        
        st.markdown("---")
        st.caption("Parameter Tanah")
        B_dasar = st.number_input("Lebar Dasar (B) [m]", value=1.3)
        phi = st.number_input("Sudut Geser (deg)", value=42.5)
        c_tanah = st.number_input("Kohesi (c) [t/m2]", value=0.142)

    with col_hasil:
        st.subheader("Hasil Analisis Safety Factor (SF)")
        
        # 1. GULING
        sf_guling = M_tahan / M_guling if M_guling != 0 else 0
        st.write(f"**1. Guling:** SF = {sf_guling:.2f}")
        if sf_guling > 1.5:
            st.success("✅ AMAN (SF > 1.5)")
        else:
            st.error("❌ BAHAYA GULING")

        # 2. GESER
        V_eff = V_tahan - V_angkat
        tan_phi = math.tan(math.radians(phi))
        H_res = (V_eff * tan_phi) + (c_tanah * B_dasar)
        sf_geser = H_res / H_dorong if H_dorong != 0 else 0
        st.write(f"**2. Geser:** SF = {sf_geser:.2f}")
        if sf_geser > 1.5:
            st.success("✅ AMAN (SF > 1.5)")
        else:
            st.error("❌ BAHAYA GESER")

        # 3. EKSENTRISITAS
        e = abs(((M_tahan - M_guling) / V_eff) - (B_dasar / 2))
        limit_e = B_dasar / 6
        st.write(f"**3. Eksentrisitas:** e = {e:.3f} m (Batas B/6 = {limit_e:.3f} m)")
        if e <= limit_e:
            st.success("✅ OK (Masuk daerah inti)")
        else:
            st.warning("⚠️ TERJADI TEGANGAN TARIK")

# ==============================================================================
# MODUL 3: BANGUNAN BAGI SADAP
# ==============================================================================
elif pilihan_modul == "3. Bangunan Bagi Sadap":
    st.header("3. Perhitungan Pintu Bangunan Bagi Sadap")
    st.info("Menghitung bukaan pintu ($a$) berdasarkan Skema Irigasi (Ref: Hal 14-15).")
    
    col_bs1, col_bs2 = st.columns(2)
    
    with col_bs1:
        st.subheader("Data Pintu")
        nama_bangunan = st.text_input("Nama Bangunan", "Sadap S.TL.1")
        # Contoh default S.TL.1 
        Q_sadap = st.number_input("Debit Rencana (Q) [m3/s]", value=0.160, format="%.4f")
        B_pintu = st.number_input("Lebar Pintu (B) [m]", value=0.40)
        h_loss = st.number_input("Kehilangan Energi (h/z) [m]", value=0.10)
        C_pintu = st.number_input("Koefisien Debit (C)", value=0.80)
        
    with col_bs2:
        st.subheader("Hasil Perhitungan")
        if st.button("Hitung Bukaan Pintu"):
            g = 9.81
            try:
                # Rumus a = Q / (C * B * sqrt(2gh))
                a_buka = Q_sadap / (C_pintu * B_pintu * math.sqrt(2 * g * h_loss))
                
                st.metric("Tinggi Bukaan (a)", f"{a_buka:.3f} m")
                st.write(f"Atau setara **{a_buka*100:.1f} cm**")
                
                st.markdown("**Rumus (Hal 14):**")
                st.latex(r"a = \frac{Q}{C \cdot B \cdot \sqrt{2gh}}")
            except:
                st.error("Pastikan input tidak nol!")
                
    st.markdown("---")
    st.markdown("**Data Referensi Bangunan Sadap (Dari Laporan):**")
    ref_data = {
        "Bangunan": ["Sadap S.TL.1", "Tersier S.TL.1", "Sadap S.TL.2", "Tersier S.TL.2", "Sadap S.TL.3 Kanan"],
        "Q (m3/s)": [0.16, 0.005, 0.128, 0.032, 0.08],
        "Lebar B (m)": [0.4, 0.2, 0.4, 0.3, 0.4],
        "Head h (m)": [0.1, 0.05, 0.12, 0.045, 0.18]
    }
    st.dataframe(pd.DataFrame(ref_data))

# ==============================================================================
# MODUL 4: BANGUNAN TERJUN
# ==============================================================================
elif pilihan_modul == "4. Bangunan Terjun (Drop Structure)":
    st.header("4. Desain Bangunan Terjun")
    st.markdown("Perhitungan kedalaman kritis, kolam olak, dan ambang akhir (Ref: Hal 16-17).")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.subheader("Input Hidrolis Terjun")
        # Default value dari Hal 16 
        Q_terjun = st.number_input("Debit (Q) [m3/s]", value=0.049, format="%.4f")
        b_saluran = st.number_input("Lebar Saluran (b) [m]", value=0.15)
        z_drop = st.number_input("Tinggi Terjun (z) [m]", value=2.40)
        
    with col_t2:
        st.subheader("Hasil Desain Kolam Olak")
        g = 9.81
        if b_saluran > 0:
            # 1. Unit Discharge
            q = Q_terjun / b_saluran
            
            # 2. Kedalaman Kritis (hc) = (q^2 / g)^(1/3)
            hc = (q**2 / g)**(1/3)
            
            # 3. Kedalaman Hilir (t) = 3.0 hc + 0.1 z (Rumus Hal 16)
            t_hilir = (3.0 * hc) + (0.1 * z_drop)
            
            # 4. Tinggi Ambang (a) = 0.28 hc * sqrt(hc/z) (Rumus Hal 17)
            try:
                a_ambang = 0.28 * hc * math.sqrt(hc / z_drop)
            except:
                a_ambang = 0
            
            st.metric("Kedalaman Kritis (hc)", f"{hc:.3f} m")
            st.metric("Kedalaman Air Hilir (t)", f"{t_hilir:.3f} m")
            st.metric("Tinggi Ambang Ujung (a)", f"{a_ambang:.3f} m")
            
            st.info(f"**Kesimpulan:** Rencanakan ambang setinggi {a_ambang*100:.1f} cm untuk meredam energi terjunan setinggi {z_drop} m.")
            
            st.latex(r"h_c = \sqrt[3]{\frac{q^2}{g}}, \quad t = 3.0 h_c + 0.1 z")

st.markdown("---")
st.caption("Developed with Python Streamlit | Based on Laporan Penunjang Buku II")
