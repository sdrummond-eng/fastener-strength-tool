"""
fastener_data.py — Fastener material and dimensional property data.

Standards Referenced:
  SAE J429:2021   — Mechanical and Material Requirements for Externally
                    Threaded Fasteners (Inch)
  ISO 898-1:2013  — Mechanical properties of fasteners — Bolts, screws
                    and studs (Metric)
  ASME B1.1-2003  — Unified Inch Screw Threads (UNC/UNF)
  ASME B1.13M-2005— Metric Screw Threads — M Profile
  Machinery's Handbook 31e — Tabulated tensile stress areas

NOTE ON INCH GRADES:
  Previous version used MPa values for inch grades (incorrect).
  SAE J429 grades are defined in psi; metric conversions shown in comments.

v2.20 CHANGES:
  - Added UNF thread data (ASME B1.1-2003 / Machinery's Handbook 31e)
  - Added input validation functions
  - calc_proof_load_inch() now accepts thread_series argument to support both UNC and UNF
"""

import math

# ─────────────────────────────────────────────────────────────────────────────
# INCH GRADES  (SAE J429:2021, Table 1)
# Tuple: (yield_psi, tensile_psi, proof_psi)
# Size range shown is for the most common diameter range (1/4"–3/4")
# ─────────────────────────────────────────────────────────────────────────────
INCH_GRADES = {
    "Grade 2":  (57_000,  74_000,  55_000),   # Low/med carbon steel, no Q&T
    "Grade 5":  (92_000, 120_000,  85_000),   # Med carbon steel, Q&T
    "Grade 8":  (130_000, 150_000, 120_000),  # Alloy steel, Q&T
}

INCH_GRADE_NOTES = {
    "Grade 2":  "SAE J429 Table 1 — 1/4\"–3/4\" dia, no heat treatment",
    "Grade 5":  "SAE J429 Table 1 — 1/4\"–1\" dia, quenched & tempered",
    "Grade 8":  "SAE J429 Table 1 — 1/4\"–1.5\" dia, alloy steel, Q&T",
}

# ─────────────────────────────────────────────────────────────────────────────
# METRIC PROPERTY CLASSES  (ISO 898-1:2013, Table 3)
# Tuple: (yield_mpa, tensile_mpa, proof_mpa)
# ─────────────────────────────────────────────────────────────────────────────
METRIC_GRADES = {
    "4.6":  (240,   400,  225),
    "5.8":  (400,   500,  380),
    "8.8":  (640,   800,  580),   # d > 16mm; use 660/830/600 for d ≤ 16mm
    "10.9": (940,  1040,  830),
    "12.9": (1100, 1220,  970),
}

METRIC_GRADE_NOTES = {
    "4.6":  "ISO 898-1:2013 Table 3 — Low/medium carbon steel",
    "5.8":  "ISO 898-1:2013 Table 3 — Low/medium carbon steel",
    "8.8":  "ISO 898-1:2013 Table 3 — Med carbon steel, Q&T (d > 16 mm shown)",
    "10.9": "ISO 898-1:2013 Table 3 — Alloy steel, quenched & tempered",
    "12.9": "ISO 898-1:2013 Table 3 — Alloy steel, Q&T, highest common grade",
}

# ─────────────────────────────────────────────────────────────────────────────
# UNC THREAD DATA  (ASME B1.1-2003 / Machinery's Handbook 31e)
# Tensile stress areas (At) are TABULATED values from Machinery's Handbook —
# not computed from diameter alone — to match empirical strength test data.
# Tuple: (nominal_dia_in, tpi, At_in2)
# ─────────────────────────────────────────────────────────────────────────────
UNC_THREADS = {
    "#4":    (0.1120, 40,  0.00604),
    "#6":    (0.1380, 32,  0.00909),
    "#8":    (0.1640, 32,  0.01400),
    "#10":   (0.1900, 24,  0.01750),
    "#12":   (0.2160, 24,  0.02430),
    "1/4":   (0.2500, 20,  0.03180),
    "5/16":  (0.3125, 18,  0.05240),
    "3/8":   (0.3750, 16,  0.07750),
    "7/16":  (0.4375, 14,  0.10600),
    "1/2":   (0.5000, 13,  0.14200),
    "9/16":  (0.5625, 12,  0.18200),
    "5/8":   (0.6250, 11,  0.22600),
    "3/4":   (0.7500, 10,  0.33400),
    "7/8":   (0.8750,  9,  0.46200),
    "1":     (1.0000,  8,  0.60600),
    "1-1/8": (1.1250,  7,  0.76300),
    "1-1/4": (1.2500,  7,  0.96900),
    "1-3/8": (1.3750,  6,  1.15500),
    "1-1/2": (1.5000,  6,  1.40500),
}

