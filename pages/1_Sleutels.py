import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Sleutels", layout="wide")

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supa = create_client(url, key)

# 3) Sleuteldata
def load_keys():
    return {
        "Bibliotheek Opmeer":            "1, 2, 3",
        "Boevenhoeve":                   "43",
        "Bovenwoningen Spanbroek":       "15",
        "Brandweer Spanbroek":           "14",
        "Electrakast Rokersplein":       "57",
        "Gaskasten algemeen":            "52, 53",
        "Gemeentehuis":                  "26,27,28,29,30,31",
        "Gemeentewerf Spanbroek":        "13",
        "General key (sport)":           "55, 56",
        "Gymzaal Aartswoud":             "16, 17",
        "Gymzaal De Weere":              "36, 37",
        "Gymzaal Hoogwoud":              "32, 33",
        "Gymzaal Opmeer":                "46, 47, 48, 49",
        "Gymzaal Spanbroek":             "34, 35",
        "Hertenkamp Hoogwoud":           "18",
        "IJsbaangebouw":                 "40",
        "Muziekschool Opmeer":           "4",
        "Peuterspeelzaal Boevenhoeve":   "42",
        "Peuterspeelzaal de Kikkerhoek": "11, 12",
        "Peuterspeelzaal Hummeltjeshonk":"44",
        "Raadhuis Hoogwoud":             "19",
        "Raadhuis Spanbroek":            "20, 21, 22",
        "Telefoon gymzalen":             "54",
        "Theresiahuis":                  "5, 6",
        "Toren Aartswoud":               "23, 24",
        "Toren Wadway":                  "25",
        "Verenigingsgebouw":             "7, 8, 9, 10",
        "Watertappunt Hoogwoud":         "50",
        "Wijksteunpunt Lindehof":        "41",
        "Zaalvoetbalhal de Weyver":      "51",
        "Zwembad De Weijver":            "38, 39"
    }

# 4) Sleutels die gereserveerd zijn ophalen
reserved_keys = set()
rows = supa.table("bookings").select("access_keys").execute().data
for row in rows:
    for key in row.get("access_keys", "").replace(" ", "").split(","):
        if key.isdigit():
            reserved_keys.add(int(key))

# 5) Tegeloverzicht
st.title("Sleuteloverzicht")
st.write("Donkere tegels zijn in gebruik of gereserveerd.")

tegelkleur = lambda k: "#d62728" if k in reserved_keys else "#2ca02c"

for rij in range(0, 54, 3):
    kol1, kol2, kol3 = st.columns(3)
    for i, kol in enumerate([kol1, kol2, kol3]):
        nummer = rij + i + 1
        if nummer > 54:
            break
        kleur = tegelkleur(nummer)
        # zoek locatie
        locatie = next((naam for naam, sleutel in load_keys().items() if str(nummer) in sleutel.split(",")), "Onbekend")
        with kol:
            st.button(f"{nummer}", key=f"knop{nummer}", help=f"Locatie: {locatie}", disabled=True)
            st.markdown(
                f"<div style='background-color:{kleur}; height:30px; width:100%; border-radius:6px'></div>",
                unsafe_allow_html=True
            )
