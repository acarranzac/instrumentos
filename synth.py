"""Convert MIDI bytes to WAV bytes for in-app preview."""
import io
import wave

import numpy as np
import pretty_midi


def _piano_like_wave(phase: np.ndarray) -> np.ndarray:
    """Rich tone: fundamental + overtones (piano-like). Phase in radians."""
    return (
        np.sin(phase)
        + 0.35 * np.sin(2 * phase)
        + 0.15 * np.sin(3 * phase)
        + 0.08 * np.sin(4 * phase)
    ) / 1.58  # scale so peak ~1


def midi_bytes_to_wav_bytes(midi_bytes: bytes, fs: int = 44100) -> bytes | None:
    """Synthesize MIDI to WAV (piano-like tone). Returns WAV file bytes, or None if empty/corrupt."""
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_file=io.BytesIO(midi_bytes))
    except Exception:
        return None
    if midi_data.get_end_time() == 0:
        return None
    audio = midi_data.synthesize(fs=fs, wave=_piano_like_wave)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = np.clip(audio, -1.0, 1.0)
    samples = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(fs)
        wav.writeframes(samples.tobytes())
    return buf.getvalue()
