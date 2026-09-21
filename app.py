"""
Aplicación Web: Notación Musical & Transpositor de Partituras en PDF
Desarrollada con Streamlit y PyMuPDF.
Permite subir partituras, transponer el cifrado de las notas según cualquier
tonalidad (con soporte estricto de alteraciones # y b), preservando intacta
la gráfica original del pentagrama y descargando el PDF final con máxima nitidez.
"""

import io
import os
import re
from pathlib import Path
import streamlit as st
from PIL import Image

from core.music_engine import (
    KEY_ACCIDENTALS, KEY_SCALES, CHROMATIC_KEYS, ENHARMONIC_MAP,
    shift_key_semitones, calculate_semitone_interval
)
from core.pdf_processor import (
    process_score_pdf, render_pdf_page_to_image, get_pdf_page_count,
    detect_pdf_key_signature
)

# Configuración de página
st.set_page_config(
    page_title="ScoreLab — Notación & Transpositor de Partituras",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS modernos y elegantes
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.3);
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.03em;
        color: #ffffff;
    }
    .main-header p {
        font-size: 1.05rem;
        margin-top: 0.5rem;
        margin-bottom: 0;
        color: #c7d2fe;
        max-width: 850px;
    }

    .badge {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.18);
        color: #e0e7ff;
        margin-bottom: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }

    .stat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .stat-card .val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #312e81;
    }
    .stat-card .lbl {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .notice-box {
        background-color: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 1.5rem;
        color: #166534;
        font-size: 0.95rem;
    }

    .sidebar-section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# Rutas de recursos y repertorio
BASE_DIR = Path(__file__).parent
EXAMPLE_PDF = BASE_DIR / "assets" / "pdf_ejemplo.pdf"
REPERTOIRE_DIR = BASE_DIR / "partituras"


@st.cache_data
def get_repertoire_files() -> list[Path]:
    """
    Escanea automáticamente la carpeta partituras/ y devuelve la lista
    de archivos PDF disponibles ordenados numéricamente.
    """
    if not REPERTOIRE_DIR.exists() or not REPERTOIRE_DIR.is_dir():
        return []
    
    def sort_key(p: Path):
        m = re.search(r"(\d+)", p.stem)
        num = int(m.group(1)) if m else 999999
        return (num, p.stem.lower())
        
    return sorted([p for p in REPERTOIRE_DIR.glob("*.pdf") if p.is_file()], key=sort_key)


def format_score_title(path: Path) -> str:
    """
    Genera un título limpio, formateado y profesional para el selector.
    Ejemplo: himno_001_santo_santo_santo.pdf -> 'Himno 001 — Santo Santo Santo'
    """
    stem = path.stem
    m = re.match(r"^himno_0*(\d+)_(.+)$", stem, re.IGNORECASE)
    if m:
        num = m.group(1).zfill(3)
        words = m.group(2).replace("_", " ").strip().title()
        return f"Himno {num} — {words}"
    return stem.replace("_", " ").title()


# Escaneo temprano de repertorio e inicialización de partitura activa
repertoire_files = get_repertoire_files()
total_repertoire = len(repertoire_files)

if "active_pdf" not in st.session_state:
    if repertoire_files:
        first_file = repertoire_files[0]
        with open(first_file, "rb") as f:
            initial_bytes = f.read()
        st.session_state["active_pdf"] = initial_bytes
        st.session_state["active_name"] = first_file.name
        st.session_state["detected_orig_key"] = detect_pdf_key_signature(initial_bytes)
    elif EXAMPLE_PDF.exists():
        with open(EXAMPLE_PDF, "rb") as f:
            initial_bytes = f.read()
        st.session_state["active_pdf"] = initial_bytes
        st.session_state["active_name"] = "pdf ejemplo.pdf"
        st.session_state["detected_orig_key"] = detect_pdf_key_signature(initial_bytes)

detected_key = st.session_state.get("detected_orig_key", "Mi Mayor")

# Header principal
st.markdown("""
<div class="main-header">
    <div class="badge">🎵 Versión Full Stack Pro · PyMuPDF Engine</div>
    <h1>ScoreLab — Notación & Transposición de Partituras</h1>
    <p>Superpone el cifrado musical (Do, Re, Mi...) directamente sobre las figuras del pentagrama con transposición armónica y detección automática de armadura, manteniendo intacta la gráfica original del PDF.</p>
</div>
""", unsafe_allow_html=True)

# ----------------- BARRA LATERAL (CONFIGURACIÓN) -----------------
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.markdown("### 🎼 Tonalidad Destino & Transposición")
    
    # Inicialización de estado para la tonalidad destino
    if "dest_key" not in st.session_state:
        st.session_state["dest_key"] = "Fa Mayor"
    if "ui_dest_key" not in st.session_state:
        st.session_state["ui_dest_key"] = st.session_state["dest_key"]

    def on_shift_key(semitones: int):
        new_key = shift_key_semitones(st.session_state.get("dest_key", "Fa Mayor"), semitones)
        st.session_state["dest_key"] = new_key
        st.session_state["ui_dest_key"] = new_key

    def on_select_key():
        st.session_state["dest_key"] = st.session_state["ui_dest_key"]

    # Fila de control: Botón (-) + Desplegable + Botón (+)
    col_k1, col_k2, col_k3 = st.columns([1, 3.8, 1])
    with col_k1:
        st.button("➖", on_click=on_shift_key, args=(-1,), help="Bajar 1 medio tono (semitono hacia abajo)", use_container_width=True)
    with col_k3:
        st.button("➕", on_click=on_shift_key, args=(1,), help="Subir 1 medio tono (semitono hacia arriba)", use_container_width=True)
    with col_k2:
        curr_key = st.session_state["dest_key"]
        if curr_key not in CHROMATIC_KEYS:
            curr_key = ENHARMONIC_MAP.get(curr_key, "Fa Mayor")
            st.session_state["dest_key"] = curr_key
        idx = CHROMATIC_KEYS.index(curr_key) if curr_key in CHROMATIC_KEYS else 5
        selected_key = st.selectbox(
            "Tonalidad Destino:",
            options=CHROMATIC_KEYS,
            index=idx,
            key="ui_dest_key",
            on_change=on_select_key,
            label_visibility="collapsed",
            help="Selecciona la tonalidad o usa los botones ➖ y ➕ para transponer por medios tonos."
        )

    # Indicador dinámico de intervalo de transposición
    interval = calculate_semitone_interval(detected_key, st.session_state["dest_key"])
    if interval > 0:
        interval_label = f"+{interval} st (♯ más agudo)"
    elif interval < 0:
        interval_label = f"{interval} st (♭ más grave)"
    else:
        interval_label = "Misma tonalidad"
        
    st.caption(f"🎹 **Transposición:** {detected_key} ➔ **{st.session_state['dest_key']}** ({interval_label})")
    
    # Muestra información de la armadura seleccionada
    acc_info = KEY_ACCIDENTALS.get(st.session_state["dest_key"], {})
    if acc_info:
        acc_text = ", ".join([f"{k} → **{v}**" for k, v in acc_info.items()])
        st.info(f"✨ **Armadura de {st.session_state['dest_key']}:** {acc_text}")
    else:
        st.info(f"✨ **{st.session_state['dest_key']}:** Escala natural (sin sostenidos ni bemoles).")

    st.markdown("---")
    st.markdown("### 🎛️ Modo de Transposición")
    
    mode_option = st.radio(
        "Método de aplicación:",
        options=[
            "Transposición Armónica Completa (Recomendado)",
            "Armadura Estricta",
            "Solo Notas Naturales (Sin alteraciones)"
        ],
        index=0,  # Transposición Armónica Completa por defecto
        help=(
            "- Transposición Armónica: Transporta la melodía desde la tonalidad de origen detectada a la tonalidad destino.\n"
            "- Armadura Estricta: Las notas del pentagrama adoptan las alteraciones de la tonalidad elegida.\n"
            "- Solo Notas Naturales: Cifrado sin alteraciones (Do, Re, Mi, Fa, Sol, La, Si)."
        )
    )
    
    mode_map = {
        "Transposición Armónica Completa (Recomendado)": "full_transposition",
        "Armadura Estricta": "direct_armadura",
        "Solo Notas Naturales (Sin alteraciones)": "natural"
    }
    mode_code = mode_map[mode_option]
    
    key_orig = detected_key
    if mode_code == "full_transposition":
        st.success(f"🔍 **Tonalidad Original:** {detected_key} *(detectada automáticamente)*")
        with st.expander("✏️ Ajustar Tonalidad de Origen (Opcional)", expanded=False):
            key_orig = st.selectbox(
                "Tonalidad Original de la Partitura:",
                options=CHROMATIC_KEYS,
                index=CHROMATIC_KEYS.index(detected_key) if detected_key in CHROMATIC_KEYS else 0,
                help="Tonalidad base de la partitura. Se autocompleta con la detectada del PDF."
            )

    st.markdown("---")
    st.markdown("### 🔤 Notación y Tipografía")
    
    notation_choice = st.radio(
        "Sistema de Cifrado:",
        options=["Español (Do, Re, Mi, Fa, Sol, La, Si)", "Americano (C, D, E, F, G, A, B)"],
        index=0
    )
    notation_code = "es" if "Español" in notation_choice else "en"
    
    st.markdown("---")
    st.markdown("### 📱 Accesibilidad Visual (Tablets & Atril)")
    
    size_preset = st.radio(
        "Tamaño de Letra del Cifrado:",
        options=["Normal", "Grande", "Muy Grande"],
        index=2,  # Muy Grande por defecto
        help="Aumenta el tamaño y grosor de las letras (Do, Fa, Sol...) para facilitar la lectura a distancia en tablets o atriles."
    )
    
    size_scale_map = {
        "Normal": 1.0,
        "Grande": 1.35,
        "Muy Grande": 1.65
    }
    
    with st.expander("🎚️ Ajuste Fino de Escala (Opcional)", expanded=False):
        custom_slider = st.slider(
            "Escala manual personalizada:",
            min_value=0.8,
            max_value=4.0,
            value=float(size_scale_map[size_preset]),
            step=0.05,
            help="Permite ajustar al milímetro el tamaño de la letra y el óvalo (hasta 4.0x para máxima visibilidad en atril)."
        )
        font_scale = custom_slider
    
    if "custom_slider" not in locals():
        font_scale = size_scale_map[size_preset]
    
    white_circles_toggle = st.toggle(
        "⚪ Círculos Blancos con Letras Negras",
        value=False,
        help="Pone todos los círculos en blanco con borde y letras negras para mayor visualización de lejos en atril o tablet. Al desactivarlo, vuelve al diseño original."
    )
    if white_circles_toggle:
        st.info("💡 **Modo Alto Contraste:** Círculos en blanco con letras negras nítidas para máxima legibilidad.")
    
    st.markdown("---")
    st.markdown("### 🎸 Acordes (Cifrado Americano)")
    
    add_chords = st.toggle(
        "🎸 Añadir Acordes sobre los Pentagramas",
        value=False,
        help="Superpone los acordes en cifrado americano (E, B7, A...) sobre cada compás. Los acordes se transponen automáticamente al cambiar la tonalidad."
    )
    
    custom_chords = None
    if add_chords:
        st.info(f"✨ Acordes activos en **cifrado americano**. Se transportarán a **{selected_key}**.")
        with st.expander("✏️ Personalizar Secuencia de Acordes (Opcional)", expanded=False):
            chords_input = st.text_area(
                "Acordes base en tonalidad original (separados por espacio o coma):",
                value="E B7 A E E A F#m B7 E A E B7 E C#m A E",
                help="Ingresa los acordes correspondientes a la tonalidad base de la partitura."
            )
            custom_chords = [c.strip() for c in re.split(r"[\s,|]+", chords_input) if c.strip()]
    
    st.markdown("---")
    st.caption("🛡️ **Restricción estricta respetada:** El cambio aplica única y exclusivamente al texto del cifrado; la gráfica original de pentagramas y notas no se mueve ni se deforma.")

# ----------------- SELECCIÓN Y CARGA DE PARTITURA -----------------
repertoire_files = get_repertoire_files()
total_repertoire = len(repertoire_files)

st.markdown("### 📂 Selección de Partitura")

# Modos de obtención de la partitura
source_mode = st.radio(
    "Selecciona el origen de la partitura:",
    options=[
        f"📚 Repertorio Local ({total_repertoire} Partituras)",
        "📤 Subir Archivo PDF Personalizado",
        "📄 Partitura de Muestra"
    ],
    horizontal=True,
    help="Elige una partitura del repertorio masivo integrado en la carpeta 'partituras/', sube un archivo propio o carga el ejemplo rápido."
)

pdf_bytes = None
file_source_name = ""

if "📚 Repertorio Local" in source_mode:
    if total_repertoire == 0:
        st.warning("⚠️ No se encontraron partituras en la carpeta `partituras/`. Asegúrate de colocar los archivos PDF allí.")
    else:
        col_search, col_stats = st.columns([3, 1])
        
        with col_search:
            # Buscador interactivo por texto / número
            search_query = st.text_input(
                "🔍 Buscar en el repertorio por título o número de himno:",
                placeholder="Ejemplo: 001, Santo, Paz, Gracia, Navidad, 150...",
                help="Escribe cualquier fragmento del número o nombre para filtrar instantáneamente el catálogo."
            )
            
            if search_query.strip():
                query_clean = search_query.strip().lower()
                filtered_files = [
                    f for f in repertoire_files
                    if query_clean in format_score_title(f).lower() or query_clean in f.stem.lower()
                ]
                if not filtered_files:
                    st.warning(f"No se encontraron partituras con '{search_query}'. Mostrando todo el catálogo.")
                    filtered_files = repertoire_files
            else:
                filtered_files = repertoire_files
            
            selected_score = st.selectbox(
                f"Selecciona una partitura ({len(filtered_files)} disponibles):",
                options=filtered_files,
                format_func=format_score_title,
                help="Usa el desplegable o escribe en él para seleccionar la partitura deseada."
            )
        
        with col_stats:
            st.write("")
            st.write("")
            if selected_score:
                file_kb = selected_score.stat().st_size / 1024
                st.markdown(f"""
                <div class="stat-card" style="padding: 0.8rem;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #312e81;">{total_repertoire}</div>
                    <div class="lbl">En Catálogo</div>
                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.3rem;">{file_kb:.1f} KB</div>
                </div>
                """, unsafe_allow_html=True)

        if selected_score and selected_score.exists():
            with open(selected_score, "rb") as f:
                pdf_bytes = f.read()
            file_source_name = selected_score.name
            if st.session_state.get("active_name") != file_source_name:
                st.session_state["detected_orig_key"] = detect_pdf_key_signature(pdf_bytes)
                st.session_state["active_pdf"] = pdf_bytes
                st.session_state["active_name"] = file_source_name
                st.rerun()
            st.session_state["active_pdf"] = pdf_bytes
            st.session_state["active_name"] = file_source_name

elif "📤 Subir Archivo PDF" in source_mode:
    uploaded_file = st.file_uploader(
        "Sube una partitura en formato PDF:",
        type=["pdf"],
        help="Arrastra o selecciona un archivo PDF de partitura musical (admite partituras de una o múltiples páginas)."
    )
    if uploaded_file is not None:
        pdf_bytes = uploaded_file.read()
        file_source_name = uploaded_file.name
        if st.session_state.get("active_name") != file_source_name:
            st.session_state["detected_orig_key"] = detect_pdf_key_signature(pdf_bytes)
            st.session_state["active_pdf"] = pdf_bytes
            st.session_state["active_name"] = file_source_name
            st.rerun()
        st.session_state["active_pdf"] = pdf_bytes
        st.session_state["active_name"] = file_source_name
    elif "active_pdf" in st.session_state and not st.session_state.get("active_name", "").startswith("himno_"):
        pdf_bytes = st.session_state["active_pdf"]
        file_source_name = st.session_state.get("active_name", "partitura.pdf")

elif "📄 Partitura de Muestra" in source_mode:
    if EXAMPLE_PDF.exists():
        with open(EXAMPLE_PDF, "rb") as f:
            pdf_bytes = f.read()
        file_source_name = "pdf ejemplo.pdf"
        if st.session_state.get("active_name") != file_source_name:
            st.session_state["detected_orig_key"] = detect_pdf_key_signature(pdf_bytes)
            st.session_state["active_pdf"] = pdf_bytes
            st.session_state["active_name"] = file_source_name
            st.rerun()
        st.session_state["active_pdf"] = pdf_bytes
        st.session_state["active_name"] = file_source_name
    else:
        st.error("No se encontró el archivo de partitura de muestra.")

if pdf_bytes is not None:
    # Título visualmente amigable para el aviso
    clean_display = format_score_title(Path(file_source_name)) if file_source_name.startswith("himno_") else file_source_name
    contrast_notice = " · ⚪ <strong>Modo:</strong> Círculos blancos con letras negras" if white_circles_toggle else ""
    st.markdown(f"""
    <div class="notice-box">
        ✅ <strong>Partitura activa:</strong> <code>{clean_display}</code> ({file_source_name}) — Tonalidad original: <strong>{key_orig}</strong> ➔ Destino: <strong>{selected_key}</strong> ({interval_label}){contrast_notice}.
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Procesando partitura y aplicando cifrado vectorial..."):
        try:
            processed_pdf_bytes, stats = process_score_pdf(
                pdf_bytes=pdf_bytes,
                key_dest=selected_key,
                key_orig=key_orig,
                mode=mode_code,
                notation=notation_code,
                font_scale=font_scale,
                add_chords=add_chords,
                custom_chords=custom_chords,
                all_white_circles=white_circles_toggle
            )
        except Exception as e:
            st.error(f"Error al procesar el PDF: {str(e)}")
            st.stop()

    total_pages = stats.get("total_pages", 1)

    # Métricas del procesamiento
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="val">{stats['total_notes']}</div>
            <div class="lbl">Figuras Rotuladas</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="val">{stats['total_staves']}</div>
            <div class="lbl">Pentagramas ({total_pages} pág{'s' if total_pages>1 else ''})</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        interval_badge = f" ({interval_label})" if interval != 0 else ""
        st.markdown(f"""
        <div class="stat-card">
            <div class="val" style="font-size: 1.25rem;">{key_orig} ➔ {selected_key}</div>
            <div class="lbl">Transposición{interval_badge}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        tag_mode = " · ⚪ Blanco/Negro" if white_circles_toggle else ""
        st.markdown(f"""
        <div class="stat-card">
            <div class="val">{size_preset}</div>
            <div class="lbl">Tamaño Cifrado ({font_scale:.2f}x{tag_mode})</div>
        </div>
        """, unsafe_allow_html=True)

    # Control de navegación para PDFs de múltiples páginas
    current_page_idx = 0
    show_all_pages = False
    
    if total_pages > 1:
        st.markdown("---")
        st.markdown(f"#### 📑 Navegación de Páginas (Documento de {total_pages} páginas)")
        p_col1, p_col2 = st.columns([3, 2])
        with p_col1:
            page_labels = [f"Página {i+1}" for i in range(total_pages)]
            selected_page_str = st.radio(
                "Seleccionar página activa para previsualizar:",
                options=page_labels,
                horizontal=True,
                index=0
            )
            current_page_idx = page_labels.index(selected_page_str)
        with p_col2:
            st.write("")
            show_all_pages = st.checkbox("📜 Ver todas las páginas continuas", value=False)

    st.write("")
    
    # ----------------- DESCARGA -----------------
    # Preparar buffer con seek(0) para garantizar que el navegador reconozca el nombre y la extensión .pdf
    result_stream = io.BytesIO(processed_pdf_bytes)
    result_stream.seek(0)
    
    down_col1, down_col2 = st.columns([2, 1])
    with down_col1:
        st.download_button(
            label=f"📥 Descargar PDF Final Completo ({total_pages} pág{'s' if total_pages>1 else ''})",
            data=result_stream,
            file_name="partitura_cifrado_americano.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with down_col2:
        # Generar imagen de alta resolución de la página activa
        preview_img = render_pdf_page_to_image(processed_pdf_bytes, page_idx=current_page_idx, dpi=250)
        img_buffer = io.BytesIO()
        preview_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        st.download_button(
            label=f"🖼️ Descargar Página {current_page_idx + 1} (PNG 250 DPI)",
            data=img_buffer,
            file_name=f"partitura_cifrado_americano_pag_{current_page_idx + 1}.png",
            mime="image/png",
            use_container_width=True
        )

    st.write("")
    
    # ----------------- VISUALIZADOR -----------------
    st.markdown("### 👁️ Vista Previa Interactiva de Alta Definición")
    
    tab_result, tab_compare = st.tabs([
        "📄 Partitura Procesada (Resultado)",
        "🔄 Comparación Original vs Resultado"
    ])
    
    with tab_result:
        if show_all_pages and total_pages > 1:
            for p_num in range(total_pages):
                st.markdown(f"##### 📄 Página {p_num + 1} de {total_pages}")
                page_img = render_pdf_page_to_image(processed_pdf_bytes, page_idx=p_num, dpi=220)
                st.image(page_img, use_container_width=True)
                if p_num < total_pages - 1:
                    st.markdown("---")
        else:
            st.image(
                preview_img,
                caption=f"Partitura procesada con cifrado en {selected_key} — Página {current_page_idx + 1} de {total_pages}",
                use_container_width=True
            )
        
    with tab_compare:
        c1, c2 = st.columns(2)
        with c1:
            orig_img = render_pdf_page_to_image(pdf_bytes, page_idx=current_page_idx, dpi=200)
            st.markdown(f"##### 📌 Partitura Original (Página {current_page_idx + 1})")
            st.image(orig_img, use_container_width=True)
        with c2:
            st.markdown(f"##### ✨ Partitura Procesada ({selected_key} — Pág. {current_page_idx + 1})")
            st.image(preview_img, use_container_width=True)

else:
    # Estado inicial: invitación a subir archivo o usar el ejemplo
    st.markdown("""
    <div style="text-align: center; padding: 3.5rem 2rem; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 16px; margin-top: 1rem;">
        <h3 style="color: #334155; margin-bottom: 0.5rem;">Sube una partitura o usa el ejemplo incluido</h3>
        <p style="color: #64748b; max-width: 600px; margin: 0 auto 1.5rem auto;">
            Sube un archivo PDF de cualquier partitura musical o haz clic en <strong>'📄 Cargar Partitura de Ejemplo'</strong> arriba para probar de inmediato con el himno <em>'Santo, Santo, Santo'</em>.
        </p>
    </div>
    """, unsafe_allow_html=True)
