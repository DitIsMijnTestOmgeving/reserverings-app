import os
import pandas as pd
import streamlit as st
from supabase import create_client

# Pagina-instelling
st.set_page_config(page_title="Sleuteloverzicht", page_icon="🔑", layout="wide")

# Supabase-verbinding
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supa = create_client(url, key)

# Sleutellijst
def load_keys():
    return {
        "Bibliotheek Opmeer": "1, 2, 3",
        "Boevenhoeve": "43",
        "Bovenwoningen Spanbroek": "15",
        "Brandweer Spanbroek": "14",
        "Electrakast Rokersplein": "57",
        "Gaskasten algemeen": "52, 53",
        "Gemeentehuis": "26,27,28,29,30,31",
        "Gemeentewerf Spanbroek": "13",
        "General key (sport)": "55, 56",
        "Gymzaal Aartswoud": "16, 17",
        "Gymzaal De Weere": "36, 37",
        "Gymzaal Hoogwoud": "32, 33",
        "Gymzaal Opmeer": "46, 47, 48, 49",
        "Gymzaal Spanbroek": "34, 35",
        "Hertenkamp Hoogwoud": "18",
        "IJsbaangebouw": "40",
        "Muziekschool Opmeer": "4",
        "Peuterspeelzaal Boevenhoeve": "42",
        "Peuterspeelzaal de Kikkerhoek": "11, 12",
        "Peuterspeelzaal Hummeltjeshonk": "44",
        "Raadhuis Hoogwoud": "19",
        "Raadhuis Spanbroek": "20, 21, 22",
        "Telefoon gymzalen": "54",
        "Theresiahuis": "5, 6",
        "Toren Aartswoud": "23, 24",
        "Toren Wadway": "25",
        "Verenigingsgebouw": "7, 8, 9, 10",
        "Watertappunt Hoogwoud": "50",
        "Wijksteunpunt Lindehof": "41",
        "Zaalvoetbalhal de Weyver": "51",
        "Zwembad De Weijver": "38, 39"
    }

st.title("🔑 Sleuteloverzicht")

# Data ophalen
bookings = supa.table("bookings").select("*").execute().data
key_map = load_keys()

gebruikte_sleutels = set()
for r in bookings:
    if r["status"] in ("Goedgekeurd", "Wachten"):
        ks = r.get("access_keys") or ""
        gebruikte_sleutels.update(k.strip() for k in ks.split(",") if k.strip())

alle_sleutels = []
for sleutels in key_map.values():
    alle_sleutels.extend(s.strip() for s in sleutels.split(","))
alle_sleutels = sorted(set(alle_sleutels), key=lambda x: int(x))

html = """
<style>
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
    gap: 6px;
    max-width: 100%;
}
.tegel {
    background-color: #90ee90;
    width: 40px;
    height: 40px;
    border-radius: 4px;
    text-align: center;
    line-height: 40px;
    font-weight: bold;
    font-size: 12px;
}
</style>
<div class='grid'>
"""

for nr in alle_sleutels:
    kleur = "#ff6961" if nr in gebruikte_sleutels else "#90ee90"
    locatie = next((loc for loc, ks in key_map.items() if nr in ks), "")
    html += f"<div class='tegel' title='{locatie}' style='background-color: {kleur};'>{nr}</div>"

html += "</div>"
st.markdown(html, unsafe_allow_html=True)

# Tabelweergave
st.markdown("### 📋 Uitgegeven sleutels")

sleutel_reserveringen = [
    {
        "Naam": r["name"],
        "Datum": r["date"],
        "Tijd": r["time"],
        "Locaties": r.get("access_locations", ""),
        "Sleutels": r.get("access_keys", ""),
        "Status": r["status"]
    }
    for r in bookings
    if r["status"] in ("Goedgekeurd", "Wachten") and r.get("access_keys")
]

if sleutel_reserveringen:
    df = pd.DataFrame(sleutel_reserveringen).sort_values(by="Datum")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Er zijn momenteel geen uitgegeven sleutels.")
