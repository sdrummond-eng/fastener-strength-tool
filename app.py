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
  VDI 2230:2014    Torque–tension (nut factor method)
  FED-STD-H28/2B   Thread stripping shear area
  Shigley's MDET 10e  §8-2, §8-5, Eq. 8-27
  Machinery's Handbook 31e  Thread stress area tables
"""

import streamlit as st
from fastener_data import (
    INCH_GRADES, INCH_GRADE_NOTES,
    METRIC_GRADES, METRIC_GRADE_NOTES,
    UNC_THREADS, METRIC_THREADS,
    calc_proof_load_inch, calc_proof_load_metric,
    calc_factor_of_safety,
    calc_torque_tension, calc_torque_tension_metric,
    calc_thread_strip_inch, calc_thread_strip_metric,
)

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
  .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; }
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
# SIDEBAR — Global Selector
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔩 Fastener Calculator")
    st.caption("SAE J429 · ISO 898-1 · VDI 2230 · ASME B1.1/B1.13M")
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
        selected_thread = st.selectbox("**Thread Size (UNC)**", list(UNC_THREADS.keys()))
        grade_note = INCH_GRADE_NOTES[selected_grade]
        Sy, Su, Sp = INCH_GRADES[selected_grade]
        dia, tpi, At = UNC_THREADS[selected_thread]
        force_unit  = "lbf"
        stress_unit = "psi"
        length_unit = "in"
        torque_unit = "in·lbf"
        area_unit   = "in²"
    else:
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
    st.caption("At = tabulated tensile stress area (Machinery's Hbk 31e)")


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📐  Tensile Strength",
    "🔧  Torque–Tension",
    "🧵  Thread Stripping",
    "📚  References & Notes",
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

        with st.expander("ℹ️ What is tensile stress area (Aₜ)?"):
            st.markdown("""
**Aₜ is a tabulated value**, not simply π/4 × d².

It represents the effective cross-sectional area of a threaded fastener
that correlates with actual tensile test break loads. It accounts for the
helical thread geometry using an effective diameter midway between the
pitch and minor diameters.

The formula (for reference only — always use tabulated values):
> **Inch:**  Aₜ = (π/4) × (d − 0.9743/n)²  *(ASME B1.1)*
> **Metric:** Aₜ = (π/4) × (d − 0.9382p)²  *(ISO 68-1)*

This calculator uses **tabulated Aₜ values from Machinery's Handbook 31e**,
which match published test data and are required by SAE J429 / ISO 898-1.
            """)

    with col_out:
        st.subheader("Results")

        if is_inch:
            r = calc_proof_load_inch(selected_thread, selected_grade)
            proof_cap   = r["proof_load_lbf"]
            tensile_cap = r["tensile_cap_lbf"]
            yield_cap   = r["yield_cap_lbf"]
        else:
            r = calc_proof_load_metric(selected_thread, selected_grade)
            proof_cap   = r["proof_load_N"]
            tensile_cap = r["tensile_cap_N"]
            yield_cap   = r["yield_cap_N"]

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Proof Load ({force_unit})",      f"{proof_cap:,.1f}")
        m2.metric(f"Tensile Capacity ({force_unit})", f"{tensile_cap:,.1f}")
        m3.metric(f"Yield Capacity ({force_unit})",   f"{yield_cap:,.1f}")

        st.divider()
        st.subheader("Factors of Safety vs. Applied Load")

        if applied > 0:
            rows = [
                ("Proof Load",     proof_cap,   "Bolt won't take permanent set"),
                ("Tensile (Ult.)", tensile_cap, "Bolt won't fracture"),
                ("Yield",          yield_cap,   "Bolt stays in elastic range"),
            ]
            for label, cap, desc in rows:
                fos, status, guidance = calc_factor_of_safety(cap, applied)
                with st.container():
                    ca, cb, cc = st.columns([1.4, 0.8, 2.8])
                    ca.markdown(f"**{label}**<br><small>{desc}</small>", unsafe_allow_html=True)
                    cb.markdown(f"### {fos:.2f}")
                    cc.markdown(f"{status}<br><small>{guidance}</small>", unsafe_allow_html=True)
                st.divider()
        else:
            st.info("Enter an applied load > 0 to calculate factors of safety.")

    # Equations expander
    with st.expander("📐 Show Equations & Standard References"):
        st.markdown(f"""
