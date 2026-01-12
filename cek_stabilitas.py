import streamlit as st
import pandas as pd
import math

# Konfigurasi Halaman
st.set_page_config(page_title="Analisis Stabilitas Bendung", layout="wide")

st.title("🛡️ Modul Analisis Stabilitas Bendung")
st.markdown("Verifikasi keamanan terhadap **Guling, Geser, Eksentrisitas,** dan **Daya Dukung Tanah** berdasarkan *Metode Gravitasi*.")

# --- SIDEBAR: INPUT DATA ---
with st.sidebar:
    st.header("1. Parameter Desain")
    kondisi = st.selectbox("Kondisi Tinjauan", ["Air Normal (M.A.N)", "Air Banjir (M.A.B)"])
    
    st.subheader("Dimensi & Tanah")
    # Default values diambil dari PDF Hal 7 & 8
    B = st.number_input("Lebar Dasar Bendung (B) [m]", value=1.30, step=0.1)
    phi = st.number_input("Sudut Geser Dalam (φ) [deg]", value=42.5)
    C = st.number_input("Kohesi Tanah (c) [ton/m2]", value=0.142, format="%.4f")
    gamma_tanah = st.number_input("Berat Jenis Tanah (γ) [ton/m3]", value=1.813, format="%.3f")
    Df = st.number_input("Kedalaman Pondasi (Df) [m]", value=3.0)
    
    st.subheader("Faktor Terzaghi (Otomatis/Manual)")
    # Default dari PDF Hal 8 [cite: 289-292]
    Nc = st.number_input("Nc", value=95.0)
    Nq = st.number_input("Nq", value=90.0)
    Ngamma = st.number_input("Ngamma", value=160.0)

# --- MAIN CONTENT ---
st.header(f"Input Gaya-Gaya: Kondisi {kondisi}")
st.info("Masukkan total gaya berdasarkan Tabel Perhitungan Gaya (Tabel 4.3 / 4.5).")

col_in1, col_in2 = st.columns(2)

with col_in1:
    st.subheader("A. Gaya Vertikal (Ton)")
    # Input Total Gaya Vertikal ke Bawah (Berat Sendiri + Air di atas bendung)
    sigma_V_bawah = st.number_input("ΣV Tahan (Berat + Air) [ton]", 
                                    value=36.37 if kondisi == "Air Normal (M.A.N)" else 40.47)
    
    # Input Gaya Angkat (Uplift)
    sigma_V_atas = st.number_input("ΣV Angkat (Uplift) [ton]", 
                                   value=4.19 if kondisi == "Air Normal (M.A.N)" else 10.38)
    
    # Hitung V Netto
    V_net = sigma_V_bawah - sigma_V_atas
    st.metric("ΣV Netto (Vb - Va)", f"{V_net:.2f} ton")

with col_in2:
    st.subheader("B. Gaya Horizontal & Momen")
    # Input Total Gaya Horizontal (Tekanan Air + Gempa + Lumpur)
    sigma_H = st.number_input("ΣH Dorong (Air + Gempa) [ton]", 
                              value=10.28 if kondisi == "Air Normal (M.A.N)" else 7.69)
    
    st.markdown("---")
    # Input Momen
    sigma_M_tahan = st.number_input("Σ Momen Penahan (MT) [ton.m]", 
                                    value=65.76 if kondisi == "Air Normal (M.A.N)" else 99.94)
    sigma_M_guling = st.number_input("Σ Momen Guling (MG) [ton.m]", 
                                     value=41.77 if kondisi == "Air Normal (M.A.N)" else 61.68)

st.markdown("---")
st.header("📊 Hasil Analisis Stabilitas")

# 1. CEK GULING (OVERTURNING)
st.subheader("1. Stabilitas Terhadap Guling")
col_g1, col_g2 = st.columns([1, 2])
with col_g1:
    SF_guling = sigma_M_tahan / sigma_M_guling if sigma_M_guling != 0 else 0
    st.metric("Safety Factor (SF) Guling", f"{SF_guling:.2f}")
with col_g2:
    if SF_guling > 1.5:
        st.success(f"✅ AMAN (SF > 1.5). Sesuai referensi PDF Hal 7[cite: 239].")
    else:
        st.error(f"❌ TIDAK AMAN (SF < 1.5). Perbesar dimensi tubuh bendung.")
    st.latex(r"SF = \frac{\Sigma M_{tahan}}{\Sigma M_{guling}}")

