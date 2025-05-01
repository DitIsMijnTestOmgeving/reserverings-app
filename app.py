import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText

# 1) Pagina-instellingen
st.set_page_config(
    page_title="Reservering Beheer",
    page_icon="🍽️",
    layout="wide"
)

# 2) Laad SMTP- en eigenaargegevens uit secrets
owner_email   = st.secrets["owner"]["email"]
smtp_server   = st.secrets["smtp"]["server"]
smtp_port     = st.secrets["smtp"]["port"]
smtp_user     = st.secrets["smtp"]["user"]
smtp_password = st.secrets["smtp"]["password"]

# 3) Functie om e-mail te sturen
def send_owner_email(res_id, name, date, time):
    body = f"""
Nieuwe reservering #{res_id}
Naam: {name}
Datum: {date}
Tijd:  {time}

Open de app om deze aanvraag te accepteren of te weigeren.
"""
    msg = MIMEText(body)
    msg["Subject"] = f"[Reservering] #{res_id} van {name}"
    msg["From"]    = smtp_user
    msg["To"]      = owner_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

# 4) Database verbinding en schema
def get_db_connection():
    conn = sqlite3.connect('bookings.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
)
""")
    conn.commit()
    return conn

# Gebruik een singleton voor de database
conn = get_db_connection()
c = conn.cursor()

# Sidebar: Nieuwe reservering
st.sidebar.header("Maak een nieuwe reservering")
naam  = st.sidebar.text_input("Naam")
datum = st.sidebar.date_input("Datum")
tijd  = st.sidebar.time_input("Tijd")
if st.sidebar.button("Verstuur aanvraag"):
    c.execute(
        "INSERT INTO bookings (name, date, time) VALUES (?, ?, ?)",
        (naam, datum.isoformat(), tijd.strftime("%H:%M"))
    )
    conn.commit()
    res_id = c.lastrowid
    send_owner_email(res_id, naam, datum.isoformat(), tijd.strftime("%H:%M"))
    st.sidebar.success("✅ Aanvraag verzonden! Je ontvangt spoedig bericht.")

# Hoofdscherm: beheer
st.title("Reserveringsbeheer")

# 5) Openstaande aanvragen
st.subheader("Openstaande aanvragen")
pending = c.execute(
    "SELECT id, name, date, time FROM bookings WHERE status='pending'"
).fetchall()
for res_id, nm, dt, tm in pending:
    st.write(f"• #{res_id} – {nm} op {dt} om {tm}")
    col_acc, col_rej = st.columns(2)
    if col_acc.button(f"✅ Accepteer {res_id}"):
        c.execute("UPDATE bookings SET status='accepted' WHERE id=?", (res_id,))
        conn.commit()
        st.success(f"Reservering #{res_id} geaccepteerd")
    if col_rej.button(f"❌ Weiger {res_id}"):
        c.execute("UPDATE bookings SET status='rejected' WHERE id=?", (res_id,))
        conn.commit()
        st.info(f"Reservering #{res_id} geweigerd")

# 6) Overzicht van alle reserveringen
st.subheader("Alle reserveringen")
all_rows = c.execute(
    "SELECT name, date, time, status FROM bookings ORDER BY date, time"
).fetchall()

table = [
    {"Naam": r[0], "Datum": r[1], "Tijd": r[2], "Status": r[3]}
    for r in all_rows
]
st.dataframe(table, height=400)
