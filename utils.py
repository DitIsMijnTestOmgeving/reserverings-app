import os
from supabase import create_client
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def get_supabase_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


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


def replace_bookmark_text(doc, bookmark_name, replacement_text):
    for bookmark_start in doc.element.xpath(f'//w:bookmarkStart[@w:name="{bookmark_name}"]'):
        parent = bookmark_start.getparent()
        index = parent.index(bookmark_start)

        if index + 1 < len(parent):
            parent.remove(parent[index + 1])

        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = replacement_text
        run.append(text)
        parent.insert(index + 1, run)


def send_owner_email(res_id, name, date, time):
    print(f"[MAILTEST] Verstuur poging voor reservering #{res_id}")
    approve_link = f"https://reserveringsapp-opmeer.onrender.com/Beheer?approve=true&res_id={res_id}"
    reject_link = f"https://reserveringsapp-opmeer.onrender.com/Beheer?reject=true&res_id={res_id}"
    beheer_link = "https://reserveringsapp-opmeer.onrender.com/Beheer?via=mail"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Reservering] Nieuwe aanvraag #{res_id}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["OWNER_EMAIL"]
    #msg["To"] = ", ".join(["bdielissen@opmeer.nl", "tkok@opmeer.nl"])

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;font-size:14px;">
      <p>Er is een nieuwe reserveringsaanvraag:</p>
      <p>
        <b>Reservering:</b> #{res_id}<br>
        <b>Bedrijf:</b> {name}<br>
        <b>Datum:</b> {date}<br>
        <b>Tijd:</b> {time}
      </p>

      <table cellspacing="10" cellpadding="0">
        <tr>
          <td>
            <a href="{approve_link}" style="background-color:#4CAF50;color:white;padding:12px 20px;text-decoration:none;border-radius:6px;display:inline-block;">
              ✅ Goedkeuren
            </a>
          </td>
        </tr>
        <tr>
          <td>
            <a href="{reject_link}" style="background-color:#f44336;color:white;padding:12px 20px;text-decoration:none;border-radius:6px;display:inline-block;">
              ❌ Afwijzen
            </a>
          </td>
        </tr>
        <tr>
          <td>
            <a href="{beheer_link}" style="background-color:#2196F3;color:white;padding:12px 20px;text-decoration:none;border-radius:6px;display:inline-block;">
              🔑 Beheerpagina openen
            </a>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)


def send_confirmation_email(email, name, date, time):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Bevestiging sleutelreservering – {date}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = email

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;font-size:14px;">
      <p>Beste {name},</p>
      <p>Jouw sleutelreservering is goedgekeurd:</p>
      <p>
        <b>Datum:</b> {date}<br>
        <b>Tijd:</b> {time}<br>
      </p>
      <p>Je ontvangt de sleutels volgens afspraak.</p>
      <p>Met vriendelijke groet,<br>Gemeente Opmeer</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.environ["SMTP_PORT"])) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    except Exception as e:
        print(f"[MAILFOUT] Bevestigingsmail mislukt: {e}")


def send_access_link_email(email, naam="Gebruiker"):
    link = "https://reserveringsapp-opmeer.onrender.com/Sleuteluitgifte?via=mail"

    msg = MIMEMultipart("mixed")
    msg["Subject"] = "Toegang tot Sleuteluitgiftepagina"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = email

    # HTML met alleen knop
    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;font-size:14px;">
      <p>Beste {naam},</p>
      <p>Via onderstaande knop krijg je direct toegang tot de sleuteluitgiftepagina:</p>
      <p>
        <a href="{link}" style="background-color:#2196F3;color:white;padding:12px 20px;
          text-decoration:none;border-radius:6px;display:inline-block;">
          🔑 Open Sleuteluitgiftepagina
        </a>
      </p>
      <p>De instructie is toegevoegd als PDF-bijlage.</p>
      <p>Met vriendelijke groet,<br>Gemeente Opmeer</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    # Voeg PDF-bijlage toe
    try:
        with open("Sleuteluitgifte uitleg.pdf", "rb") as f:
            from email.mime.application import MIMEApplication
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header('Content-Disposition', 'attachment', filename="Sleuteluitgifte uitleg.pdf")
            msg.attach(part)
    except Exception as e:
        print(f"[PDF-ERROR] Kan PDF niet bijvoegen: {e}")

    # Versturen
    try:
        with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.environ["SMTP_PORT"])) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    except Exception as e:
        print(f"[MAILFOUT] Sleuteluitgifte e-mail mislukt: {e}")

 
