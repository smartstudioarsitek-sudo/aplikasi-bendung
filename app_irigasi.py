import streamlit as st
import pandas as pd
import numpy as np
import math
import io
import matplotlib.pyplot as plt

# Cek library tambahan untuk fitur ekspor (Excel/DXF)
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

# ==============================================================================
# KONFIGURASI HALAMAN (Wajib paling atas)
# ==============================================================================
st.set_page_config(page_title="Sistem Desain Irigasi Terpadu", layout="wide")

# ==============================================================================
# BAGIAN 1: FUNGSI LOGIKA (PERHITUNGAN)
# ==============================================================================

# --- A. LOGIKA USBR & TERJUNAN ---
def hitung_usbr(Q, B, y1, g=9.81):
    V1 = Q / (B * y1)
    Fr1 = V1 / np.sqrt(g * y1)
    y2 = 0.5 * y1 * (np.sqrt(1 + 8 * Fr1**2) - 1)
    
    tipe = "Unknown"; k = 0; hs = 0; catatan = ""

    if Fr1 < 1.7:
        tipe = "Aliran Undular"; catatan = "Loncatan tidak sempurna"; k = 4.0
    elif Fr1 < 2.5:
        tipe = "USBR I"; catatan = "Loncatan lemah"; k = 5.0
    elif Fr1 <= 4.5:
        tipe = "USBR IV"; catatan = "Loncatan berombang"; k = 6.0; hs = 0.1 * y2
    else:
        if V1 < 18.0:
            tipe = "USBR III"; catatan = "Efisien dengan blok"; k = 2.7; hs = 0.15 * y2
        else:
            tipe = "USBR II"; catatan = "Kecepatan tinggi"; k = 4.3; hs = 0.1 * y2

    return {
        "Tipe USBR": tipe, "Catatan": catatan, "Fr1": round(Fr1, 3),
        "Kecepatan V1": round(V1, 3), "y1 (m)": round(y1, 3), "y2 (m)": round(y2, 3),
        "Panjang Kolam": round(k * y2, 3), "End Sill": round(hs, 3),
        "Tebal Lantai": round(max(0.3, 0.25 * y2), 3)
    }

def hitung_bangunan_terjun(Q, B, H_total, H_max_tiap_terjun, mode_hemat=False, g=9.81):
    n_terjun = int(np.ceil(H_total / H_max_tiap_terjun))
    if n_terjun == 0: n_terjun = 1
    H_tiap = H_total / n_terjun

    q = Q / B
    yk = (q**2 / g) ** (1/3)
    V1 = np.sqrt(2 * g * H_tiap)
    y1 = q / V1
    
    data_usbr = hitung_usbr(Q, B, y1, g)
    
    drop_number = (q**2) / (g * H_tiap**3)
    L_drop = 4.30 * H_tiap * (drop_number ** 0.27)
    L_kolam_standard = data_usbr["Panjang Kolam"]
    
    is_hemat_active = mode_hemat and (H_tiap <= 1.2)
    if is_hemat_active:
        L_kolam_intermediate = 0.5; L_kolam_final = L_kolam_standard
        tipe_desain = "Mode Hemat (Kolam Hilir Saja)"
    else:
        L_kolam_intermediate = L_kolam_standard; L_kolam_final = L_kolam_standard
        tipe_desain = "Standard (Full USBR)"

    return {
        "Jumlah Terjun": n_terjun, "Tinggi Terjun per Tingkat (m)": round(H_tiap, 3),
        "Debit Persatuan Lebar (q)": round(q, 3), "Kedalaman Kritis yc (m)": round(yk, 3),
        "Kedalaman di Kaki (y1)": round(y1, 3), "Kedalaman Konjugasi (y2)": data_usbr.get("y2 (m)", 0),
        "Tipe Kolam": data_usbr["Tipe USBR"], "Desain Mode": tipe_desain,
        "Panjang Jatuhan Ld (m)": round(L_drop, 3),
        "Panjang Kolam Intermediate (m)": round(L_kolam_intermediate, 3),
        "Panjang Kolam Final (m)": round(L_kolam_final, 3),
        "Panjang Lantai Intermediate (m)": round(L_drop + L_kolam_intermediate, 3),
        "Panjang Lantai Final (m)": round(L_drop + L_kolam_final, 3),
        "Tinggi End Sill (m)": data_usbr["End Sill"]
    }

