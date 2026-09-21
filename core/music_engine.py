"""
Módulo de Teoría Musical, Tonalidades y Transposición.
Maneja escalas, armaduras, cifrado español (Do, Re, Mi...) y americano (C, D, E...).
"""

from typing import Dict, List, Optional, Tuple

# Notas diatónicas base
SPANISH_NOTES = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]
ENGLISH_NOTES = ["C", "D", "E", "F", "G", "A", "B"]

SPANISH_TO_ENGLISH = {
    "Do": "C", "Re": "D", "Mi": "E", "Fa": "F", "Sol": "G", "La": "A", "Si": "B"
}
ENGLISH_TO_SPANISH = {v: k for k, v in SPANISH_TO_ENGLISH.items()}

# Alteraciones según la armadura de cada tonalidad mayor
KEY_ACCIDENTALS: Dict[str, Dict[str, str]] = {
    "Do Mayor": {},
    "Sol Mayor": {"Fa": "Fa#"},
    "Re Mayor": {"Fa": "Fa#", "Do": "Do#"},
    "La Mayor": {"Fa": "Fa#", "Do": "Do#", "Sol": "Sol#"},
    "Mi Mayor": {"Fa": "Fa#", "Do": "Do#", "Sol": "Sol#", "Re": "Re#"},
    "Si Mayor": {"Fa": "Fa#", "Do": "Do#", "Sol": "Sol#", "Re": "Re#", "La": "La#"},
    "Fa# Mayor": {"Fa": "Fa#", "Do": "Do#", "Sol": "Sol#", "Re": "Re#", "La": "La#", "Mi": "Mi#"},
    "Do# Mayor": {"Fa": "Fa#", "Do": "Do#", "Sol": "Sol#", "Re": "Re#", "La": "La#", "Mi": "Mi#", "Si": "Si#"},
    "Fa Mayor": {"Si": "Sib"},
    "Sib Mayor": {"Si": "Sib", "Mi": "Mib"},
    "Mib Mayor": {"Si": "Sib", "Mi": "Mib", "La": "Lab"},
    "Lab Mayor": {"Si": "Sib", "Mi": "Mib", "La": "Lab", "Re": "Reb"},
    "Reb Mayor": {"Si": "Sib", "Mi": "Mib", "La": "Lab", "Re": "Reb", "Sol": "Solb"},
    "Solb Mayor": {"Si": "Sib", "Mi": "Mib", "La": "Lab", "Re": "Reb", "Sol": "Solb", "Do": "Dob"},
}

# Escalas mayores completas (grados 1 al 7)
KEY_SCALES: Dict[str, List[str]] = {
    "Do Mayor":  ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"],
    "Sol Mayor": ["Sol", "La", "Si", "Do", "Re", "Mi", "Fa#"],
    "Re Mayor":  ["Re", "Mi", "Fa#", "Sol", "La", "Si", "Do#"],
    "La Mayor":  ["La", "Si", "Do#", "Re", "Mi", "Fa#", "Sol#"],
    "Mi Mayor":  ["Mi", "Fa#", "Sol#", "La", "Si", "Do#", "Re#"],
    "Si Mayor":  ["Si", "Do#", "Re#", "Mi", "Fa#", "Sol#", "La#"],
    "Fa# Mayor": ["Fa#", "Sol#", "La#", "Si", "Do#", "Re#", "Mi#"],
    "Do# Mayor": ["Do#", "Re#", "Mi#", "Fa#", "Sol#", "La#", "Si#"],
    "Fa Mayor":  ["Fa", "Sol", "La", "Sib", "Do", "Re", "Mi"],
    "Sib Mayor": ["Sib", "Do", "Re", "Mib", "Fa", "Sol", "La"],
    "Mib Mayor": ["Mib", "Fa", "Sol", "Lab", "Sib", "Do", "Re"],
    "Lab Mayor": ["Lab", "Sib", "Do", "Reb", "Mib", "Fa", "Sol"],
    "Reb Mayor": ["Reb", "Mib", "Fa", "Solb", "Lab", "Sib", "Do"],
    "Solb Mayor": ["Solb", "Lab", "Sib", "Dob", "Reb", "Mib", "Fa"],
}