# ─────────────────────────────────────────────────────────────────────────────
# UNF THREAD DATA  (ASME B1.1-2003 / Machinery's Handbook 31e)
# Fine thread series — commonly used in aerospace, precision, and thin-walled
# applications where finer pitch improves locking and allows finer adjustment.
# Tuple: (nominal_dia_in, tpi, At_in2)
# ─────────────────────────────────────────────────────────────────────────────
UNF_THREADS = {
    "#4":    (0.1120, 48,  0.00661),
    "#6":    (0.1380, 40,  0.01015),
    "#8":    (0.1640, 36,  0.01474),
    "#10":   (0.1900, 32,  0.02000),
    "#12":   (0.2160, 28,  0.02580),
    "1/4":   (0.2500, 28,  0.03640),
    "5/16":  (0.3125, 24,  0.05800),
    "3/8":   (0.3750, 24,  0.08780),
    "7/16":  (0.4375, 20,  0.11800),
    "1/2":   (0.5000, 20,  0.15900),
    "9/16":  (0.5625, 18,  0.20300),
    "5/8":   (0.6250, 18,  0.25600),
    "3/4":   (0.7500, 16,  0.37300),
    "7/8":   (0.8750, 14,  0.50900),
    "1":     (1.0000, 12,  0.66300),
    "1-1/8": (1.1250, 12,  0.85600),
    "1-1/4": (1.2500, 12,  1.07300),
    "1-3/8": (1.3750, 12,  1.31500),
    "1-1/2": (1.5000, 12,  1.58100),
}

# ─────────────────────────────────────────────────────────────────────────────
# METRIC COARSE THREAD DATA  (ASME B1.13M / ISO 68-1 / Machinery's Handbook)
# Tuple: (nominal_dia_mm, pitch_mm, At_mm2)
# ─────────────────────────────────────────────────────────────────────────────
METRIC_THREADS = {
    "M3":   ( 3.0, 0.50,   5.03),
    "M4":   ( 4.0, 0.70,   8.78),
    "M5":   ( 5.0, 0.80,  14.20),
    "M6":   ( 6.0, 1.00,  20.10),
    "M8":   ( 8.0, 1.25,  36.60),
    "M10":  (10.0, 1.50,  58.00),
    "M12":  (12.0, 1.75,  84.30),
    "M14":  (14.0, 2.00, 115.00),
    "M16":  (16.0, 2.00, 157.00),
    "M18":  (18.0, 2.50, 192.00),
    "M20":  (20.0, 2.50, 245.00),
    "M22":  (22.0, 2.50, 303.00),
    "M24":  (24.0, 3.00, 353.00),
    "M27":  (27.0, 3.00, 459.00),
    "M30":  (30.0, 3.50, 561.00),
    "M33":  (33.0, 3.50, 694.00),
    "M36":  (36.0, 4.00, 817.00),
}


# ─────────────────────────────────────────────────────────────────────────────
# CALCULATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def calc_proof_load_inch(size: str, grade: str, thread_series: str = "UNC") -> dict:
    """
    Proof Load (lbf) = Sp (psi) × At (in²)
    SAE J429:2021 §5.2

    Uses tabulated At from Machinery's Handbook — NOT computed from diameter.
    Supports both UNC and UNF thread series (ASME B1.1-2003).

    Args:
        size: Thread size string (e.g. "1/2", "#10")
        grade: SAE grade string (e.g. "Grade 8")
        thread_series: "UNC" or "UNF"
    """
    thread_table = UNF_THREADS if thread_series == "UNF" else UNC_THREADS
    dia, tpi, At = thread_table[size]
    Sy, Su, Sp = INCH_GRADES[grade]

    return {
        "size": size,
        "grade": grade,
        "thread_series": thread_series,
        "dia_in": dia,
        "tpi": tpi,
        "At_in2": At,
        "Sy_psi": Sy,
        "Su_psi": Su,
        "Sp_psi": Sp,
        "proof_load_lbf":   Sp * At,
        "tensile_cap_lbf":  Su * At,
        "yield_cap_lbf":    Sy * At,
        "standard": "SAE J429:2021 Table 1 / Machinery's Handbook 31e",
        "At_source": f"Tabulated (ASME B1.1 {thread_series} / Machinery's Hbk) — not calculated",
    }


