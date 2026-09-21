"""
Módulo de Procesamiento y Modificación de Partituras en PDF con PyMuPDF.
Detecta pentagramas, figuras musicales, calcula la altura tonal y superpone
los óvalos con el texto del cifrado directamente en la capa vectorial del PDF.
"""

import io
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import pymupdf

from .music_engine import BASS_STEPS, TREBLE_STEPS, get_transposed_label, transpose_chord


def detect_staves_on_page(page: pymupdf.Page) -> List[List[float]]:
    """
    Detecta y agrupa las líneas de los pentagramas (5 líneas horizontales por pentagrama).
    Retorna una lista de pentagramas, donde cada pentagrama es una lista de 5 posiciones Y ordenadas.
    """
    staff_lines = []
    
    # 1. Buscar en dibujos vectoriales
    for d in page.get_drawings():
        for it in d.get("items", []):
            if it[0] == "l":  # línea recta
                p1, p2 = it[1], it[2]
                # Una línea de pentagrama es prácticamente horizontal y tiene longitud significativa
                if abs(p1.y - p2.y) < 0.2 and abs(p1.x - p2.x) > 150:
                    staff_lines.append(p1.y)
                    
    # Si no se detectaron suficientes por items, buscar rectángulos muy delgados
    if len(staff_lines) < 5:
        for d in page.get_drawings():
            r = d["rect"]
            if r.height <= 1.2 and r.width > 150:
                staff_lines.append((r.y0 + r.y1) / 2.0)
                
    staff_lines = sorted(list(set([round(y, 2) for y in staff_lines])))
    
    staves = []
    curr_group = []
    for y in staff_lines:
        if not curr_group or abs(y - curr_group[-1]) < 9.0:
            curr_group.append(y)
        else:
            if len(curr_group) == 5:
                staves.append(curr_group)
            curr_group = [y]
    if len(curr_group) == 5:
        staves.append(curr_group)
        
    return staves


def detect_key_signature(page: pymupdf.Page, staves: List[List[float]]) -> str:
    """
    Detecta la tonalidad original a partir de las alteraciones (armadura)
    al inicio del primer pentagrama.
    """
    if not staves:
        return "Do Mayor"
        
    first_staff_top = staves[0][0] - 10
    first_staff_bottom = staves[0][4] + 10
    
    text_dict = page.get_text("rawdict")
    sharps_count = 0
    flats_count = 0
    
    for b in text_dict["blocks"]:
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                for c in s.get("chars", []):
                    bbox = c["bbox"]
                    cy = (bbox[1] + bbox[3]) / 2.0
                    cx = (bbox[0] + bbox[2]) / 2.0
                    # Armadura al inicio del pentagrama (x entre 25 y 70 aprox)
                    if first_staff_top <= cy <= first_staff_bottom and 25 <= cx <= 70:
                        code = ord(c["c"])
                        if code in (35, 0x23, 0xE262):  # '#'
                            sharps_count += 1
                        elif code in (98, ord('b'), 0xE260):  # 'b'
                            flats_count += 1
                            
    # Círculo de quintas para tonalidades mayores
    if sharps_count == 1:
        return "Sol Mayor"
    elif sharps_count == 2:
        return "Re Mayor"
    elif sharps_count == 3:
        return "La Mayor"
    elif sharps_count == 4:
        return "Mi Mayor"
    elif sharps_count == 5:
        return "Si Mayor"
    elif sharps_count == 6:
        return "Fa# Mayor"
    elif sharps_count >= 7:
        return "Do# Mayor"
    elif flats_count == 1:
        return "Fa Mayor"
    elif flats_count == 2:
        return "Sib Mayor"
    elif flats_count == 3:
        return "Mib Mayor"
    elif flats_count == 4:
        return "Lab Mayor"
    elif flats_count == 5:
        return "Reb Mayor"
    elif flats_count >= 6:
        return "Solb Mayor"
        
    return "Do Mayor"


def detect_pdf_key_signature(pdf_bytes: bytes) -> str:
    """
    Detecta de forma automática la tonalidad original de cualquier partitura en PDF.
    """
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 0:
            staves = detect_staves_on_page(doc[0])
            return detect_key_signature(doc[0], staves)
    except Exception:
        pass
    return "Do Mayor"


