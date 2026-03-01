import math
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ======================================================
# FASTENER STRENGTH GUI CALCULATOR (UPGRADED)
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
# THREAD DATA
# ======================================================

METRIC_PITCH = {
    3:0.5, 4:0.7, 5:0.8, 6:1.0, 7:1.0, 8:1.25,
    10:1.5, 12:1.75, 14:2.0, 16:2.0, 18:2.5,
    20:2.5, 22:2.5, 24:3.0, 27:3.0, 30:3.5,
    33:3.5, 36:4.0
}

UNC_TPI = {
    "#4":40, "#6":32, "#8":32, "#10":24, "#12":24,
    "1/4":20, "5/16":18, "3/8":16, "7/16":14,
    "1/2":13, "9/16":12, "5/8":11, "3/4":10,
    "7/8":9, "1":8, "1-1/8":7, "1-1/4":7,
    "1-3/8":6, "1-1/2":6
}

NUMBER_DIAMETERS = {
    "#4":0.112, "#6":0.138, "#8":0.164, "#10":0.190, "#12":0.216
}


# ======================================================
# CALCULATIONS
# ======================================================

def metric_area(d, pitch):
    return math.pi/4 * (d - 0.9382*pitch)**2


def inch_area(d, tpi):
    return math.pi/4 * (d - 0.9743/tpi)**2 * 645.16  # convert to mm²


def inch_diameter(size):
    if size.startswith("#"):
        return NUMBER_DIAMETERS[size]

    if "-" in size:
        whole, frac = size.split("-")
        n, d = frac.split("/")
        return float(whole) + float(n)/float(d)

    if "/" in size:
        n, d = size.split("/")
        return float(n)/float(d)

    return float(size)


def format_inch_label(size):
    return f"{size} ({inch_diameter(size):.3f} in)"


# ======================================================
# GUI LOGIC
# ======================================================

def update_dropdowns(*args):
    system = system_var.get()

    if system == "Metric":
        size_combo["values"] = [f"M{s}" for s in METRIC_PITCH.keys()]
        grade_combo["values"] = list(METRIC_GRADES.keys())
    else:
        size_combo["values"] = [format_inch_label(s) for s in UNC_TPI.keys()]
        grade_combo["values"] = list(INCH_GRADES.keys())

    size_combo.set("")
    grade_combo.set("")
    result_text.delete(1.0, tk.END)


def convert_stress(value_mpa):
    return value_mpa * 0.145038 if unit_var.get() == "ksi" else value_mpa


def convert_force(value_kn):
    return value_kn * 224.809 if unit_var.get() == "lbf" else value_kn


def calculate():
    if not size_var.get() or not grade_var.get():
        return

    system = system_var.get()
    grade = grade_var.get()
    size = size_var.get().split(" ")[0]

    sf = float(sf_var.get() or 1)

    if system == "Metric":
        d = int(size.replace("M", ""))
        pitch = METRIC_PITCH[d]
        area = metric_area(d, pitch)
        ys, uts, proof = METRIC_GRADES[grade]
    else:
        d = inch_diameter(size)
        tpi = UNC_TPI[size]
        area = inch_area(d, tpi)
        ys, uts, proof = INCH_GRADES[grade]

    proof_force = area * proof / 1000  # kN
    allowable = proof_force / sf

    stress_unit = unit_var.get()
    force_unit = force_var.get()

    ys = convert_stress(ys)
    uts = convert_stress(uts)
    proof = convert_stress(proof)
    proof_force = convert_force(proof_force)
    allowable = convert_force(allowable)

    result = (
        f"Stress area: {area:.2f} mm²\n"
        f"Yield: {ys:.1f} {stress_unit}\n"
        f"Tensile: {uts:.1f} {stress_unit}\n"
        f"Proof: {proof:.1f} {stress_unit}\n\n"
        f"Proof force: {proof_force:.1f} {force_unit}\n"
        f"Allowable (SF={sf}): {allowable:.1f} {force_unit}"
    )

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, result)


def clear_fields():
    size_combo.set("")
    grade_combo.set("")
    result_text.delete(1.0, tk.END)


def copy_results():
    root.clipboard_clear()
    root.clipboard_append(result_text.get(1.0, tk.END))


def export_csv():
    text = result_text.get(1.0, tk.END).strip()
    if not text:
        return

    filename = filedialog.asksaveasfilename(defaultextension=".csv")
    if not filename:
        return

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        for line in text.split("\n"):
            writer.writerow([line])

    messagebox.showinfo("Saved", "CSV exported successfully")


# ======================================================
# GUI LAYOUT
# ======================================================

root = tk.Tk()
root.title("Fastener Strength Calculator")
root.geometry("420x470")

system_var = tk.StringVar(value="Metric")
size_var = tk.StringVar()
grade_var = tk.StringVar()
unit_var = tk.StringVar(value="MPa")
force_var = tk.StringVar(value="kN")
sf_var = tk.StringVar(value="1")

# ---- dropdowns ----
ttk.Label(root, text="System").pack()
ttk.Combobox(root, textvariable=system_var,
             values=["Metric", "Imperial"],
             state="readonly").pack()

ttk.Label(root, text="Size").pack()
size_combo = ttk.Combobox(root, textvariable=size_var, state="readonly")
size_combo.pack()

ttk.Label(root, text="Grade").pack()
grade_combo = ttk.Combobox(root, textvariable=grade_var, state="readonly")
grade_combo.pack()

# ---- units ----
ttk.Label(root, text="Stress Units").pack()
ttk.Combobox(root, textvariable=unit_var,
             values=["MPa", "ksi"],
             state="readonly").pack()

ttk.Label(root, text="Force Units").pack()
ttk.Combobox(root, textvariable=force_var,
             values=["kN", "lbf"],
             state="readonly").pack()

# ---- safety factor ----
ttk.Label(root, text="Safety Factor").pack()
ttk.Entry(root, textvariable=sf_var).pack()

# ---- buttons ----
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=8)

ttk.Button(btn_frame, text="Calculate", command=calculate).grid(row=0, column=0, padx=3)
ttk.Button(btn_frame, text="Copy", command=copy_results).grid(row=0, column=1, padx=3)
ttk.Button(btn_frame, text="Export CSV", command=export_csv).grid(row=0, column=2, padx=3)
ttk.Button(btn_frame, text="Clear", command=clear_fields).grid(row=0, column=3, padx=3)

# ---- results box ----
result_text = tk.Text(root, height=12, width=45)
result_text.pack(pady=8)

# ---- bindings ----
system_var.trace_add("write", update_dropdowns)
update_dropdowns()

root.mainloop()