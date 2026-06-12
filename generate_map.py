"""
generate_map.py
---------------
Run this script whenever new events are added to the CSV files.
It will regenerate busadi_map.html with the latest data.

Usage:
    python generate_map.py
"""

import os
import json
import base64
import ast
import io
import pandas as pd
from PIL import Image

# ── Config ────────────────────────────────────────────────────────────────
PATH_2025  = r"C:\Users\Admin\Desktop\BUSADI\BUSADI Events 2025.csv"
PATH_2026  = r"C:\Users\Admin\Desktop\BUSADI\BUSADI Events 2026.csv"
LOGOS_DIR  = r"C:\Users\Admin\Desktop\BUSADI\Logos"
OUTPUT_HTML = r"C:\Users\Admin\Desktop\BUSADI\busadi_map.html"

# ── Country coordinates ───────────────────────────────────────────────────
COUNTRY_COORDS = {
    "Singapore":      (1.3521,   103.8198),
    "Hong Kong":      (22.3193,  114.1694),
    "Vietnam":        (14.0583,  108.2772),
    "China":          (35.8617,  104.1954),
    "Indonesia":      (-0.7893,  113.9213),
    "Malaysia":       (4.2105,   101.9758),
    "Thailand":       (15.8700,  100.9925),
    "Germany":        (51.1657,   10.4515),
    "Canada":         (56.1304, -106.3468),
    "Taiwan (China)": (23.6978,  120.9605),
    "Taiwan":         (23.6978,  120.9605),
    "Australia":      (-25.2744, 133.7751),
    "Chile":          (-35.6751, -71.5430),
    "South Korea":    (35.9078,  127.7669),
    "Japan":          (36.2048,  138.2529),
    "India":          (20.5937,   78.9629),
    "United Kingdom": (55.3781,   -3.4360),
    "United States":  (37.0902,  -95.7129),
}

# ── Partner → logo filename mapping ──────────────────────────────────────
PARTNER_LOGO_FILES = {
    "Antai College of Economics and Management / Shanghai Jiao Tong University": "Antai College of Economics and Management.jpg",
    "BINUS University":                          "BINUS University.png",
    "Bank Indonesia":                            "Bank Indonesia.jpg",
    "Boustead Singapore":                        "Boustead Singapore.jpg",
    "Yu Loon Wong":                              "Boustead Singapore.jpg",
    "City University of Hong Kong":              "City University of Hong Kong.jpg",
    "CUHK":                                      "CUHK.jpg",
    "East China Normal University":              "East China Normal University.png",
    "Chunghua County Council":                   "Emblem_of_Changhua_County.svg",
    "Enterprise Singapore":                      "Enterprise Singapore.jpg",
    "Fudan University":                          "Fudan University.jpg",
    "HKUST":                                     "HKUST.avif",
    "Hamburg University of Technology":          "Hamburg University of Technology.png",
    "Hong Kong Metropolitan University":         "Hong Kong Metropolitan University.jpg",
    "Investment NSW":                            "Investment NSW.jpg",
    "Nanyang Technological University":          "Nanyang Technological University.png",
    "OJK (Financial Services Authority Indonesia)": "OJK (Financial Services Authority Indonesia).png",
    "Sarawak Digital Economy Corporation":       "Sarawak Digital Economy Corporation.png",
    "Shanghai Jiao Tong University":             "Shanghai Jiao Tong University.png",
    "SIM Global Education":                      "SIM Global Education.png",
    "Singapore Institute of Technology":         "Singapore Institute of Technology.png",
    "Singapore Parliament":                      "Singapore Parliament.jpg",
    "StudyNSW":                                  "StudyNSW.png",
    "Sungkyunkwan University":                   "Sungkyunkwan University.jpg",
    "Thammasat University":                      "Thammasat University.png",
    "The Hong Kong Polytechnic University":      "The Hong Kong Polytechnic University.png",
    "Tsinghua University":                       "Tsinghua University.png",
    "UNSW":                                      "UNSW.png",
    "Universitas Indonesia":                     "Universitas Indonesia.jpg",
    "University of Calgary":                     "University of Calgary.png",
    "Vietnam National University - University of Economics and Business": "Vietnam National University - University of Economics and Business.jpg",
    "Vietnam National University":               "Vietnam National University.jpg",
    "Weslink International School":              "Weslink International School.png",
}

