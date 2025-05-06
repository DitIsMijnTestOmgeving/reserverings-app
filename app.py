import os
import streamlit as st
from datetime import time
from supabase import create_client
import datetime

# Supabase instellen
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supa = create_client(url, key)

# Functie: bedrijven laden
def load_companies():
    return {
        "Aesy Liften B.V.": "info@aesyliften.nl",
        "Alura hekwerken": "info@alura.nl",
        "Assa Abloy": "service.nl.crawford@assaabloy.com",
        "Bodem Belang": "info@bodembelang.nl",
        "G. v. Diepen": "info@vandiependakengevel.nl",
        "Giant Security": "info@giant.nl",
        "GP Groot": "info@gpgroot.nl",
        "HB Bouw": "d.blom@hbbouwopmeer.nl",
        "HB Controle": "info@hbcontrole.nu",
        "Heras": "info@heras.nl",
        "Klaver": "info@klavertechniek.nl",
        "Novoferm": "industrie@novoferm.nl",
        "Rijkhoff Installatie techniek": "info@rijkhoff.nl",
        "Schermer installatie techniek": "info@schermerbv.nl",
        "SkySafe Valbeveiliging": "info@skysafe.nl",
        "Teeuwissen Rioolreiniging": "info@teeuwissen.com",
        "Van Lierop": "info@vanlierop.nl",
        "Vastenburg": "info@vastenburg.nl"
    }

# Sleutels laden

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

# Dummy e-mailfunctie
def send_owner_email(res_id, name, date, time):
    print(f"[TESTMAIL] Reservering #{res_id} voor {name} op {date} om {time}")

# Pagina layout
st.set_page_config(page_title="Sleutelreservering", page_icon="📅", layout="wide")
st.title("Sleutelreservering aanvragen")

bedrijven = load_companies()
bedrijf = st.selectbox("Bedrijf", sorted(bedrijven.keys()))
email = bedrijven[bedrijf]
st.text_input("E-mail", value=email, disabled=True)

datum = st.date_input("Datum")
tijd = st.time_input("Tijd", value=time(8, 0))
tijd_str = tijd.strftime("%H:%M")

toegang = st.checkbox("Toegang tot locatie(s)?")
locaties = []
if toegang:
    locaties = st.multiselect("Selecteer locatie(s)", sorted(load_keys().keys()))

if st.button("Verstuur aanvraag"):
    key_map = load_keys()
    data = {
        "name": bedrijf,
        "email": email,
        "date": datum.isoformat(),
        "time": tijd_str,
        "access": "Ja" if toegang else "Nee",
        "access_locations": ", ".join(locaties),
        "access_keys": ", ".join(key_map[loc] for loc in locaties),
        "status": "Wachten"
    }
    res = supa.table("bookings").insert(data).execute()
    res_id = res.data[0]["id"]
    send_owner_email(res_id, bedrijf, datum, tijd_str)
    st.success("✅ Aanvraag succesvol verzonden!")