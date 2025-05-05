# app.py
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

# Supabase
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supa = create_client(url, key)

# directe goedkeur/afwijs via URL-query
params = st.query_params
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", int(params["res_id"][0])).execute()
    st.success("✅ De reservering is goedgekeurd.")
    st.stop()
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", int(params["res_id"][0])).execute()
    st.error("❌ De reservering is afgewezen.")
    st.stop()

# PAGINA-INSTELLINGEN
st.set_page_config(page_title="Reservering Beheer", page_icon="📅", layout="wide")

# Logo toevoegen
col_spacer, col_logo = st.columns([2, 1])
with col_logo:
    st.image("Opmeer.png", width=400)

# Sidebar inklappen
components.html("""
<script>
document.addEventListener("click", function(event) {
    const sidebar = window.parent.document.querySelector('aside[data-testid="stSidebar"]');
    const toggleButton = window.parent.document.querySelector('button[title="Collapse sidebar"]');
    if (sidebar && toggleButton && !sidebar.contains(event.target)) {
        toggleButton.click();
    }
});
</script>
""", height=0)

# Sidebar knop naar uitgifte
#st.sidebar.markdown("---")
#st.sidebar.page_link("/?mode=uitgifte", label="🔑 Sleuteluitgifte", icon="🔑")

# Taalinstelling
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'nld')
    except:
        pass

# Dummy functie voor bevestigingsmail

def send_confirmation_email(to_email, bedrijf, datum, tijd):
    print(f"Mail naar {to_email}: reservering bevestigd voor {bedrijf} op {datum} om {tijd}.")

# 2) Bedrijven
def load_companies():
    return {
        "Aesy Liften B.V.": "info@aesyliften.nl",
        "Alura hekwerken": "info@alura.nl",
        "Assa Abloy": "service.nl.crawford@assaabloy.com",
        "Bodem Belang": "info@bodembelang.nl",
        "G. v. Diepen": "info@vandiependakengevel.nl",
        "Giant Security": "info@giant.nl",
        "GP Groot": "info@gpgroot.nl",
        "HB Bouw": "d.blom@hbbouwopmeer.nl",
        "HB Controle": "info@hbcontrole.nu",
        "Heras": "info@heras.nl",
        "Klaver": "info@klavertechniek.nl",
        "Novoferm": "industrie@novoferm.nl",
        "Rijkhoff Installatie techniek": "info@rijkhoff.nl",
        "Schermer installatie techniek": "info@schermerbv.nl",
        "SkySafe Valbeveiliging": "info@skysafe.nl",
        "Teeuwissen Rioolreiniging": "info@teeuwissen.com",
        "Van Lierop": "info@vanlierop.nl",
        "Vastenburg": "info@vastenburg.nl"
    }

# 3) Sleutellijst
def load_keys():
    return {
        "Bibliotheek Opmeer": "1, 2, 3",
        "Boevenhoeve": "43",
        "Bovenwoningen Spanbroek": "15",
        "Brandweer Spanbroek": "14",
        "Electrakast Rokersplein": "57",
        "Gaskasten algemeen": "52, 53",
        "Gemeentehuis": "26,27,28,29,30,31",
        "Gemeentewerf Spanbroek": "13",
        "General key (sport)": "55, 56",
        "Gymzaal Aartswoud": "16, 17",
        "Gymzaal De Weere": "36, 37",
        "Gymzaal Hoogwoud": "32, 33",
        "Gymzaal Opmeer": "46, 47, 48, 49",
        "Gymzaal Spanbroek": "34, 35",
        "Hertenkamp Hoogwoud": "18",
        "IJsbaangebouw": "40",
        "Muziekschool Opmeer": "4",
        "Peuterspeelzaal Boevenhoeve": "42",
        "Peuterspeelzaal de Kikkerhoek": "11, 12",
        "Peuterspeelzaal Hummeltjeshonk": "44",
        "Raadhuis Hoogwoud": "19",
        "Raadhuis Spanbroek": "20, 21, 22",
        "Telefoon gymzalen": "54",
        "Theresiahuis": "5, 6",
        "Toren Aartswoud": "23, 24",
        "Toren Wadway": "25",
        "Verenigingsgebouw": "7, 8, 9, 10",
        "Watertappunt Hoogwoud": "50",
        "Wijksteunpunt Lindehof": "41",
        "Zaalvoetbalhal de Weyver": "51",
        "Zwembad De Weijver": "38, 39"
    }

