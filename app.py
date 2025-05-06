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

# Verander de titel in de sidebar van 'app' naar 'Reserveren'
st.markdown("""
<style>
/* 📅 Reserveren */
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

/* 🛠 Beheer - verberg en blokkeer enkel op '/' */
body:has(main[data-testid="stAppViewContainer"] h1:has-text("Sleutelreservering aanvragen")) 
  section[data-testid="stSidebar"] a[href$="/Beheer"],
body:has(main[data-testid="stAppViewContainer"] h1:has-text("Sleutelreservering aanvragen")) 
  section[data-testid="stSidebar"] a[href$="/Beheer"] * {
    color: transparent !important;
    pointer-events: none !important;
}

/* 🔑 Sleuteluigifte - verberg en blokkeer enkel op '/' */
body:has(main[data-testid="stAppViewContainer"] h1:has-text("Sleutelreservering aanvragen")) 
  section[data-testid="stSidebar"] a[href$="/Uitgifte"],
body:has(main[data-testid="stAppViewContainer"] h1:has-text("Sleutelreservering aanvragen")) 
  section[data-testid="stSidebar"] a[href$="/Uitgifte"] * {
    color: transparent !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)


# ➤ Supabase
supa = get_supabase_client()

# ➤ Verwerk goedkeuren/afwijzen via e-mail-link (bijv. ?approve=true&res_id=123)
# ➤ UI
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
