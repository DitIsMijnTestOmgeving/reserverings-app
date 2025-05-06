import os
import smtplib
import streamlit as st
from supabase import create_client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit.components.v1 as components
import pandas as pd
import datetime
from datetime import time
import locale
from docx import Document
from io import BytesIO
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def replace_bookmark_text(doc, bookmark_name, replacement_text):
    for bookmark_start in doc.element.xpath(f'//w:bookmarkStart[@w:name="{bookmark_name}"]'):
        parent = bookmark_start.getparent()
        index = parent.index(bookmark_start)
        if index + 1 < len(parent):
            next_elem = parent[index + 1]
            texts = next_elem.xpath(".//w:t")
            if texts and texts[0].text and "_" in texts[0].text:
                parent.remove(next_elem)
        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = replacement_text
        run.append(text)
        parent.insert(index + 1, run)

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supa = create_client(url, key)

params = st.query_params
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", int(params["res_id"][0])).execute()
    st.query_params.clear()
    st.session_state["show_all_modes"] = True
    st.session_state["gekozen_mode"] = "Beheer"
    st.rerun()
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", int(params["res_id"][0])).execute()
    st.error("❌ De reservering is afgewezen.")
    st.stop()

st.set_page_config(page_title="Reservering Beheer", page_icon="📅", layout="wide")

col_spacer, col_logo = st.columns([2, 1])
with col_logo:
    st.image("Opmeer.png", width=400)

components.html("""
<script>
window.addEventListener("load", function() {
    const sidebar = window.parent.document.querySelector('aside[data-testid="stSidebar"]');
    const toggleButton = window.parent.document.querySelector("button[title='Collapse sidebar']");
    if (sidebar && toggleButton && sidebar.offsetWidth > 250) {
        toggleButton.click();
    }
});
</script>
""", height=0)

try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'nld')
    except:
        pass

def load_companies():
    return {
        "Aesy Liften B.V.": "info@aesyliften.nl",
        "GP Groot": "info@gpgroot.nl",
        "HB Bouw": "d.blom@hbbouwopmeer.nl"
    }

def load_keys():
    return {
        "Bibliotheek Opmeer": "1, 2, 3",
        "Gemeentehuis": "26,27,28",
        "Gymzaal De Weere": "36, 37"
    }

if "show_all_modes" not in st.session_state:
    st.session_state["show_all_modes"] = False

if st.sidebar.button("🔐", help="Geavanceerde weergave tonen"):
    st.session_state["show_all_modes"] = True

st.sidebar.markdown("## Modus kiezen")
if st.session_state["show_all_modes"]:
    mode = st.sidebar.radio("Kies weergave:", ["Reserveren", "Beheer", "Sleuteluitgifte"])
else:
    mode = "Reserveren"

if mode == "Beheer":
    st.title("Beheer aanvragen")
    st.markdown("_Hieronder kun je openstaande aanvragen accepteren, afwijzen of verwijderen._")

    rows = supa.table("bookings").select("*").eq("status", "Wachten").order("date").execute().data

    if not rows:
        st.info("Geen openstaande aanvragen.")
    else:
        for r in rows:
            with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
                col1, col2, col3 = st.columns(3)
                if col1.button("✅ Goedkeuren", key=f"g{r['id']}"):
                    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", r["id"]).execute()
                    st.rerun()
                if col2.button("❌ Afwijzen", key=f"a{r['id']}"):
                    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", r["id"]).execute()
                    st.rerun()
                if col3.button("🗑️ Verwijder", key=f"d{r['id']}"):
                    supa.table("bookings").delete().eq("id", r["id"]).execute()
                    st.rerun()

    all_rows = supa.table("bookings").select("*").order("date").execute().data
    st.subheader("Alle reserveringen")
    st.dataframe([
        {
            "#": x["id"],
            "Naam": x["name"],
            "Datum": x["date"],
            "Tijd": x["time"],
            "Toegang": x["access"],
            "Locaties": x.get("access_locations", ""),
            "Sleutels": x.get("access_keys", ""),
            "Status": x["status"]
        } for x in all_rows
    ], use_container_width=True)

