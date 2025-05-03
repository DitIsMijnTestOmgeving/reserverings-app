import smtplib
import streamlit as st
from supabase import create_client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit.components.v1 as components
import pandas as pd
import datetime

# 0) PAGINA-INSTELLINGEN
st.set_page_config(page_title="Reservering Beheer", page_icon="🍽️", layout="wide")

components.html("""
<script>
setTimeout(function() {
    const sidebar = window.parent.document.querySelector('aside[data-testid="stSidebar"]');
    const toggle = window.parent.document.querySelector('button[title="Collapse sidebar"]');
    if (sidebar && toggle && sidebar.offsetWidth > 250) {
        toggle.click();
    }
}, 1000);
</script>
""", height=0)

col_spacer, col_logo = st.columns([2, 1])
with col_logo:
    st.image("Opmeer.png", width=400)

# 1) Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supa = create_client(url, key)

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
    base_url = "https://ideal-lamp-7vw6p666j6v62rxr4-8501.app.github.dev"
    approve_link = f"{base_url}/?approve=true&res_id={res_id}"
    reject_link = f"{base_url}/?reject=true&res_id={res_id}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Reservering] Nieuwe aanvraag #{res_id}"
    msg["From"] = st.secrets["smtp"]["user"]
    msg["To"] = st.secrets["owner"]["email"]

    html = f"""
    <html><body>
      <p>Nieuwe reservering:<br>
         <b>Nummer:</b> {res_id}<br>
         <b>Bedrijf:</b> {name}<br>
         <b>Datum:</b> {date}<br>
         <b>Tijd:</b> {time}</p>
      <p>
        <a href="{approve_link}" style="background-color:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">✅ Goedkeuren</a>
        &nbsp;
        <a href="{reject_link}" style="background-color:#f44336;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;">❌ Weigeren</a>
      </p></body></html>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(st.secrets["smtp"]["server"], st.secrets["smtp"]["port"]) as s:
        s.starttls()
        s.login(st.secrets["smtp"]["user"], st.secrets["smtp"]["password"])
        s.send_message(msg)

# 5) Toegang & Moduslogica
beheer_toegang = st.session_state.get("beheer_toegang", False)
mode = None

params = st.query_params
handled = False

# Goedkeur-/weigerlinks verwerken
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", int(params["res_id"][0])).execute()
    st.query_params.clear()
    handled = True
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", int(params["res_id"][0])).execute()
    st.query_params.clear()
    handled = True

if handled:
    st.session_state["beheer_toegang"] = True
    beheer_toegang = True
    mode = "Agenda"
else:
    if not beheer_toegang:
        gekozen_optie = st.sidebar.radio("Modus:", ["Reserveren", "Beheer"])
        if gekozen_optie == "Beheer":
            wachtwoord = st.sidebar.text_input("Beheerderswachtwoord", type="password", key="beheer_wachtwoord")
            if wachtwoord == "00":
                st.session_state["beheer_toegang"] = True
                st.rerun()  # Herlaad om toegang te geven
            else:
                st.sidebar.warning("Geen toegang. Voer correct wachtwoord in.")
                st.stop()
        else:
            mode = gekozen_optie
    else:
        gekozen_submodus = st.sidebar.radio("Beheeronderdeel:", ["Beheer", "Sleutels", "Agenda"])
        mode = gekozen_submodus

# Als niets gekozen is of toegang is geweigerd
if mode is None:
    st.stop()

# 7) Reserveren
if mode == "Reserveren":
    import datetime
    st.title("Reservering maken")
    companies = load_companies()
    naam = st.selectbox("Bedrijf", sorted(companies.keys()))
    email_input = companies[naam]
    st.text_input("E-mail", value=email_input, disabled=True)
    datum = st.date_input("Datum")

    tijdopties = [
        (datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0)) + datetime.timedelta(minutes=15 * i)).time()
        for i in range(int((17 - 8) * 4))
    ]
    tijd_str_opties = [t.strftime("%H:%M") for t in tijdopties]
    tijd_str = st.selectbox("Tijd", tijd_str_opties, index=4)
    tijd = datetime.datetime.strptime(tijd_str, "%H:%M").time()

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
            "time": tijd.strftime("%H:%M"),
            "access": "Ja" if access else "Nee",
            "access_locations": ", ".join(locs),
            "access_keys": ", ".join(key_map[loc] for loc in locs),
            "status": "Wachten"
        }
        res = supa.table("bookings").insert(data).execute()
        res_id = res.data[0]["id"]
        send_owner_email(res_id, naam, data["date"], data["time"])
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
    for r in rows:
        with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            col1, col2, col3 = st.columns([1, 1, 1])
            if col1.button("✅ Goedkeuren", key=f"g{r['id']}"):
                supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", r["id"]).execute()
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

# 10) Agenda
elif mode == "Agenda":
    st.title("📅 Agenda overzicht")
    all_rows = supa.table("bookings").select("*").order("date").execute().data

    if all_rows:
        import pandas as pd
        df_agenda = pd.DataFrame([
            {
                "Datum": pd.to_datetime(r["date"]).strftime("%-d %B %Y"),
                "Tijd": r["time"][:5],
                "Bedrijf": r["name"],
                "Locaties": r.get("access_locations", ""),
                "Status": r["status"]
            }
            for r in all_rows
        ])
        df_agenda = df_agenda.sort_values(by=["Datum", "Tijd"])
        st.dataframe(df_agenda, use_container_width=True)
    else:
        st.info("Er zijn geen reserveringen gepland.")

