def calc_proof_load_metric(size: str, grade: str) -> dict:
    """
    Proof Load (N) = Sp (MPa) × At (mm²)
    ISO 898-1:2013 §9.1

    Uses tabulated At from Machinery's Handbook.
    """
    dia, pitch, At = METRIC_THREADS[size]
    Sy, Su, Sp = METRIC_GRADES[grade]

    return {
        "size": size,
        "grade": grade,
        "dia_mm": dia,
        "pitch_mm": pitch,
        "At_mm2": At,
        "Sy_mpa": Sy,
        "Su_mpa": Su,
        "Sp_mpa": Sp,
        "proof_load_N":   Sp * At,
        "tensile_cap_N":  Su * At,
        "yield_cap_N":    Sy * At,
        "standard": "ISO 898-1:2013 Table 3 / Machinery's Handbook 31e",
        "At_source": "Tabulated (ASME B1.13M / Machinery's Hbk) — not calculated",
    }


def calc_factor_of_safety(capacity: float, applied: float) -> tuple[float, str, str]:
    """Returns (FoS value, status label, guidance string)."""
    if applied <= 0:
        return None, "—", "Applied load must be > 0"
    fos = capacity / applied
    if fos >= 2.0:
        return fos, "✅ PASS",     "Robust margin — suitable for most static applications."
    elif fos >= 1.5:
        return fos, "⚠️ MARGINAL", "Acceptable for well-controlled loading. Review if cyclic."
    elif fos >= 1.0:
        return fos, "⚠️ LOW",      "Near yield. Revisit load assumptions or upsize fastener."
    else:
        return fos, "❌ FAIL",     "Fastener will fail under stated load. Redesign required."


def calc_torque_tension(torque_in_lbf: float, K: float, dia_in: float) -> dict:
    """
    Clamp force from applied torque — Nut-Factor (K-Factor) method.

    F_i = T / (K × d)

    Ref: VDI 2230:2014 Eq. (R8) / Shigley's Machine Design 10e Eq. 8-27

    Args:
        torque_in_lbf: Applied torque in in·lbf
        K: Nut factor (dimensionless). Typical values:
             0.10–0.15  Lubricated / MoS₂
             0.18–0.22  As-received (unlubricated) ← most common default
             0.25–0.30  Zinc-plated, dry
        dia_in: Nominal bolt diameter in inches

    Returns dict with clamp force and metadata.
    """
    clamp_force_lbf = torque_in_lbf / (K * dia_in)
    return {
        "clamp_force_lbf": clamp_force_lbf,
        "torque_in_lbf": torque_in_lbf,
        "K": K,
        "dia_in": dia_in,
        "equation": "F_i = T / (K × d)",
        "standard": "VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27",
    }


def calc_torque_tension_metric(torque_Nmm: float, K: float, dia_mm: float) -> dict:
    """
    Metric version of torque-tension.
    F_i (N) = T (N·mm) / (K × d (mm))
    """
    clamp_force_N = torque_Nmm / (K * dia_mm)
    return {
        "clamp_force_N": clamp_force_N,
        "torque_Nmm": torque_Nmm,
        "K": K,
        "dia_mm": dia_mm,
        "equation": "F_i = T / (K × d)",
        "standard": "VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27",
    }