# --- B. CEK STABILITAS (TERJUNAN) ---
def cek_stabilitas_terjun(B, L, t, y1, y2, H_drop, qa=150, gamma_c=24, gamma_w=9.81):
    W_beton = L * B * t * gamma_c
    Vol_air = 0.5 * (y1 + y2) * L * B
    W_air   = Vol_air * gamma_w
    Total_Berat = W_beton + W_air
    Head_hulu_bawah_tanah = y2 + (0.5 * H_drop)
    Uplift_Force = 0.5 * (Head_hulu_bawah_tanah + y2) * L * B * gamma_w
    SF_uplift = Total_Berat / Uplift_Force if Uplift_Force > 0 else 99.0
    Tekanan_Netto = (Total_Berat - Uplift_Force) / (B * L)
    if Tekanan_Netto < 0: Tekanan_Netto = 0 
    return {
        "Berat Beton (kN)": round(W_beton, 2), "Gaya Uplift (kN)": round(Uplift_Force, 2),
        "SF Uplift": round(SF_uplift, 2), "Tekanan Tanah (kN/m2)": round(Tekanan_Netto, 2),
        "Aman Uplift": SF_uplift >= 1.5, "Aman Daya Dukung": Tekanan_Netto <= qa
    }

# --- C. FUNGSI GAMBAR ---
def gambar_potongan_bertingkat(n_terjun, H_total, H_drop, L_drop, L_kolam_inter, L_kolam_final, y1, y2, hs, yc):
    fig, ax = plt.subplots(figsize=(10, 6))
    curr_x = 0.0; curr_y_floor = float(H_total)
    ax.plot([-2, curr_x], [curr_y_floor, curr_y_floor], 'k-', lw=2)
    ax.plot([-2, curr_x], [curr_y_floor + yc, curr_y_floor + yc], 'b-', lw=1)
    for i in range(n_terjun):
        is_final = (i == n_terjun - 1)
        L_kolam_curr = L_kolam_final if is_final else L_kolam_inter
        x_bibir = curr_x; y_bibir = curr_y_floor
        y_lantai_bawah = y_bibir - H_drop
        x_akhir = x_bibir + L_drop + L_kolam_curr
        y_ambang = y_lantai_bawah + (hs if is_final else 0)
        ax.plot([x_bibir, x_bibir], [y_bibir, y_lantai_bawah], 'k-', lw=2)
        ax.plot([x_bibir, x_akhir], [y_lantai_bawah, y_lantai_bawah], 'k-', lw=2)
        ax.plot([x_akhir, x_akhir], [y_lantai_bawah, y_ambang], 'k-', lw=2)
        x_traj = np.linspace(x_bibir, x_bibir+L_drop, 20)
        y_traj = (y_bibir + yc) - ((H_drop + yc - y1) * ((x_traj - x_bibir) / L_drop)**2)
        ax.plot(x_traj, y_traj, 'b-', lw=1)
        ax.plot([x_bibir+L_drop, x_akhir], [y_lantai_bawah+y1, y_lantai_bawah+(y2 if is_final else y1)], 'b-', lw=1)
        curr_x = x_akhir + 0.5; curr_y_floor = y_ambang
        ax.plot([x_akhir, curr_x], [curr_y_floor, curr_y_floor], 'k-', lw=2)
    ax.plot([curr_x, curr_x+2], [curr_y_floor, curr_y_floor], 'k-', lw=2)
    ax.plot([curr_x, curr_x+2], [curr_y_floor+yc, curr_y_floor+yc], 'b--', lw=1)
    ax.set_title("Potongan Memanjang (Simplified)"); ax.grid(True, linestyle='--', alpha=0.5); ax.axis('equal')
    return fig

def gambar_denah_bertingkat(n_terjun, B, L_drop, L_kolam_inter, L_kolam_final):
    fig, ax = plt.subplots(figsize=(10, 4))
    half_B = B / 2.0; curr_x = 0.0
    ax.plot([-2, 0], [half_B, half_B], 'k-'); ax.plot([-2, 0], [-half_B, -half_B], 'k-')
    for i in range(n_terjun):
        is_final = (i == n_terjun - 1)
        L_curr = L_drop + (L_kolam_final if is_final else L_kolam_inter)
        x_akhir = curr_x + L_curr
        ax.plot([curr_x, x_akhir], [half_B, half_B], 'k-'); ax.plot([curr_x, x_akhir], [-half_B, -half_B], 'k-')
        ax.plot([curr_x, curr_x], [-half_B, half_B], 'k-'); ax.plot([x_akhir, x_akhir], [-half_B, half_B], 'k-')
        curr_x = x_akhir + 0.5
        ax.plot([x_akhir, curr_x], [half_B, half_B], 'k-'); ax.plot([x_akhir, curr_x], [-half_B, -half_B], 'k-')
    ax.plot([curr_x, curr_x+2], [half_B, half_B], 'k-'); ax.plot([curr_x, curr_x+2], [-half_B, -half_B], 'k-')
    ax.axis('equal'); ax.set_title("Denah Situasi"); return fig

