"""
pdf_report.py — Engineering Calculation Report Generator
=========================================================
Generates a professional PDF calculation sheet from fastener analysis results.

Uses ReportLab Platypus for structured layout.
NOTE: No Unicode sub/superscript characters used — ReportLab built-in fonts
do not support them. Using <sub>/<super> XML tags in Paragraph objects instead.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)


# ─────────────────────────────────────────────────────────────────────────────
# COLOR PALETTE
# ─────────────────────────────────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#1a3a5c")
MID_BLUE    = colors.HexColor("#2c5f8a")
LIGHT_BLUE  = colors.HexColor("#dce8f5")
ACCENT      = colors.HexColor("#e07b00")
PASS_GREEN  = colors.HexColor("#1a7a3f")
WARN_ORANGE = colors.HexColor("#b35900")
FAIL_RED    = colors.HexColor("#a0000a")
LIGHT_GRAY  = colors.HexColor("#f4f4f4")
MID_GRAY    = colors.HexColor("#cccccc")
TEXT_DARK   = colors.HexColor("#1a1a1a")


# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#b0c8e0"),
            alignment=TA_LEFT,
        ),
        "timestamp": ParagraphStyle(
            "Timestamp",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#b0c8e0"),
            alignment=TA_RIGHT,
        ),
        "section": ParagraphStyle(
            "SectionHead",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=DARK_BLUE,
            spaceBefore=10,
            spaceAfter=4,
            borderPad=2,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9,
            textColor=TEXT_DARK,
            spaceAfter=3,
            leading=13,
        ),
        "eq": ParagraphStyle(
            "Equation",
            fontName="Courier",
            fontSize=9,
            textColor=DARK_BLUE,
            leftIndent=12,
            spaceAfter=3,
            leading=13,
        ),
        "ref": ParagraphStyle(
            "Reference",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor("#555555"),
            leftIndent=12,
            spaceAfter=4,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            textColor=colors.HexColor("#777777"),
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=TEXT_DARK,
        ),
        "fos_pass": ParagraphStyle(
            "FoSPass",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=PASS_GREEN,
        ),
        "fos_warn": ParagraphStyle(
            "FoSWarn",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=WARN_ORANGE,
        ),
        "fos_fail": ParagraphStyle(
            "FoSFail",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=FAIL_RED,
        ),
    }
    return styles


# ─────────────────────────────────────────────────────────────────────────────
# HELPER BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _header_block(styles, unit_system, thread, grade, timestamp):
    """Dark blue header banner with title and metadata."""
    # Header table: title left, timestamp right
    header_data = [[
        Paragraph("FASTENER STRENGTH CALCULATION REPORT", styles["title"]),
        Paragraph(timestamp, styles["timestamp"]),
    ]]
    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), DARK_BLUE),
        ("TOPPADDING",  (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0), (0,-1),  14),
        ("RIGHTPADDING",(-1,0),(-1,-1), 14),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))

    # Sub-header: unit system, thread, grade
    sub_data = [[
        Paragraph(f"Unit System: {unit_system}", styles["subtitle"]),
        Paragraph(f"Thread: {thread}", styles["subtitle"]),
        Paragraph(f"Grade / Class: {grade}", styles["subtitle"]),
    ]]
    sub_table = Table(sub_data, colWidths=[2.3*inch, 2.3*inch, 2.4*inch])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), MID_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))

    return [header_table, sub_table, Spacer(1, 10)]


def _section_title(text, styles):
    return [
        Paragraph(text, styles["section"]),
        HRFlowable(width="100%", thickness=1, color=MID_BLUE, spaceAfter=4),
    ]


def _result_table(rows, styles):
    """
    rows: list of (label, value, unit, standard_ref)
    """
    header = [
        Paragraph("Parameter", styles["table_header"]),
        Paragraph("Value", styles["table_header"]),
        Paragraph("Unit", styles["table_header"]),
        Paragraph("Reference", styles["table_header"]),
    ]
    data = [header]
    for i, (lbl, val, unit, ref) in enumerate(rows):
        bg = LIGHT_GRAY if i % 2 == 0 else colors.white
        data.append([
            Paragraph(str(lbl), styles["table_cell"]),
            Paragraph(str(val), styles["table_cell"]),
            Paragraph(str(unit), styles["table_cell"]),
            Paragraph(str(ref),  styles["table_cell"]),
        ])

    col_w = [2.5*inch, 1.3*inch, 0.9*inch, 2.3*inch]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  MID_BLUE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LIGHT_GRAY, colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t


def _fos_table(fos_rows, styles):
    """
    fos_rows: list of (label, capacity, applied, fos, status)
    """
    header = [
        Paragraph("Check", styles["table_header"]),
        Paragraph("Capacity", styles["table_header"]),
        Paragraph("Applied", styles["table_header"]),
        Paragraph("FoS", styles["table_header"]),
        Paragraph("Status", styles["table_header"]),
    ]
    data = [header]
    row_styles = []

    for i, (lbl, cap, app, fos, status) in enumerate(fos_rows):
        fos_str = f"{fos:.2f}" if fos else "—"
        if "PASS" in status:
            fos_style = styles["fos_pass"]
        elif "FAIL" in status:
            fos_style = styles["fos_fail"]
        else:
            fos_style = styles["fos_warn"]

        data.append([
            Paragraph(lbl,     styles["table_cell"]),
            Paragraph(cap,     styles["table_cell"]),
            Paragraph(app,     styles["table_cell"]),
            Paragraph(fos_str, fos_style),
            Paragraph(status,  fos_style),
        ])

    col_w = [1.8*inch, 1.4*inch, 1.3*inch, 0.8*inch, 1.7*inch]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  MID_BLUE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LIGHT_GRAY, colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t


def _equation_block(equations, styles):
    """equations: list of (equation_str, reference_str)"""
    items = []
    for eq, ref in equations:
        items.append(Paragraph(eq,  styles["eq"]))
        items.append(Paragraph(f"Ref: {ref}", styles["ref"]))
    return items


def _footer_table(styles):
    data = [[
        Paragraph(
            "This report is generated for engineering reference only. "
            "Results must be verified by a licensed engineer for safety-critical applications. "
            "All calculations per cited standards.",
            styles["disclaimer"]
        )
    ]]
    t = Table(data, colWidths=[7*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("BOX",           (0,0), (-1,-1), 0.5, MID_GRAY),
    ]))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf_report(
    unit_system: str,
    thread: str,
    grade: str,
    tensile_data: dict,
    torque_data: dict = None,
    strip_data: dict = None,
) -> bytes:
    """
    Generate a PDF engineering calculation report.

    Args:
        unit_system:  "Inch (SAE/ASTM)" or "Metric (ISO)"
        thread:       Selected thread size string
        grade:        Selected grade/class string
        tensile_data: Dict from calc_proof_load_inch/metric + applied load + FoS results
        torque_data:  Optional dict from torque-tension calculation
        strip_data:   Optional dict from thread stripping calculation

    Returns:
        PDF file as bytes (ready for st.download_button)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.6*inch,
        bottomMargin=0.75*inch,
        title="Fastener Strength Calculation Report",
        author="Fastener Strength Calculator",
        subject=f"{thread} {grade}",
    )

    styles = _build_styles()
    is_inch = "Inch" in unit_system
    force_unit  = "lbf"  if is_inch else "N"
    stress_unit = "psi"  if is_inch else "MPa"
    length_unit = "in"   if is_inch else "mm"
    area_unit   = "in2"  if is_inch else "mm2"
    torque_unit = "in-lbf" if is_inch else "N-mm"

    timestamp = datetime.now().strftime("Generated: %Y-%m-%d  %H:%M")
    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    story += _header_block(styles, unit_system, thread, grade, timestamp)

    # ── SECTION 1: FASTENER PROPERTIES ────────────────────────────────────────
    story += _section_title("1. Fastener Properties", styles)

    if is_inch:
        prop_rows = [
            ("Nominal Diameter",      f"{tensile_data['dia_in']:.4f}",  length_unit, "ASME B1.1-2003"),
            ("Threads per Inch (TPI)", f"{tensile_data['tpi']}",        "TPI",       "ASME B1.1-2003"),
            ("Tensile Stress Area At", f"{tensile_data['At_in2']}",     area_unit,   "Machinery's Hbk 31e (tabulated)"),
            ("Proof Strength Sp",      f"{tensile_data['Sp_psi']:,}",   stress_unit, "SAE J429:2021 Table 1"),
            ("Min Tensile Strength Su",f"{tensile_data['Su_psi']:,}",   stress_unit, "SAE J429:2021 Table 1"),
            ("Min Yield Strength Sy",  f"{tensile_data['Sy_psi']:,}",   stress_unit, "SAE J429:2021 Table 1"),
        ]
        std_note = "SAE J429:2021 — Mechanical and Material Requirements for Externally Threaded Fasteners"
    else:
        prop_rows = [
            ("Nominal Diameter",        f"{tensile_data['dia_mm']:.1f}",  length_unit, "ASME B1.13M-2005"),
            ("Thread Pitch",            f"{tensile_data['pitch_mm']}",    "mm",        "ASME B1.13M-2005"),
            ("Tensile Stress Area At",  f"{tensile_data['At_mm2']}",      area_unit,   "Machinery's Hbk 31e (tabulated)"),
            ("Proof Strength Sp",       f"{tensile_data['Sp_mpa']:,}",    stress_unit, "ISO 898-1:2013 Table 3"),
            ("Min Tensile Strength Su", f"{tensile_data['Su_mpa']:,}",    stress_unit, "ISO 898-1:2013 Table 3"),
            ("Min Yield Strength Sy",   f"{tensile_data['Sy_mpa']:,}",    stress_unit, "ISO 898-1:2013 Table 3"),
        ]
        std_note = "ISO 898-1:2013 — Mechanical properties of fasteners — Bolts, screws and studs"

    story.append(_result_table(prop_rows, styles))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Standard: {std_note}", styles["ref"]))
    story.append(Spacer(1, 8))

    # ── SECTION 2: TENSILE STRENGTH ────────────────────────────────────────────
    story += _section_title("2. Tensile Strength Analysis", styles)

    if is_inch:
        proof_load   = tensile_data["proof_load_lbf"]
        tensile_cap  = tensile_data["tensile_cap_lbf"]
        yield_cap    = tensile_data["yield_cap_lbf"]
        Sp = tensile_data["Sp_psi"];  Su = tensile_data["Su_psi"];  Sy = tensile_data["Sy_psi"]
        At = tensile_data["At_in2"]
    else:
        proof_load   = tensile_data["proof_load_N"]
        tensile_cap  = tensile_data["tensile_cap_N"]
        yield_cap    = tensile_data["yield_cap_N"]
        Sp = tensile_data["Sp_mpa"];  Su = tensile_data["Su_mpa"];  Sy = tensile_data["Sy_mpa"]
        At = tensile_data["At_mm2"]

    cap_rows = [
        ("Proof Load",      f"{proof_load:,.1f}",  force_unit, "F_proof = Sp x At"),
        ("Tensile Capacity",f"{tensile_cap:,.1f}", force_unit, "F_tensile = Su x At"),
        ("Yield Capacity",  f"{yield_cap:,.1f}",   force_unit, "F_yield = Sy x At"),
    ]
    story.append(_result_table(cap_rows, styles))
    story.append(Spacer(1, 6))

    # Equations
    story += _equation_block([
        (f"F_proof   = Sp x At = {Sp:,} x {At} = {proof_load:,.1f} {force_unit}",
         "SAE J429:2021 §5.2 / ISO 898-1:2013 §9.1"),
        (f"F_tensile = Su x At = {Su:,} x {At} = {tensile_cap:,.1f} {force_unit}",
         "SAE J429:2021 §5.2 / ISO 898-1:2013 §9.1"),
        (f"F_yield   = Sy x At = {Sy:,} x {At} = {yield_cap:,.1f} {force_unit}",
         "SAE J429:2021 §5.2 / ISO 898-1:2013 §9.1"),
    ], styles)
    story.append(Spacer(1, 6))

    # FoS table
    if "fos_rows" in tensile_data:
        story.append(Paragraph("Factors of Safety", styles["section"]))
        story.append(_fos_table(tensile_data["fos_rows"], styles))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "FoS = F_capacity / F_applied   |   Target: >= 2.0 robust, >= 1.5 acceptable, < 1.0 fail",
            styles["ref"]
        ))
    story.append(Spacer(1, 10))

    # ── SECTION 3: TORQUE–TENSION (optional) ──────────────────────────────────
    if torque_data:
        story += _section_title("3. Torque-Tension Analysis", styles)

        if is_inch:
            torque_rows = [
                ("Applied Torque",      f"{torque_data['torque']:,.1f}",        torque_unit, "Input"),
                ("Nut Factor K",        f"{torque_data['K']:.3f}",              "—",         "VDI 2230:2014"),
                ("Nominal Diameter",    f"{torque_data['dia']:.4f}",            length_unit, "ASME B1.1"),
                ("Resulting Clamp Force",f"{torque_data['clamp_force']:,.1f}",  force_unit,  "VDI 2230:2014 Eq. (R8)"),
            ]
        else:
            torque_rows = [
                ("Applied Torque",       f"{torque_data['torque']:,.1f}",       torque_unit, "Input"),
                ("Nut Factor K",         f"{torque_data['K']:.3f}",             "—",         "VDI 2230:2014"),
                ("Nominal Diameter",     f"{torque_data['dia']:.1f}",           length_unit, "ASME B1.13M"),
                ("Resulting Clamp Force",f"{torque_data['clamp_force']:,.1f}",  force_unit,  "VDI 2230:2014 Eq. (R8)"),
            ]

        story.append(_result_table(torque_rows, styles))
        story.append(Spacer(1, 6))
        story += _equation_block([
            (f"F_i = T / (K x d) = {torque_data['torque']:,.1f} / ({torque_data['K']} x {torque_data['dia']}) = {torque_data['clamp_force']:,.1f} {force_unit}",
             "VDI 2230:2014 Eq. (R8) / Shigley's MDET 10e Eq. 8-27"),
        ], styles)
        story.append(Paragraph(
            "Note: K (nut factor) has typical real-world variability of +/-20-30%. "
            "Measure experimentally for safety-critical joints.",
            styles["ref"]
        ))
        story.append(Spacer(1, 10))

    # ── SECTION 4: THREAD STRIPPING (optional) ────────────────────────────────
    if strip_data:
        sec_num = "4" if torque_data else "3"
        story += _section_title(f"{sec_num}. Thread Stripping Analysis", styles)

        if is_inch:
            strip_rows = [
                ("Thread Engagement Length", f"{strip_data['engagement']:.4f}",         length_unit, "Input"),
                ("Minor Diameter",           f"{strip_data['d_minor']:.4f}",             length_unit, "ASME B1.1 / d_minor = d - 1.2990/n"),
                ("Bolt Thread Shear Area",   f"{strip_data['shear_area_ext']:.4f}",      area_unit,   "FED-STD-H28/2B §2.9"),
                ("Nut Thread Shear Area",    f"{strip_data['shear_area_int']:.4f}",      area_unit,   "FED-STD-H28/2B §2.9"),
                ("Shear Strength (tau)",     f"{strip_data['tau']:,.0f}",                stress_unit, "0.577 x Su — von Mises criterion"),
                ("Bolt Strip Load",          f"{strip_data['strip_load_ext']:,.1f}",     force_unit,  "F_strip = tau x A_s"),
                ("Nut/Hole Strip Load",      f"{strip_data['strip_load_int']:,.1f}",     force_unit,  "F_strip = tau x A_s"),
            ]
        else:
            strip_rows = [
                ("Thread Engagement Length", f"{strip_data['engagement']:.1f}",          length_unit, "Input"),
                ("Minor Diameter",           f"{strip_data['d_minor']:.3f}",              length_unit, "ISO 68-1 / d_minor = d - 1.2269p"),
                ("Bolt Thread Shear Area",   f"{strip_data['shear_area_ext']:.2f}",       area_unit,   "FED-STD-H28/2B §2.9"),
                ("Nut Thread Shear Area",    f"{strip_data['shear_area_int']:.2f}",       area_unit,   "FED-STD-H28/2B §2.9"),
                ("Shear Strength (tau)",     f"{strip_data['tau']:,.0f}",                 stress_unit, "0.577 x Su — von Mises criterion"),
                ("Bolt Strip Load",          f"{strip_data['strip_load_ext']:,.1f}",      force_unit,  "F_strip = tau x A_s"),
                ("Nut/Hole Strip Load",      f"{strip_data['strip_load_int']:,.1f}",      force_unit,  "F_strip = tau x A_s"),
            ]

        story.append(_result_table(strip_rows, styles))
        story.append(Spacer(1, 6))
        story += _equation_block([
            ("A_s (bolt) = 0.5 x pi x d_minor x Le",
             "FED-STD-H28/2B §2.9 / Shigley's MDET 10e §8-5"),
            ("F_strip = tau x A_s,   tau = 0.577 x Su  (von Mises)",
             "Shigley's MDET 10e §8-5"),
        ], styles)

        # Governing failure mode note
        governing = min(strip_data["strip_load_ext"], strip_data["strip_load_int"])
        if is_inch:
            tensile_ult = tensile_data["tensile_cap_lbf"]
        else:
            tensile_ult = tensile_data["tensile_cap_N"]

        if tensile_ult <= governing:
            governs_text = "RESULT: Bolt tensile failure governs — thread engagement is sufficient. (Preferred outcome)"
            governs_style = styles["fos_pass"]
        else:
            governs_text = "RESULT: Thread stripping governs — increase engagement length or upsize fastener."
            governs_style = styles["fos_warn"]

        story.append(Spacer(1, 4))
        story.append(Paragraph(governs_text, governs_style))
        story.append(Spacer(1, 10))

    # ── STANDARDS SUMMARY ─────────────────────────────────────────────────────
    sec_num = str(int(sec_num if strip_data else ("3" if torque_data else "2")) + 1)
    story += _section_title(f"{sec_num}. Standards References", styles)

    std_rows_data = [
        [Paragraph("Standard", styles["table_header"]),
         Paragraph("Title", styles["table_header"]),
         Paragraph("Used For", styles["table_header"])],
    ]
    all_stds = [
        ("SAE J429:2021",      "Mech. Requirements — Inch Fasteners",      "Grade proof/tensile/yield strengths"),
        ("ISO 898-1:2013",     "Mech. Properties — Metric Fasteners",      "Property class mechanical properties"),
        ("ASME B1.1-2003",     "Unified Inch Screw Threads",               "UNC thread geometry, stress area formula"),
        ("ASME B1.13M-2005",   "Metric Screw Threads — M Profile",         "Metric thread geometry, stress area formula"),
        ("VDI 2230:2014",      "Systematic Calc. of Bolted Joints",        "Torque-tension relationship (Eq. R8)"),
        ("FED-STD-H28/2B",     "Screw Thread Standards",                   "Thread stripping shear area (§2.9)"),
        ("Shigley's MDET 10e", "Mechanical Engineering Design",             "§8-2 stress area, §8-5 stripping, Eq. 8-27"),
        ("Machinery's Hbk 31e","Machinery's Handbook",                     "Tabulated tensile stress areas"),
    ]
    for std, title, use in all_stds:
        std_rows_data.append([
            Paragraph(std,   styles["table_cell"]),
            Paragraph(title, styles["table_cell"]),
            Paragraph(use,   styles["table_cell"]),
        ])

    std_table = Table(std_rows_data, colWidths=[1.5*inch, 2.4*inch, 3.1*inch], repeatRows=1)
    std_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  MID_BLUE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LIGHT_GRAY, colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(std_table)
    story.append(Spacer(1, 14))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(_footer_table(styles))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