# Consortium partners — shown as a collage of logos
CONSORTIUM_PARTNERS = {
    "CUHK, HKUST, CityU HK, Fudan University, Shanghai Jiao Tong University": [
        "CUHK.jpg",
        "HKUST.avif",
        "City University of Hong Kong.jpg",
        "Fudan University.jpg",
        "Shanghai Jiao Tong University.png",
    ]
}


# ── Step 1: Load and clean data ───────────────────────────────────────────
def parse_category(val):
    """Extract first category from JSON list string like '[\"Partner Meetings\"]'"""
    try:
        parsed = ast.literal_eval(str(val))
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[0].strip()
    except Exception:
        pass
    return str(val).strip()


def load_data(path_2025, path_2026):
    df25 = pd.read_csv(path_2025)
    df26 = pd.read_csv(path_2026)

    df25 = df25.rename(columns={
        "Purpose":              "Event Name",
        "START DATE":           "Start Date",
        "END DATE":             "End Date",
        "COUNTRY ":             "Country",
        "CITY":                 "City",
        "In Country or Overseas": "Local/Overseas",
    })
    df26 = df26.rename(columns={"Australia or Overseas": "Local/Overseas"})

    df25["Year"] = 2025
    df26["Year"] = 2026

    df25["Local/Overseas"] = df25["Local/Overseas"].str.strip().replace({"In Country": "Local"})
    df26["Local/Overseas"] = df26["Local/Overseas"].str.strip().replace({"Australia": "Local"})

    df = pd.concat([df25, df26], ignore_index=True)
    df["Country"]      = df["Country"].str.strip()
    df["Partner Name"] = df["Partner Name"].fillna("").str.strip()
    df["Event Name"]   = df["Event Name"].fillna("").str.strip()
    df["Category"]     = df["Category"].apply(parse_category).replace({
        "Industry Partnership": "Industry Partnerships"
    })
    df["Start Date"]   = pd.to_datetime(df["Start Date"], errors="coerce", dayfirst=True)
    df["Month"]        = df["Start Date"].dt.strftime("%B %Y")

    return df


# ── Step 2: Build per-country event data ─────────────────────────────────
def build_country_data(df):
    country_data = {}
    for country, group in df.groupby("Country"):
        if country not in COUNTRY_COORDS:
            print(f"  ⚠  No coordinates for '{country}' — skipping")
            continue
        events = []
        for _, row in group.iterrows():
            events.append({
                "name":     row["Event Name"],
                "partner":  row["Partner Name"] if row["Partner Name"] else None,
                "date":     row["Month"],
                "category": row["Category"],
                "year":     int(row["Year"]),
            })
        country_data[country] = {
            "coords": list(COUNTRY_COORDS[country]),
            "events": events,
        }
    return country_data


