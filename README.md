# Instrumentos: Image to Piano Piece (Web App)

An artistic web app that turns images into piano pieces (in MIDI format). Upload an image, tweak a few settings, and download WAV and MIDI.

## Overview

**Instrumentos** (Spanish for "instruments") is a Streamlit app that:

1. **Image → Binary** — Your image is resized and converted to a binary string
2. **Binary → WAV** — That data is written as raw audio (WAV)
3. **WAV → MIDI** — Basic Pitch (AI) transcribes the WAV into MIDI notes
4. **Preview** — You can listen to a synthesized preview in the browser; downloads are the raw WAV and MIDI files

The app uses **pretty_midi** for in-browser MIDI preview (sine + overtones).

## Requirements

- **Python 3.11+**

### Python dependencies

- **Pillow** — Image load, resize, RGB
- **basic-pitch** — Pitch detection and MIDI transcription
- **numpy** — Array operations (used by pretty_midi)
- **pretty_midi** — MIDI load and synthesize (preview)
- **streamlit** — Web UI

## Installation

1. Clone or download this repository.

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the app:
   ```bash
   streamlit run app.py
   ```

2. Open the URL in your browser (usually `http://localhost:8501`).

3. In the **Create** tab: upload an image, optionally adjust the sidebar settings, then click **Convert**.

4. Listen to the WAV and MIDI previews, then use **Download WAV** and **Download MIDI** to save the files (named after your image, e.g. `test.wav`, `test.mid`).

### Tabs

- **Create** — Upload, settings, convert, listen, download.
- **The idea** — Plain-language description of what the app does.
- **Under the hood** — Pipeline, libraries, and main functions (for developers).

### Supported image formats

Any format supported by Pillow: PNG, JPG, JPEG, WebP, GIF, BMP, etc.

### Settings (sidebar)

All conversion parameters are in the sidebar with short descriptions and ranges (image resize, sample rate, note segmentation, confidence threshold, pitch range, note length, tempo, transpose semitones 0–24 default 6). Tooltips explain what moving each slider does.

## Project structure

```
instrumentos/
├── app.py                 # Streamlit web app (UI + flow)
├── main.py                # Pipeline logic (image → binary → WAV → MIDI)
├── synth.py               # MIDI → WAV bytes for in-app preview
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .streamlit/
    └── config.toml        # Theme (black/white/grey, Roboto font)
```

## How it works (short)

- The image is scaled (max dimension configurable), converted to RGB, then to a binary string. That string is written as 8-bit mono WAV.
- **Basic Pitch** analyzes the WAV and outputs MIDI (note onsets and pitches).
- The app stores WAV and MIDI; the **preview** is made by synthesizing the MIDI with **pretty_midi** (sine + overtones) in Python. Download files are the raw WAV and MIDI, not the preview.

## Limitations & notes

- Conversion can take tens of seconds to a few minutes depending on image size and settings.
- The result is algorithmic and abstract — not tuned for strict melody or harmony.
- Larger images produce more data and longer audio; smaller max image size speeds things up.

## Troubleshooting

- **"Image not found"** — Ensure you selected a file and it uploaded (check the preview in the Create tab).
- **Slow conversion** — Reduce the "Image resize" slider so the image is scaled down more.
- **Preview sounds odd** — The in-app preview is a simple synth; the downloaded MIDI can be played in any DAW or player with a better soundfont.

## License

This project is provided as-is for artistic exploration.
