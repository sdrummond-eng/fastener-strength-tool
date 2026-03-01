import sys
import math

# ======================================================
# FASTENER STRENGTH LOOKUP TOOL
# Metric + UNC fasteners
# ======================================================


# ======================================================
# PROPERTY CLASSES / GRADES (MPa)
# (yield, tensile, proof)
# ======================================================

METRIC_GRADES = {
    "4.6":  (240, 400, 225),
    "5.8":  (400, 500, 380),
    "8.8":  (640, 800, 580),
    "10.9": (940, 1040, 830),
    "12.9": (1100, 1220, 970),
}

INCH_GRADES = {
    "Grade2": (390, 620, 380),
    "Grade5": (635, 830, 580),
    "Grade8": (940, 1040, 830),
}


# ======================================================
# METRIC COARSE PITCHES (ISO)
# size(mm) : pitch(mm)
# ======================================================

METRIC_PITCH = {
    3:0.5, 4:0.7, 5:0.8, 6:1.0, 7:1.0, 8:1.25,
    10:1.5, 12:1.75, 14:2.0, 16:2.0, 18:2.5,
    20:2.5, 22:2.5, 24:3.0, 27:3.0, 30:3.5,
    33:3.5, 36:4.0
}


# ======================================================
# UNC THREADS
# ======================================================

UNC_TPI = {
    "#4":40, "#6":32, "#8":32, "#10":24, "#12":24,
    "1/4":20, "5/16":18, "3/8":16, "7/16":14,
    "1/2":13, "9/16":12, "5/8":11, "3/4":10,
    "7/8":9, "1":8, "1-1/8":7, "1-1/4":7,
    "1-3/8":6, "1-1/2":6
}

NUMBER_DIAMETERS = {
    "#4":0.112,
    "#6":0.138,
    "#8":0.164,
    "#10":0.190,
    "#12":0.216
}


# ======================================================
# STRESS AREA FORMULAS
# ======================================================

def metric_stress_area(d_mm, pitch):
    # ISO tensile stress area
    return math.pi/4 * (d_mm - 0.9382*pitch)**2


def inch_stress_area(d_in, tpi):
    # in² → mm²
    return math.pi/4 * (d_in - 0.9743/tpi)**2 * 645.16


# ======================================================
# SIZE PARSING
# ======================================================

def inch_diameter(size):
    if size.startswith("#"):
        return NUMBER_DIAMETERS[size]

    if "-" in size:  # 1-1/4
        whole, frac = size.split("-")
        num, den = frac.split("/")
        return float(whole) + float(num)/float(den)

    if "/" in size:  # 1/4
        num, den = size.split("/")
        return float(num)/float(den)

    return float(size)


# ======================================================
# LOOKUP FUNCTIONS
# ======================================================

def metric_lookup(grade, size):
    d = int(size.replace("M", ""))

    if d not in METRIC_PITCH:
        print("Metric size not supported")
        return

    pitch = METRIC_PITCH[d]
    area = metric_stress_area(d, pitch)

    ys, uts, proof = METRIC_GRADES[grade]
    proof_force = area * proof

    print(f"\nMetric {size}  Class {grade}")
    print(f"Stress area: {area:.1f} mm²")
    print(f"Yield: {ys} MPa")
    print(f"Tensile: {uts} MPa")
    print(f"Proof: {proof} MPa")
    print(f"Proof force: {proof_force/1000:.1f} kN")


def inch_lookup(grade, size):
    if size not in UNC_TPI:
        print("UNC size not supported")
        return

    d = inch_diameter(size)
    tpi = UNC_TPI[size]

    area = inch_stress_area(d, tpi)

    ys, uts, proof = INCH_GRADES[grade]
    proof_force = area * proof

    print(f"\nUNC {size}\"  {grade}")
    print(f"Stress area: {area:.1f} mm²")
    print(f"Yield: {ys} MPa")
    print(f"Tensile: {uts} MPa")
    print(f"Proof: {proof} MPa")
    print(f"Proof force: {proof_force/1000:.1f} kN")


# ======================================================
# MAIN PROGRAM
# ======================================================

def run_lookup(grade, size):
    if size.startswith("M"):
        metric_lookup(grade, size)
    else:
        inch_lookup(grade, size)


if __name__ == "__main__":

    # CLI mode
    if len(sys.argv) == 3:
        run_lookup(sys.argv[1], sys.argv[2])
        sys.exit()

    # Interactive mode
    print("\n=== Fastener Strength Lookup Tool ===")
    print("Press Enter anytime to quit\n")

    while True:
        grade = input("Enter grade/class: ").strip()
        if not grade:
            break

        size = input("Enter size (M10, 1/2, 1-1/4, #10): ").strip()
        if not size:
            break

        run_lookup(grade, size)

        print("\n-----------------------------\n")