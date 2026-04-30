import streamlit as st
import pandas as pd
from lxml import etree
import os
import io
import uuid

# Setup directories
SCHEMAS_DIR = "schemas"
TEMP_XML_DIR = "temp_xml_files"
for d in [SCHEMAS_DIR, TEMP_XML_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

is_view_mode = "view_xml" in st.query_params

if is_view_mode:
    st.set_page_config(page_title="XML Ansicht", layout="wide")
    xml_id = st.query_params["view_xml"]
    
    file_dir = os.path.join(TEMP_XML_DIR, xml_id)
    if os.path.exists(file_dir) and os.path.isdir(file_dir):
        files = os.listdir(file_dir)
        if files:
            file_to_open = os.path.join(file_dir, files[0])
            filename = files[0]
            with open(file_to_open, "r", encoding="utf-8") as f:
                xml_content = f.read()
            st.title(f"XML Ansicht: {filename}")
            st.code(xml_content, language="xml", line_numbers=True)
        else:
            st.error("Die XML-Datei wurde nicht gefunden.")
    else:
        st.error("Die XML-Datei wurde nicht gefunden. Möglicherweise ist die Sitzung abgelaufen.")
    
    st.stop()
else:
    st.set_page_config(page_title="XML Validator", page_icon="✅", layout="wide")

# Custom CSS for vibrant dark mode, shadows, and hover effects
custom_css = """
<style>
    /* Main container background gradient */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e17 0%, #111827 100%);
    }

    /* Top decoration bar */
    [data-testid="stHeader"] {
        background: rgba(10, 14, 23, 0.8) !important;
        backdrop-filter: blur(10px);
    }
    
    /* Upload Dropzone Hover & Neon Glow */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed rgba(0, 242, 254, 0.5) !important;
        background: rgba(30, 41, 59, 0.4) !important;
        border-radius: 12px;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border: 2px dashed #00f2fe !important;
        background: rgba(0, 242, 254, 0.05) !important;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.3);
        transform: translateY(-2px);
    }

    /* Buttons */
    .stButton > button, [data-testid="stDownloadButton"] > button {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 20px rgba(0, 114, 255, 0.6) !important;
        background: linear-gradient(90deg, #00d2ff 0%, #0088ff 100%) !important;
    }
    
    /* Metrics Boxes */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.4);
        border: 1px solid rgba(0, 242, 254, 0.3);
    }
    [data-testid="stMetricValue"] {
        color: #00f2fe !important;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }

    /* DataFrame Container */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("XML Validator")
st.markdown("Lade XML-Dateien hoch, um sie auf Syntax und gegen XSD-Schemas zu validieren.")
st.markdown("ℹ️ **Angewendete Schemas:** Offizielles XML Schema Package der [ASD S1000D Issue 4.2](https://www.s-series.org/s1000d/)")

def parse_xml(file_bytes):
    """Parses XML and checks for well-formedness."""
    parser = etree.XMLParser(recover=False)
    try:
        tree = etree.parse(io.BytesIO(file_bytes), parser)
        return tree, True, "Erfolgreich"
    except etree.XMLSyntaxError as e:
        return None, False, f"Zeile {e.lineno}: {e.msg}"
    except Exception as e:
        return None, False, str(e)

def detect_schema(tree):
    """Tries to detect schema from root element."""
    root = tree.getroot()
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    
    # Check for xsi:noNamespaceSchemaLocation
    no_ns_loc = root.get(f"{{{xsi_ns}}}noNamespaceSchemaLocation")
    if no_ns_loc:
        return no_ns_loc.split('/')[-1]

    # Check for xsi:schemaLocation
    schema_loc = root.get(f"{{{xsi_ns}}}schemaLocation")
    if schema_loc:
        # schemaLocation typically contains namespace and location separated by space
        parts = schema_loc.split()
        if len(parts) >= 2:
            return parts[1].split('/')[-1] # Returning the location part
        return parts[0].split('/')[-1]
        
    # Check namespace
    nsmap = root.nsmap
    if None in nsmap:
        return nsmap[None]
        
    return "Unbekannt"

def find_local_xsd(schema_hint):
    """Finds a matching XSD in the schemas directory."""
    if not schema_hint or schema_hint == "Unbekannt":
        return None
        
    available_xsds = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith('.xsd')]
    
    # Simple heuristic: Does the hint match an exact filename?
    for xsd in available_xsds:
        if xsd in schema_hint or schema_hint in xsd:
            return os.path.join(SCHEMAS_DIR, xsd)
            
    # Default to the first one if there's only one, or return None
    if len(available_xsds) == 1:
        return os.path.join(SCHEMAS_DIR, available_xsds[0])
        
    return None

def validate_xml(tree, xsd_path):
    """Validates XML tree against given XSD path."""
    try:
        schema_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(schema_doc)
        
        if schema.validate(tree):
            return True, "Erfolgreich"
        else:
            errors = "; ".join([f"Zeile {err.line}: {err.message}" for err in schema.error_log])
            return False, errors
            
    except Exception as e:
        return False, f"Fehler beim Laden/Validieren des Schemas: {str(e)}"

# File uploader
uploaded_files = st.file_uploader("XML Dateien hierher ziehen (Drag & Drop) oder auswählen", type="xml", accept_multiple_files=True)

if uploaded_files:
    results = []
    
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        
        xml_id = str(uuid.uuid4())
        file_dir = os.path.join(TEMP_XML_DIR, xml_id)
        os.makedirs(file_dir, exist_ok=True)
        
        safe_filename = "".join([c for c in filename if c.isalnum() or c in (' ', '.', '-', '_')]).rstrip()
        if not safe_filename:
            safe_filename = "unnamed.xml"
        temp_filepath = os.path.join(file_dir, safe_filename)
        
        # 1. Parsing
        tree, parse_success, parse_msg = parse_xml(file_bytes)
        
        # Save beautified or raw XML
        if parse_success:
            beautified_xml = etree.tostring(tree, pretty_print=True, encoding='unicode')
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(beautified_xml)
        else:
            try:
                raw_xml = file_bytes.decode('utf-8')
            except:
                raw_xml = str(file_bytes)
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(raw_xml)
        
        if not parse_success:
            results.append({
                "__xml_id": xml_id,
                "Dateiname": filename,
                "Status (Parsing)": "Fehlerhaft",
                "Status (Validierung)": "N/A",
                "Angewendetes Schema": "N/A",
                "Fehlerdetails": parse_msg
            })
            continue
            
        # 2. Schema Detection
        schema_hint = detect_schema(tree)
        xsd_path = find_local_xsd(schema_hint)
        
        if not xsd_path:
            results.append({
                "__xml_id": xml_id,
                "Dateiname": filename,
                "Status (Parsing)": "Erfolgreich",
                "Status (Validierung)": "Fehlerhaft",
                "Angewendetes Schema": f"Nicht gefunden ({schema_hint})",
                "Fehlerdetails": "Kein passendes XSD im /schemas/ Ordner gefunden."
            })
            continue
            
        # 3. Validation
        val_success, val_msg = validate_xml(tree, xsd_path)
        xsd_filename = os.path.basename(xsd_path)
        
        results.append({
            "__xml_id": xml_id,
            "Dateiname": filename,
            "Status (Parsing)": "Erfolgreich",
            "Status (Validierung)": "Erfolgreich" if val_success else "Fehlerhaft",
            "Angewendetes Schema": xsd_filename,
            "Fehlerdetails": val_msg if not val_success else ""
        })
        
    df = pd.DataFrame(results)
    
    # Summary Metrics
    st.subheader("Zusammenfassung")
    total_files = len(df)
    successful = len(df[(df["Status (Parsing)"] == "Erfolgreich") & (df["Status (Validierung)"] == "Erfolgreich")])
    failed = total_files - successful
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamtanzahl Dateien", total_files)
    col2.metric("Erfolgreich", successful)
    col3.metric("Fehlerhaft", failed)
    
    # Excel Export Data Generation
    output = io.BytesIO()
    export_df = df.drop(columns=['__xml_id'])
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Validierungsergebnisse')
    export_data = output.getvalue()
    
    # Display Table Header with Download Button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("Detailergebnisse")
    with header_col2:
        # Move button slightly down to align with subheader text
        st.write("") 
        st.download_button(
            label="Ergebnisse als Excel (.xlsx)",
            data=export_data,
            file_name="xml_validierung_ergebnisse.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )
    
    def color_status(val):
        if val == 'Erfolgreich':
            return 'color: #00e676; font-weight: bold;'  # Vibrant neon green
        elif val == 'Fehlerhaft':
            return 'color: #ff1744; font-weight: bold;'  # Vibrant neon red
        return 'color: #f8fafc;'
        
    display_df = df.copy()
    display_df.index = display_df.index + 1  # Index startet bei 1
    
    display_df["Dateiname"] = display_df.apply(
        lambda x: f"/?view_xml={x['__xml_id']}&name={x['Dateiname']}", 
        axis=1
    )
    display_df = display_df.drop(columns=['__xml_id'])
    
    # Platzhalter für die Tabelle, damit wir das Dropdown darunter rendern können
    table_placeholder = st.container()
    
    # Dropdown für Zeilenanzahl rechts unten
    col_empty, col_select = st.columns([3, 1])
    with col_select:
        page_size = st.selectbox("Angezeigte Zeilen", options=[10, 20, 50, 100], index=0)
        
    # Höhe berechnen (Header ~40px + ca. 36px pro Zeile)
    actual_rows = min(len(display_df), page_size)
    df_height = 40 + (max(1, actual_rows) * 36)
        
    with table_placeholder:
        st.dataframe(
            display_df.style.map(color_status, subset=['Status (Parsing)', 'Status (Validierung)']),
            column_config={
                "Dateiname": st.column_config.LinkColumn("Dateiname", display_text=r"name=(.+)$")
            },
            width="stretch",
            height=df_height
        )
    
    # End of results display
else:
    st.info("Bitte lade eine oder mehrere XML-Dateien hoch, um zu beginnen.")
    
    with st.expander("Hinweise zur Verwendung"):
        st.markdown(f'''
        1. Stelle sicher, dass XSD-Dateien im Ordner `{os.path.abspath(SCHEMAS_DIR)}` liegen.
        2. Die Applikation sucht im Root-Element der XML nach `xsi:schemaLocation` oder Namespaces, um das passende Schema zu finden.
        ''')
