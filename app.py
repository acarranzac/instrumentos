import os
import re
import tempfile

import streamlit as st

from main import binary_to_wav, get_output_paths, image_to_binary, wav_to_midi
from synth import midi_bytes_to_wav_bytes

_ABOUT_STYLE = "font-size: 1.15rem; text-align: justify;"

st.set_page_config(page_title="Instrumentos", page_icon="🎹", initial_sidebar_state="expanded")

# Black/white/grey aesthetic override (buttons, sliders, links)
st.markdown(
    """
    <style>
    .stButton > button { background-color: #333; color: #fff; border-color: #555; }
    .stButton > button:hover { background-color: #555; border-color: #333; }
    [data-testid="stSlider"] [role="slider"] { background: #333; }
    a { color: #333 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Instrumentos")
st.markdown("Turn an image into a piano piece — upload, tweak, and download WAV and MIDI.")

def _slider_setting(title: str, desc: str, min_val, max_val, default, step=1, help_text=""):
    st.markdown(f"**{title}**  \n*{desc}*")
    return st.slider(title, min_val, max_val, default, step, help=help_text, label_visibility="collapsed")

with st.sidebar:
    st.subheader("Settings")
    max_image_size = _slider_setting("Image resize", "How much we scale down your image", 100, 1000, 320, help_text="Left: Smaller image, less data. Right: Larger image, more data.")
    st.markdown("**WAV sample rate**  \n*WAV audio file quality*")
    sample_rate = st.selectbox("WAV sample rate", [22050, 44100, 48000], index=0, label_visibility="collapsed")
    onset_threshold = _slider_setting("Note Segmentation", "How easily a note should be split into two", 0.05, 0.95, 0.90, 0.01, "Left: Split notes. Right: Merge notes.")
    frame_threshold = _slider_setting("Model Confidence Threshold", "The model confidence required to create a note", 0.05, 0.95, 0.15, 0.01, "Left: More notes. Right: Fewer notes.")
    min_pitch = _slider_setting("Minimum Pitch", "The minimum allowed pitch, in Hz", 0, 2000, 30, 10, "Left: Lower notes. Right: Higher notes.")
    max_pitch = _slider_setting("Maximum Pitch", "The maximum allowed pitch, in Hz", 40, 3000, 3000, 10, "Left: Lower notes. Right: Higher notes.")
    min_note_length = _slider_setting("Minimum Note Length", "The minimum length required to emit a note, in milliseconds", 3, 50, 20, 1, "Left: Short notes. Right: Long notes.")
    midi_tempo = _slider_setting("Midi File Tempo", "The tempo used to export the MIDI file", 24, 224, 60, 1, "Left: Slower. Right: Faster.")
    transpose_semitones = _slider_setting("Transpose", "Transpose semitones up and down", 0, 24, 6, 1, "Left: lower notes melody. Right: higher notes melody.")

if min_pitch >= max_pitch:
    st.warning("Minimum Pitch must be less than Maximum Pitch.")

tab_create, tab_idea, tab_tech = st.tabs(["Create", "The idea", "Under the hood"])

with tab_create:
    uploaded = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "webp", "gif", "bmp"])

    if uploaded is not None:
        st.subheader("Image preview")
        st.image(uploaded, width="stretch")

    # Init session state
    for key in ("wav_bytes", "midi_bytes", "midi_preview_wav_bytes", "output_basename", "last_converted_name", "last_converted_params"):
        if key not in st.session_state:
            st.session_state[key] = None

    # Clear results only when user changes file or settings (not when clicking download/preview)
    current_params = (max_image_size, sample_rate, onset_threshold, frame_threshold, min_pitch, max_pitch, min_note_length, midi_tempo, transpose_semitones)
    if st.session_state.wav_bytes is not None and (
        uploaded is None
        or uploaded.name != st.session_state.last_converted_name
        or current_params != st.session_state.last_converted_params
    ):
        st.session_state.wav_bytes = None
        st.session_state.midi_bytes = None
        st.session_state.midi_preview_wav_bytes = None
        st.session_state.output_basename = None
        st.session_state.last_converted_name = None
        st.session_state.last_converted_params = None

    if uploaded and st.button("Convert", disabled=(min_pitch >= max_pitch)):
        ext = os.path.splitext(uploaded.name)[1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            wav_path, midi_path = get_output_paths(tmp_path)
            with st.spinner("Converting…"):
                binary = image_to_binary(tmp_path, max_image_size=max_image_size)
                binary_to_wav(binary, wav_path, sample_rate=sample_rate)
                wav_to_midi(
                    wav_path,
                    midi_path,
                    onset_threshold=onset_threshold,
                    frame_threshold=frame_threshold,
                    minimum_frequency=min_pitch,
                    maximum_frequency=max_pitch,
                    minimum_note_length=min_note_length,
                    midi_tempo=midi_tempo,
                    transpose_semitones=transpose_semitones,
                )
            output_basename = (re.sub(r"[^\w\-]", "_", os.path.splitext(uploaded.name)[0]).strip("_") or "piano")[:200]
            st.session_state.output_basename = output_basename
            st.session_state.last_converted_name = uploaded.name
            st.session_state.last_converted_params = (max_image_size, sample_rate, onset_threshold, frame_threshold, min_pitch, max_pitch, min_note_length, midi_tempo, transpose_semitones)
            with open(wav_path, "rb") as f:
                st.session_state.wav_bytes = f.read()
            with open(midi_path, "rb") as f:
                st.session_state.midi_bytes = f.read()
            try:
                st.session_state.midi_preview_wav_bytes = midi_bytes_to_wav_bytes(st.session_state.midi_bytes, fs=sample_rate)
            except Exception:
                st.session_state.midi_preview_wav_bytes = None
            for p in (tmp_path, wav_path, midi_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
            st.success("Done. Download your files below.")
        except Exception as e:
            st.error(str(e))
            st.session_state.wav_bytes = None
            st.session_state.midi_bytes = None
            st.session_state.midi_preview_wav_bytes = None
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    if st.session_state.wav_bytes is not None and st.session_state.midi_bytes is not None:
        st.subheader("Listen")
        st.audio(st.session_state.wav_bytes, format="audio/wav")
        st.caption("WAV preview (image-as-audio)")
        if st.session_state.midi_preview_wav_bytes is not None:
            st.audio(st.session_state.midi_preview_wav_bytes, format="audio/wav")
            st.caption("MIDI preview (synthesized)")
        else:
            st.caption("MIDI preview unavailable")
        st.subheader("Download")
        base = st.session_state.get("output_basename") or "piano"
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Download WAV", data=st.session_state.wav_bytes, file_name=f"{base}.wav", mime="audio/wav")
        with col2:
            st.download_button("Download MIDI", data=st.session_state.midi_bytes, file_name=f"{base}.mid", mime="audio/midi")
        if st.button("Clear results"):
            st.session_state.wav_bytes = None
            st.session_state.midi_bytes = None
            st.session_state.midi_preview_wav_bytes = None
            st.session_state.output_basename = None
            st.session_state.last_converted_name = None
            st.session_state.last_converted_params = None
            st.rerun()

with tab_idea:
    st.subheader("What it does")
    st.markdown(f'<p style="{_ABOUT_STYLE}">You upload an image. You can tweak a few sliders (how much to scale it, how the notes are detected). You press <strong>Convert</strong>. You get two files: a WAV and a MIDI.</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="{_ABOUT_STYLE}">The WAV is your image turned into sound — the raw data of the picture, played as audio. The MIDI is that sound translated into notes by a small AI, so you can edit it, play it in any instrument, or turn it into sheet music.</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="{_ABOUT_STYLE}">No musical knowledge needed. Each image gives a different piece.</p>', unsafe_allow_html=True)

with tab_tech:
    st.subheader("Pipeline")
    st.markdown(f'<p style="{_ABOUT_STYLE}">1. <strong>Image → binary</strong> — Image is resized (Pillow), converted to RGB, then to a binary string.<br>2. <strong>Binary → WAV</strong> — Binary chunks become raw audio samples; written as mono WAV.<br>3. <strong>WAV → MIDI</strong> — Basic Pitch (pitch-to-MIDI model) transcribes the WAV into note onsets and pitches.<br>4. <strong>Preview</strong> — MIDI is synthesized to WAV in the browser using pretty_midi (sine + overtones); download stays raw MIDI.</p>', unsafe_allow_html=True)
    st.subheader("Libraries")
    st.markdown(
        f'<ul style="{_ABOUT_STYLE}">'
        f'<li><strong>Pillow</strong> — Image load, resize, RGB.</li>'
        f'<li><strong><a href="https://basicpitch.spotify.com/" target="_blank">basic_pitch</a></strong> — Pitch detection and MIDI transcription. Open source project by Spotify.</li>'
        f'<li><strong>pretty_midi</strong> — Load MIDI, synthesize to numpy (preview).</li>'
        f'<li><strong>wave</strong> (stdlib) — WAV write.</li>'
        '</ul>',
        unsafe_allow_html=True
    )
    st.subheader("Main functions")
    st.markdown(f'<ul style="{_ABOUT_STYLE}"><li><code>image_to_binary</code>, <code>binary_to_wav</code>, <code>wav_to_midi</code> (main.py) — pipeline steps.</li><li><code>midi_bytes_to_wav_bytes</code> (synth.py) — MIDI → WAV bytes for in-app preview.</li></ul>', unsafe_allow_html=True)