def calc_thread_strip_inch(size: str, engagement_in: float,
                            shear_strength_psi: float) -> dict:
    """
    Thread stripping shear area and strip load for UNC external thread.

    Shear Area:  A_s = 0.5 × π × d_minor × L_e
    Strip Load:  F_strip = τ × A_s,   τ ≈ 0.577 × Su (von Mises)

    d_minor ≈ d - 1.2990/n  (60° UNC thread form, ASME B1.1)

    Ref: FED-STD-H28/2B §2.9 / Shigley's MDET 10e §8-5
    """
    dia, tpi, At = UNC_THREADS[size]
    d_minor = dia - (1.2990 / tpi)
    shear_area_ext = 0.5 * math.pi * d_minor * engagement_in   # bolt threads
    shear_area_int = 0.5 * math.pi * dia      * engagement_in   # nut/tapped hole
    strip_load_ext = shear_strength_psi * shear_area_ext
    strip_load_int = shear_strength_psi * shear_area_int

    return {
        "d_minor_in": d_minor,
        "engagement_in": engagement_in,
        "shear_area_ext_in2": shear_area_ext,
        "shear_area_int_in2": shear_area_int,
        "strip_load_ext_lbf": strip_load_ext,
        "strip_load_int_lbf": strip_load_int,
        "equation_area": "A_s = 0.5 × π × d_minor × L_e",
        "equation_strip": "F_strip = τ × A_s,  τ ≈ 0.577 × Su (von Mises)",
        "standard": "FED-STD-H28/2B §2.9 / Shigley's MDET 10e §8-5",
    }


def calc_thread_strip_metric(size: str, engagement_mm: float,
                              shear_strength_mpa: float) -> dict:
    """
    Thread stripping — metric M-profile thread.
    d_minor ≈ d - 1.2269 × pitch  (ISO 68-1 thread form)
    """
    dia, pitch, At = METRIC_THREADS[size]
    d_minor = dia - 1.2269 * pitch
    shear_area_ext = 0.5 * math.pi * d_minor * engagement_mm
    shear_area_int = 0.5 * math.pi * dia      * engagement_mm
    strip_load_ext = shear_strength_mpa * shear_area_ext
    strip_load_int = shear_strength_mpa * shear_area_int

    return {
        "d_minor_mm": d_minor,
        "engagement_mm": engagement_mm,
        "shear_area_ext_mm2": shear_area_ext,
        "shear_area_int_mm2": shear_area_int,
        "strip_load_ext_N": strip_load_ext,
        "strip_load_int_N": strip_load_int,
        "equation_area": "A_s = 0.5 × π × d_minor × L_e",
        "equation_strip": "F_strip = τ × A_s,  τ ≈ 0.577 × Su (von Mises)",
        "standard": "FED-STD-H28/2B §2.9 / Shigley's MDET 10e §8-5 / ISO 68-1",
    }


# ─────────────────────────────────────────────────────────────────────────────
# INPUT VALIDATION  (v2.20)
# Returns a list of warning dicts: {"level": "error"|"warning"|"info", "msg": str}
# ─────────────────────────────────────────────────────────────────────────────

def validate_tensile_inputs(applied_load: float, proof_load: float,
                             tensile_cap: float, yield_cap: float,
                             force_unit: str) -> list:
    """
    Validate tensile strength inputs and results.
    Returns list of {"level": ..., "msg": ...} dicts, empty if all clear.
    """
    warnings = []

    if applied_load <= 0:
        warnings.append({
            "level": "error",
            "msg": "Applied load must be greater than 0.",
        })
        return warnings  # no point checking further

    if applied_load > tensile_cap:
        warnings.append({
            "level": "error",
            "msg": f"Applied load ({applied_load:,.1f} {force_unit}) exceeds tensile capacity "
                   f"({tensile_cap:,.1f} {force_unit}). Fastener will fracture.",
        })
    elif applied_load > yield_cap:
        warnings.append({
            "level": "error",
            "msg": f"Applied load ({applied_load:,.1f} {force_unit}) exceeds yield capacity "
                   f"({yield_cap:,.1f} {force_unit}). Permanent deformation will occur.",
        })
    elif applied_load > proof_load:
        warnings.append({
            "level": "warning",
            "msg": f"Applied load ({applied_load:,.1f} {force_unit}) exceeds proof load "
                   f"({proof_load:,.1f} {force_unit}). Fastener may take a permanent set. "
                   "Consider a higher grade or larger size.",
        })

    fos = tensile_cap / applied_load
    if fos < 1.0:
        pass  # already caught above
    elif fos < 1.5:
        warnings.append({
            "level": "warning",
            "msg": f"Factor of safety ({fos:.2f}) is below 1.5. Acceptable only for very well-controlled, "
                   "static, non-critical loading. Review assumptions.",
        })

    return warnings