# ── Step 3: Encode logos to base64 ───────────────────────────────────────
def encode_logo(filepath):
    """Convert any image (jpg, png, svg, avif) to a base64 data URI."""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".svg":
            with open(filepath, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/svg+xml;base64,{b64}"
        else:
            img = Image.open(filepath)
            img = img.convert("RGBA" if ext == ".png" else "RGB")
            buf = io.BytesIO()
            fmt  = "PNG" if ext == ".png" else "JPEG"
            mime = "image/png" if ext == ".png" else "image/jpeg"
            img.save(buf, format=fmt, quality=85)
            b64 = base64.b64encode(buf.getvalue()).decode()
            return f"data:{mime};base64,{b64}"
    except Exception as e:
        print(f"  ⚠  Could not encode {filepath}: {e}")
        return ""


def build_logo_maps(logos_dir):
    """Return (logo_map, consortium_map) with base64 data URIs."""
    logo_map = {}
    for partner, filename in PARTNER_LOGO_FILES.items():
        path = os.path.join(logos_dir, filename)
        if os.path.exists(path):
            logo_map[partner] = encode_logo(path)
        else:
            print(f"  ⚠  Logo not found: {filename}")
            logo_map[partner] = ""

    consortium_map = {}
    for partner, filenames in CONSORTIUM_PARTNERS.items():
        uris = []
        for filename in filenames:
            path = os.path.join(logos_dir, filename)
            uris.append(encode_logo(path) if os.path.exists(path) else "")
        consortium_map[partner] = uris

    return logo_map, consortium_map


# ── Step 4: Generate HTML ─────────────────────────────────────────────────
def generate_html(country_data, logo_map, consortium_map):
    country_data_js  = json.dumps(country_data)
    logo_map_js      = json.dumps(logo_map)
    consortium_map_js = json.dumps(consortium_map)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BUSADI International Engagement Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; display:flex; height:100vh; overflow:hidden; }}
  #map {{ flex:1; height:100vh; }}
  #sidebar {{
    width:360px; min-width:360px; height:100vh; background:white;
    box-shadow:-4px 0 20px rgba(0,0,0,0.1); display:flex; flex-direction:column;
    transition:transform 0.3s ease; z-index:1000; overflow:hidden;
  }}
  #sidebar.hidden {{ transform:translateX(360px); }}
  #sidebar-header {{ background:#002147; color:white; padding:20px; flex-shrink:0; }}
  #sidebar-header h2 {{ font-size:16px; font-weight:600; color:#FFD100; margin-bottom:4px; }}
  #sidebar-header p {{ font-size:12px; color:rgba(255,255,255,0.7); }}
  #event-count {{ font-size:12px; color:rgba(255,255,255,0.6); margin-top:6px; }}
  #sidebar-body {{ overflow-y:auto; flex:1; padding:16px; }}
  .event-card {{ border:0.5px solid #e8e8e8; border-radius:10px; padding:14px; margin-bottom:12px; background:#fafafa; }}
  .event-card:hover {{ background:#f0f4ff; border-color:#002147; }}
  .event-header {{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }}
  .partner-logo {{ width:40px; height:40px; object-fit:contain; border-radius:6px; border:0.5px solid #e0e0e0; background:white; padding:2px; flex-shrink:0; }}
  .partner-logo-placeholder {{ width:40px; height:40px; border-radius:6px; background:#e8edf5; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }}
  .event-name {{ font-size:13px; font-weight:600; color:#002147; line-height:1.3; }}
  .partner-name {{ font-size:11px; color:#666; margin-top:2px; }}
  .event-meta {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }}
  .badge {{ font-size:10px; padding:3px 8px; border-radius:20px; font-weight:500; }}
  .badge-date {{ background:#e8f0fe; color:#1a56c4; }}
  .badge-category {{ background:#e8f5e9; color:#2e7d32; }}
  .badge-year-2025 {{ background:#002147; color:#FFD100; }}
  .badge-year-2026 {{ background:#C0392B; color:white; }}
  .collage {{ display:flex; flex-wrap:wrap; gap:4px; width:40px; }}
  .collage img {{ width:17px; height:17px; object-fit:contain; border-radius:3px; border:0.5px solid #e0e0e0; background:white; }}
  #default-message {{ display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:#999; text-align:center; padding:40px 20px; }}
  #default-message .icon {{ font-size:48px; margin-bottom:16px; }}
  #default-message h3 {{ font-size:15px; color:#555; margin-bottom:8px; }}
  #default-message p {{ font-size:13px; line-height:1.5; }}
  .legend {{ position:absolute; bottom:30px; left:20px; background:white; border-radius:10px; padding:12px 16px; z-index:999; box-shadow:0 2px 12px rgba(0,0,0,0.15); font-size:12px; }}
  .legend-title {{ font-weight:600; color:#002147; margin-bottom:8px; font-size:13px; }}
  .legend-item {{ display:flex; align-items:center; gap:8px; margin-bottom:5px; }}
  .legend-dot {{ border-radius:50%; background:#002147; opacity:0.8; }}
</style>
</head>
<body>
<div id="map"></div>
<div id="sidebar" class="hidden">
  <div id="sidebar-header">
    <h2 id="sidebar-country">Country</h2>
    <p>BUSADI International Engagement</p>
    <p id="event-count"></p>
  </div>
  <div id="sidebar-body">
    <div id="default-message">
      <div class="icon">🌏</div>
      <h3>Hover over a country</h3>
      <p>Mouse over a bubble on the map to see events and partners for that location.</p>
    </div>
    <div id="event-list"></div>
  </div>
</div>
<div class="legend">
  <div class="legend-title">Events by Country</div>
  <div class="legend-item"><div class="legend-dot" style="width:8px;height:8px"></div> 1–2 events</div>
  <div class="legend-item"><div class="legend-dot" style="width:12px;height:12px"></div> 3–5 events</div>
  <div class="legend-item"><div class="legend-dot" style="width:18px;height:18px"></div> 6+ events</div>
</div>
<script>
const LOGO_MAP = {logo_map_js};
const CONSORTIUM_LOGOS = {consortium_map_js};
const COUNTRY_DATA = {country_data_js};

function getLogoHTML(partner) {{
  if (!partner) return '<div class="partner-logo-placeholder">🏛️</div>';
  if (CONSORTIUM_LOGOS[partner]) {{
    const imgs = CONSORTIUM_LOGOS[partner].map(src => `<img src="${{src}}">`).join('');
    return `<div class="collage">${{imgs}}</div>`;
  }}
  if (LOGO_MAP[partner]) return `<img class="partner-logo" src="${{LOGO_MAP[partner]}}">`;
  return '<div class="partner-logo-placeholder">🏛️</div>';
}}

function deduplicateEvents(events) {{
  return events.map(ev => {{ return {{ ...ev, isDuplicate: false }}; }});
}}

function showSidebar(country, data) {{
  document.getElementById('sidebar').classList.remove('hidden');
  document.getElementById('default-message').style.display = 'none';
  document.getElementById('sidebar-country').textContent = country;
  const events = deduplicateEvents(data.events);
  document.getElementById('event-count').textContent = `${{events.length}} event${{events.length !== 1 ? 's' : ''}}`;
  document.getElementById('event-list').innerHTML = events.map(ev => `
    <div class="event-card">
      <div class="event-header">
        ${{ev.isDuplicate ? '<div class="partner-logo-placeholder" style="opacity:0"></div>' : getLogoHTML(ev.partner)}}
        <div>
          <div class="event-name">${{ev.name}}</div>
          ${{ev.partner ? `<div class="partner-name">${{ev.partner}}</div>` : ''}}
        </div>
      </div>
      <div class="event-meta">
        <span class="badge badge-date">${{ev.date}}</span>
        <span class="badge badge-category">${{ev.category}}</span>
        <span class="badge badge-year-${{ev.year}}">${{ev.year}}</span>
      </div>
    </div>
  `).join('');
}}

const map = L.map('map').setView([20, 95], 3);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 19
}}).addTo(map);

Object.entries(COUNTRY_DATA).forEach(([country, data]) => {{
  const count = data.events.length;
  const radius = 8 + Math.sqrt(count) * 6;
  const circle = L.circleMarker(data.coords, {{
    radius, fillColor: '#002147', color: '#FFD100', weight: 2, opacity: 1, fillOpacity: 0.75
  }}).addTo(map);
  const icon = L.divIcon({{
    className: '',
    html: `<div style="color:white;font-size:11px;font-weight:600;text-align:center;line-height:${{radius*2}}px;width:${{radius*2}}px;height:${{radius*2}}px;margin-left:-${{radius}}px;margin-top:-${{radius}}px">${{count}}</div>`,
    iconSize: [radius*2, radius*2], iconAnchor: [radius, radius]
  }});
  L.marker(data.coords, {{ icon, interactive: false }}).addTo(map);
  circle.on('mouseover', () => showSidebar(country, data));
  circle.on('click', () => showSidebar(country, data));
}});
</script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print("BUSADI Map Generator")
    print("=" * 40)

    print("\n1. Loading CSV data...")
    df = load_data(PATH_2025, PATH_2026)
    print(f"   Loaded {len(df)} events ({(df['Year']==2025).sum()} in 2025, {(df['Year']==2026).sum()} in 2026)")

    print("\n2. Building country data...")
    country_data = build_country_data(df)
    print(f"   Found {len(country_data)} countries")

    print("\n3. Encoding logos...")
    logo_map, consortium_map = build_logo_maps(LOGOS_DIR)
    loaded = sum(1 for v in logo_map.values() if v)
    print(f"   Encoded {loaded}/{len(logo_map)} logos successfully")

    print("\n4. Generating HTML...")
    html = generate_html(country_data, logo_map, consortium_map)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUTPUT_HTML) // 1024
    print(f"   Saved to {OUTPUT_HTML} ({size_kb} KB)")

    print("\n✓ Done! Open busadi_map.html in your browser to view.")
    print("\nTo add a new partner logo:")
    print("  1. Add the logo file to your Logos folder")
    print("  2. Add an entry to PARTNER_LOGO_FILES in this script")
    print("  3. Run this script again")


if __name__ == "__main__":
    main()
