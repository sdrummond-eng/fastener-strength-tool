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

def calc_proof_load_inch(size: str, grade: str) -> dict:
    """
    Proof Load (lbf) = Sp (psi) × At (in²)
    SAE J429:2021 §5.2

    Uses tabulated At from Machinery's Handbook — NOT computed from diameter.
    Previous version incorrectly converted At to mm² for inch fasteners.
    """
    dia, tpi, At = UNC_THREADS[size]
    Sy, Su, Sp = INCH_GRADES[grade]

    return {
        "size": size,
        "grade": grade,
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
        "At_source": "Tabulated (ASME B1.1 / Machinery's Hbk) — not calculated",
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
