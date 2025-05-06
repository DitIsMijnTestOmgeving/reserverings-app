import streamlit as st
import os
from supabase import create_client

# Supabase
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supa = create_client(url, key)

st.set_page_config(page_title="Beheer reserveringen", page_icon="🛠️", layout="wide")
st.title("🛠️ Beheer reserveringen")

rows = supa.table("bookings").select("*").eq("status", "Wachten").order("date").execute().data

if not rows:
    st.info("Geen openstaande aanvragen.")
else:
    for r in rows:
        with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            col1, col2, col3 = st.columns(3)

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
