import streamlit as st
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
import datetime
import uuid

# --- Supabase initialisatie ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supa = create_client(url, key)

# --- Bedrijfslijst met e-mails ---
def load_companies():
    return {
        "ABC-hekwerk": "info@heras.nl",
        "Aesy Liften B.V.": "info@aesyliften.nl",
        "Alura hekwerken": "info@alura.nl",
        "Assa Abloy": "service.nl.crawford@assaabloy.com",
        "Bodem Belang": "info@bodembelang.nl",
        "ContrAll Inspectie": "info@contrall.nl",
        "Espero BV": "info@espero.nl",
        "G. v. Diepen": "info@vandiependakengevel.nl",
        "Giant Security": "info@giant.nl",
        "GP Groot": "info@gpgroot.nl",
        "HB Bouw": "d.blom@hbbouwopmeer.nl",
        "HB Controle": "info@hbcontrole.nu",
        "Heras": "info@heras.nl",
        "Hoefnagels": "info@hoefnagels.com",
        "Klaver": "info@klavertechniek.nl",
        "Novoferm": "industrie@novoferm.nl",
        "Rijkhoff Installatietechniek": "info@rijkhoff.nl",
        "Schermer installatie techniek": "info@schermerbv.nl",
        "SkySafe Valbeveiliging": "info@skysafe.nl",
        "Teeuwissen Rioolreiniging": "info@teeuwissen.com",
        "Van Lierop": "info@vanlierop.nl",
        "Vastenburg": "info@vastenburg.nl",
        "Veldhuis": "info@veldhuis.nl"
    }

# --- E-mail setup ---
owner_email   = st.secrets["owner"]["email"]
smtp_server   = st.secrets["smtp"]["server"]
smtp_port     = st.secrets["smtp"]["port"]
smtp_user     = st.secrets["smtp"]["user"]
smtp_password = st.secrets["smtp"]["password"]

def send_owner_email(res_id, name, date, time):
    base    = "https://limazv2gjxwr82bgefrl2t.streamlit.app"
    approve = f"{base}/?approve=true&res_id={res_id}"
    reject  = f"{base}/?reject=true&res_id={res_id}"
    subject = f"[Reservering] Nieuwe aanvraag #{res_id}"
    body = f"""
Er is een nieuwe reservering:

• Nummer: {res_id}
• Bedrijf: {name}
• Datum:   {date}
• Tijd:    {time}

✅ Goedkeuren: {approve}
❌ Afwijzen:   {reject}
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = owner_email
    with smtplib.SMTP(smtp_server, smtp_port) as s:
        s.starttls()
        s.login(smtp_user, smtp_password)
        s.send_message(msg)

# --- One‑click handlers via URL‑params ---
params = st.query_params
if "approve" in params and "res_id" in params:
    supa.table("bookings")\
        .update({"status": "Goedgekeurd"})\
        .eq("id", int(params["res_id"][0]))\
        .execute()
    st.success("✅ Reservering goedgekeurd via link!")
elif "reject" in params and "res_id" in params:
    supa.table("bookings")\
        .update({"status": "Afgewezen"})\
        .eq("id", int(params["res_id"][0]))\
        .execute()
    st.info("❌ Reservering afgewezen via link!")

# --- Pagina‑configuratie ---
st.set_page_config(page_title="Reservering Beheer", page_icon="🍽️", layout="wide")
mode = st.sidebar.radio("Modus:", ["Reserveren", "Beheer"])

# --- Reserveren‑modus ---
if mode == "Reserveren":
    st.title("Reservering maken")
    companies   = load_companies()
    naam        = st.sidebar.selectbox("Bedrijf", list(companies.keys()))
    email_input = companies[naam]
    st.sidebar.text_input("E‑mail", value=email_input, disabled=True)
    datum       = st.sidebar.date_input("Datum")
    tijd        = st.sidebar.time_input("Tijd")
    access      = st.sidebar.checkbox("Toegang nodig?")
    ready = all([naam, email_input, datum, tijd])
    if not ready:
        st.sidebar.info("Vul alle velden in om te verzenden")
    if st.sidebar.button("Verstuur aanvraag", disabled=not ready):
        data = {
            "name":   naam,
            "email":  email_input,
            "date":   datum.isoformat(),
            "time":   tijd.strftime("%H:%M"),
            "access": "Ja" if access else "Nee",
            "status": "Wachten"
        }
        resp = supa.table("bookings").insert(data).execute()
        res_id = resp.data[0]["id"]
        send_owner_email(res_id, naam, data["date"], data["time"])
        st.sidebar.success("✅ Aanvraag verzonden!")

# --- Beheer‑modus ---
else:
    st.title("Beheer aanvragen")
    pending = supa.table("bookings")\
                  .select("*")\
                  .neq("status", "Goedgekeurd")\
                  .neq("status", "Afgewezen")\
                  .order("date", {"ascending": True})\
                  .execute().data
    if not pending:
        st.info("Geen openstaande aanvragen.")
    for r in pending:
        with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            col1, col2 = st.columns(2)
            if col1.button("✅ Goedkeuren", key=f"g{r['id']}"):
                supa.table("bookings")\
                    .update({"status": "Goedgekeurd"})\
                    .eq("id", r["id"]).execute()
                st.experimental_rerun()
            if col2.button("❌ Afwijzen", key=f"a{r['id']}"):
                supa.table("bookings")\
                    .update({"status": "Afgewezen"})\
                    .eq("id", r["id"]).execute()
                st.experimental_rerun()

    st.subheader("Alle reserveringen")
    all_rows = supa.table("bookings")\
                  .select("*")\
                  .order("date", {"ascending": True})\
                  .execute().data
    st.dataframe([
        {
            "Naam":    x["name"],
            "E‑mail":  x["email"],
            "Datum":   x["date"],
            "Tijd":    x["time"],
            "Toegang": x["access"],
            "Status":  x["status"]
        }
        for x in all_rows
    ], height=400)
