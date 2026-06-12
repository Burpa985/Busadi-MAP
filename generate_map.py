"""
generate_map.py
---------------
Fully dynamic map generator — no hardcoded partners or countries.
- Partners are matched to logos automatically by filename
- Countries are looked up from a built-in world coordinates dictionary
- To add a new partner logo: just upload the logo file to the Logos folder
  with the exact same name as the partner in the CSV (e.g. "New University.png")
- To add a new country: it will be found automatically if it's a real country name

Usage:
    python generate_map.py
"""

import os
import json
import base64
import ast
import io
import re
import pandas as pd
from PIL import Image

# ── Config ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PATH_2025   = os.path.join(BASE_DIR, "BUSADI Events 2025.csv")
PATH_2026   = os.path.join(BASE_DIR, "BUSADI Events 2026.csv")
LOGOS_DIR   = os.path.join(BASE_DIR, "Logos")
OUTPUT_HTML = os.path.join(BASE_DIR, "busadi_map.html")

# ── World country coordinates (comprehensive) ─────────────────────────────
WORLD_COORDS = {
    "Afghanistan": (33.9391, 67.7100), "Albania": (41.1533, 20.1683),
    "Algeria": (28.0339, 1.6596), "Argentina": (-38.4161, -63.6167),
    "Armenia": (40.0691, 45.0382), "Australia": (-25.2744, 133.7751),
    "Austria": (47.5162, 14.5501), "Azerbaijan": (40.1431, 47.5769),
    "Bangladesh": (23.6850, 90.3563), "Belarus": (53.7098, 27.9534),
    "Belgium": (50.5039, 4.4699), "Bolivia": (-16.2902, -63.5887),
    "Brazil": (-14.2350, -51.9253), "Bulgaria": (42.7339, 25.4858),
    "Cambodia": (12.5657, 104.9910), "Cameroon": (7.3697, 12.3547),
    "Canada": (56.1304, -106.3468), "Chile": (-35.6751, -71.5430),
    "China": (35.8617, 104.1954), "Colombia": (4.5709, -74.2973),
    "Croatia": (45.1000, 15.2000), "Cuba": (21.5218, -77.7812),
    "Czech Republic": (49.8175, 15.4730), "Denmark": (56.2639, 9.5018),
    "Ecuador": (-1.8312, -78.1834), "Egypt": (26.8206, 30.8025),
    "Ethiopia": (9.1450, 40.4897), "Finland": (61.9241, 25.7482),
    "France": (46.2276, 2.2137), "Georgia": (42.3154, 43.3569),
    "Germany": (51.1657, 10.4515), "Ghana": (7.9465, -1.0232),
    "Greece": (39.0742, 21.8243), "Guatemala": (15.7835, -90.2308),
    "Hong Kong": (22.3193, 114.1694), "Hungary": (47.1625, 19.5033),
    "India": (20.5937, 78.9629), "Indonesia": (-0.7893, 113.9213),
    "Iran": (32.4279, 53.6880), "Iraq": (33.2232, 43.6793),
    "Ireland": (53.1424, -7.6921), "Israel": (31.0461, 34.8516),
    "Italy": (41.8719, 12.5674), "Japan": (36.2048, 138.2529),
    "Jordan": (30.5852, 36.2384), "Kazakhstan": (48.0196, 66.9237),
    "Kenya": (-0.0236, 37.9062), "Kuwait": (29.3117, 47.4818),
    "Laos": (19.8563, 102.4955), "Lebanon": (33.8547, 35.8623),
    "Libya": (26.3351, 17.2283), "Malaysia": (4.2105, 101.9758),
    "Mexico": (23.6345, -102.5528), "Mongolia": (46.8625, 103.8467),
    "Morocco": (31.7917, -7.0926), "Mozambique": (-18.6657, 35.5296),
    "Myanmar": (21.9162, 95.9560), "Nepal": (28.3949, 84.1240),
    "Netherlands": (52.1326, 5.2913), "New Zealand": (-40.9006, 174.8860),
    "Nigeria": (9.0820, 8.6753), "North Korea": (40.3399, 127.5101),
    "Norway": (60.4720, 8.4689), "Oman": (21.4735, 55.9754),
    "Pakistan": (30.3753, 69.3451), "Palestine": (31.9522, 35.2332),
    "Panama": (8.5380, -80.7821), "Papua New Guinea": (-6.3150, 143.9555),
    "Paraguay": (-23.4425, -58.4438), "Peru": (-9.1900, -75.0152),
    "Philippines": (12.8797, 121.7740), "Poland": (51.9194, 19.1451),
    "Portugal": (39.3999, -8.2245), "Qatar": (25.3548, 51.1839),
    "Romania": (45.9432, 24.9668), "Russia": (61.5240, 105.3188),
    "Saudi Arabia": (23.8859, 45.0792), "Singapore": (1.3521, 103.8198),
    "Slovakia": (48.6690, 19.6990), "Slovenia": (46.1512, 14.9955),
    "South Africa": (-30.5595, 22.9375), "South Korea": (35.9078, 127.7669),
    "Spain": (40.4637, -3.7492), "Sri Lanka": (7.8731, 80.7718),
    "Sudan": (12.8628, 30.2176), "Sweden": (60.1282, 18.6435),
    "Switzerland": (46.8182, 8.2275), "Syria": (34.8021, 38.9968),
    "Taiwan": (23.6978, 120.9605), "Taiwan (China)": (23.6978, 120.9605),
    "Tajikistan": (38.8610, 71.2761), "Tanzania": (-6.3690, 34.8888),
    "Thailand": (15.8700, 100.9925), "Tunisia": (33.8869, 9.5375),
    "Turkey": (38.9637, 35.2433), "Turkmenistan": (38.9697, 59.5563),
    "Uganda": (1.3733, 32.2903), "Ukraine": (48.3794, 31.1656),
    "United Arab Emirates": (23.4241, 53.8478),
    "United Kingdom": (55.3781, -3.4360),
    "United States": (37.0902, -95.7129), "Uruguay": (-32.5228, -55.7658),
    "Uzbekistan": (41.3775, 64.5853), "Venezuela": (6.4238, -66.5897),
    "Vietnam": (14.0583, 108.2772), "Yemen": (15.5527, 48.5164),
    "Zambia": (-13.1339, 27.8493), "Zimbabwe": (-19.0154, 29.1549),
}


