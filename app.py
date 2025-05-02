import streamlit as st
from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 0) PAGINA-INSTELLINGEN (moet als eerste)
st.set_page_config(
    page_title="Reservering Beheer",
    page_icon="🍽️",
    layout="wide"
)

# Header met logo rechtsboven
col_spacer, col_logo = st.columns([3, 1])
with col_logo:
    st.image("Opmeer.png", width=300)

# 1) Supabase initialiseren
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supa = create_client(url, key)

# 2) Bedrijfslijst met e-mails
def load_companies():
    return {
        "ABC-hekwerk": "info@heras.nl",
        "Aesy Liften B.V.": "info@aesyliften.nl",
        # … alle andere bedrijven …
        "Veldhuis": "info@veldhuis.nl"
    }

# 3) Sleutel-lijst: locatie -> sleutelnummers
def load_keys():
    return {
        "Bibliotheek Opmeer":            "1, 2, 3",
        "Boevenhoeve":                   "43",
        "Bovenwoningen Spanbroek":       "15",
        "Brandweer Spanbroek":           "14",
        "Electrakast Rokersplein":       "57",
        "Gaskasten algemeen":            "52, 53",
        "Gemeentehuis":                  "26,27,28,29,30,31",
        "Gemeentewerf Spanbroek":        "13",
        "General key (sport)":           "55, 56",
        "Gymzaal Aartswoud":             "16, 17",
        "Gymzaal De Weere":              "36, 37",
        "Gymzaal Hoogwoud":              "32, 33",
        "Gymzaal Opmeer":                "46, 47, 48, 49",
        "Gymzaal Spanbroek":             "34, 35",
        "Hertenkamp Hoogwoud":           "18",
        "IJsbaangebouw":                 "40",
        "Muziekschool Opmeer":           "4",
        "Peuterspeelzaal Boevenhoeve":   "42",
        "Peuterspeelzaal de Kikkerhoek": "11, 12",
        "Peuterspeelzaal Hummeltjeshonk":"44",
        "Raadhuis Hoogwoud":             "19",
        "Raadhuis Spanbroek":            "20, 21, 22",
        "Telefoon gymzalen":             "54",
        "Theresiahuis":                  "5, 6",
        "Toren Aartswoud":               "23, 24",
        "Toren Wadway":                  "25",
        "Verenigingsgebouw":             "7, 8, 9, 10",
        "Watertappunt Hoogwoud":         "50",
        "Wijksteunpunt Lindehof":        "41",
        "Zaalvoetbalhal de Weyver":      "51",
        "Zwembad De Weijver":            "38, 39"
    }

# 4) E-mail setup
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
     <b>Tijd:</b> {time}
  </p>
  <p>
    <a href=\"{approve_link}\" style=\"
       background-color: #4CAF50;
       color: white; padding:10px 20px;
       text-decoration:none; border-radius:4px;\">
      ✅ Goedkeuren
    </a>
    &nbsp;
    <a href=\"{reject_link}\" style=\"
       background-color: #f44336;
       color: white; padding:10px 20px;
       text-decoration:none; border-radius:4px;\">
      ❌ Weigeren
    </a>
  </p>
</body></html>
"""
    part = MIMEText(html, "html")
    msg.attach(part)

    with smtplib.SMTP(st.secrets["smtp"]["server"], st.secrets["smtp"]["port"]) as s:
        s.starttls()
        s.login(st.secrets["smtp"]["user"], st.secrets["smtp"]["password"])
        s.send_message(msg)

# 5) URL-params afhandeling
params = st.query_params
handled = False
if "approve" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Goedgekeurd"})\
        .eq("id", int(params["res_id"][0])).execute()
    st.experimental_set_query_params()
    handled = True
elif "reject" in params and "res_id" in params:
    supa.table("bookings").update({"status": "Afgewezen"})\
        .eq("id", int(params["res_id"][0])).execute()
    st.experimental_set_query_params()
    handled = True

# 6) Modus-keuze
if handled:
    mode = "Beheer"
else:
    mode = st.sidebar.radio("Modus:", ["Reserveren", "Beheer"] )

# 7) Reserveren-modus
if mode == "Reserveren":
    st.title("Reservering maken")
    companies = load_companies()
    naam = st.selectbox("Bedrijf", sorted(companies.keys()))
    email_input = companies[naam]
    st.text_input("E-mail", value=email_input, disabled=True)
    datum = st.date_input("Datum")
    tijd = st.time_input("Tijd")
    access = st.checkbox("Toegang nodig?")

    # alleen locaties tonen, alfabetisch
    selected_locs = []
    if access:
        key_map = load_keys()
        selected_locs = st.multiselect(
            "Selecteer locatie(s)", sorted(key_map.keys())
        )

    ready = all([naam, email_input, datum, tijd])
    if not ready:
        st.info("Vul alle velden in om te verzenden")
    if st.button("Verstuur aanvraag", disabled=not ready):
        key_map = load_keys()
        locs_str = ", ".join(selected_locs)
        keys_str = ", ".join(key_map[loc] for loc in selected_locs)
        data = {
            "name": naam,
            "email": email_input,
            "date": datum.isoformat(),
            "time": tijd.strftime("%H:%M"),
            "access": "Ja" if access else "Nee",
            "access_locations": locs_str,
            "access_keys": keys_str,
            "status": "Wachten"
        }
        resp = supa.table("bookings").insert(data).execute()
        res_id = resp.data[0]["id"]
        send_owner_email(res_id, naam, data["date"], data["time"])
        st.success("✅ Aanvraag succesvol verzonden!")

# 8) Beheer-modus
else:
    st.title("Beheer aanvragen")
    st.markdown("_Hieronder kun je openstaande aanvragen direct accepteren of afwijzen._")
    rows = supa.table("bookings") \
               .select("*") \
               .neq("status", "Goedgekeurd") \
               .neq("status", "Afgewezen") \
               .order("date") \
               .execute().data

    if not rows:
        st.info("Geen openstaande aanvragen.")
    for r in rows:
        with st.expander(f"🔔 #{r['id']} – {r['name']} ({r['date']} {r['time']})"):
            col1, col2 = st.columns(2)
            if col1.button("✅ Goedkeuren", key=f"g{r['id']}"):
                supa.table("bookings").update({"status": "Goedgekeurd"})\
                    .eq("id", r["id"]).execute()
                st.experimental_set_query_params()
                st.experimental_rerun()
            if col2.button("❌ Weigeren", key=f"a{r['id']}"):
                supa.table("bookings").update({"status": "Afgewezen"})\
                    .eq("id", r["id"]).execute()
                st.experimental_set_query_params()
                st.experimental_rerun()

    st.subheader("Alle reserveringen")
    all_rows = supa.table("bookings") \
                  .select("*") \
                  .order("date") \
                  .execute().data
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
    ], height=400)
