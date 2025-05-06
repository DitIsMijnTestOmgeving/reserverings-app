import streamlit as st
import os
from supabase import create_client
from docx import Document
from io import BytesIO
import datetime

# Supabase
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supa = create_client(url, key)

# Sleutels
def load_keys():
    return {
        "Gemeentehuis": "26,27,28,29,30",
        "Gymzaal De Weere": "36, 37",
        "Brandweer Spanbroek": "14",
        # voeg hier alles toe
    }

def replace_bookmark_text(doc, bookmark_name, replacement_text):
    for bookmark_start in doc.element.xpath(f'//w:bookmarkStart[@w:name="{bookmark_name}"]'):
        parent = bookmark_start.getparent()
        index = parent.index(bookmark_start)
        if index + 1 < len(parent):
            parent.remove(parent[index + 1])
        from docx.oxml import OxmlElement
        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = replacement_text
        run.append(text)
        parent.insert(index + 1, run)

st.set_page_config(page_title="Sleuteluitgifte", page_icon="🔑", layout="wide")
st.title("🔑 Sleuteluitgifte")

bookings = supa.table("bookings").select("*").execute().data
key_map = load_keys()

goedgekeurd = [r for r in bookings if r["status"] == "Goedgekeurd"]
uitgegeven = [r for r in bookings if str(r["status"]).startswith("Uitgegeven")]

st.subheader("📄 Uitgifteformulier")
for r in goedgekeurd:
    with st.expander(f"#{r['id']} – {r['name']} ({r['date']} {r['time']})"):
        if st.button("📝 Genereer formulier", key=f"gen_{r['id']}"):
            doc = Document("Sleutel Afgifte Formulier.docx")
            replace_bookmark_text(doc, "Firma", r["name"])
            replace_bookmark_text(doc, "Sleutelnummer", r.get("access_keys", ""))
            replace_bookmark_text(doc, "Bestemd", r.get("access_locations", ""))
            replace_bookmark_text(doc, "AfgifteDatum", str(datetime.date.today()))

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            supa.table("bookings").update({"status": f"Uitgegeven op {datetime.date.today()}"}) \
                .eq("id", r["id"]).execute()

            st.download_button(
                label="⬇️ Download formulier",
                data=buffer,
                file_name="Sleutel_Afgifte_Formulier.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.rerun()

st.subheader("🔁 Retourmelding")
for r in uitgegeven:
    with st.expander(f"#{r['id']} – {r['name']} ({r['date']} {r['time']})"):
        if st.button("✅ Markeer als ingeleverd", key=f"inlever_{r['id']}"):
            supa.table("bookings").update({
                "status": f"Ingeleverd op {datetime.date.today()}"
            }).eq("id", r["id"]).execute()
            st.success("Gemarkeerd als ingeleverd.")
            st.rerun()