elif mode == "Sleuteluitgifte":
    st.title("🔑 Sleuteluitgifte")

    st.markdown("""
    **Legenda:**
    🟨 Gereserveerd (wacht op goedkeuring)  
    🟧 Goedgekeurd (klaar voor uitgifte)  
    🟥 Uitgegeven  
    🟩 Ingeleverd
    """)

    key_map = load_keys()
    bookings = supa.table("bookings").select("*").execute().data

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

    alle_sleutels = sorted(set(k.strip() for v in key_map.values() for k in v.split(",")), key=lambda x: int(x))
    html = """
    <style>
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
        gap: 6px;
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

    st.markdown("### 📋 Sleutels retourmelden")
    retour = [r for r in bookings if str(r["status"]).startswith("Uitgegeven op")]
    if retour:
        opties = [f"#{r['id']} – {r['name']} ({r['date']} {r['time']})" for r in retour]
        keuze = st.selectbox("Selecteer reservering voor retour", opties)
        geselecteerd = next(r for r in retour if f"#{r['id']}" in keuze)

        st.write(f"**Locaties:** {geselecteerd.get('access_locations', '')}")
        st.write(f"**Sleutels:** {geselecteerd.get('access_keys', '')}")

        if st.button("🔁 Markeer als ingeleverd"):
            vandaag = datetime.date.today().isoformat()
            supa.table("bookings").update({"status": f"Ingeleverd op {vandaag}"}).eq("id", geselecteerd["id"]).execute()
            st.success("Sleutels gemarkeerd als ingeleverd.")
            st.rerun()
    else:
        st.info("Geen sleutels om retour te melden.")


# 10) Sleuteluitgifte

elif mode == "Sleuteluitgifte":
    st.title("🔑 Sleuteluitgifte")

    key_map = load_keys()
    bookings = supa.table("bookings").select("*").execute().data

    # Tegeloverzicht genereren
    alle_sleutels = []
    for sleutels in key_map.values():
        alle_sleutels.extend(s.strip() for s in sleutels.split(","))
    alle_sleutels = sorted(set(alle_sleutels), key=lambda x: int(x))

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
        kleur = "#90ee90"
        for r in bookings:
            if not r.get("access_keys"):
                continue
            sleutel_lijst = [k.strip() for k in r["access_keys"].split(",") if k.strip()]
            if nr in sleutel_lijst:
                status = r.get("status", "")
                if status == "Wachten":
                    kleur = "#ffff99"; break
                elif status == "Goedgekeurd":
                    kleur = "#ffb347"; break
                elif str(status).startswith("Uitgegeven op"):
                    kleur = "#ff6961"; break
                elif str(status).startswith("Ingeleverd op"):
                    kleur = "#90ee90"; break
        locatie = next((loc for loc, ks in key_map.items() if nr in ks), "")
        html += f"<div class='tegel' title='{locatie}' style='background-color: {kleur};'>{nr}</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Sleutels uitgeven
    st.markdown("### 📋 Uitgifte goedgekeurde reserveringen")
    goedgekeurd = [r for r in bookings if r["status"] == "Goedgekeurd"]

    for r in goedgekeurd:
        with st.expander(f"📄 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            st.markdown(f"**Bedrijf:** {r['name']}")
            st.markdown(f"**Datum:** {r['date']}")
            st.markdown(f"**Tijd:** {r['time']}")
            st.markdown(f"**Locaties:** {r.get('access_locations', '')}")
            st.markdown(f"**Sleutels:** {r.get('access_keys', '')}")

            if st.button("🔑 Sleutel uitgeven", key=f"uitgifte_{r['id']}"):
                doc = Document("Sleutel Afgifte Formulier.docx")
                replace_bookmark_text(doc, "Firma", r["name"])
                replace_bookmark_text(doc, "Sleutelnummer", r.get("access_keys", ""))
                replace_bookmark_text(doc, "Bestemd", r.get("access_locations", ""))
                replace_bookmark_text(doc, "AfgifteDatum", r["date"])

                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)

                supa.table("bookings").update({"status": f"Uitgegeven op {datetime.date.today()}"}).eq("id", r["id"]).execute()
                st.download_button(
                    label="⬇️ Download ingevuld formulier",
                    data=buffer,
                    file_name="Sleutel_Afgifte_Formulier.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                st.rerun()

    st.markdown("### 🔁 Sleutels retourmelden")
    uitgegeven = [r for r in bookings if str(r["status"]).startswith("Uitgegeven op")]

    if uitgegeven:
        keuze = st.selectbox("Kies een reservering voor retourmelding:", [f"#{r['id']} – {r['name']} ({r['date']} {r['time']})" for r in uitgegeven])
        geselecteerd = next(r for r in uitgegeven if f"#{r['id']}" in keuze)

        if st.button("🔁 Markeer als ingeleverd"):
            vandaag = datetime.date.today().isoformat()
            supa.table("bookings").update({"status": f"Ingeleverd op {vandaag}"}).eq("id", geselecteerd["id"]).execute()
            st.success("Sleutels gemarkeerd als ingeleverd.")
            st.rerun()
    else:
        st.info("Er zijn geen sleutels om retour te melden.")