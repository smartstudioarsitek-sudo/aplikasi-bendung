import streamlit as st
import math

st.set_page_config(page_title="Analisis Stabilitas Bendung", layout="wide")
st.title("🛡️ Cek Stabilitas (Guling, Geser, Tanah)")

with st.sidebar:
    st.header("Input Parameter Tanah")
    B = st.number_input("Lebar Dasar (B) [m]", value=1.3)
    phi = st.number_input("Sudut Geser (φ) [deg]", value=42.5)
    C = st.number_input("Kohesi (c) [t/m2]", value=0.142)
    
    st.header("Input Gaya (Rekapitulasi)")
    # Default angka dari PDF Hal 7 (Kondisi Normal)
    Sigma_V_tahan = st.number_input("ΣV Penahan (Berat) [ton]", value=36.37)
    Sigma_V_angkat = st.number_input("ΣV Angkat (Uplift) [ton]", value=4.19)
    Sigma_H = st.number_input("ΣH Dorong Total [ton]", value=10.28)
    Sigma_M_tahan = st.number_input("Σ Momen Tahan [tm]", value=65.76)
    Sigma_M_guling = st.number_input("Σ Momen Guling [tm]", value=41.77)

# PERHITUNGAN
st.header("Hasil Analisis Safety Factor")

# 1. Guling
SF_guling = Sigma_M_tahan / Sigma_M_guling if Sigma_M_guling != 0 else 0
st.metric("SF Guling (Ijin > 1.5)", f"{SF_guling:.2f}", delta="Aman" if SF_guling>1.5 else "Bahaya")

# 2. Geser
V_eff = Sigma_V_tahan - Sigma_V_angkat
tan_phi = math.tan(math.radians(phi))
H_tahan = (V_eff * tan_phi) + (C * B)
SF_geser = H_tahan / Sigma_H if Sigma_H != 0 else 0
st.metric("SF Geser (Ijin > 1.5)", f"{SF_geser:.2f}", delta="Aman" if SF_geser>1.5 else "Bahaya")

# 3. Eksentrisitas
M_net = Sigma_M_tahan - Sigma_M_guling
e = abs((M_net / V_eff) - (B/2)) if V_eff != 0 else 0
limit = B/6
st.metric("Eksentrisitas (e)", f"{e:.3f} m")
if e <= limit:
    st.success(f"✅ OK (e < B/6 = {limit:.3f} m)")
else:
    st.warning(f"⚠️ Warning (e > {limit:.3f} m)")

# 4. Tegangan Tanah (Daya Dukung)
sigma_max = (V_eff / B) * (1 + (6*e/B))
st.metric("Tegangan Tanah Max", f"{sigma_max:.2f} t/m2")
