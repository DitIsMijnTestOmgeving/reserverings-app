# ✅ 2_Sleuteluitgifte.py
import streamlit as st
import datetime
from io import BytesIO
from docx import Document
from utils import get_supabase_client, load_keys, replace_bookmark_text
import os

# Pagina-instellingen
st.set_page_config(page_title="Sleuteluitgifte", page_icon="🔑", layout="wide")

# Wachtwoordbeveiliging
if "beheer_toegang" not in st.session_state:
    st.session_state["beheer_toegang"] = False

params = st.query_params
via_link = params.get("via") == "mail"

if not st.session_state["beheer_toegang"] and not via_link:
    wachtwoord = st.text_input("Voer beheerderswachtwoord in:", type="password")
    if st.button("Inloggen"):
        if wachtwoord == os.environ.get("BEHEER_WACHTWOORD"):
            st.session_state["beheer_toegang"] = True
            st.rerun()
        else:
            st.error("❌ Ongeldig wachtwoord.")
    st.stop()

# Supabase verbinding
supa = get_supabase_client()
st.title("🔑 Sleuteluitgifte")

key_map = load_keys()
bookings = supa.table("bookings").select("*").execute().data

# Statuskleur per sleutelnummer
kleur_per_sleutel = {}
for r in bookings:
    status = r.get("status", "")
    sleutels = r.get("access_keys", "")
    if not sleutels:
        continue
    for s in sleutels.split(","):
        s = s.strip()
        if not s:
            continue
        if status == "Wachten":
            kleur_per_sleutel[s] = "#ffff99"
        elif status == "Goedgekeurd":
            kleur_per_sleutel[s] = "#ffb347"
        elif str(status).startswith("Uitgegeven op"):
            kleur_per_sleutel[s] = "#ff6961"
        elif str(status).startswith("Ingeleverd op"):
            kleur_per_sleutel[s] = "#90ee90"

# Tegeloverzicht
alle_sleutels = sorted(set(k.strip() for v in key_map.values() for k in v.split(",")), key=lambda x: int(x))
html = """
<style>
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
    gap: 6px;
    max-width: 100%;
}
.tegel {
    width: 40px;
    height: 40px;
    border-radius: 4px;
    text-align: center;
    line-height: 40px;
    font-weight: bold;
    font-size: 12px;
}
</style>
<div class='grid'>
"""
for nr in alle_sleutels:
    kleur = kleur_per_sleutel.get(nr, "#90ee90")
    locatie = next((loc for loc, ks in key_map.items() if nr in ks), "")
    html += f"<div class='tegel' title='{locatie}' style='background-color: {kleur};'>{nr}</div>"
html += "</div>"
st.markdown(html, unsafe_allow_html=True)

# Legenda
st.markdown("""
<div style='margin-top: 10px; font-size: 14px;'>
🟨 <b>Wachten</b><br>
🟧 <b>Goedgekeurd</b><br>
🟥 <b>Uitgegeven</b><br>
🟩 <b>Ingeleverd</b>
</div>
""", unsafe_allow_html=True)

# Sleutels uitgeven
st.markdown("### 📄 Sleutels uitgeven")

if "uitgifte_buffer" not in st.session_state:
    st.session_state["uitgifte_buffer"] = None
    st.session_state["uitgifte_id"] = None

goedgekeurd = [r for r in bookings if r["status"] == "Goedgekeurd"]
for r in goedgekeurd:
    with st.expander(f"📋 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
        st.write(f"**Bedrijf**: {r['name']}")
        st.write(f"**Datum**: {r['date']}")
        st.write(f"**Tijd**: {r['time']}")
        st.write(f"**Locaties**: {r.get('access_locations', '')}")
        st.write(f"**Sleutels**: {r.get('access_keys', '')}")

        if st.button("🔑 Sleutel uitgifteformulier genereren", key=f"gen_{r['id']}"):
            doc = Document("Sleutel Afgifte Formulier.docx")
            replace_bookmark_text(doc, "Firma", r["name"])
            replace_bookmark_text(doc, "Sleutelnummer", r.get("access_keys", ""))
            replace_bookmark_text(doc, "Bestemd", r.get("access_locations", ""))
            replace_bookmark_text(doc, "AfgifteDatum", str(datetime.date.today()))

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            st.session_state["uitgifte_buffer"] = buffer
            st.session_state["uitgifte_id"] = r["id"]

        if st.session_state.get("uitgifte_id") == r["id"] and st.session_state["uitgifte_buffer"]:
            st.download_button(
                label="⬇️ Download formulier en markeer als uitgegeven",
                data=st.session_state["uitgifte_buffer"],
                file_name="Sleutel_Afgifte_Formulier.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            if st.button("✅ Bevestig uitgifte", key=f"bevestig_{r['id']}"):
                vandaag = datetime.date.today().isoformat()
                supa.table("bookings").update({"status": f"Uitgegeven op {vandaag}"}).eq("id", r["id"]).execute()
                st.success("Sleutel gemarkeerd als uitgegeven.")
                st.session_state["uitgifte_buffer"] = None
                st.session_state["uitgifte_id"] = None
                st.rerun()

# Sleutels retourmelden
st.markdown("### 🔁 Sleutels retourmelden")
uitgegeven = [r for r in bookings if str(r["status"]).startswith("Uitgegeven op")]
if uitgegeven:
    for r in uitgegeven:
        with st.expander(f"🔁 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            st.markdown(f"**Bedrijf:** {r['name']}")
            st.markdown(f"**Datum:** {r['date']}")
            st.markdown(f"**Tijd:** {r['time']}")
            st.markdown(f"**Locaties:** {r.get('access_locations', '')}")
            st.markdown(f"**Sleutels:** {r.get('access_keys', '')}")

            if st.button("🔁 Markeer als ingeleverd", key=f"inleverd_{r['id']}"):
                vandaag = datetime.date.today().isoformat()
                supa.table("bookings").update({"status": f"Ingeleverd op {vandaag}"}).eq("id", r["id"]).execute()
                st.success("Sleutels gemarkeerd als ingeleverd.")
                st.rerun()
else:
    st.info("Geen sleutels om retour te melden.")