def generate_dxf_potongan(n_terjun, H_total, H_drop, L_drop, L_kolam_inter, L_kolam_final, y1, y2, hs, yc):
    if not HAS_EZDXF: return None
    doc = ezdxf.new('R2010'); msp = doc.modelspace()
    curr_x = 0.0; curr_y = float(H_total)
    msp.add_lwpolyline([(-2, curr_y), (0, curr_y)])
    for i in range(n_terjun):
        is_final = (i == n_terjun-1)
        L_k = L_kolam_final if is_final else L_kolam_inter
        x_bibir = curr_x; y_floor = curr_y - H_drop; x_end = x_bibir + L_drop + L_k; y_ambang = y_floor + (hs if is_final else 0)
        msp.add_lwpolyline([(x_bibir, curr_y), (x_bibir, y_floor), (x_end, y_floor), (x_end, y_ambang)])
        curr_x = x_end + 0.5; curr_y = y_ambang
        msp.add_line((x_end, y_ambang), (curr_x, curr_y))
    msp.add_lwpolyline([(curr_x, curr_y), (curr_x+5, curr_y)])
    out = io.StringIO(); doc.write(out); return out.getvalue().encode('utf-8')

def generate_excel(input_dict, hasil, stabil):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(list(input_dict.items()), columns=["Input", "Val"]).to_excel(writer, sheet_name="Input")
        pd.DataFrame(list(hasil.items()), columns=["Hidrolis", "Val"]).to_excel(writer, sheet_name="Hidrolis")
        pd.DataFrame(list(stabil.items()), columns=["Stabilitas", "Val"]).to_excel(writer, sheet_name="Stabilitas")
    return output.getvalue()

# ==============================================================================
# BAGIAN 2: INTERFACE UTAMA
# ==============================================================================
st.title("🏗️ Sistem Desain Irigasi Terpadu")
st.markdown("---")

with st.sidebar:
    st.header("🗂️ Navigasi Modul")
    pilihan_modul = st.radio("Pilih Modul:", [
        "1. Hidrolika Bendung & Rembesan", 
        "2. Cek Stabilitas Bendung (Lengkap)", 
        "3. Bangunan Bagi Sadap", 
        "4. Bangunan Terjun (Pro Version)"
    ])
    st.divider()