def extract_notes_from_page(page: pymupdf.Page, staves: List[List[float]]) -> List[Dict[str, Any]]:
    """
    Extrae las posiciones y características de las cabezas de nota en la página.
    Soporta múltiples fuentes musicales (Petrucci, Maestro, SMuFL, etc.)
    y fallback a curvas vectoriales.
    """
    notes = []
    text_dict = page.get_text("rawdict")
    
    # 1. Búsqueda por fuentes musicales conocidas
    for b in text_dict["blocks"]:
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                font_name = s.get("font", "").lower()
                is_music_font = any(f in font_name for f in ["petrucci", "maestro", "bravura", "emmentaler", "opus", "music", "feta", "leland"])
                
                for c in s.get("chars", []):
                    code = ord(c["c"])
                    bbox = c["bbox"]
                    
                    # Identificar cabeza de nota según codificación
                    # Petrucci: 339 (negra/corchea), 729 (blanca), 119 (redonda 'w')
                    # SMuFL: 0xE0A2 (redonda), 0xE0A3 (blanca), 0xE0A4 (negra)
                    if code in (339, 0x153):
                        notes.append({
                            "code": code,
                            "bbox": bbox,
                            "origin": c.get("origin"),
                            "is_filled": True,
                            "font_size": s.get("size", 24.0)
                        })
                    elif code in (729, 0x2D9):
                        notes.append({
                            "code": code,
                            "bbox": bbox,
                            "origin": c.get("origin"),
                            "is_filled": False,
                            "font_size": s.get("size", 24.0)
                        })
                    elif code in (119, ord('w')) and is_music_font:
                        notes.append({
                            "code": code,
                            "bbox": bbox,
                            "origin": c.get("origin"),
                            "is_filled": False,
                            "font_size": s.get("size", 24.0)
                        })
                    elif code == 0xE0A4:  # SMuFL negra
                        notes.append({"code": code, "bbox": bbox, "origin": c.get("origin"), "is_filled": True})
                    elif code in (0xE0A2, 0xE0A3):  # SMuFL redonda/blanca
                        notes.append({"code": code, "bbox": bbox, "origin": c.get("origin"), "is_filled": False})

    # Si no se encontraron por fuente musical, intentar detección por dibujos vectoriales
    if len(notes) == 0 and staves:
        all_drawings = page.get_drawings()
        for d in all_drawings:
            r = d["rect"]
            w, h = r.width, r.height
            # Proporción típica de una cabeza de figura musical (óvalo inclinado pequeño)
            if 3.2 <= w <= 8.5 and 2.5 <= h <= 7.0:
                cy = (r.y0 + r.y1) / 2.0
                # Verificar si está dentro del rango vertical de algún pentagrama (+/- 25pt)
                in_staff_range = any(s[0] - 25 <= cy <= s[4] + 25 for s in staves)
                if in_staff_range:
                    is_filled = (d.get("fill") is not None)
                    notes.append({
                        "code": 0,
                        "bbox": (r.x0, r.y0, r.x1, r.y1),
                        "origin": (r.x0, cy),
                        "is_filled": is_filled
                    })

    return notes


# Secuencia de acordes por defecto en la tonalidad original (Mi Mayor / E) para el himno
DEFAULT_CHORDS = [
    "E", "B7", "A", "E",
    "E", "A", "F#m", "B7",
    "E", "A", "E", "B7",
    "E", "C#m", "A", "E"
]


