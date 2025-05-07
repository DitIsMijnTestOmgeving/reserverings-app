# app.py
import streamlit as st
import datetime
import time as systime
from datetime import time
import os
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

# ➤ Supabase
supa = get_supabase_client()

# ➤ Verwerk goedkeuren/afwijzen via e-mail-link (bijv. ?approve=true&res_id=123)
params = st.query_params
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", int(params["res_id"][0])).execute()
    st.session_state["authorized"] = True
    st.query_params.clear()
    st.switch_page("🛠 Beheer")
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", int(params["res_id"][0])).execute()
    st.session_state["authorized"] = True
    st.query_params.clear()
    st.switch_page("🛠 Beheer")

# ➤ Verberg beheeropties standaard
if "authorized" not in st.session_state:
    st.session_state["authorized"] = False

# ➤ Sidebar beveiliging
st.sidebar.markdown("## Navigatie")

if not st.session_state["authorized"]:
    code = st.sidebar.text_input("🔐 Toegangscode", type="password", placeholder="Beheer toegang")
    if code == os.environ.get("TOEGANGSCODE", "GEHEIM123"):
        st.session_state["authorized"] = True
        st.sidebar.success("Beheer ontgrendeld.")
        st.rerun()
    elif code:
        st.sidebar.error("Ongeldige toegangscode.")

# ➤ Sidebar navigatie
st.sidebar.page_link("app.py", label="📅 Reserveren")
if st.session_state["authorized"]:
    st.sidebar.page_link("pages/1_Beheer.py", label="🛠 Beheer")
    st.sidebar.page_link("pages/2_Sleuteluitgifte.py", label="🔑 Sleuteluitgifte")

# ➤ UI Reservering aanvragen
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
