import streamlit as st
from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 0) PAGINA-INSTELLINGEN
st.set_page_config(page_title="Reservering Beheer", page_icon="🍽️", layout="wide")

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
        "ABC-hekwerk": "info@heras.nl",
        "Aesy Liften B.V.": "info@aesyliften.nl",
        "Veldhuis": "info@veldhuis.nl"
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

# 5) Linkverwerking
params = st.query_params
handled = False
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"}).eq("id", int(params["res_id"][0])).execute()
    st.query_params.clear()
    handled = True
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"}).eq("id", int(params["res_id"][0])).execute()
    st.query_params.clear()
    handled = True

# 6) Modus
if handled:
    mode = "Beheer"

# Alleen toegang tot 'Beheer' als juiste wachtwoord is ingevoerd
beheer_toegang = False
beheer_optie = st.sidebar.radio("Modus:", ["Reserveren", "Beheer", "Sleutels"])

if beheer_optie == "Beheer":
    wachtwoord = st.sidebar.text_input("Beheerderswachtwoord", type="password")
    if wachtwoord == st.secrets["beheer_wachtwoord"]:
        beheer_toegang = True
        mode = "Beheer"
    else:
        st.sidebar.warning("Geen toegang tot Beheer. Voer correct wachtwoord in.")
        mode = "Reserveren"
else:
    mode = beheer_optie

# 7) Reserveren
if mode == "Reserveren":
    st.title("Reservering maken")
    companies = load_companies()
    naam = st.selectbox("Bedrijf", sorted(companies.keys()))
    email_input = companies[naam]
    st.text_input("E-mail", value=email_input, disabled=True)
    datum = st.date_input("Datum")
    tijd = st.time_input("Tijd")
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

    # Geaccepteerde en afgewezen aanvragen in tabel
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

    # Extra verwijderoptie via keuzelijst
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
