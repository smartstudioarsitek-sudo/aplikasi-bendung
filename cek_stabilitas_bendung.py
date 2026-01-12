import streamlit as st
import math
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="Analisis Stabilitas Bendung", layout="wide")

st.title("🛡️ Analisis Stabilitas Bendung (Gravity Method)")
st.markdown("""
Aplikasi ini digunakan untuk mengontrol keamanan bendung terhadap:
1. **Guling (Overturning)**
2. **Geser (Sliding)**
3. **Eksentrisitas (Eccentricity)**
4. **Daya Dukung Tanah (Bearing Capacity)**
""")
st.info("Referensi Rumus: Laporan Penunjang Buku II (Bab 4)")

# --- 1. SIDEBAR: INPUT PARAMETER TANAH & DIMENSI ---
with st.sidebar:
    st.header("1. Parameter Tanah & Dimensi")
    
    # [cite_start]Dimensi Dasar [cite: 263, 288]
    B = st.number_input("Lebar Dasar Bendung (B) [m]", value=1.30, step=0.1)
    Df = st.number_input("Kedalaman Pondasi (Df) [m]", value=3.0, step=0.5)
    
    st.markdown("---")
    st.write("**Data Tanah:**")
    # [cite_start]Data Tanah [cite: 247-251, 282-293]
    gamma_tanah = st.number_input("Berat Jenis Tanah (γ) [t/m3]", value=1.813, format="%.3f")
    phi = st.number_input("Sudut Geser Dalam (φ) [deg]", value=42.5)
    c = st.number_input("Kohesi (c) [t/m2]", value=0.142, format="%.3f")
    
    st.markdown("---")
    st.write("**Faktor Terzaghi (Untuk Daya Dukung):**")
    # [cite_start]Faktor Terzaghi [cite: 290-293]
    Nc = st.number_input("Nc", value=95.0)
    Nq = st.number_input("Nq", value=90.0)
    Ngamma = st.number_input("Ngamma", value=160.0)

# --- 2. MAIN AREA: INPUT GAYA ---
st.header("2. Input Gaya-Gaya (Rekapitulasi)")
st.caption("Masukkan hasil rekapitulasi gaya dari Tabel 4.3 (Kondisi Normal) atau Tabel 4.5 (Kondisi Banjir).")

col_kondisi, col_dummy = st.columns(2)
with col_kondisi:
    kondisi = st.radio("Kondisi Tinjauan:", ["Air Normal (M.A.N)", "Air Banjir (M.A.B)"], horizontal=True)

# [cite_start]Set Default Value berdasarkan PDF agar Kakak mudah cek [cite: 238-246, 345-355]
if kondisi == "Air Normal (M.A.N)":
    def_V_tahan = 36.37
    def_V_angkat = 4.19
    def_H = 10.28
    def_Mt = 65.76
    def_Mg = 41.77
else: # Banjir
    def_V_tahan = 40.47
    def_V_angkat = 10.38
    def_H = 7.69
    def_Mt = 99.94
    def_Mg = 61.68

col1, col2 = st.columns(2)

with col1:
    st.subheader("Gaya Vertikal & Horizontal")
    Sigma_V_tahan = st.number_input("ΣV Penahan (Berat Sendiri + Air) [ton]", value=def_V_tahan)
    Sigma_V_angkat = st.number_input("ΣV Angkat (Uplift) [ton]", value=def_V_angkat)
    Sigma_H = st.number_input("ΣH Gaya Horizontal Total [ton]", value=def_H)
    
    # Hitung V Efektif
    V_eff = Sigma_V_tahan - Sigma_V_angkat
    st.info(f"ΣV Efektif (V_tahan - V_uplift) = **{V_eff:.2f} ton**")

with col2:
    st.subheader("Momen")
    Sigma_M_tahan = st.number_input("Σ Momen Penahan (MT) [tm]", value=def_Mt)
    Sigma_M_guling = st.number_input("Σ Momen Guling (MG) [tm]", value=def_Mg)
    
    # Hitung Momen Netto
    M_net = Sigma_M_tahan - Sigma_M_guling
    st.info(f"Σ Momen Netto (MT - MG) = **{M_net:.2f} tm**")

st.markdown("---")

