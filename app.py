import streamlit as st
import datetime
import time as systime
from datetime import time

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

# ➤ Sidebar styling – Beheer en Uitgifte blokkeren op hoofdpagina, iconen tonen
st.markdown("""
<style>
/* Alleen op hoofdpagina: verberg en blokkeer Beheer + Sleuteluitgifte */
body:has(h1:contains("Sleutelreservering aanvragen")) section[data-testid="stSidebar"] a[href$="/Beheer"],
body:has(h1:contains("Sleutelreservering aanvragen")) section[data-testid="stSidebar"] a[href$="/Beheer"] *,
body:has(h1:contains("Sleutelreservering aanvragen")) section[data-testid="stSidebar"] a[href$="/Uitgifte"],
body:has(h1:contains("Sleutelreservering aanvragen")) section[data-testid="stSidebar"] a[href$="/Uitgifte"] * {
    color: transparent !important;
    pointer-events: none !important;
    user-select: none;
}

/* Icon-only voor Reserveren (deze pagina) */
section[data-testid="stSidebar"] a[href="/"] > span {
    visibility: hidden;
    position: relative;
}
section[data-testid="stSidebar"] a[href="/"]::after {
    content: "📅";
    position: absolute;
    left: 1.3rem;
    font-size: 18px;
}

/* Icon-only voor Beheer */
section[data-testid="stSidebar"] a[href$="/Beheer"] > span {
    visibility: hidden;
    position: relative;
}
section[data-testid="stSidebar"] a[href$="/Beheer"]::after {
    content: "🛠️";
    position: absolute;
    left: 1.3rem;
    font-size: 18px;
}

/* Icon-only voor Sleuteluitgifte */
section[data-testid="stSidebar"] a[href$="/Uitgifte"] > span {
    visibility: hidden;
    position: relative;
}
section[data-testid="stSidebar"] a[href$="/Uitgifte"]::after {
    content: "🔑";
    position: absolute;
    left: 1.3rem;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ➤ Supabase client
supa = get_supabase_client()

# ➤ UI: Reserveringsformulier
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
