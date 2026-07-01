# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
from lxml import etree
import os
import io
import uuid
import re
import shutil
import time
import socket
import concurrent.futures

# Setup directories with memory protection constants
SCHEMAS_DIR = "schemas"
TEMP_XML_DIR = "temp_xml_files"
MAX_TEMP_DIRS = 50  # Limitierung temporärer Verzeichnisse (Memory Protection)
socket.setdefaulttimeout(30)  # Timeout für Parsing großer Dateien
for d in [SCHEMAS_DIR, TEMP_XML_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

def sanitize_filename(filename):
    """Sichert Filenamen vor Path-Traversal und XSS-Angriffen."""
    base, ext = os.path.splitext(filename)
    dangerous_patterns = ['..', '<script>', 'javascript:', 'onload', 'onclick']
    for pattern in dangerous_patterns:
        base = re.sub(pattern.lower(), '', base, flags=re.IGNORECASE)
    sanitized = "".join(c for c in base if c.isalnum() or c in (' ', '.', '-', '_', '@'))
    sanitized = sanitized.strip()
    return (sanitized or "unnamed") + ext

def cleanup_expired_temp_files(max_age_hours=12):
    """
    Löscht alle Unterverzeichnisse in TEMP_XML_DIR, die älter als max_age_hours sind.
    Entfernt auch alte Verzeichnisse, wenn Limit (MAX_TEMP_DIRS) erreicht.
    """
    if not os.path.exists(TEMP_XML_DIR):
        return

    now = time.time()
    max_age_seconds = max_age_hours * 3600

    # Alle Unterverzeichnisse auflisten und nach Änderungszeit sortieren
    dirs = []
    for entry in os.listdir(TEMP_XML_DIR):
        path = os.path.join(TEMP_XML_DIR, entry)
        if os.path.isdir(path):
            dirs.append((path, os.path.getmtime(path)))
            
    # Sortieren nach mtime (älteste zuerst)
    dirs.sort(key=lambda x: x[1])

    # 1. Ältere Verzeichnisse löschen (> max_age_hours)
    remaining_dirs = []
    for path, mtime in dirs:
        if (now - mtime) > max_age_seconds:
            try:
                shutil.rmtree(path)
            except Exception:
                pass
        else:
            remaining_dirs.append(path)

    # 2. Wenn Limit überschritten, die ältesten verbleibenden löschen
    if len(remaining_dirs) > MAX_TEMP_DIRS:
        to_delete = remaining_dirs[:len(remaining_dirs) - MAX_TEMP_DIRS]
        for path in to_delete:
            try:
                shutil.rmtree(path)
            except Exception:
                pass

# Führe Bereinigung einmalig beim Start aus
cleanup_expired_temp_files()

is_view_mode = "view_xml" in st.query_params

if is_view_mode:
    st.set_page_config(page_title="XML Ansicht", layout="wide")
    xml_id = st.query_params["view_xml"]
    
    file_dir = os.path.join(TEMP_XML_DIR, xml_id)
    
    # Pfad-Traversal absichern
    resolved_path = os.path.abspath(file_dir)
    base_path = os.path.abspath(TEMP_XML_DIR)
    if not resolved_path.startswith(base_path):
        st.error("Ungültiger Zugriffspfad.")
        st.stop()
        
    if os.path.exists(file_dir) and os.path.isdir(file_dir):
        files = os.listdir(file_dir)
        raw_file = next((f for f in files if f.startswith("raw_")), None)
        pretty_file = next((f for f in files if f.startswith("pretty_")), None)
        
        if not files:
            st.error("Die XML-Datei wurde nicht gefunden.")
        else:
            # Fallback falls die Dateien noch nach altem Namensschema gespeichert wurden
            if not raw_file and not pretty_file:
                raw_file = files[0]
                
            filename = raw_file[4:] if (raw_file and raw_file.startswith("raw_")) else raw_file
            st.title(f"XML Ansicht: {filename}")
            
            if raw_file and pretty_file:
                mode = st.radio("Ansichtsmodus:", ["Original (für exakte Zeilennummern)", "Formatiert (Beautified)"], horizontal=True)
                file_to_open = os.path.join(file_dir, raw_file if "Original" in mode else pretty_file)
            else:
                st.info("Diese Datei konnte nicht geparst werden oder liegt nur in einem Format vor. Es wird die verfügbare Ansicht angezeigt.")
                file_to_open = os.path.join(file_dir, raw_file or pretty_file)
                
            with open(file_to_open, "r", encoding="utf-8") as f:
                xml_content = f.read()
            st.code(xml_content, language="xml", line_numbers=True)
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
st.markdown("ℹ️ **Angewendete Schemas:** Offizielle XML Schema Packages der **ASD S1000D Issues 2.3, 3.0, 4.0.1, 4.1, 4.2 und 5.0** (automatische Erkennung)")

def parse_xml(file_bytes):
    """Parses XML and checks for well-formedness with timeout protection. Allows loading external DTDs like ISOEntities."""
    # Sicherheitsmaßnahme: no_network=True verhindert externe Netzwerkanfragen (XXE Schutz)
    parser = etree.XMLParser(recover=False, no_network=True, load_dtd=True)
    try:
        tree = etree.parse(io.BytesIO(file_bytes), parser)
        return tree, True, "Erfolgreich"
    except socket.timeout:
        return None, False, f"Parsing-Timeout (Datei zu groß für {socket.getdefaulttimeout()}s)"
    except etree.XMLSyntaxError as e:
        return None, False, f"Zeile {e.lineno}: {e.msg}"
    except ValueError as e:
        # UTF-8 Decoding Fehler
        return None, False, f"Enkodierungsfehler: {str(e)[:200]}"
    except OSError as e:
        # Speicher-Fehler
        return None, False, f"Speicher-Fehler: {str(e)}"
    except Exception as e:
        # Unbekannte Fehler kategorisieren
        error_type = type(e).__name__
        return None, False, f"{error_type}: {str(e)[:500]}"

@st.cache_resource
def load_schema(xsd_path):
    """Parses and compiles an XSD schema from the given path, cached by Streamlit."""
    schema_doc = etree.parse(xsd_path)
    return etree.XMLSchema(schema_doc)

# Available issues in priority order
ISSUES = [
    {"name": "5.0", "folder": "5-0"},
    {"name": "4.2", "folder": "4-2"},
    {"name": "4.1", "folder": "4-1"},
    {"name": "4.0.1", "folder": "4-0-1"},
    {"name": "3.0", "folder": "3-0"},
    {"name": "2.3", "folder": "2-3"},
]

def detect_issue_and_xsd(tree):
    """Detects S1000D issue version and selects corresponding schema file."""
    root = tree.getroot()
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    
    # Extract schema hint
    schema_hint = None
    version_check_str = ""
    no_ns_loc = root.get(f"{{{xsi_ns}}}noNamespaceSchemaLocation")
    if no_ns_loc:
        schema_hint = no_ns_loc.strip()
        version_check_str = schema_hint
    else:
        schema_loc = root.get(f"{{{xsi_ns}}}schemaLocation")
        if schema_loc:
            parts = schema_loc.split()
            if len(parts) >= 2:
                schema_hint = parts[1].strip()
            else:
                schema_hint = parts[0].strip()
            version_check_str = schema_loc
    
    # Extract schema filename (e.g. descript.xsd)
    schema_file = None
    if schema_hint:
        schema_file = schema_hint.split('/')[-1].split('\\')[-1]
        
    # Collect all potential URI strings to check for version info
    uris_to_check = []
    if version_check_str:
        uris_to_check.append(version_check_str)
    # Also add root namespaces
    for ns_uri in root.nsmap.values():
        if ns_uri:
            uris_to_check.append(ns_uri)
            
    # First attempt: Detect from URIs or namespaces
    detected_issue = None
    for uri in uris_to_check:
        uri_lower = uri.lower()
        if "5-0" in uri_lower or "5.0" in uri_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "5.0")
            break
        elif "4-2" in uri_lower or "4.2" in uri_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "4.2")
            break
        elif "4-1" in uri_lower or "4.1" in uri_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "4.1")
            break
        elif "4-0-1" in uri_lower or "4.0.1" in uri_lower or "4-0" in uri_lower or "4.0" in uri_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "4.0.1")
            break
        elif "3-0" in uri_lower or "3.0" in uri_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "3.0")
            break
        elif "2-3" in uri_lower or "2.3" in uri_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "2.3")
            break
    
    # Second attempt: check DOCTYPE system ID if schema_hint didn't work or was ambiguous
    if not detected_issue and tree.docinfo.system_url:
        sys_url_lower = tree.docinfo.system_url.lower()
        if "5-0" in sys_url_lower or "5.0" in sys_url_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "5.0")
        elif "4-2" in sys_url_lower or "4.2" in sys_url_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "4.2")
        elif "4-1" in sys_url_lower or "4.1" in sys_url_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "4.1")
        elif "4-0-1" in sys_url_lower or "4.0.1" in sys_url_lower or "4-0" in sys_url_lower or "4.0" in sys_url_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "4.0.1")
        elif "3-0" in sys_url_lower or "3.0" in sys_url_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "3.0")
        elif "2-3" in sys_url_lower or "2.3" in sys_url_lower:
            detected_issue = next(i for i in ISSUES if i["name"] == "2.3")
            
        if not schema_file:
            base_name = tree.docinfo.system_url.split('/')[-1].split('\\')[-1]
            if base_name:
                if base_name.endswith('.dtd'):
                    schema_file = base_name[:-4] + '.xsd'
                else:
                    schema_file = base_name

    # Third attempt: structural heuristics
    if not detected_issue:
        if root.find(".//idstatus") is not None:
            if root.find(".//status/srcdmaddres") is not None:
                detected_issue = next(i for i in ISSUES if i["name"] == "3.0")
            elif root.find(".//idstatus/srcdmaddres") is not None:
                detected_issue = next(i for i in ISSUES if i["name"] == "2.3")
            elif root.find(".//applic/displaytext") is not None:
                detected_issue = next(i for i in ISSUES if i["name"] == "3.0")
            elif root.find(".//applic/type") is not None or root.find(".//applic/model") is not None:
                detected_issue = next(i for i in ISSUES if i["name"] == "2.3")
            else:
                detected_issue = next(i for i in ISSUES if i["name"] == "3.0")

    # Resolve schema path and fallback search
    xsd_path = None
    if schema_file:
        if detected_issue:
            potential_path = os.path.join(SCHEMAS_DIR, detected_issue["folder"], schema_file)
            if os.path.exists(potential_path):
                xsd_path = potential_path
        
        # If not found in detected issue folder, or not yet detected, try checking all folders
        if not xsd_path:
            for issue in ISSUES:
                p = os.path.join(SCHEMAS_DIR, issue["folder"], schema_file)
                if os.path.exists(p):
                    xsd_path = p
                    if not detected_issue:
                        detected_issue = issue
                    break

    # If no schema file found, infer by tag
    if not xsd_path:
        tag_to_schema = {
            "dmodule": "descript.xsd",
            "pm": "pm.xsd",
            "ddn": "ddn.xsd",
            "dml": "dml.xsd",
            "brex": "brex.xsd",
            "appliccrossreftable": "appliccrossreftable.xsd",
            "condcrossreftable": "condcrossreftable.xsd",
            "prdcrossreftable": "prdcrossreftable.xsd",
            "container": "container.xsd",
        }
        tag = root.tag
        if "}" in tag:
            tag = tag.split("}")[1]
        inferred_file = tag_to_schema.get(tag)
        if inferred_file:
            schema_file = inferred_file
            if detected_issue:
                p = os.path.join(SCHEMAS_DIR, detected_issue["folder"], schema_file)
                if os.path.exists(p):
                    xsd_path = p
            else:
                for issue in ISSUES:
                    p = os.path.join(SCHEMAS_DIR, issue["folder"], schema_file)
                    if os.path.exists(p):
                        xsd_path = p
                        detected_issue = issue
                        break
                        
    return detected_issue, xsd_path, schema_hint or "Unbekannt"