# ── Step 1: Load and clean CSV data ──────────────────────────────────────
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

    # Standardise 2025 column names
    rename_25 = {}
    for col in df25.columns:
        stripped = col.strip()
        if stripped.upper() in ("PURPOSE", "EVENT NAME"):
            rename_25[col] = "Event Name"
        elif "START" in stripped.upper():
            rename_25[col] = "Start Date"
        elif "END" in stripped.upper():
            rename_25[col] = "End Date"
        elif stripped.upper() == "COUNTRY" or stripped.upper() == "COUNTRY ":
            rename_25[col] = "Country"
        elif "IN COUNTRY" in stripped.upper() or "OVERSEAS" in stripped.upper():
            rename_25[col] = "Local/Overseas"
    df25 = df25.rename(columns=rename_25)

    # Standardise 2026 column names
    rename_26 = {}
    for col in df26.columns:
        stripped = col.strip()
        if "AUSTRALIA" in stripped.upper() or "OVERSEAS" in stripped.upper():
            rename_26[col] = "Local/Overseas"
    df26 = df26.rename(columns=rename_26)

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


# ── Step 2: Build per-country event structure ─────────────────────────────
def build_country_data(df):
    country_data = {}
    skipped = []
    for country, group in df.groupby("Country"):
        coords = WORLD_COORDS.get(country)
        if not coords:
            skipped.append(country)
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
        country_data[country] = {"coords": list(coords), "events": events}
    if skipped:
        print(f"  ⚠  No coordinates found for: {', '.join(skipped)}")
        print(f"     Add them to WORLD_COORDS in generate_map.py")
    return country_data


# ── Step 3: Dynamic logo matching ────────────────────────────────────────
def normalise(s):
    """Lowercase, remove punctuation and extra spaces for fuzzy matching."""
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()


def build_logo_index(logos_dir):
    """Scan Logos folder and build a normalised name → filepath index."""
    index = {}
    if not os.path.exists(logos_dir):
        print(f"  ⚠  Logos folder not found: {logos_dir}")
        return index
    for filename in os.listdir(logos_dir):
        name, ext = os.path.splitext(filename)
        if ext.lower() in (".jpg", ".jpeg", ".png", ".svg", ".avif", ".webp"):
            index[normalise(name)] = os.path.join(logos_dir, filename)
    return index


