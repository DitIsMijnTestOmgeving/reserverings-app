# ✅ 1_Beheer.py
import streamlit as st
import os
from utils import get_supabase_client

# Pagina-instellingen
st.set_page_config(page_title="Beheer reserveringen", page_icon="🛠️", layout="wide")

# Query parameters ophalen
params = st.query_params
via_link = ("approve" in params or "reject" in params) and "res_id" in params

# Wachtwoordbeveiliging (overslaan bij goedkeur-/afwijslink)
if "beheer_toegang" not in st.session_state:
    st.session_state["beheer_toegang"] = False

if not st.session_state["beheer_toegang"] and not via_link:
    wachtwoord = st.text_input("Voer beheerderswachtwoord in:", type="password")
    if st.button("Inloggen"):
        if wachtwoord == os.environ.get("BEHEER_WACHTWOORD"):
            st.session_state["beheer_toegang"] = True
            st.rerun()
        else:
            st.error("❌ Ongeldig wachtwoord.")
    st.stop()

# Supabase client
supa = get_supabase_client()

st.title("🛠️ Beheer reserveringen")

# Verwerk goedkeuren/afwijzen via e-mail-link
if "approve" in params and "res_id" in params:
    res_id = int(params["res_id"][0])
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", res_id).execute()
    st.success(f"✅ Reservering #{res_id} is goedgekeurd.")
    st.query_params.clear()
    st.stop()
elif "reject" in params and "res_id" in params:
    res_id = int(params["res_id"][0])
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", res_id).execute()
    st.error(f"❌ Reservering #{res_id} is afgewezen.")
    st.query_params.clear()
    st.stop()

# Openstaande aanvragen
st.markdown("_Hieronder kun je openstaande aanvragen goedkeuren, afwijzen of verwijderen._")
rows = supa.table("bookings").select("*").eq("status", "Wachten").order("date").execute().data

if not rows:
    st.info("Geen openstaande aanvragen.")
else:
    for r in rows:
        with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            col1, col2, col3 = st.columns([1, 1, 1])
            if col1.button("✅ Goedkeuren", key=f"g{r['id']}"):
                supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", r["id"]).execute()
                st.success("Goedgekeurd.")
                st.rerun()
            if col2.button("❌ Afwijzen", key=f"a{r['id']}"):
                supa.table("bookings").update({"status": "Afgewezen"}).eq("id", r["id"]).execute()
                st.rerun()
            if col3.button("🗑️ Verwijder", key=f"d{r['id']}"):
                supa.table("bookings").delete().eq("id", r["id"]).execute()
                st.rerun()

# Tabel met alle reserveringen
st.subheader("📋 Alle reserveringen")
all_rows = supa.table("bookings").select("*").order("date").execute().data

data = [
    {
        "ID": x["id"],
        "Naam": x["name"],
        "E-mail": x["email"],
        "Datum": x["date"],
        "Tijd": x["time"],
        "Toegang": x["access"],
        "Locaties": x.get("access_locations", ""),
        "Sleutels": x.get("access_keys", ""),
        "Status": x["status"]
    } for x in all_rows
]

st.dataframe(data, height=450)

# Handmatig verwijderen
st.subheader("🗑️ Verwijder reservering")
verwijderbare = [
    {"id": x["id"], "label": f"#{x['id']} – {x['name']} ({x['date']} {x['time']})"}
    for x in all_rows
]

if verwijderbare:
    opties = {r["label"]: r["id"] for r in verwijderbare}
    keuze = st.selectbox("Kies een reservering:", list(opties.keys()))
    if st.button("Verwijderen"):
        supa.table("bookings").delete().eq("id", opties[keuze]).execute()
        st.success("Reservering verwijderd.")
        st.rerun()
else:
    st.info("Er zijn geen reserveringen om te verwijderen.")