def translate_error(msg):
    if "[facet 'pattern'] The value" in msg and "(cm|in|mm|pc|pt)" in msg:
        val = re.search(r"The value '(.*?)'", msg)
        v = val.group(1) if val else "Unbekannt"
        return f"Fehlende oder falsche Maßeinheit für Wert '{v}'. Erlaubt sind z.B. 'mm', 'cm', 'in', 'pt'."
    if "[facet 'enumeration'] The value" in msg and "is not an element of the set" in msg:
        val = re.search(r"The value '(.*?)'", msg)
        v = val.group(1) if val else "Unbekannt"
        return f"Der Wert '{v}' ist ungültig (nicht in der vorgegebenen Liste)."
    if "[facet 'pattern'] The value" in msg:
        val = re.search(r"The value '(.*?)'", msg)
        pat = re.search(r"pattern '(.*?)'", msg)
        v = val.group(1) if val else "Unbekannt"
        p = pat.group(1) if pat else ""
        return f"Der Wert '{v}' hat das falsche Format (Erwartet: '{p}')."
    if "This element is not expected." in msg:
        expected = re.search(r"Expected is one of (.*?)\.", msg)
        if expected:
            return f"Tag an dieser Stelle nicht erlaubt. Erwartet wird: {expected.group(1)}."
        expected_single = re.search(r"Expected is (.*?)\.", msg)
        if expected_single:
             return f"Tag an dieser Stelle nicht erlaubt. Erwartet wird: {expected_single.group(1)}."
        return "Tag an dieser Stelle laut Schema nicht erlaubt."
    if "Missing child element(s)." in msg:
        expected = re.search(r"Expected is (.*?)\.", msg)
        if expected:
            return f"Struktur unvollständig. Es fehlt: {expected.group(1)}."
        return "Struktur unvollständig. Es fehlen Unter-Elemente."
    if "is not allowed" in msg and "attribute" in msg.lower():
         attr = re.search(r"attribute '(.*?)'", msg)
         a = attr.group(1) if attr else "Unbekannt"
         return f"Das Attribut '{a}' ist hier nicht erlaubt."
    return msg