# Tonalidades organizadas en orden cromático estricto (por medios tonos de 0 a 11)
CHROMATIC_KEYS: List[str] = [
    "Do Mayor",     # 0
    "Reb Mayor",    # 1
    "Re Mayor",     # 2
    "Mib Mayor",    # 3
    "Mi Mayor",     # 4
    "Fa Mayor",     # 5
    "Fa# Mayor",    # 6
    "Sol Mayor",    # 7
    "Lab Mayor",    # 8
    "La Mayor",     # 9
    "Sib Mayor",    # 10
    "Si Mayor"      # 11
]

ENHARMONIC_MAP: Dict[str, str] = {
    "Do# Mayor": "Reb Mayor",
    "Solb Mayor": "Fa# Mayor",
}


def shift_key_semitones(key_name: str, semitones: int) -> str:
    """
    Sube o baja una tonalidad por medios tonos (semitonos).
    semitones: +1 para subir medio tono, -1 para bajar medio tono.
    """
    canonical = ENHARMONIC_MAP.get(key_name, key_name)
    if canonical in CHROMATIC_KEYS:
        idx = CHROMATIC_KEYS.index(canonical)
        new_idx = (idx + semitones) % len(CHROMATIC_KEYS)
        return CHROMATIC_KEYS[new_idx]
    return key_name


def calculate_semitone_interval(key_orig: str, key_dest: str) -> int:
    """
    Calcula la distancia en semitonos entre dos tonalidades (-6 a +6).
    Ejemplo: Mi Mayor a Fa Mayor -> +1 medio tono.
    """
    c_orig = ENHARMONIC_MAP.get(key_orig, key_orig)
    c_dest = ENHARMONIC_MAP.get(key_dest, key_dest)
    if c_orig in CHROMATIC_KEYS and c_dest in CHROMATIC_KEYS:
        diff = (CHROMATIC_KEYS.index(c_dest) - CHROMATIC_KEYS.index(c_orig)) % 12
        if diff > 6:
            diff -= 12
        return diff
    return 0


# Mapeo de grados en la escala de Mi Mayor (tonalidad original del ejemplo)
MI_MAYOR_DEGREES = {
    "Mi": 0, "Fa": 1, "Sol": 2, "La": 3, "Si": 4, "Do": 5, "Re": 6
}

# Mapeo de grados en Do Mayor
DO_MAYOR_DEGREES = {
    "Do": 0, "Re": 1, "Mi": 2, "Fa": 3, "Sol": 4, "La": 5, "Si": 6
}

# Pasos verticales en la clave de Sol (Treble):
# Línea 1 (inferior, paso 0) = Mi4
TREBLE_STEPS = ["Mi", "Fa", "Sol", "La", "Si", "Do", "Re"]

# Pasos verticales en la clave de Fa (Bass):
# Línea 1 (inferior, paso 0) = Sol2
BASS_STEPS = ["Sol", "La", "Si", "Do", "Re", "Mi", "Fa"]


def to_american_notation(note_str: str) -> str:
    """Convierte una nota española (ej. Sib, Fa#) a cifrado americano (Bb, F#)."""
    for sp, en in SPANISH_TO_ENGLISH.items():
        if note_str.startswith(sp):
            accidental = note_str[len(sp):]
            return f"{en}{accidental}"
    return note_str