# 2. CEK GESER (SLIDING)
st.subheader("2. Stabilitas Terhadap Geser")
col_s1, col_s2 = st.columns([1, 2])
with col_s1:
    tan_phi = math.tan(math.radians(phi))
    # Rumus Standar: (V_net * tan_phi + c * B) / H
    # Note: Di PDF Hal 7[cite: 258], rumus agak berbeda, tapi kita gunakan rumus umum teknik sipil yang lebih konservatif/standar.
    Gaya_gesek = (V_net * tan_phi) + (C * B)
    SF_geser = Gaya_gesek / sigma_H if sigma_H != 0 else 0
    st.metric("Safety Factor (SF) Geser", f"{SF_geser:.2f}")
with col_s2:
    if SF_geser > 1.5:
        st.success("✅ AMAN (SF > 1.5).")
    else:
        st.error("❌ TIDAK AMAN (SF < 1.5). Cek lantai muka atau tambah gigi geligi.")
    
    st.write(f"**Detail Perhitungan:**")
    st.write(f"Tan φ = {tan_phi:.3f}")
    st.write(f"Gaya Penahan Geser = ({V_net:.2f} × {tan_phi:.3f}) + ({C} × {B}) = {Gaya_gesek:.2f} ton")
    st.latex(r"SF = \frac{\Sigma V \cdot \tan\phi + c \cdot B}{\Sigma H}")

# 3. EKSENTRISITAS (ECCENTRICITY)
st.subheader("3. Kontrol Eksentrisitas (e)")
col_e1, col_e2 = st.columns([1, 2])
with col_e1:
    M_sisa = sigma_M_tahan - sigma_M_guling
    if V_net != 0:
        e = abs((M_sisa / V_net) - (B / 2))
    else:
        e = 0
    st.metric("Eksentrisitas (e)", f"{e:.3f} m")
    
    batas_kern = B / 6
    st.write(f"Batas Kern (B/6): {batas_kern:.3f} m")

with col_e2:
    if e <= batas_kern:
        st.success("✅ OK (Resultante gaya masuk daerah Kern/Inti).")
    else:
        st.warning("⚠️ WARNING (Terjadi tegangan tarik). Bahaya guling meningkat.")
    st.latex(r"e = \left| \frac{\Sigma M_{net}}{\Sigma V} - \frac{B}{2} \right| \le \frac{B}{6}")

# 4. DAYA DUKUNG TANAH (BEARING CAPACITY)
st.subheader("4. Daya Dukung Tanah (Metode Terzaghi)")
# Hitung Lebar Efektif (Meyerhof) seperti di PDF Hal 8 
B_eff = B - (2 * e)

# Kapasitas Dukung Ultimit (q_ult)
# Rumus PDF Hal 8[cite: 294]: q_ult = c.Nc + gamma.Df(Nq-1) + 0.5.gamma.B'.Ngamma
# Note: PDF menggunakan (Nq-1) untuk surcharge, ini pendekatan umum untuk fondasi dangkal
q_ult = (C * Nc) + (gamma_tanah * Df * (Nq - 1)) + (0.5 * gamma_tanah * B_eff * Ngamma)

# Tegangan Ijin (sigma_ijin) - FS Tanah biasanya 3, tapi di PDF digunakan angka calculated
# PDF Hal 8 [cite: 296] menghitung tegangan ijin = q_ult / FS.
FS_tanah = st.number_input("Safety Factor Tanah (FS)", value=2.5 if kondisi == "Air Banjir (M.A.B)" else 3.0) 
sigma_ijin = q_ult / FS_tanah

# Tegangan Yang Terjadi (sigma_max)
sigma_max = (V_net / B) * (1 + (6 * e / B))
sigma_min = (V_net / B) * (1 - (6 * e / B))

col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    st.metric("Tegangan Ijin Tanah", f"{sigma_ijin:.2f} ton/m2")
    st.caption(f"q_ult: {q_ult:.2f} t/m2")
with col_d2:
    st.metric("Tegangan Max Terjadi", f"{sigma_max:.2f} ton/m2")
with col_d3:
    if sigma_max < sigma_ijin:
        st.success("✅ AMAN (σ max < σ ijin)")
    else:
        st.error("❌ GAGAL (Tanah runtuh)")

st.write("**Distribusi Tegangan Dasar:**")
st.latex(r"\sigma_{max/min} = \frac{\Sigma V}{B} \left( 1 \pm \frac{6e}{B} \right)")

st.markdown("---")
st.caption("Referensi Rumus: Laporan Penunjang Buku II (DI Tambah Luhur) Bab 4.")