def validate_torque_inputs(K: float, clamp_force: float, proof_load: float,
                            force_unit: str) -> list:
    """
    Validate torque-tension inputs.
    """
    warnings = []

    if K < 0.08:
        warnings.append({
            "level": "warning",
            "msg": f"K = {K:.3f} is unusually low. Typical minimum for any lubricated condition "
                   "is ~0.08. Verify lube condition and surface finish.",
        })
    elif K > 0.35:
        warnings.append({
            "level": "warning",
            "msg": f"K = {K:.3f} is unusually high. Values above 0.35 suggest heavy corrosion, "
                   "damaged threads, or incorrect surface condition. Verify inputs.",
        })

    if proof_load > 0:
        preload_ratio = clamp_force / proof_load
        if preload_ratio > 0.90:
            warnings.append({
                "level": "error",
                "msg": f"Clamp force ({clamp_force:,.1f} {force_unit}) is {preload_ratio*100:.0f}% of proof load. "
                       "Risk of yielding during tightening. Target 75–85% of proof load (VDI 2230 §5.4).",
            })
        elif preload_ratio > 0.85:
            warnings.append({
                "level": "warning",
                "msg": f"Clamp force is {preload_ratio*100:.0f}% of proof load — at the upper end of the "
                       "recommended range. Consider reducing torque slightly.",
            })
        elif preload_ratio < 0.50:
            warnings.append({
                "level": "info",
                "msg": f"Clamp force is only {preload_ratio*100:.0f}% of proof load. "
                       "Low preload increases risk of joint separation and fatigue. "
                       "Typical target is 75–85% of proof load (VDI 2230 §5.4).",
            })

    return warnings


def validate_strip_inputs(engagement: float, dia: float, length_unit: str,
                           tensile_cap: float, governing_strip: float,
                           force_unit: str) -> list:
    """
    Validate thread stripping inputs.
    """
    warnings = []

    if dia > 0:
        ratio = engagement / dia
        if ratio < 0.8:
            warnings.append({
                "level": "error",
                "msg": f"Thread engagement ({engagement:.3f} {length_unit}) is only {ratio:.2f}× diameter. "
                       "Minimum recommended is 1.0× for steel, 1.5× for aluminum. "
                       "Thread stripping failure likely.",
            })
        elif ratio < 1.0:
            warnings.append({
                "level": "warning",
                "msg": f"Thread engagement ({engagement:.3f} {length_unit}) is {ratio:.2f}× diameter — "
                       "below the 1.0× minimum recommendation for steel tapped holes. "
                       "Increase engagement if possible.",
            })
        elif ratio < 1.5:
            warnings.append({
                "level": "info",
                "msg": f"Engagement is {ratio:.2f}× diameter. Acceptable for steel. "
                       "If tapped hole is aluminum, increase to ≥ 1.5× diameter.",
            })

    if tensile_cap < governing_strip:
        pass  # stripping governs — already shown prominently in results
    else:
        fos_strip = governing_strip / tensile_cap if tensile_cap > 0 else 0
        if fos_strip < 1.2:
            warnings.append({
                "level": "warning",
                "msg": "Strip load is close to tensile capacity. "
                       "Small increases in load could shift failure mode to stripping. "
                       "Consider increasing engagement length.",
            })

    return warnings


def render_validations(warnings: list) -> None:
    """
    Render validation warnings in Streamlit.
    Import streamlit inside function to keep fastener_data.py GUI-independent
    for use in scripts/tests without streamlit installed.
    """
    import streamlit as st
    for w in warnings:
        if w["level"] == "error":
            st.error(f"🚨 {w['msg']}")
        elif w["level"] == "warning":
            st.warning(f"⚠️ {w['msg']}")
        elif w["level"] == "info":
            st.info(f"ℹ️ {w['msg']}")
