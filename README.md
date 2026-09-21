# 🎼 ScoreLab — Notación Musical & Transpositor de Partituras en PDF

Aplicación web Full Stack moderna, ligera y funcional diseñada para transcribir y superponer el cifrado de notas (Do, Re, Mi... o cifrado americano) directamente sobre las figuras musicales de cualquier partitura en PDF, permitiendo cambiar de tonalidad con soporte estricto de alteraciones (# y b) y manteniendo la partitura gráfica 100% intacta.

---

## 🚀 Características Principales

1. **Repertorio Masivo Integrado (730+ Partituras):**
   - Escaneo automático de la carpeta local `partituras/` que alberga más de 730 partituras en PDF.
   - Menú de selección interactivo con formateo limpio de títulos (`Himno 001 — Santo Santo Santo`, etc.).
   - Buscador en tiempo real por número o título con filtrado instantáneo.
   - Carga directa desde el servidor local con procesamiento y transposición inmediata.

2. **Detección Automática de Tonalidad Original & Transposición Armónica:**
   - Detecta de forma instantánea y precisa la tonalidad original de la partitura a partir de la armadura del primer pentagrama (0 alteraciones = Do Mayor, 1 a 6 sostenidos o bemoles).
   - **Método por defecto:** *Transposición Armónica Completa (Recomendado)*, transportando la melodía armónicamente desde la tonalidad original hacia la tonalidad destino.
   - **Control de Medios Tonos (Semitonos):** Botones **`➖`** y **`➕`** para subir o bajar rápidamente medio tono por medio tono con un solo toque, además del menú desplegable cromático.
   - Indicador en tiempo real del intervalo de transposición (ej. `Mi Mayor ➔ Fa Mayor (+1 st ♯)` o `Sib Mayor ➔ Fa Mayor (-5 st ♭)`).

3. **Accesibilidad Visual para Tablets & Atril:**
   - **Tamaño por defecto:** *Muy Grande (1.65x)* para máxima visibilidad inmediata en atriles y tablets.
   - Opciones adicionales de tamaño: *Normal (1.0x)*, *Grande (1.35x)* y deslizador continuo **hasta 4.00x**.
   - Prioridad estricta de capas: la **voz principal (notas superiores)** se dibuja siempre en la capa superior sin quedar tapada por notas de acompañamiento.
   - Tipografía adaptativa anti-empaste con márgenes internos ampliados.

4. **Acordes en Cifrado Americano con Transposición Dinámica:**
   - Interruptor para superponer acordes (*lead sheet chords*) sobre cada compás.
   - Los acordes se muestran en **cifrado americano** (**C**, **D7**, **G**, **Em**, **Bb**...) y se transponen automáticamente al cambiar la tonalidad.
   - Opción para personalizar y editar la secuencia armónica.

5. **Soporte Completo de Partituras Multi-Página & Descarga Tablet:**
   - Procesa y genera documentos PDF de múltiples páginas íntegramente.
   - Navegador interactivo de páginas (`Página 1`, `Página 2`, etc.) y opción de **vista continua** para desplazarse por todo el documento.
   - Descarga garantizada con nombre estricto `file_name="partitura_cifrado_americano.pdf"` listo para atril y tablets.

---

## 📁 Estructura del Proyecto

```text
App_partituras/
│
├── app.py                     # Aplicación web principal (Streamlit)
├── requirements.txt           # Lista de dependencias de Python
├── run.bat                    # Script de ejecución con un clic para Windows
├── README.md                  # Documentación completa del proyecto
│
├── partituras/                # Repertorio masivo de partituras PDF (730+ himnos)
│   ├── himno_001_santo_santo_santo.pdf
│   ├── himno_002_mirando_al_cielo.pdf
│   └── ...
│
├── core/                      # Módulos de lógica del sistema
│   ├── __init__.py
│   ├── music_engine.py        # Teoría musical, escalas y reglas de armadura
│   └── pdf_processor.py       # Detección de pentagramas y renderizado vectorial PyMuPDF
│
└── assets/                    # Partituras de ejemplo y recursos
    ├── pdf_ejemplo.pdf
    └── pdf_ejemplo_resultado.pdf
```

---

## 🛠️ Instalación y Requisitos

### 1. Prerrequisitos
- **Python 3.10 o superior** (probado y compatible con Python 3.10, 3.11, 3.12, 3.13 y 3.14).

### 2. Instalación de Dependencias

Abre una terminal (PowerShell o CMD) en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

Las librerías principales utilizadas son:
- **`streamlit`**: Interfaz de usuario interactiva y moderna.
- **`pymupdf` (fitz)**: Motor ultra-rápido para manipular vectores y texto en PDFs sin rasterización.
- **`pillow` (PIL)**: Renderizado de imágenes de alta resolución para la vista previa web.

---

## 🏃 Cómo Ejecutar la Aplicación

### Opción A (Recomendada en Windows):
Simplemente haz doble clic en el archivo:
```text
run.bat
```

### Opción B (Línea de comandos):
```bash
streamlit run app.py
```

O si utilizas una ruta específica de Python en Windows:
```bash
& "$env:LOCALAPPDATA\Python\bin\python.exe" -m streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador predeterminado en:
👉 **`http://localhost:8501`**

---

## 🎵 Guía de Uso Rápido

1. **Cargar la partitura:** Haz clic en *"📄 Cargar Partitura de Ejemplo"* o arrastra tu propio archivo PDF.
2. **Seleccionar tonalidad:** En la barra lateral izquierda, selecciona la tonalidad deseada (ej. *Fa Mayor* para que los Si se muestren *Sib*).
3. **Elegir modo y opciones:** Elige entre Cifrado Español o Americano, y ajusta la escala de texto si lo deseas.
4. **Revisar:** Consulta la comparativa antes/después en la pestaña *"🔄 Comparación Original vs Resultado"*.
5. **Descargar:** Haz clic en el botón principal *"📥 Descargar PDF Final"* para obtener tu partitura lista para imprimir o compartir.