# 4) Mail
def send_owner_email(res_id, name, date, time):
    approve_link = f"https://reserveringsapp-opmeer.onrender.com/?approve=true&res_id={res_id}"
    reject_link = f"https://reserveringsapp-opmeer.onrender.com/?reject=true&res_id={res_id}"
    sleutels_link = "https://reserveringsapp-opmeer.onrender.com/?mode=sleutels"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Reservering] Nieuwe aanvraag #{res_id}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["OWNER_EMAIL"]
    html = f"""
    <html><body>
      <p>Nieuwe reservering:<br>
         <b>Nummer:</b> {res_id}<br>
         <b>Bedrijf:</b> {name}<br>
         <b>Datum:</b> {date}<br>
         <b>Tijd:</b> {time}</p>
      <p>
        <div><a href="{approve_link}" style="background-color:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">✅ Goedkeuren</a></div>
        <div><a href="{reject_link}" style="background-color:#f44336;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">❌ Weigeren</a></div>
        <div><a href="{sleutels_link}" style="background-color:#2196F3;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">🔑 Sleuteloverzicht</a></div>
      </p>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.environ["SMTP_PORT"])) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg)

# 6) Modus — géén inlog meer, alles openbaar
st.sidebar.markdown("## Modus kiezen")
mode = st.sidebar.radio("Kies weergave:", ["Reserveren", "Beheer", "Agenda"])

# 7) Reserveren
if mode == "Reserveren":
    st.title("Reservering maken")

    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    import locale
    from datetime import time

    # Stel Nederlandse taal in voor datum
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')  # Linux/macOS
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'nld')  # Windows
        except:
            pass  # fallback

    companies = load_companies()
    naam = st.selectbox("Bedrijf", sorted(companies.keys()))
    email_input = companies[naam]
    st.text_input("E-mail", value=email_input, disabled=True)

    datum = st.date_input("Datum")
    datum_nederlands = datum.strftime("%d %B %Y").lstrip("0")
    st.markdown(f"Geselecteerde datum: **{datum_nederlands}**")

    tijd = st.time_input("Tijd", value=time(8, 0), step=900)
    tijd_str = tijd.strftime("%H:%M")

    access = st.checkbox("Toegang nodig?")
    locs = []
    if access:
        key_map = load_keys()
        locs = st.multiselect("Selecteer locatie(s)", sorted(key_map.keys()))

    if st.button("Verstuur aanvraag"):
        key_map = load_keys()
        data = {
            "name": naam,
            "email": email_input,
            "date": datum.isoformat(),
            "time": tijd_str,
            "access": "Ja" if access else "Nee",
            "access_locations": ", ".join(locs),
            "access_keys": ", ".join(key_map[loc] for loc in locs),
            "status": "Wachten"
        }
        res = supa.table("bookings").insert(data).execute()
        res_id = res.data[0]["id"]
        send_owner_email(res_id, naam, data["date"], tijd_str)
        st.success("✅ Aanvraag succesvol verzonden!")


# 8) Beheer
elif mode == "Beheer":
    st.title("Beheer aanvragen")
    st.markdown("_Hieronder kun je openstaande aanvragen accepteren, afwijzen of verwijderen._")

    rows = supa.table("bookings").select("*") \
        .neq("status", "Goedgekeurd").neq("status", "Afgewezen") \
        .order("date").execute().data

    if not rows:
        st.info("Geen openstaande aanvragen.")
    else:
        for r in rows:
            with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
                col1, col2, col3 = st.columns([1, 1, 1])

                if col1.button("✅ Goedkeuren", key=f"g{r['id']}"):
                    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", r["id"]).execute()

                    # Bevestigingsmail sturen naar testadres
                    send_confirmation_email(
                        to_email="bendielissen@gmail.com",  # tijdelijk testadres
                        # to_email=r["email"],  # ← uiteindelijke live-versie
                        bedrijf=r["name"],
                        datum=r["date"],
                        tijd=r["time"]
                    )

                    st.query_params.clear()
                    st.rerun()

                if col2.button("❌ Afwijzen", key=f"a{r['id']}"):
                    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", r["id"]).execute()
                    st.query_params.clear()
                    st.rerun()

                if col3.button("🗑️ Verwijder", key=f"d{r['id']}"):
                    supa.table("bookings").delete().eq("id", r["id"]).execute()
                    st.rerun()

    all_rows = supa.table("bookings").select("*").order("date").execute().data
    st.subheader("Alle reserveringen")
    st.dataframe([
        {
            "Naam": x["name"],
            "E-mail": x["email"],
            "Datum": x["date"],
            "Tijd": x["time"],
            "Toegang": x["access"],
            "Locaties": x.get("access_locations", ""),
            "Sleutels": x.get("access_keys", ""),
            "Status": x["status"]
        } for x in all_rows
    ], height=450)

    st.subheader("Reservering verwijderen")
    verwijderbare_rows = [
        {
            "id": x["id"],
            "label": f"{x['name']} – {x['date']} {x['time']}",
        } for x in all_rows
    ]

    if verwijderbare_rows:
        opties = {r["label"]: r["id"] for r in verwijderbare_rows}
        selectie = st.selectbox("Kies een reservering om te verwijderen:", list(opties.keys()))

        if st.button("🗑️ Verwijder geselecteerde reservering"):
            supa.table("bookings").delete().eq("id", opties[selectie]).execute()
            st.success("Reservering verwijderd.")
            st.rerun()
    else:
        st.info("Er zijn geen reserveringen om te verwijderen.")

# 9) Sleutels
elif mode == "Sleutels":
    st.title("🔑 Sleuteloverzicht")

    key_map = load_keys()
    bookings = supa.table("bookings").select("*").execute().data

    gebruikte_sleutels = set()
    for r in bookings:
        if r["status"] in ("Goedgekeurd", "Wachten"):
            ks = r.get("access_keys") or ""
            gebruikte_sleutels.update(k.strip() for k in ks.split(",") if k.strip())

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
        background-color: #90ee90;
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
        kleur = "#ff6961" if nr in gebruikte_sleutels else "#90ee90"
        locatie = next((loc for loc, ks in key_map.items() if nr in ks), "")
        html += f"<div class='tegel' title='{locatie}' style='background-color: {kleur};'>{nr}</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("### 📋 Uitgegeven sleutels")

    sleutel_reserveringen = [
        {
            "Naam": r["name"],
            "Datum": r["date"],
            "Tijd": r["time"],
            "Locaties": r.get("access_locations", ""),
            "Sleutels": r.get("access_keys", ""),
            "Status": r["status"]
        }
        for r in bookings
        if r["status"] in ("Goedgekeurd", "Wachten") and r.get("access_keys")
    ]

    if sleutel_reserveringen:
        import pandas as pd
        df_sleutels = pd.DataFrame(sleutel_reserveringen)
        df_sleutels = df_sleutels.sort_values(by="Datum")
        st.dataframe(df_sleutels, use_container_width=True)
    else:
        st.info("Er zijn momenteel geen uitgegeven sleutels.")

# 10) Sleuteluitgifte
elif mode == "Uitgifte":
    st.title("🔑 Sleutels uitgeven")

    key_map = load_keys()
    bookings = supa.table("bookings").select("*").eq("status", "Goedgekeurd").execute().data

    gebruikte_sleutels = set()
    for r in bookings:
        ks = r.get("access_keys") or ""
        gebruikte_sleutels.update(k.strip() for k in ks.split(",") if k.strip())

    alle_sleutels = sorted(gebruikte_sleutels, key=lambda x: int(x))

    html = """
    <style>
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
        gap: 6px;
        max-width: 100%;
    }
    .tegel {
        background-color: #ffd966;
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
        locatie = next((loc for loc, ks in key_map.items() if nr in ks), "")
        html += f"<div class='tegel' title='{locatie}'>{nr}</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("### 📋 Selecteer reservering om formulier te genereren")

    opties = {
        f"#{r['id']} – {r['name']} ({r['date']} {r['time']})": r
        for r in bookings
    }

    selectie = st.selectbox("Selecteer reservering", list(opties.keys()))
    gekozen = opties[selectie]

    if st.button("📄 Genereer afgifteformulier"):
        doc = Document("Sleutel Afgifte Formulier.docx")

        for para in doc.paragraphs:
            para.text = para.text.replace("BEDRIJF", gekozen["name"])
            para.text = para.text.replace("DATUM", gekozen["date"])
            para.text = para.text.replace("TIJD", gekozen["time"])
            para.text = para.text.replace("SLEUTELS", gekozen.get("access_keys", ""))
            para.text = para.text.replace("LOCATIES", gekozen.get("access_locations", ""))

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download ingevuld formulier",
            data=buffer,
            file_name="Sleutel_Afgifte_Formulier.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
# 11) Agenda
elif mode == "Agenda":
    st.title("🗓️ Sleuteluitgifte bevestigen")
    goedgekeurd = supa.table("bookings").select("*").eq("status", "Goedgekeurd").execute().data

    if not goedgekeurd:
        st.info("Er zijn geen goedgekeurde reserveringen.")
    else:
        for r in goedgekeurd:
            with st.expander(f"📄 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
                st.markdown(f"**Bedrijf:** {r['name']}")
                st.markdown(f"**Datum:** {r['date']}")
                st.markdown(f"**Tijd:** {r['time']}")
                st.markdown(f"**Locaties:** {r.get('access_locations', '')}")
                st.markdown(f"**Sleutels:** {r.get('access_keys', '')}")

                if st.button(f"📄 Genereer & markeer als uitgegeven", key=f"agenda_print_{r['id']}"):
                    doc = Document("Sleutel Afgifte Formulier.docx")
                    for para in doc.paragraphs:
                        para.text = para.text.replace("______________________", "")
                        para.text = para.text.replace("Firma:", f"Firma: {r['name']}")
                        para.text = para.text.replace("Sleutelnummer:", f"Sleutelnummer: {r.get('access_keys', '')}")
                        para.text = para.text.replace("Bestemd Voor (ruimte/locatie):", f"Bestemd Voor (ruimte/locatie): {r.get('access_locations', '')}")
                        para.text = para.text.replace("Datum van Afgifte:", f"Datum van Afgifte: {r['date']}")

                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                    supa.table("bookings").update({"status": f"Uitgegeven op {datetime.date.today()}"}).eq("id", r["id"]).execute()

                    st.download_button(
                        label="⬇️ Download afgifteformulier",
                        data=buffer,
                        file_name="Sleutel_Afgifte_Formulier.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

