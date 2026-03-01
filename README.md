# 🔩 Fastener Strength Calculator

A web-based engineering tool for fastener strength calculations, joint design, and manufacturing considerations.

**[▶ Launch the App](https://your-app.streamlit.app)** ← update after deployment

---

## Features

| Module | Calculations | Standards |
|---|---|---|
| **Tensile Strength** | Proof load, tensile & yield capacity, FoS | SAE J429:2021, ISO 898-1:2013 |
| **Torque–Tension** | Clamp force from torque, required torque from target preload | VDI 2230:2014 |
| **Thread Stripping** | Bolt & nut shear area, strip load, governing failure mode | FED-STD-H28/2B, Shigley's §8-5 |

**Fastener systems supported:**
- Inch UNC: #4 through 1-1/2", SAE Grades 2, 5, 8
- Metric coarse: M3–M36, ISO Property Classes 4.6, 5.8, 8.8, 10.9, 12.9

---

## Running Locally (VS Code)

```bash
# 1. Clone the repo
git clone https://github.com/sdrummond-eng/fastener-strength-tool
cd fastener-strength-tool

# 2. Install dependencies (one time)
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

---

## Deploying to the Web (Free — Streamlit Cloud)

1. Push this code to your GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub → **"New app"**
4. Select: repo = `fastener-strength-tool`, branch = `main`, main file = `app.py`
5. Click **Deploy** — your public URL is ready in ~60 seconds

No server, no Docker, no cost.

---

## Standards Referenced

| Standard | Used For |
|---|---|
| SAE J429:2021 | Inch grade mechanical properties (proof, tensile, yield) |
| ISO 898-1:2013 | Metric property class mechanical properties |
| ASME B1.1-2003 | UNC thread geometry, tensile stress area |
| ASME B1.13M-2005 | Metric thread geometry, tensile stress area |
| VDI 2230:2014 | Torque–tension (nut factor method), Eq. (R8) |
| FED-STD-H28/2B §2.9 | Thread stripping shear area |
| Shigley's MDET 10e §8-2, §8-5, Eq. 8-27 | Stress area, stripping, torque-tension |
| Machinery's Handbook 31e | Tabulated tensile stress area values |

---

## File Structure

```
fastener-strength-tool/
├── app.py               ← Streamlit web app (UI)
├── fastener_data.py     ← Grade data, thread data, calculation functions
├── requirements.txt     ← Streamlit dependency
└── README.md
```

`fastener_data.py` is pure Python with no UI dependency — calculations can be
imported and used independently of Streamlit (e.g., in scripts or notebooks).

---

## Bug Fixes from v1.0

| Issue | v1.0 | Fixed |
|---|---|---|
| Inch stress area | Converted in² → mm² incorrectly | Tabulated in² values, no conversion |
| Inch grade strength values | Used ISO MPa values for SAE grades | Corrected to SAE J429 psi |
| Standard references | None | All equations cite governing standard |
| Thread stripping | Not implemented | Added |
| Torque–tension | Not implemented | Added |

---

## Limitations

- Properties shown are for common diameter ranges; some grades specify reduced values
  at larger diameters. Always verify against the full standard table.
- The nut factor K (torque–tension) has ±20–30% real-world variability. Measure
  experimentally for critical joints.
- No fatigue, dynamic loading, temperature, corrosion, or coating effects.
- Not a substitute for review by a licensed engineer on safety-critical applications.

---

## Contributing

Issues and pull requests welcome. If you find a calculation error or a missing thread
size/grade, please open an issue with the relevant standard reference.

---

*Developed by [@sdrummond-eng](https://github.com/sdrummond-eng)*