def draw_chords_on_page(
    page: pymupdf.Page,
    staves: List[List[float]],
    chords_list: List[str],
    key_orig: str = "Mi Mayor",
    key_dest: str = "Fa Mayor",
    page_idx: int = 0
):
    """
    Dibuja los acordes en cifrado americano en la parte superior de cada sistema/pentagrama.
    Los acordes se transponen automáticamente a la tonalidad destino.
    """
    if not staves or not chords_list:
        return
        
    treble_staves = [s for i, s in enumerate(staves) if i % 2 == 0]
    if not treble_staves:
        treble_staves = staves
        
    num_systems = len(treble_staves)
    for sys_idx, s in enumerate(treble_staves):
        global_sys_idx = page_idx * num_systems + sys_idx
        start_ci = (global_sys_idx * 4) % len(chords_list)
        sys_chords = chords_list[start_ci : start_ci + 4]
        if len(sys_chords) < 4:
            sys_chords += chords_list[: 4 - len(sys_chords)]
            
        y_chord = s[0] - 6.0
        x_positions = [75.0, 165.0, 240.0, 325.0]
        
        for c_idx, raw_ch in enumerate(sys_chords):
            if c_idx < len(x_positions) and raw_ch.strip():
                trans_ch = transpose_chord(raw_ch.strip(), key_orig=key_orig, key_dest=key_dest)
                cx = x_positions[c_idx]
                fsize = 7.0
                tw = pymupdf.get_text_length(trans_ch, fontname="hebo", fontsize=fsize)
                
                # Rectángulo blanco con borde sutil para destacar el acorde
                pill_rect = pymupdf.Rect(cx - 3.0, y_chord - fsize + 1.2, cx + tw + 3.0, y_chord + 2.0)
                shape = page.new_shape()
                shape.draw_rect(pill_rect)
                shape.finish(fill=(1.0, 1.0, 1.0), color=(0.6, 0.6, 0.75), width=0.35)
                shape.commit()
                
                page.insert_text(
                    pymupdf.Point(cx, y_chord),
                    trans_ch,
                    fontname="hebo",
                    fontsize=fsize,
                    color=(0.1, 0.15, 0.5)  # Azul marino elegante
                )