# --- 3. HASIL ANALISIS ---
if st.button("RUN ANALISIS STABILITAS", type="primary"):
    st.header("3. Hasil Perhitungan Safety Factor")
    
    # [cite_start]A. CEK GULING (OVERTURNING) [cite: 239, 348]
    st.subheader("A. Kontrol Guling")
    try:
        SF_guling = Sigma_M_tahan / Sigma_M_guling
    except ZeroDivisionError:
        SF_guling = 0
        
    col_g1, col_g2 = st.columns([1, 3])
    with col_g1:
        st.metric("SF Guling", f"{SF_guling:.2f}")
    with col_g2:
        if SF_guling >= 1.5:
            st.success("✅ **AMAN** (SF > 1.5)")
        else:
            st.error("❌ **TIDAK AMAN** (SF < 1.5)")
        st.latex(r"SF = \frac{\Sigma M_{tahan}}{\Sigma M_{guling}}")

    # [cite_start]B. CEK GESER (SLIDING) [cite: 259-260]
    st.subheader("B. Kontrol Geser")
    tan_phi = math.tan(math.radians(phi))
    
    # Rumus Gaya Tahan Geser: (V_eff * tan_phi) + (c * B)
    # Note: Di PDF Kakak (Hal 7) rumusnya sedikit unik menggunakan faktor 'f', 
    # tapi disini kita gunakan rumus umum teknik sipil (Mohr-Coulomb) yang lebih standard & aman.
    Gaya_Gesek = (V_eff * tan_phi) + (c * B)
    
    try:
        SF_geser = Gaya_Gesek / Sigma_H
    except ZeroDivisionError:
        SF_geser = 0
        
    col_s1, col_s2 = st.columns([1, 3])
    with col_s1:
        st.metric("SF Geser", f"{SF_geser:.2f}")
    with col_s2:
        if SF_geser >= 1.5:
            st.success("✅ **AMAN** (SF > 1.5)")
        else:
            st.error("❌ **TIDAK AMAN** (SF < 1.5)")
        st.write(f"Gaya Penahan Geser: {Gaya_Gesek:.2f} ton")
        st.latex(r"SF = \frac{(\Sigma V - U)\tan\phi + c \cdot B}{\Sigma H}")

    # [cite_start]C. EKSENTRISITAS [cite: 270, 380]
    st.subheader("C. Kontrol Eksentrisitas (e)")
    try:
        e = abs((M_net / V_eff) - (B / 2))
    except ZeroDivisionError:
        e = 0
        
    batas_kern = B / 6
    
    col_e1, col_e2 = st.columns([1, 3])
    with col_e1:
        st.metric("Nilai e", f"{e:.3f} m")
        st.caption(f"Batas Izin (B/6): {batas_kern:.3f} m")
    with col_e2:
        if e <= batas_kern:
            st.success("✅ **AMAN** (Resultante gaya masuk daerah inti / Kern)")
        else:
            st.warning("⚠️ **TIDAK AMAN** (Terjadi tegangan tarik pada pondasi)")
        st.latex(r"e = \left| \frac{\Sigma M_{net}}{\Sigma V} - \frac{B}{2} \right|")

    # [cite_start]D. DAYA DUKUNG TANAH [cite: 295-301]
    st.subheader("D. Kontrol Daya Dukung Tanah")
    
    # 1. Lebar Efektif (Meyerhof)
    B_eff = B - (2 * e)
    
    # 2. Daya Dukung Ultimit (q_ult)
    # Rumus Terzaghi Umum untuk Pondasi Menerus
    # q_ult = c.Nc + gamma.Df.Nq + 0.5.gamma.B'.Ngamma
    # Di PDF Hal 8 menggunakan (Nq-1) untuk surcharge term, kita ikuti PDF:
    term_c = c * Nc
    term_q = gamma_tanah * Df * (Nq - 1)
    term_gamma = 0.5 * gamma_tanah * B_eff * Ngamma
    
    q_ult = term_c + term_q + term_gamma
    
    # 3. Tegangan Ijin
    FS_tanah = 3.0 if kondisi == "Air Normal (M.A.N)" else 2.5 # Biasanya saat banjir FS boleh turun sedikit
    sigma_ijin = q_ult / FS_tanah
    
    # 4. Tegangan Terjadi (Sigma Max)
    # Sigma_max = V/B * (1 + 6e/B)
    sigma_max = (V_eff / B) * (1 + (6 * e / B))
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write("**Kapasitas Tanah:**")
        st.write(f"Lebar Efektif ($B'$): {B_eff:.3f} m")
        st.write(f"Daya Dukung Ultimit ($q_{{ult}}$): {q_ult:.2f} t/m2")
        st.metric("Tegangan Ijin Tanah", f"{sigma_ijin:.2f} t/m2")
        
    with col_d2:
        st.write("**Tegangan Terjadi:**")
        st.metric("Tegangan Maksimum", f"{sigma_max:.2f} t/m2")
        
        if sigma_max <= sigma_ijin:
            st.success("✅ **AMAN** (σ max < σ ijin)")
        else:
            st.error("❌ **TIDAK AMAN** (Tanah Runtuh)")

    st.markdown("---")
    
    # Tampilkan Tabel Ringkasan
    summary_data = {
        "Parameter": ["Guling (SF)", "Geser (SF)", "Eksentrisitas (e)", "Daya Dukung Tanah"],
        "Nilai": [f"{SF_guling:.2f}", f"{SF_geser:.2f}", f"{e:.3f} m", f"{sigma_max:.2f} t/m2"],
        "Batas Izin": [">= 1.5", ">= 1.5", f"<= {batas_kern:.3f} m", f"<= {sigma_ijin:.2f} t/m2"],
        "Status": ["AMAN" if SF_guling >=1.5 else "BAHAYA", 
                   "AMAN" if SF_geser >=1.5 else "BAHAYA",
                   "AMAN" if e <= batas_kern else "WARNING",
                   "AMAN" if sigma_max <= sigma_ijin else "BAHAYA"]
    }
    st.table(pd.DataFrame(summary_data))