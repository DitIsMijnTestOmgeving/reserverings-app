# ✅ app.py
import streamlit as st
import datetime
from datetime import time
from utils import (
    get_supabase_client,
    load_companies,
    load_keys,
    send_owner_email
)

# Pagina-instellingen
st.set_page_config(
    page_title="Sleutelreservering",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from PIL import Image

# Toon logo bovenaan
logo = Image.open("Opmeer.png")
st.image(logo, use_column_width=False)

# Supabase verbinding
supa = get_supabase_client()

# Verwerk e-mailacties (goedkeuren / afwijzen)
params = st.query_params
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", int(params["res_id"][0])).execute()
    st.session_state["beheer_toegang"] = True
    st.query_params.clear()
    st.switch_page("🛠 Beheer")
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", int(params["res_id"][0])).execute()
    st.session_state["beheer_toegang"] = True
    st.query_params.clear()
    st.switch_page("🔑 Sleuteluitgifte")

# Sidebar navigatie (zonder invoervelden)
st.sidebar.page_link("app.py", label="📅 Reserveren")
st.sidebar.page_link("pages/1_Beheer.py", label="🛠 Beheer")
st.sidebar.page_link("pages/2_Sleuteluitgifte.py", label="🔑 Sleuteluitgifte")

# Hoofdpagina: Sleutelreservering aanvragen
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

    try:
        send_owner_email(res_id, bedrijf, datum, tijd_str)
        st.success("✅ Aanvraag succesvol verzonden!")
    except Exception as e:
        st.error("❌ Aanvraag opgeslagen, maar e-mail kon niet worden verzonden.")
        st.exception(e)