def process_score_pdf(
    pdf_bytes: bytes,
    key_dest: str = "Fa Mayor",
    key_orig: str = "Mi Mayor",
    mode: str = "direct_armadura",
    notation: str = "es",
    font_scale: float = 1.0,
    add_chords: bool = False,
    custom_chords: Optional[List[str]] = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Procesa el archivo PDF de la partitura:
    - Conserva intacta la partitura original (vectorial).
    - Aplica la transposición exclusivamente a los textos del cifrado.
    - Dibuja óvalos con el cifrado correspondiente exactamente sobre cada cabeza de figura.
    - Soporta alteraciones de armadura (# y b) según la tonalidad elegida.
    - Opcionalmente añade acordes en cifrado americano transportados a la tonalidad destino.
    
    Retorna los bytes del PDF modificado y un diccionario con estadísticas.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    total_notes = 0
    total_staves = 0
    detected_key = "Mi Mayor"
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        staves = detect_staves_on_page(page)
        total_staves += len(staves)
        
        if page_idx == 0:
            detected_key = detect_key_signature(page, staves)
            
        if not staves:
            continue
            
        # Dibujar acordes si la opción está activada
        if add_chords:
            chords_to_use = custom_chords if (custom_chords and len(custom_chords) > 0) else DEFAULT_CHORDS
            draw_chords_on_page(
                page=page,
                staves=staves,
                chords_list=chords_to_use,
                key_orig=key_orig,
                key_dest=key_dest,
                page_idx=page_idx
            )
            
        notes = extract_notes_from_page(page, staves)
        total_notes += len(notes)
        
        # Orden de dibujado (Voz principal siempre en la capa superior):
        # En coordenadas de PDF, Y aumenta hacia abajo. Las notas más bajas en el pentagrama
        # (voces de acompañamiento / inferiores) tienen mayor coordenada Y.
        # Al ordenar de mayor a menor Y (descendente), las notas inferiores se dibujan primero
        # y las notas superiores (voz principal / soprano) se dibujan al final (encima),
        # asegurando que la melodía principal nunca quede tapada.
        notes.sort(key=lambda n: -(n["origin"][1] if n.get("origin") else (n["bbox"][1] + n["bbox"][3]) / 2.0))
        
        for n in notes:
            bx = n["bbox"]
            cx = (bx[0] + bx[2]) / 2.0
            ny = n["origin"][1] if n.get("origin") else (bx[1] + bx[3]) / 2.0
            
            # Asociar nota al pentagrama más cercano
            best_si = 0
            min_dist = 99999.0
            for si, s in enumerate(staves):
                d = min(abs(ny - s[0]), abs(ny - s[4]))
                if s[0] - 18 <= ny <= s[4] + 18:
                    best_si = si
                    break
                if d < min_dist:
                    min_dist = d
                    best_si = si
                    
            s = staves[best_si]
            step_sz = (s[4] - s[0]) / 8.0  # medio espacio entre líneas
            diff_steps = int(round((s[4] - ny) / step_sz))
            
            # Posición Y exacta en el centro de la línea o espacio
            exact_cy = s[4] - diff_steps * step_sz
            
            # Clave: Sol (pares 0, 2, 4...) o Fa (impares 1, 3, 5...)
            is_treble = (best_si % 2 == 0)
            base_note = TREBLE_STEPS[diff_steps % 7] if is_treble else BASS_STEPS[diff_steps % 7]
            
            # Obtener etiqueta según tonalidad y modo
            note_label = get_transposed_label(
                base_note=base_note,
                key_dest=key_dest,
                key_orig=key_orig,
                mode=mode,
                notation=notation
            )
            
            # 1. Selección dinámica de tipografía según la escala:
            # Para escalas estándar (<= 1.25x), 'hebo' (Helvetica-Bold) aporta el contraste necesario.
            # Al aumentar de tamaño (> 1.25x), usamos 'helv' (Helvetica regular) para reducir el grosor
            # excesivo del trazo y evitar que letras como 'a', 'e', '#' se empasten o cierren.
            font_name = "hebo" if font_scale <= 1.25 else "helv"
            
            # 2. Ajuste armónico del tamaño de fuente con suficiente holgura interna
            char_count = len(note_label)
            base_fsize = 3.15 * font_scale
            if char_count >= 4:
                fsize = base_fsize * 0.70
            elif char_count == 3:
                fsize = base_fsize * 0.78
            else:
                fsize = base_fsize * 0.90
                
            tw = pymupdf.get_text_length(note_label, fontname=font_name, fontsize=fsize)
            
            # 3. Dimensiones del óvalo con margen interno amplio para que el texto nunca quede pegado a los bordes
            min_w = 4.56 * (1.0 + (font_scale - 1.0) * 0.85)
            padding_x = 2.8 * (1.0 + (font_scale - 1.0) * 0.45)
            w = max(min_w, tw + padding_x)
            h = max(3.84 * (1.0 + (font_scale - 1.0) * 0.65), fsize * 1.35)
                
            oval_rect = pymupdf.Rect(cx - w / 2.0, exact_cy - h / 2.0, cx + w / 2.0, exact_cy + h / 2.0)
            
            # Dibujar óvalo de fondo
            shape = page.new_shape()
            shape.draw_oval(oval_rect)
            
            border_width = 0.4 if font_scale <= 1.2 else 0.55
            if n["is_filled"]:
                # Nota negra: Fondo negro, texto blanco
                # Borde blanco sutil para dar separación y nitidez cuando dos notas se superponen
                stroke_color = (1.0, 1.0, 1.0) if font_scale > 1.15 else (0.0, 0.0, 0.0)
                shape.finish(fill=(0.0, 0.0, 0.0), color=stroke_color, width=border_width)
                text_color = (1.0, 1.0, 1.0)
            else:
                # Nota blanca / redonda: Fondo blanco, borde negro, texto negro
                shape.finish(fill=(1.0, 1.0, 1.0), color=(0.0, 0.0, 0.0), width=border_width)
                text_color = (0.0, 0.0, 0.0)
            shape.commit()
            
            # Inserción de texto perfectamente centrado
            tx = cx - tw / 2.0
            ty = exact_cy + fsize * 0.35
            
            page.insert_text(
                pymupdf.Point(tx, ty),
                note_label,
                fontname=font_name,
                fontsize=fsize,
                color=text_color
            )
            
    out_buffer = io.BytesIO()
    doc.save(out_buffer, garbage=3, deflate=True)
    out_pdf_bytes = out_buffer.getvalue()
    
    stats = {
        "total_notes": total_notes,
        "total_staves": total_staves,
        "total_pages": len(doc),
        "detected_key": detected_key,
        "applied_key": key_dest,
        "mode": mode,
        "notation": notation
    }
    
    return out_pdf_bytes, stats


def render_pdf_page_to_image(pdf_bytes: bytes, page_idx: int = 0, dpi: int = 200) -> Image.Image:
    """Renderiza una página del PDF a una imagen PIL con alta nitidez."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    if page_idx >= len(doc):
        page_idx = max(0, len(doc) - 1)
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return img


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Retorna el número total de páginas del PDF."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return len(doc)
