# ✅ app.py
import streamlit as st
import datetime
from PIL import Image
import base64
from io import BytesIO
from datetime import time, timedelta, datetime
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

# Laad en converteer logo naar base64
logo = Image.open("Opmeer.png")
buffer = BytesIO()
logo.save(buffer, format="PNG")
encoded_logo = base64.b64encode(buffer.getvalue()).decode()

# Toon logo rechts uitgelijnd
st.markdown(
    f"""
    <div style="text-align: right;">
        <img src="data:image/png;base64,{encoded_logo}" alt="Logo" style="height:200px;" />
    </div>
    """,
    unsafe_allow_html=True
)

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
#st.text_input("E-mail", value=email, disabled=True)

datum = st.date_input("Datum")

from datetime import time, timedelta, datetime

# Genereer tijdslijst van 08:00 tot 18:00 in stappen van 15 minuten
tijden = []
start = datetime.strptime("08:00", "%H:%M")
end = datetime.strptime("18:00", "%H:%M")
while start <= end:
    tijden.append(start.strftime("%H:%M"))
    start += timedelta(minutes=15)

# Toon dropdown
tijd_str = st.selectbox("Tijd", tijden)


#tijd = st.time_input("Tijd", value=time(8, 0))
#tijd_str = tijd.strftime("%H:%M")

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