| Quantity | Equation | Applied Here | Standard |
|---|---|---|---|
| Proof Load | `F_proof = Sp × At` | `{Sp:,} × {At} = {proof_cap:,.1f} {force_unit}` | SAE J429 §5.2 / ISO 898-1 §9.1 |
| Tensile Capacity | `F_tensile = Su × At` | `{Su:,} × {At} = {tensile_cap:,.1f} {force_unit}` | SAE J429 §5.2 / ISO 898-1 §9.1 |
| Yield Capacity | `F_yield = Sy × At` | `{Sy:,} × {At} = {yield_cap:,.1f} {force_unit}` | SAE J429 §5.2 / ISO 898-1 §9.1 |
| Factor of Safety | `FoS = F_capacity / F_applied` | — | Engineering convention |
        """)
        st.markdown('<div class="ref-box">Tensile stress area Aₜ: tabulated per Machinery\'s Handbook 31e / ASME B1.1 (inch) / ASME B1.13M (metric). NOT computed from nominal diameter.</div>', unsafe_allow_html=True)


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
        "As-received / unlubricated (K ≈ 0.20)": 0.20,
        "Lightly oiled (K ≈ 0.15)":              0.15,
        "MoS₂ / wax-based lube (K ≈ 0.12)":     0.12,
        "Zinc-plated, dry (K ≈ 0.28)":           0.28,
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

Typical values (VDI 2230 / Shigley's):

| Condition | K |
|---|---|
| MoS₂ or wax lube | 0.10–0.14 |
| Oil, light lube | 0.14–0.17 |
| As-received (no lube) | 0.18–0.22 |
| Zinc-plated, dry | 0.25–0.30 |

⚠️ K has the largest uncertainty of any input (±20–30% is common). For
critical joints, measure K experimentally with a torque-tension tester.
            """)

    with col_out2:
        st.subheader("Results")

        if direction == "Clamp Force from Applied Torque":
            if is_inch:
                res = calc_torque_tension(torque_val, K, dia)
                clamp_result = res["clamp_force_lbf"]
            else:
                res = calc_torque_tension_metric(torque_val, K, dia)
                clamp_result = res["clamp_force_N"]

            st.metric(f"Resulting Clamp Force ({force_unit})", f"{clamp_result:,.1f}")
            st.divider()

            # Compare clamp force to proof load
            if is_inch:
                r = calc_proof_load_inch(selected_thread, selected_grade)
                proof_cap = r["proof_load_lbf"]
            else:
                r = calc_proof_load_metric(selected_thread, selected_grade)
                proof_cap = r["proof_load_N"]

            fos_proof, status_proof, guidance_proof = calc_factor_of_safety(proof_cap, clamp_result)
            st.markdown(f"**FoS: Clamp Force vs. Proof Load** — `{fos_proof:.2f}`  {status_proof}")
            st.caption(guidance_proof)
            st.caption("⚠️ Preload should target 75–85% of proof load for most structural joints (VDI 2230 §5.4)")

            with st.expander("📐 Show Equation"):
                st.markdown(f"""
<div class="eq-box">F_i = T / (K × d) = {torque_val} / ({K} × {dia}) = {clamp_result:,.1f} {force_unit}</div>
<div class="ref-box">VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27</div>
                """, unsafe_allow_html=True)

        else:
            # Required torque for target clamp force
            if is_inch:
                torque_result = K * dia * target_clamp
                torque_disp = f"{torque_result:,.1f} in·lbf  ({torque_result/12:,.1f} ft·lbf)"
            else:
                torque_result = K * dia * target_clamp
                torque_disp = f"{torque_result:,.1f} N·mm  ({torque_result/1000:,.2f} N·m)"

            st.metric(f"Required Torque", torque_disp)

            with st.expander("📐 Show Equation"):
                st.markdown(f"""
<div class="eq-box">T = K × d × F_i = {K} × {dia} × {target_clamp} = {torque_result:,.1f} {torque_unit}</div>
<div class="ref-box">VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27</div>
                """, unsafe_allow_html=True)


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
            st.caption(f"Rule of thumb: ≥ 1.0× d for steel, ≥ 1.5× d for aluminum tapped holes")
            st.caption(f"1.0× d for this size = {dia:.3f} in")
        else:
            default_eng = round(dia * 1.0)
            engagement = st.number_input(
                f"Thread Engagement Length ({length_unit})",
                min_value=0.1, max_value=200.0,
                value=float(default_eng), step=1.0,
            )
            st.caption(f"Rule of thumb: ≥ 1.0× d steel, ≥ 1.5× d aluminum")
            st.caption(f"1.0× d for this size = {dia:.0f} mm")

        nut_material = st.selectbox(
            "Nut/Tapped Hole Material",
            ["Same as bolt (steel)", "Aluminum (reduce τ by ~40%)", "Custom shear strength"],
        )

        tau = Su * 0.577   # von Mises criterion: τ_ult ≈ 0.577 × Su
        if nut_material == "Aluminum (reduce τ by ~40%)":
            tau_int = tau * 0.60
        elif nut_material == "Custom shear strength":
            tau_int = st.number_input(
                f"Custom τ for internal thread ({stress_unit})",
                min_value=1.0, value=tau * 0.6, step=100.0,
            )
        else:
            tau_int = tau

        st.caption(f"Bolt shear strength τ = 0.577 × Su = 0.577 × {Su:,} = {tau:,.0f} {stress_unit}")

    with col_out3:
        st.subheader("Results")

        if is_inch:
            res = calc_thread_strip_inch(selected_thread, engagement, tau)
            ext_area  = res["shear_area_ext_in2"]
            int_area  = res["shear_area_int_in2"]
            ext_strip = res["strip_load_ext_lbf"]
            # Recalculate internal with potentially different tau
            int_strip = tau_int * int_area
            d_minor   = res["d_minor_in"]
        else:
            res = calc_thread_strip_metric(selected_thread, engagement, tau)
            ext_area  = res["shear_area_ext_mm2"]
            int_area  = res["shear_area_int_mm2"]
            ext_strip = res["strip_load_ext_N"]
            int_strip = tau_int * int_area
            d_minor   = res["d_minor_mm"]

        m1, m2 = st.columns(2)
        m1.metric(f"Bolt Thread Shear Area ({area_unit})",  f"{ext_area:.4f}" if is_inch else f"{ext_area:.1f}")
        m2.metric(f"Nut Thread Shear Area ({area_unit})",   f"{int_area:.4f}" if is_inch else f"{int_area:.1f}")
        m1.metric(f"Bolt Strip Load ({force_unit})",  f"{ext_strip:,.1f}")
        m2.metric(f"Nut/Hole Strip Load ({force_unit})", f"{int_strip:,.1f}")

        st.divider()
        st.markdown("**Governing Failure Mode**")

        if is_inch:
            r = calc_proof_load_inch(selected_thread, selected_grade)
            tensile_cap = r["tensile_cap_lbf"]
        else:
            r = calc_proof_load_metric(selected_thread, selected_grade)
            tensile_cap = r["tensile_cap_N"]

        governing_strip = min(ext_strip, int_strip)
        if tensile_cap <= governing_strip:
            st.success("✅ **Bolt tensile failure governs** — thread engagement is sufficient.")
            st.caption("Preferred failure mode: bolt breaks before threads strip (more predictable, inspectable).")
        else:
            st.warning("⚠️ **Thread stripping governs** — increase engagement length or upsize fastener.")
            st.caption("Thread stripping is a sudden, hard-to-detect failure mode. Avoid by design.")

        with st.expander("📐 Show Equations & Standard References"):
            st.markdown(f"""
| Quantity | Equation | Applied Here | Standard |
|---|---|---|---|
| Minor diameter | `d_minor = d − 1.2990/n` (UNC) | `{dia} − {1.2990/(tpi if is_inch else 1):.4f} = {d_minor:.4f} {length_unit}` | ASME B1.1 |
| Shear area (bolt) | `A_s = 0.5 × π × d_minor × Le` | `0.5π × {d_minor:.4f} × {engagement} = {ext_area:.4f} {area_unit}` | FED-STD-H28/2B §2.9 |
| Shear area (nut) | `A_s = 0.5 × π × d_nom × Le` | `0.5π × {dia} × {engagement} = {int_area:.4f} {area_unit}` | FED-STD-H28/2B §2.9 |
| Shear strength | `τ ≈ 0.577 × Su` (von Mises) | `0.577 × {Su:,} = {tau:,.0f} {stress_unit}` | Shigley's MDET 10e §8-5 |
| Strip load | `F_strip = τ × A_s` | — | FED-STD-H28/2B / Shigley's §8-5 |
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
         "UNC thread geometry. Tensile stress area formula: At = (π/4)(d − 0.9743/n)²."),
        ("ASME B1.13M-2005",  "Metric Screw Threads — M Profile",
         "Metric thread geometry. Tensile stress area: At = (π/4)(d − 0.9382p)²."),
        ("VDI 2230:2014",     "Systematic Calculation of Highly Stressed Bolted Joints",
         "Torque-tension relationship using nut factor method (Eq. R8): Fi = T/(K×d)."),
        ("FED-STD-H28/2B",    "Screw Thread Standards for Federal Services — Part 2B",
         "Thread stripping shear area formulas for UNC/UNF threads."),
        ("Shigley's MDET 10e","Shigley's Mechanical Engineering Design, 10th Edition (Budynas & Nisbett)",
         "§8-2 tensile stress area, §8-5 thread stripping, Eq. 8-27 torque-tension."),
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
  reduced values for larger diameters (e.g., SAE J429 Grade 5 ≥ 1\" dia). Always
  verify your exact size range against the full standard table.
- Fatigue, dynamic, or impact loading are **not** accounted for. Use VDI 2230
  Part 1 for fatigue-loaded bolted joints.

**Torque–Tension Tab**
- The nut factor K has significant real-world variability (±20–30% is common).
  For critical joints, measure K experimentally on representative hardware.
- Does not account for torque-induced torsional stress in the bolt shank
  (combined tension + torsion). For critical joints, check combined stress per
  VDI 2230 §5.5.

**Thread Stripping Tab**
- Uses the simplified FED-STD-H28 shear area formula (conservative).
  Shigley's Eq. 8-29 provides a more detailed formulation accounting for
  thread profile modifications.
- Internal shear area uses nominal bolt diameter (conservative for standard nuts).
  Actual nut/tapped hole minor diameter is slightly larger.

**General**
- Calculations assume fully threaded engagement (no partial threads at load point).
- No corrosion, hydrogen embrittlement, elevated temperature, or coating effects
  are included. Consult material-specific standards for these conditions.
    """)

    st.divider()
    st.subheader("Bug Fixes from v1.0 Desktop Tool")
    st.markdown("""
The following issues were corrected in this version:

| Issue | v1.0 (Tkinter) | Fixed Here |
|---|---|---|
| Inch stress area units | `inch_area()` converted in² → mm² incorrectly | At values tabulated in in², never converted |
| Inch grade values | Used MPa values (ISO 8.8/10.9/12.9 data) for SAE grades | Corrected to SAE J429 psi values |
| Standard references | None | All equations cite governing standard |
| Thread stripping | Not implemented | Added (FED-STD-H28/2B) |
| Torque–tension | Not implemented | Added (VDI 2230) |
    """)

    st.divider()
    st.caption("Tool developed by sdrummond-eng · Open source · github.com/sdrummond-eng/fastener-strength-tool")
    st.caption("Not a substitute for review by a licensed engineer. Verify results against governing standards for safety-critical applications.")