# --- MODUL 1: BENDUNG ---
if pilihan_modul == "1. Hidrolika Bendung & Rembesan":
    st.header("1. Hidrolika & Rembesan Bendung")
    tab1, tab2 = st.tabs(["Hidrolika Mercu", "Kontrol Rembesan"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            Bn = st.number_input("Lebar Total (B)", value=11.0); Q_banjir = st.number_input("Debit Banjir (Q50)", value=39.59)
        with col2:
            Cd = st.number_input("Koef. Cd", value=1.45); beff = Bn - 1.5
            st.metric("Lebar Efektif Asumsi", f"{beff} m"); He = (Q_banjir / (Cd * 1.704 * beff))**(2/3)
            st.success(f"Tinggi Muka Air (He): {He:.3f} m")
    with tab2:
        Lv = st.number_input("Panjang Vertikal (Lv)", value=12.6); Lh = st.number_input("Panjang Horizontal (Lh)", value=17.0); dH = st.number_input("Beda Tinggi (dH)", value=2.516)
        L_weighted = Lv + (Lh/3); st.metric("L Weighted", f"{L_weighted:.2f} m")
        if L_weighted > (4 * dH): st.success("Aman Piping") 
        else: st.error("Bahaya Piping")

# --- MODUL 2: STABILITAS BENDUNG (LENGKAP) ---
elif pilihan_modul == "2. Cek Stabilitas Bendung (Lengkap)":
    st.header("2. Analisis Stabilitas Bendung (Gravity Method)")
    st.info("Termasuk kontrol: Guling, Geser, Eksentrisitas, & Daya Dukung Tanah.")

    # --- INPUT PARAMETER (DIPINDAHKAN DARI SIDEBAR KE MAIN BIAR RAPI) ---
    with st.expander("📝 1. Parameter Tanah & Dimensi (Klik untuk Edit)", expanded=False):
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            # Dimensi Dasar
            B_dasar = st.number_input("Lebar Dasar Bendung (B) [m]", value=1.30, step=0.1)
            Df = st.number_input("Kedalaman Pondasi (Df) [m]", value=3.0, step=0.5)
            # Data Tanah
            gamma_tanah = st.number_input("Berat Jenis Tanah (γ) [t/m3]", value=1.813, format="%.3f")
            phi = st.number_input("Sudut Geser Dalam (φ) [deg]", value=42.5)
            c_tanah = st.number_input("Kohesi (c) [t/m2]", value=0.142, format="%.3f")
        with c_t2:
            # Faktor Terzaghi
            st.write("**Faktor Terzaghi (Daya Dukung):**")
            Nc = st.number_input("Nc", value=95.0)
            Nq = st.number_input("Nq", value=90.0)
            Ngamma = st.number_input("Ngamma", value=160.0)

    # --- INPUT GAYA ---
    st.subheader("2. Input Gaya-Gaya (Rekapitulasi)")
    kondisi = st.radio("Kondisi Tinjauan:", ["Air Normal (M.A.N)", "Air Banjir (M.A.B)"], horizontal=True)

    # Default Value sesuai PDF
    if kondisi == "Air Normal (M.A.N)":
        def_Vt = 36.37; def_Va = 4.19; def_H = 10.28; def_Mt = 65.76; def_Mg = 41.77
    else: 
        def_Vt = 40.47; def_Va = 10.38; def_H = 7.69; def_Mt = 99.94; def_Mg = 61.68

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        Sigma_V_tahan = st.number_input("ΣV Penahan (Berat + Air) [ton]", value=def_Vt)
        Sigma_V_angkat = st.number_input("ΣV Angkat (Uplift) [ton]", value=def_Va)
        Sigma_H = st.number_input("ΣH Gaya Horizontal Total [ton]", value=def_H)
        V_eff = Sigma_V_tahan - Sigma_V_angkat
        st.caption(f"ΣV Efektif = {V_eff:.2f} ton")
    with col_g2:
        Sigma_M_tahan = st.number_input("Σ Momen Penahan (MT) [tm]", value=def_Mt)
        Sigma_M_guling = st.number_input("Σ Momen Guling (MG) [tm]", value=def_Mg)
        M_net = Sigma_M_tahan - Sigma_M_guling
        st.caption(f"Σ Momen Netto = {M_net:.2f} tm")

    # --- HASIL ANALISIS ---
    st.divider()
    st.subheader("3. Hasil Safety Factor")
    
    # 1. GULING
    SF_guling = Sigma_M_tahan / Sigma_M_guling if Sigma_M_guling != 0 else 0
    # 2. GESER
    tan_phi = math.tan(math.radians(phi))
    Gaya_Gesek = (V_eff * tan_phi) + (c_tanah * B_dasar)
    SF_geser = Gaya_Gesek / Sigma_H if Sigma_H != 0 else 0
    # 3. EKSENTRISITAS
    e = abs((M_net / V_eff) - (B_dasar / 2)) if V_eff != 0 else 0
    limit_e = B_dasar / 6
    # 4. DAYA DUKUNG
    B_eff_tanah = B_dasar - (2 * e)
    q_ult = (c_tanah * Nc) + (gamma_tanah * Df * (Nq - 1)) + (0.5 * gamma_tanah * B_eff_tanah * Ngamma)
    FS_tanah = 3.0 if kondisi == "Air Normal (M.A.N)" else 2.5
    sigma_ijin = q_ult / FS_tanah
    sigma_max = (V_eff / B_dasar) * (1 + (6 * e / B_dasar)) if B_dasar != 0 else 0

    # Display Grid
    c_out1, c_out2, c_out3, c_out4 = st.columns(4)
    with c_out1:
        st.metric("1. Guling (SF)", f"{SF_guling:.2f}", delta="Min 1.5")
        if SF_guling < 1.5: st.error("TIDAK AMAN")
    with c_out2:
        st.metric("2. Geser (SF)", f"{SF_geser:.2f}", delta="Min 1.5")
        if SF_geser < 1.5: st.error("TIDAK AMAN")
    with c_out3:
        st.metric("3. Eksentrisitas", f"{e:.3f} m")
        st.caption(f"Izin: < {limit_e:.3f} m")
        if e > limit_e: st.warning("Retak (Tarik)")
    with c_out4:
        st.metric("4. Tegangan Tanah", f"{sigma_max:.2f} t/m2")
        st.caption(f"Izin: {sigma_ijin:.2f}")
        if sigma_max > sigma_ijin: st.error("Runtuh")
        else: st.success("OK")

# --- MODUL 3: BAGI SADAP ---
elif pilihan_modul == "3. Bangunan Bagi Sadap":
    st.header("3. Pintu Bagi Sadap")
    Q = st.number_input("Debit (Q)", value=0.16); B = st.number_input("Lebar Pintu (B)", value=0.4); h = st.number_input("Kehilangan Tinggi (z)", value=0.1)
    if st.button("Hitung Bukaan"):
        a = Q / (0.8 * B * math.sqrt(2*9.81*h))
        st.metric("Bukaan Pintu (a)", f"{a:.3f} m")

# --- MODUL 4: TERJUNAN PRO ---
elif pilihan_modul == "4. Bangunan Terjun (Pro Version)":
    st.header("4. Desain Bangunan Terjun Bertingkat")
    with st.sidebar:
        st.markdown("### ⚙️ Input Terjunan")
        Q_terjun = st.number_input("Debit (Q) m3/s", value=1.5); B_terjun = st.number_input("Lebar (B) m", value=2.0)
        H_total = st.number_input("Total Tinggi Terjun (m)", value=3.5); H_max = st.number_input("Tinggi Max per Trap (m)", value=1.5)
        mode_hemat = st.checkbox("Mode Hemat (Kolam Pendek)", value=True); t_lantai = st.number_input("Tebal Lantai (m)", value=0.5)
        btn_hitung = st.button("🚀 Hitung Terjunan", type="primary")

    if btn_hitung or 'hasil_terjun' in st.session_state:
        if btn_hitung:
            hasil = hitung_bangunan_terjun(Q_terjun, B_terjun, H_total, H_max, mode_hemat)
            L_stabil = hasil["Panjang Lantai Final (m)"] - hasil["Panjang Jatuhan Ld (m)"]
            stabil = cek_stabilitas_terjun(B_terjun, L_stabil, t_lantai, hasil["Kedalaman di Kaki (y1)"], hasil["Kedalaman Konjugasi (y2)"], hasil["Tinggi Terjun per Tingkat (m)"])
            st.session_state['hasil_terjun'] = hasil; st.session_state['stabil_terjun'] = stabil; st.session_state['input_terjun'] = {"Q": Q_terjun, "B": B_terjun, "H": H_total}

        res = st.session_state['hasil_terjun']; stab = st.session_state['stabil_terjun']
        t1, t2, t3 = st.tabs(["📊 Visualisasi", "📑 Data & Stabilitas", "📥 Download"])
        with t1:
            st.subheader(f"Hasil: {res['Jumlah Terjun']} Trap - {res['Desain Mode']}")
            st.pyplot(gambar_potongan_bertingkat(res["Jumlah Terjun"], H_total, res["Tinggi Terjun per Tingkat (m)"], res["Panjang Jatuhan Ld (m)"], res["Panjang Kolam Intermediate (m)"], res["Panjang Kolam Final (m)"], res["Kedalaman di Kaki (y1)"], res["Kedalaman Konjugasi (y2)"], res["Tinggi End Sill (m)"], res["Kedalaman Kritis yc (m)"]))
            st.pyplot(gambar_denah_bertingkat(res["Jumlah Terjun"], B_terjun, res["Panjang Jatuhan Ld (m)"], res["Panjang Kolam Intermediate (m)"], res["Panjang Kolam Final (m)"]))
        with t2:
            c1, c2 = st.columns(2)
            with c1: st.write("##### Data Hidrolis"); st.dataframe(pd.DataFrame(list(res.items()), columns=["Param", "Nilai"]))
            with c2: 
                st.write("##### Cek Uplift Lantai Kolam"); st.dataframe(pd.DataFrame(list(stab.items()), columns=["Param", "Nilai"]))
                if stab["Aman Uplift"]: st.success("✅ Aman Uplift")
                else: st.error("❌ Bahaya Uplift (Pertebal Lantai)")
        with t3:
            xls = generate_excel(st.session_state['input_terjun'], res, stab)
            st.download_button("📥 Excel Laporan", xls, "Laporan_Terjun.xlsx")
            dxf_pot = generate_dxf_potongan(res["Jumlah Terjun"], H_total, res["Tinggi Terjun per Tingkat (m)"], res["Panjang Jatuhan Ld (m)"], res["Panjang Kolam Intermediate (m)"], res["Panjang Kolam Final (m)"], res["Kedalaman di Kaki (y1)"], res["Kedalaman Konjugasi (y2)"], res["Tinggi End Sill (m)"], res["Kedalaman Kritis yc (m)"])
            if dxf_pot: st.download_button("📐 CAD Potongan (.dxf)", dxf_pot, "Potongan.dxf")
    else: st.info("👈 Masukkan data terjunan di Sidebar dan klik 'Hitung Terjunan'")
