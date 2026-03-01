"""
app.py — Fastener Strength Calculator  (Streamlit Web App)
===========================================================
Run locally:  streamlit run app.py
Deploy free:  share.streamlit.io — connect your GitHub repo, done.

Standards Referenced:
  SAE J429:2021    Inch grade mechanical properties
  ISO 898-1:2013   Metric property class mechanical properties
  ASME B1.1-2003   UNC tensile stress area (tabulated)
  ASME B1.13M-2005 Metric tensile stress area (tabulated)
  VDI 2230:2014    Torque-tension (nut factor method)
  FED-STD-H28/2B   Thread stripping shear area
  Shigley's MDET 10e  Sections 8-2, 8-5, Eq. 8-27
  Machinery's Handbook 31e  Thread stress area tables
"""

import streamlit as st
from fastener_data import (
    INCH_GRADES, INCH_GRADE_NOTES,
    METRIC_GRADES, METRIC_GRADE_NOTES,
    UNC_THREADS, UNF_THREADS, METRIC_THREADS,
    calc_proof_load_inch, calc_proof_load_metric,
    calc_factor_of_safety,
    calc_torque_tension, calc_torque_tension_metric,
    calc_thread_strip_inch, calc_thread_strip_metric,
    validate_tensile_inputs, validate_torque_inputs,
    validate_strip_inputs, render_validations,
)
from pdf_report import generate_pdf_report

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fastener Strength Calculator",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; }
  .stTabs [data-baseweb="tab-list"] { height: auto !important; overflow: visible !important; align-items: center !important; padding-top: 8px !important; }
  .stTabs [data-baseweb="tab"] { font-size: 0.88rem !important; font-weight: 600 !important; height: auto !important; line-height: 1.5 !important; padding: 10px 16px !important; overflow: visible !important; }
  .stTabs [data-baseweb="tab"] > div { overflow: visible !important; }
  .eq-box {
      background: #f0f4ff;
      border-left: 4px solid #3b5bdb;
      padding: 0.6rem 1rem;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.9rem;
      margin: 0.4rem 0;
  }
  .ref-box {
      background: #f8f9fa;
      border-left: 4px solid #868e96;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      font-size: 0.82rem;
      color: #495057;
      margin: 0.3rem 0;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE — persist calc results across tabs for PDF export
# ─────────────────────────────────────────────────────────────────────────────
if "tensile_data_for_pdf" not in st.session_state:
    st.session_state.tensile_data_for_pdf = None
if "torque_data_for_pdf" not in st.session_state:
    st.session_state.torque_data_for_pdf = None
if "strip_data_for_pdf" not in st.session_state:
    st.session_state.strip_data_for_pdf = None


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Global Selector + PDF Export
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔩 Fastener Calculator")
    st.caption("v2.20  |  SAE J429 · ISO 898-1 · VDI 2230 · ASME B1.1/B1.13M")
    st.divider()

    unit_system = st.radio(
        "**Unit System**",
        ["Inch (SAE/ASTM)", "Metric (ISO)"],
        horizontal=True,
    )
    is_inch = (unit_system == "Inch (SAE/ASTM)")

    st.divider()

    if is_inch:
        selected_grade  = st.selectbox("**SAE Grade**", list(INCH_GRADES.keys()))
        thread_series   = st.radio("**Thread Series**", ["UNC", "UNF"], horizontal=True,
                                   help="UNC = Unified National Coarse, UNF = Unified National Fine")
        thread_table    = UNF_THREADS if thread_series == "UNF" else UNC_THREADS
        selected_thread = st.selectbox("**Thread Size**", list(thread_table.keys()))
        grade_note = INCH_GRADE_NOTES[selected_grade]
        Sy, Su, Sp = INCH_GRADES[selected_grade]
        dia, tpi, At = thread_table[selected_thread]
        force_unit  = "lbf"
        stress_unit = "psi"
        length_unit = "in"
        torque_unit = "in·lbf"
        area_unit   = "in²"
    else:
        thread_series   = "Metric"
        selected_grade  = st.selectbox("**ISO Property Class**", list(METRIC_GRADES.keys()))
        selected_thread = st.selectbox("**Thread Size (Metric Coarse)**", list(METRIC_THREADS.keys()))
        grade_note = METRIC_GRADE_NOTES[selected_grade]
        Sy, Su, Sp = METRIC_GRADES[selected_grade]
        dia, pitch, At = METRIC_THREADS[selected_thread]
        force_unit  = "N"
        stress_unit = "MPa"
        length_unit = "mm"
        torque_unit = "N·mm"
        area_unit   = "mm²"

    st.caption(f"📋 {grade_note}")
    st.divider()

    st.markdown("**Selected Properties**")
    c1, c2 = st.columns(2)
    c1.metric(f"Sp ({stress_unit})", f"{Sp:,}")
    c2.metric(f"Su ({stress_unit})", f"{Su:,}")
    c1.metric(f"Sy ({stress_unit})", f"{Sy:,}")
    c2.metric(f"At ({area_unit})",   f"{At}")
    if is_inch:
        c1.metric("Threads per Inch", f"{tpi} TPI")
        c2.metric("Nominal Dia (in)", f"{dia}")
    else:
        c1.metric("Pitch (mm)", f"{pitch}")
        c2.metric("Nominal Dia (mm)", f"{dia}")
    st.caption("At = tabulated tensile stress area (Machinery's Hbk 31e)")

    st.divider()

    # ── PDF EXPORT ────────────────────────────────────────────────────────────
    st.markdown("**📄 Export Calculation Report**")

    if st.session_state.tensile_data_for_pdf is not None:
        try:
            pdf_bytes = generate_pdf_report(
                unit_system=unit_system,
                thread=selected_thread,
                grade=selected_grade,
                tensile_data=st.session_state.tensile_data_for_pdf,
                torque_data=st.session_state.torque_data_for_pdf,
                strip_data=st.session_state.strip_data_for_pdf,
            )
            safe_thread = selected_thread.replace("/", "-").replace(" ", "_")
            safe_grade  = selected_grade.replace(" ", "_")
            filename = f"fastener_{safe_thread}_{safe_grade}.pdf"

            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
            # Show what's included
            sections = ["✅ Fastener Properties", "✅ Tensile Strength"]
            if st.session_state.torque_data_for_pdf:
                sections.append("✅ Torque–Tension")
            if st.session_state.strip_data_for_pdf:
                sections.append("✅ Thread Stripping")
            sections.append("✅ Standards References")
            for s in sections:
                st.caption(s)

        except Exception as e:
            st.error(f"PDF generation error: {e}")
    else:
        st.info("Complete a calculation in any tab to enable PDF export.", icon="ℹ️")


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Tensile Strength",
    "Torque–Tension",
    "Thread Stripping",
    "References",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — TENSILE STRENGTH
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Tensile Strength Analysis")
    st.caption("Proof load, tensile capacity, yield capacity, and factor of safety vs. applied load.")

    col_in, col_out = st.columns([1, 1.6], gap="large")

    with col_in:
        st.subheader("Applied Load Input")
        applied = st.number_input(
            f"Applied Tensile Load ({force_unit})",
            min_value=0.0,
            value=1_000.0 if is_inch else 5_000.0,
            step=100.0,
            help="Maximum expected axial load on the fastener in service.",
        )
        st.caption("Thread and grade are selected in the sidebar →")

        with st.expander("ℹ️ What is tensile stress area (At)?"):
            st.markdown("""
**At is a tabulated value**, not simply π/4 × d².

It represents the effective cross-sectional area of a threaded fastener
that correlates with actual tensile test break loads. It accounts for the
helical thread geometry using an effective diameter midway between the
pitch and minor diameters.

The formula (for reference only — always use tabulated values):
> **Inch:**  At = (π/4) × (d − 0.9743/n)²  *(ASME B1.1)*
> **Metric:** At = (π/4) × (d − 0.9382p)²  *(ISO 68-1)*

This calculator uses **tabulated At values from Machinery's Handbook 31e**,
which match published test data and are required by SAE J429 / ISO 898-1.
            """)

    with col_out:
        st.subheader("Results")

        if is_inch:
            r = calc_proof_load_inch(selected_thread, selected_grade, thread_series)
            proof_cap   = r["proof_load_lbf"]
            tensile_cap = r["tensile_cap_lbf"]
            yield_cap   = r["yield_cap_lbf"]
        else:
            r = calc_proof_load_metric(selected_thread, selected_grade)
            proof_cap   = r["proof_load_N"]
            tensile_cap = r["tensile_cap_N"]
            yield_cap   = r["yield_cap_N"]

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Proof Load ({force_unit})",       f"{proof_cap:,.1f}")
        m2.metric(f"Tensile Capacity ({force_unit})",  f"{tensile_cap:,.1f}")
        m3.metric(f"Yield Capacity ({force_unit})",    f"{yield_cap:,.1f}")

        st.divider()
        st.subheader("Factors of Safety vs. Applied Load")

        fos_rows_for_pdf = []
        if applied > 0:
            rows_def = [
                ("Proof Load",     proof_cap,   "Bolt won't take permanent set"),
                ("Tensile (Ult.)", tensile_cap, "Bolt won't fracture"),
                ("Yield",          yield_cap,   "Bolt stays in elastic range"),
            ]
            for label, cap, desc in rows_def:
                fos, status, guidance = calc_factor_of_safety(cap, applied)
                fos_rows_for_pdf.append((
                    label,
                    f"{cap:,.1f} {force_unit}",
                    f"{applied:,.1f} {force_unit}",
                    fos,
                    status,
                ))
                with st.container():
                    ca, cb, cc = st.columns([1.4, 0.8, 2.8])
                    ca.markdown(f"**{label}**<br><small>{desc}</small>", unsafe_allow_html=True)
                    cb.markdown(f"### {fos:.2f}")
                    cc.markdown(f"{status}<br><small>{guidance}</small>", unsafe_allow_html=True)
                st.divider()
        else:
            st.info("Enter an applied load > 0 to calculate factors of safety.")

        # Store in session state for PDF
        tensile_pdf_data = dict(r)
        tensile_pdf_data["applied_load"] = applied
        tensile_pdf_data["fos_rows"] = fos_rows_for_pdf
        st.session_state.tensile_data_for_pdf = tensile_pdf_data

        # Validation warnings
        warnings = validate_tensile_inputs(
            applied, proof_cap, tensile_cap, yield_cap, force_unit
        )
        if warnings:
            st.divider()
            st.subheader("⚠️ Validation Warnings")
            render_validations(warnings)

    with st.expander("📐 Show Equations & Standard References"):
        st.markdown(f"""
| Quantity | Equation | Applied Here | Standard |
|---|---|---|---|
| Proof Load | `F_proof = Sp x At` | `{Sp:,} x {At} = {proof_cap:,.1f} {force_unit}` | SAE J429 §5.2 / ISO 898-1 §9.1 |
| Tensile Capacity | `F_tensile = Su x At` | `{Su:,} x {At} = {tensile_cap:,.1f} {force_unit}` | SAE J429 §5.2 / ISO 898-1 §9.1 |
| Yield Capacity | `F_yield = Sy x At` | `{Sy:,} x {At} = {yield_cap:,.1f} {force_unit}` | SAE J429 §5.2 / ISO 898-1 §9.1 |
| Factor of Safety | `FoS = F_capacity / F_applied` | — | Engineering convention |
        """)
        st.caption("At: tabulated per Machinery's Handbook 31e / ASME B1.1 (inch) / ASME B1.13M (metric). NOT computed from nominal diameter.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TORQUE–TENSION
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Torque–Tension Relationship")
    st.caption("Nut-factor (K-factor) method.  Ref: VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27")

    direction = st.radio(
        "Calculate:",
        ["Clamp Force from Applied Torque", "Required Torque for Target Clamp Force"],
        horizontal=True,
    )

    col_in2, col_out2 = st.columns([1, 1.6], gap="large")

    K_PRESETS = {
        "As-received / unlubricated (K = 0.20)": 0.20,
        "Lightly oiled (K = 0.15)":              0.15,
        "MoS2 / wax-based lube (K = 0.12)":     0.12,
        "Zinc-plated, dry (K = 0.28)":           0.28,
        "Custom":                                 None,
    }

    with col_in2:
        st.subheader("Inputs")

        preset_label = st.selectbox("Surface / Lube Condition", list(K_PRESETS.keys()))
        K_preset_val = K_PRESETS[preset_label]

        if K_preset_val is None:
            K = st.number_input("Custom K (Nut Factor)", min_value=0.01, max_value=1.0,
                                value=0.20, step=0.01)
        else:
            K = K_preset_val
            st.caption(f"K = {K}")

        if direction == "Clamp Force from Applied Torque":
            torque_val = st.number_input(
                f"Applied Torque ({torque_unit})",
                min_value=0.0,
                value=200.0 if is_inch else 25_000.0,
                step=10.0,
            )
        else:
            target_clamp = st.number_input(
                f"Target Clamp Force ({force_unit})",
                min_value=0.0,
                value=1_000.0 if is_inch else 5_000.0,
                step=100.0,
            )

        st.caption(f"Nominal diameter from sidebar: {dia} {length_unit}")

        with st.expander("ℹ️ About the K (Nut) Factor"):
            st.markdown("""
The nut factor **K** lumps together thread friction, bearing surface friction,
and thread helix angle into a single empirical coefficient.

| Condition | K |
|---|---|
| MoS2 or wax lube | 0.10–0.14 |
| Oil, light lube | 0.14–0.17 |
| As-received (no lube) | 0.18–0.22 |
| Zinc-plated, dry | 0.25–0.30 |

K has typical real-world variability of +/-20-30%. For critical joints,
measure K experimentally with a torque-tension tester.
            """)

    with col_out2:
        st.subheader("Results")

        if direction == "Clamp Force from Applied Torque":
            if is_inch:
                res_t = calc_torque_tension(torque_val, K, dia)
                clamp_result = res_t["clamp_force_lbf"]
            else:
                res_t = calc_torque_tension_metric(torque_val, K, dia)
                clamp_result = res_t["clamp_force_N"]

            st.metric(f"Resulting Clamp Force ({force_unit})", f"{clamp_result:,.1f}")
            st.divider()

            if is_inch:
                r_t = calc_proof_load_inch(selected_thread, selected_grade, thread_series)
                proof_cap_t = r_t["proof_load_lbf"]
            else:
                r_t = calc_proof_load_metric(selected_thread, selected_grade)
                proof_cap_t = r_t["proof_load_N"]

            fos_t, status_t, guidance_t = calc_factor_of_safety(proof_cap_t, clamp_result)
            st.markdown(f"**FoS: Clamp Force vs. Proof Load** — `{fos_t:.2f}`  {status_t}")
            st.caption(guidance_t)
            st.caption("Target preload: 75–85% of proof load for most structural joints (VDI 2230 §5.4)")

            st.session_state.torque_data_for_pdf = {
                "torque": torque_val, "K": K, "dia": dia, "clamp_force": clamp_result,
            }

            # Validation warnings
            if is_inch:
                r_proof = calc_proof_load_inch(selected_thread, selected_grade, thread_series)
                proof_for_val = r_proof["proof_load_lbf"]
            else:
                r_proof = calc_proof_load_metric(selected_thread, selected_grade)
                proof_for_val = r_proof["proof_load_N"]
            t_warnings = validate_torque_inputs(K, clamp_result, proof_for_val, force_unit)
            if t_warnings:
                st.divider()
                st.subheader("⚠️ Validation Warnings")
                render_validations(t_warnings)

            with st.expander("Show Equation"):
                st.code(f"F_i = T / (K x d) = {torque_val} / ({K} x {dia}) = {clamp_result:,.1f} {force_unit}")
                st.caption("Ref: VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27")

        else:
            torque_result = K * dia * target_clamp
            if is_inch:
                torque_disp = f"{torque_result:,.1f} in·lbf  ({torque_result/12:,.1f} ft·lbf)"
            else:
                torque_disp = f"{torque_result:,.1f} N·mm  ({torque_result/1000:,.2f} N·m)"

            st.metric("Required Torque", torque_disp)

            st.session_state.torque_data_for_pdf = {
                "torque": torque_result, "K": K, "dia": dia, "clamp_force": target_clamp,
            }

            with st.expander("Show Equation"):
                st.code(f"T = K x d x F_i = {K} x {dia} x {target_clamp} = {torque_result:,.1f} {torque_unit}")
                st.caption("Ref: VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — THREAD STRIPPING
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Thread Stripping Strength")
    st.caption("Shear area of bolt (external) and nut/tapped-hole (internal) threads vs. engagement length.")

    col_in3, col_out3 = st.columns([1, 1.6], gap="large")

    with col_in3:
        st.subheader("Inputs")

        if is_inch:
            default_eng = round(dia * 1.0, 3)
            engagement = st.number_input(
                f"Thread Engagement Length ({length_unit})",
                min_value=0.001, max_value=6.0,
                value=default_eng, step=0.01,
                help="Axial length over which threads are in contact.",
            )
            st.caption(f"Rule of thumb: >= 1.0x d for steel, >= 1.5x d for aluminum")
            st.caption(f"1.0x d for this size = {dia:.3f} in")
        else:
            default_eng = round(dia * 1.0)
            engagement = st.number_input(
                f"Thread Engagement Length ({length_unit})",
                min_value=0.1, max_value=200.0,
                value=float(default_eng), step=1.0,
            )
            st.caption(f"Rule of thumb: >= 1.0x d steel, >= 1.5x d aluminum")
            st.caption(f"1.0x d for this size = {dia:.0f} mm")

        nut_material = st.selectbox(
            "Nut/Tapped Hole Material",
            ["Same as bolt (steel)", "Aluminum (reduce tau by ~40%)", "Custom shear strength"],
        )

        tau = Su * 0.577
        if nut_material == "Aluminum (reduce tau by ~40%)":
            tau_int = tau * 0.60
        elif nut_material == "Custom shear strength":
            tau_int = st.number_input(
                f"Custom tau for internal thread ({stress_unit})",
                min_value=1.0, value=tau * 0.6, step=100.0,
            )
        else:
            tau_int = tau

        st.caption(f"Bolt shear strength tau = 0.577 x Su = 0.577 x {Su:,} = {tau:,.0f} {stress_unit}")

    with col_out3:
        st.subheader("Results")

        if is_inch:
            res_s = calc_thread_strip_inch(selected_thread, engagement, tau)
            ext_area  = res_s["shear_area_ext_in2"]
            int_area  = res_s["shear_area_int_in2"]
            ext_strip = res_s["strip_load_ext_lbf"]
            int_strip = tau_int * int_area
            d_minor   = res_s["d_minor_in"]
        else:
            res_s = calc_thread_strip_metric(selected_thread, engagement, tau)
            ext_area  = res_s["shear_area_ext_mm2"]
            int_area  = res_s["shear_area_int_mm2"]
            ext_strip = res_s["strip_load_ext_N"]
            int_strip = tau_int * int_area
            d_minor   = res_s["d_minor_mm"]

        m1, m2 = st.columns(2)
        m1.metric(f"Bolt Shear Area ({area_unit})",  f"{ext_area:.4f}" if is_inch else f"{ext_area:.1f}")
        m2.metric(f"Nut Shear Area ({area_unit})",   f"{int_area:.4f}" if is_inch else f"{int_area:.1f}")
        m1.metric(f"Bolt Strip Load ({force_unit})",     f"{ext_strip:,.1f}")
        m2.metric(f"Nut/Hole Strip Load ({force_unit})", f"{int_strip:,.1f}")

        st.divider()
        st.markdown("**Governing Failure Mode**")

        if is_inch:
            r_s2 = calc_proof_load_inch(selected_thread, selected_grade, thread_series)
            tensile_cap_s = r_s2["tensile_cap_lbf"]
        else:
            r_s2 = calc_proof_load_metric(selected_thread, selected_grade)
            tensile_cap_s = r_s2["tensile_cap_N"]

        governing_strip = min(ext_strip, int_strip)
        if tensile_cap_s <= governing_strip:
            st.success("✅ **Bolt tensile failure governs** — thread engagement is sufficient.")
            st.caption("Preferred failure mode: bolt breaks before threads strip (predictable, inspectable).")
        else:
            st.warning("⚠️ **Thread stripping governs** — increase engagement length or upsize fastener.")
            st.caption("Thread stripping is a sudden, hard-to-detect failure mode. Avoid by design.")

        # Store for PDF
        st.session_state.strip_data_for_pdf = {
            "engagement":     engagement,
            "d_minor":        d_minor,
            "shear_area_ext": ext_area,
            "shear_area_int": int_area,
            "tau":            tau,
            "tau_int":        tau_int,
            "strip_load_ext": ext_strip,
            "strip_load_int": int_strip,
        }

        # Validation warnings
        s_warnings = validate_strip_inputs(
            engagement, dia, length_unit,
            tensile_cap_s, governing_strip, force_unit
        )
        if s_warnings:
            st.divider()
            st.subheader("⚠️ Validation Warnings")
            render_validations(s_warnings)

        with st.expander("📐 Show Equations & Standard References"):
            st.markdown(f"""
| Quantity | Equation | Result | Standard |
|---|---|---|---|
| Minor diameter | `d_minor = d - 1.2990/n` | `{d_minor:.4f} {length_unit}` | ASME B1.1 |
| Bolt shear area | `A_s = 0.5 x pi x d_minor x Le` | `{ext_area:.4f} {area_unit}` | FED-STD-H28/2B §2.9 |
| Nut shear area | `A_s = 0.5 x pi x d_nom x Le` | `{int_area:.4f} {area_unit}` | FED-STD-H28/2B §2.9 |
| Shear strength | `tau = 0.577 x Su` | `{tau:,.0f} {stress_unit}` | Shigley's MDET 10e §8-5 |
| Strip load | `F_strip = tau x A_s` | — | FED-STD-H28/2B |
            """)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — REFERENCES & NOTES
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Standards References & Engineering Notes")

    st.subheader("Standards Used")
    refs = [
        ("SAE J429:2021",     "Mechanical and Material Requirements for Externally Threaded Fasteners",
         "Source of all inch-series grade mechanical properties (proof, tensile, yield strength)."),
        ("ISO 898-1:2013",    "Mechanical properties of fasteners — Bolts, screws and studs",
         "Source of all metric property class mechanical properties."),
        ("ASME B1.1-2003",    "Unified Inch Screw Threads (UN/UNR Thread Form)",
         "UNC thread geometry. Tensile stress area formula: At = (pi/4)(d - 0.9743/n)^2."),
        ("ASME B1.13M-2005",  "Metric Screw Threads — M Profile",
         "Metric thread geometry. Tensile stress area: At = (pi/4)(d - 0.9382p)^2."),
        ("VDI 2230:2014",     "Systematic Calculation of Highly Stressed Bolted Joints",
         "Torque-tension relationship using nut factor method (Eq. R8): Fi = T/(K x d)."),
        ("FED-STD-H28/2B",    "Screw Thread Standards for Federal Services — Part 2B",
         "Thread stripping shear area formulas for UNC/UNF threads."),
        ("Shigley's MDET 10e","Shigley's Mechanical Engineering Design, 10th Edition (Budynas & Nisbett)",
         "Sections 8-2 tensile stress area, 8-5 thread stripping, Eq. 8-27 torque-tension."),
        ("Machinery's Hbk 31e","Machinery's Handbook, 31st Edition (Industrial Press)",
         "Tabulated tensile stress areas for all common UNC and metric coarse thread sizes."),
    ]
    for std, title, usage in refs:
        with st.expander(f"📘 {std} — {title}"):
            st.markdown(f"**Used for:** {usage}")

    st.divider()
    st.subheader("Known Limitations & Assumptions")
    st.markdown("""
**Tensile Strength Tab**
- Grade properties shown are for the most common diameter range. Some grades have
  reduced values for larger diameters (e.g., SAE J429 Grade 5 >= 1" dia). Always
  verify your exact size range against the full standard table.
- Fatigue, dynamic, or impact loading are **not** accounted for.

**Torque–Tension Tab**
- K has typical real-world variability of +/-20-30%. Measure experimentally for critical joints.
- Does not account for combined tension + torsion stress. See VDI 2230 §5.5 for critical joints.

**Thread Stripping Tab**
- Uses the simplified FED-STD-H28 shear area formula (conservative).
- Internal shear area uses nominal bolt diameter (conservative for standard nuts).

**General**
- Assumes fully threaded engagement and no partial threads at load point.
- No corrosion, hydrogen embrittlement, elevated temperature, or coating effects included.
    """)

    st.divider()
    st.subheader("Changelog")
    st.markdown("""
**v2.20** *(current)*
| Change | Details |
|---|---|
| UNF thread support | Added all standard UNF sizes #4 through 1-1/2" (ASME B1.1-2003) |
| Input validation | Engineering warnings on all three calc tabs — flags unsafe inputs and results |
| TPI / Pitch display | Sidebar now shows threads per inch (UNC/UNF) or pitch (metric) for selected thread |

**v2.10**
| Change | Details |
|---|---|
| PDF export | Download full calculation report with equations, FoS, and standards references |
| Tab header fix | Resolved vertical clipping of tab labels in browser |
| Equation display fix | Resolved blank equation boxes in dark mode (Torque–Tension tab) |

**v2.0**
| Change | Details |
|---|---|
| Web app | Migrated from desktop Tkinter GUI to Streamlit web app |
| Torque–Tension | Added nut-factor torque-tension calculation (VDI 2230:2014) |
| Thread Stripping | Added thread shear area and strip load (FED-STD-H28/2B) |
| Standards references | All equations now cite governing standard |
| Inch stress area bug | Fixed incorrect mm² conversion — now uses tabulated in² values |
| Inch grade values bug | Fixed SAE grades that incorrectly used ISO MPa values |

**v1.0**
| Change | Details |
|---|---|
| Initial release | Desktop Tkinter GUI, tensile/proof load for UNC and metric coarse threads |
    """)

    st.divider()
    st.caption("Tool developed by sdrummond-eng · Open source · github.com/sdrummond-eng/fastener-strength-tool")
    st.caption("Not a substitute for review by a licensed engineer. Verify results against governing standards for safety-critical applications.")
