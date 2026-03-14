import wave
from pathlib import Path

from PIL import Image


def get_output_paths(image_path: str) -> tuple[str, str]:
    """Generate output file paths for WAV and MIDI based on the image filename."""
    base = str(Path(image_path).with_suffix(""))
    wav_path = f"{base}.wav"
    midi_path = f"{base}.mid"
    return wav_path, midi_path


def image_to_binary(image_path: str, max_image_size: int = 320) -> str:
    """Convert image to binary string (RGB → scaled → bits)."""
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            width, height = img.size
            scale = max_image_size / max(width, height)
            img = img.resize(
                (round(width * scale), round(height * scale)),
                Image.Resampling.LANCZOS
            )
            return ''.join(f'{byte:08b}' for byte in img.tobytes())
    except Exception as e:
        raise Exception(f"Failed to process image: {e}") from e


def binary_to_wav(binary: str, wav_path: str, sample_rate: int = 22050) -> None:
    """Write binary string as mono 8-bit WAV file."""
    try:
        n = len(binary) // 8
        samples = bytes(int(binary[i * 8:i * 8 + 8], 2) for i in range(n))
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setparams((1, 1, sample_rate, n, 'NONE', 'not compressed'))
            wav_file.writeframes(samples)
    except Exception as e:
        raise Exception(f"Failed to create WAV file: {e}") from e


def wav_to_midi(
    wav_path: str,
    midi_path: str,
    onset_threshold: float = 0.90,
    frame_threshold: float = 0.15,
    minimum_frequency: float = 30,
    maximum_frequency: float = 3000,
    minimum_note_length: float = 20,
    midi_tempo: int = 60,
    transpose_semitones: int = 6,
) -> None:
    """Transcribe WAV to MIDI using Basic Pitch model."""
    from basic_pitch.inference import predict
    
    if not Path(wav_path).exists():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")
    
    try:
        _, midi_data, _ = predict(
            wav_path,
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_frequency=minimum_frequency,
            maximum_frequency=maximum_frequency,
            minimum_note_length=minimum_note_length,
            midi_tempo=midi_tempo,
        )
        if transpose_semitones != 0:
            for inst in midi_data.instruments:
                for note in inst.notes:
                    note.pitch = max(0, min(127, note.pitch + transpose_semitones))
        midi_data.write(midi_path)
    except Exception as e:
        raise Exception(f"Failed to convert WAV to MIDI: {e}") from e