def format_error(line, message):
    parts = message.split(": ", 1)
    if len(parts) > 1 and ("Element " in parts[0] or "attribute " in parts[0]):
        context = parts[0].replace("Element ", "<").replace("', attribute", "> | Attribut").replace("'", "")
        if "<" in context and ">" not in context: context += ">"
        reason = parts[1]
        friendly_reason = translate_error(reason)
        return f"Zeile {line} [{context}]: {friendly_reason}"
    else:
        return f"Zeile {line}: {translate_error(message)}"

def validate_xml(tree, xsd_path):
    """Validates XML tree against given XSD path using thread-safe assertValid."""
    try:
        schema = load_schema(xsd_path)
        
        try:
            schema.assertValid(tree)
            return True, "Erfolgreich"
        except etree.DocumentInvalid as e:
            errors_list = []
            for err in e.error_log:
                errors_list.append(format_error(err.line, err.message))
            errors = " | ".join(errors_list)
            return False, errors
            
    except Exception as e:
        return False, f"Fehler beim Laden/Validieren des Schemas: {str(e)}"

def process_single_file(uploaded_file):
    """Parses, detects schema, and validates a single uploaded XML file."""
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name
    
    xml_id = str(uuid.uuid4())
    file_dir = os.path.join(TEMP_XML_DIR, xml_id)
    os.makedirs(file_dir, exist_ok=True)
    
    safe_filename = sanitize_filename(filename)
        
    raw_filepath = os.path.join(file_dir, f"raw_{safe_filename}")
    pretty_filepath = os.path.join(file_dir, f"pretty_{safe_filename}")
    
    # 1. Parsing
    tree, parse_success, parse_msg = parse_xml(file_bytes)
    
    # Immer die Originaldatei speichern (für korrekte Zeilennummern bei Validierungsfehlern)
    try:
        raw_xml = file_bytes.decode('utf-8')
    except Exception:
        raw_xml = str(file_bytes)
    try:
        with open(raw_filepath, "w", encoding="utf-8") as f:
            f.write(raw_xml)
    except Exception:
        pass
        
    # Wenn geparst werden konnte, auch eine formatierte Version speichern
    if parse_success:
        try:
            beautified_xml = etree.tostring(tree, pretty_print=True, encoding='unicode')
            with open(pretty_filepath, "w", encoding="utf-8") as f:
                f.write(beautified_xml)
        except Exception:
            pass
    
    if not parse_success:
        return {
            "__xml_id": xml_id,
            "Dateiname": filename,
            "Erkannter Issue": "N/A",
            "Status (Parsing)": "Fehlerhaft",
            "Status (Validierung)": "N/A",
            "Angewendetes Schema": "N/A",
            "Fehlerdetails": parse_msg
        }
        
    # 2. Schema Detection & Version Detection
    detected_issue, xsd_path, schema_hint = detect_issue_and_xsd(tree)
    
    if not xsd_path:
        return {
            "__xml_id": xml_id,
            "Dateiname": filename,
            "Erkannter Issue": f"Issue {detected_issue['name']}" if detected_issue else "Unbekannt",
            "Status (Parsing)": "Erfolgreich",
            "Status (Validierung)": "Fehlerhaft",
            "Angewendetes Schema": f"Nicht gefunden ({schema_hint})" if schema_hint else "Nicht gefunden",
            "Fehlerdetails": "Kein passendes XSD im /schemas/ Ordner gefunden."
        }
        
    # 3. Validation
    val_success, val_msg = validate_xml(tree, xsd_path)
    xsd_filename = os.path.basename(xsd_path)
    
    return {
        "__xml_id": xml_id,
        "Dateiname": filename,
        "Erkannter Issue": f"Issue {detected_issue['name']}" if detected_issue else "Unbekannt",
        "Status (Parsing)": "Erfolgreich",
        "Status (Validierung)": "Erfolgreich" if val_success else "Fehlerhaft",
        "Angewendetes Schema": xsd_filename,
        "Fehlerdetails": val_msg if not val_success else ""
    }

