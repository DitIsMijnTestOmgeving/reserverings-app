import streamlit as st
from datetime import time
import datetime
import urllib

from utils import (
    get_supabase_client,
    load_companies,
    load_keys,
    send_owner_email
)

# ➤ Pagina instellingen
st.set_page_config(
    page_title="Sleutelreservering",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ➤ Verberg "Beheer" en "Sleuteluitgifte" links op hoofdpagina
path = urllib.parse.urlparse(st.experimental_get_url()).path
if path in ["/", "/index", "/index.html"]:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] a[href*="Beheer"],
    section[data-testid="stSidebar"] a[href*="Sleuteluitgifte"] {
        color: transparent !important;
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)

# ➤ Supabase client
supa = get_supabase_client()

# ➤ Hoofdtitel
st.title("Sleutelreservering aanvragen")

# ➤ Formulier
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

# ➤ Aanvraag versturen
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