def get_transposed_label(
    base_note: str,
    key_dest: str = "Fa Mayor",
    key_orig: str = "Mi Mayor",
    mode: str = "direct_armadura",
    notation: str = "es"
) -> str:
    """
    Calcula el texto de la nota según la tonalidad y el modo seleccionado.
    
    Modos:
    - direct_armadura: La nota leída del pentagrama (ej. Si) se altera con la armadura
      de la tonalidad elegida (ej. en Fa Mayor, Si -> Sib).
    - full_transposition: Mueve los grados musicales desde la tonalidad original
      a la tonalidad destino (ej. Mi Mayor -> Fa Mayor).
    - natural: Notas naturales puras sin alteraciones (ej. Do, Re, Mi... como en el PDF resultado original).
    """
    label = base_note
    
    if mode == "direct_armadura":
        acc_dict = KEY_ACCIDENTALS.get(key_dest, {})
        label = acc_dict.get(base_note, base_note)
        
    elif mode == "full_transposition":
        orig_scale = KEY_SCALES.get(key_orig, KEY_SCALES["Mi Mayor"])
        target_scale = KEY_SCALES.get(key_dest, KEY_SCALES["Do Mayor"])
        
        # Encontrar grado en la escala original
        deg = -1
        for i, s_note in enumerate(orig_scale):
            if s_note.startswith(base_note):
                deg = i
                break
        if deg == -1:
            # Por defecto según Mi Mayor
            deg = MI_MAYOR_DEGREES.get(base_note, 0)
            
        label = target_scale[deg % 7]
        
    elif mode == "natural":
        label = base_note

    if notation == "en":
        return to_american_notation(label)
    return label


# ------------------ ACORDES EN CIFRADO AMERICANO ------------------
import re

NOTE_TO_SEMITONE = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11
}

KEY_CHORD_SPELLINGS = {
    "Do Mayor":   ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "Sol Mayor":  ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "Re Mayor":   ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "La Mayor":   ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "Mi Mayor":   ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "Si Mayor":   ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "Fa# Mayor":  ["B#", "C#", "D", "D#", "E", "E#", "F#", "G", "G#", "A", "A#", "B"],
    "Fa Mayor":   ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "Sib Mayor":  ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "Mib Mayor":  ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "Lab Mayor":  ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "Reb Mayor":  ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "Solb Mayor": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
}

KEY_TONIC_SEMITONE = {
    "Do Mayor": 0,
    "Reb Mayor": 1,
    "Re Mayor": 2,
    "Mib Mayor": 3,
    "Mi Mayor": 4,
    "Fa Mayor": 5,
    "Fa# Mayor": 6,
    "Sol Mayor": 7,
    "Lab Mayor": 8,
    "La Mayor": 9,
    "Sib Mayor": 10,
    "Si Mayor": 11
}

def transpose_chord(chord_str: str, key_orig: str = "Mi Mayor", key_dest: str = "Fa Mayor") -> str:
    """
    Transpone un acorde en cifrado americano (ej. E, B7, F#m, E/G#)
    desde key_orig hacia key_dest, respetando sufijos y bajos invertidos.
    """
    if not chord_str or not chord_str.strip():
        return ""
        
    semitones = (KEY_TONIC_SEMITONE.get(key_dest, 0) - KEY_TONIC_SEMITONE.get(key_orig, 4)) % 12
    spelling = KEY_CHORD_SPELLINGS.get(key_dest, KEY_CHORD_SPELLINGS["Do Mayor"])
    
    parts = chord_str.strip().split('/')
    main_chord = parts[0]
    bass_part = parts[1] if len(parts) > 1 else None
    
    m = re.match(r"^([A-G][#b]?)(.*)$", main_chord)
    if not m:
        return chord_str
        
    root, quality = m.group(1), m.group(2)
    orig_semi = NOTE_TO_SEMITONE.get(root, 0)
    new_semi = (orig_semi + semitones) % 12
    new_root = spelling[new_semi]
    
    res = f"{new_root}{quality}"
    if bass_part:
        bm = re.match(r"^([A-G][#b]?)(.*)$", bass_part)
        if bm:
            b_root, b_qual = bm.group(1), bm.group(2)
            b_semi = (NOTE_TO_SEMITONE.get(b_root, 0) + semitones) % 12
            new_b_root = spelling[b_semi]
            res += f"/{new_b_root}{b_qual}"
        else:
            res += f"/{bass_part}"
            
    return res