# File uploader
uploaded_files = st.file_uploader("XML Dateien hierher ziehen (Drag & Drop) oder auswählen", type="xml", accept_multiple_files=True)

if uploaded_files:
    # 0. Bereinigung alter temporärer Verzeichnisse bei jedem Upload-Event ausführen
    cleanup_expired_temp_files()
    
    # Eindeutige ID für diesen Satz von Dateien (Name und Größe kombinieren)
    upload_id = "-".join([f"{f.name}_{f.size}" for f in uploaded_files])
    
    # Prüfen, ob sich der Upload geändert hat oder noch nichts validiert wurde
    if "last_upload_id" not in st.session_state or st.session_state.last_upload_id != upload_id:
        # Parallelisierte Validierung mit ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(process_single_file, uploaded_files))
            
        df = pd.DataFrame(results)
        
        # Excel Export Daten einmalig generieren
        output = io.BytesIO()
        export_df = df.drop(columns=['__xml_id'])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Validierungsergebnisse')
        export_data = output.getvalue()
        
        # In Session-State speichern
        st.session_state.validation_results = df
        st.session_state.excel_data = export_data
        st.session_state.last_upload_id = upload_id
    else:
        # Ergebnisse aus dem Session-State laden (verhindert Neuberechnung bei UI-Reruns)
        df = st.session_state.validation_results
        export_data = st.session_state.excel_data
        
    # Summary Metrics
    st.subheader("Zusammenfassung")
    total_files = len(df)
    successful = len(df[(df["Status (Parsing)"] == "Erfolgreich") & (df["Status (Validierung)"] == "Erfolgreich")])
    failed = total_files - successful
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamtanzahl Dateien", total_files)
    col2.metric("Erfolgreich", successful)
    col3.metric("Fehlerhaft", failed)
    
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
        1. Stelle sicher, dass die XSD-Dateien in den entsprechenden Unterordnern für die S1000D Issues im Ordner `{os.path.abspath(SCHEMAS_DIR)}` liegen (z. B. `schemas/2-3/`, `schemas/3-0/`, `schemas/4-0-1/`, `schemas/4-1/`, `schemas/4-2/`, `schemas/5-0/`).
        2. Die Applikation sucht im Root-Element der XML nach `xsi:noNamespaceSchemaLocation`, `xsi:schemaLocation`, DOCTYPE-Angaben oder Namespaces, um den S1000D Issue automatisch zu bestimmen und das passende Schema anzuwenden.
        ''')