def find_logo(partner, logo_index):
    """Try to match a partner name to a logo file."""
    if not partner:
        return None
    key = normalise(partner)
    # Exact match
    if key in logo_index:
        return logo_index[key]
    # Partial match — logo filename is contained in partner name or vice versa
    for logo_key, path in logo_index.items():
        if logo_key in key or key in logo_key:
            return path
    return None


def encode_logo(filepath):
    """Convert any image to a base64 data URI."""
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


def build_logo_map(df, logo_index):
    """Build partner → base64 URI map for all unique partners in the data."""
    logo_map = {}
    no_logo  = []
    partners = df["Partner Name"].dropna().unique()

    for partner in partners:
        partner = partner.strip()
        if not partner:
            continue
        # Handle consortium partners (comma-separated multiple orgs)
        if "," in partner:
            parts = [p.strip() for p in partner.split(",")]
            uris  = []
            for part in parts:
                path = find_logo(part, logo_index)
                uris.append(encode_logo(path) if path else "")
            logo_map[partner] = {"type": "consortium", "uris": uris}
        else:
            path = find_logo(partner, logo_index)
            if path:
                logo_map[partner] = {"type": "single", "uri": encode_logo(path)}
            else:
                no_logo.append(partner)

    if no_logo:
        print(f"  ⚠  No logo found for: {', '.join(no_logo)}")
        print(f"     Add logo files to Logos/ with the partner name as filename")

    return logo_map


# ── Step 4: Generate HTML ─────────────────────────────────────────────────
def generate_html(country_data, logo_map):
    country_data_js = json.dumps(country_data)
    logo_map_js     = json.dumps(logo_map)

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
  .badge-year-2027 {{ background:#6c3483; color:white; }}
  .badge-year-2028 {{ background:#1a5276; color:white; }}
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
const COUNTRY_DATA = {country_data_js};

function getLogoHTML(partner) {{
  if (!partner) return '<div class="partner-logo-placeholder">🏛️</div>';
  const entry = LOGO_MAP[partner];
  if (!entry) return '<div class="partner-logo-placeholder">🏛️</div>';
  if (entry.type === 'consortium') {{
    const imgs = entry.uris.filter(u => u).map(u => `<img src="${{u}}">`).join('');
    return `<div class="collage">${{imgs}}</div>`;
  }}
  return `<img class="partner-logo" src="${{entry.uri}}">`;
}}

function showSidebar(country, data) {{
  document.getElementById('sidebar').classList.remove('hidden');
  document.getElementById('default-message').style.display = 'none';
  document.getElementById('sidebar-country').textContent = country;
  document.getElementById('event-count').textContent = `${{data.events.length}} event${{data.events.length !== 1 ? 's' : ''}}`;
  document.getElementById('event-list').innerHTML = data.events.map(ev => `
    <div class="event-card">
      <div class="event-header">
        ${{getLogoHTML(ev.partner)}}
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

    print("\n3. Scanning logos folder and matching partners...")
    logo_index = build_logo_index(LOGOS_DIR)
    print(f"   Found {len(logo_index)} logo files")
    logo_map = build_logo_map(df, logo_index)
    matched = sum(1 for v in logo_map.values())
    print(f"   Matched {matched} partners to logos")

    print("\n4. Generating HTML...")
    html = generate_html(country_data, logo_map)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = os.path.getsize(OUTPUT_HTML) // 1024
    print(f"   Saved to {OUTPUT_HTML} ({size_kb} KB)")

    print("\n✓ Done! Open busadi_map.html in your browser to view.")
    print("\nTo add new events:")
    print("  1. Update the CSV files")
    print("  2. Run this script again")
    print("\nTo add a new partner logo:")
    print("  1. Save the logo to the Logos/ folder")
    print("     Name it exactly as the partner appears in the CSV")
    print("     e.g. 'New University.png'")
    print("  2. Run this script again")
    print("\nTo add a new country not in the list:")
    print("  1. Add it to WORLD_COORDS in this script")
    print("  2. Run this script again")


if __name__ == "__main__":
    main()
