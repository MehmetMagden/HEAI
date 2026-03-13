import os
import torch
import logging
import numpy as np
import soundfile as sf
from pathlib import Path

logger = logging.getLogger(__name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
VOICE_SAMPLES_DIR = Path(__file__).parent.parent / "data" / "voice_samples"
REFERENCE_WAV     = VOICE_SAMPLES_DIR / "reference.wav"
OUTPUT_DIR        = Path(__file__).parent.parent / "data" / "audio_output"
UPLOAD_DIR        = Path(__file__).parent.parent / "data" / "audio_upload"

XTTS_MODEL_PATH = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "tts",
    "tts_models--multilingual--multi-dataset--xtts_v2"
)

for d in [VOICE_SAMPLES_DIR, OUTPUT_DIR, UPLOAD_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class VoiceService:
    def __init__(self):
        self.device = DEVICE
        self._whisper = None
        self._tts_model = None
        self._tts_config = None
        self._gpt_cond_latent = None
        self._speaker_embedding = None
        logger.info(f"🎙️ VoiceService başlatıldı — Cihaz: {self.device}")

    def _load_whisper(self):
        if self._whisper is None:
            from faster_whisper import WhisperModel
            compute = "float16" if self.device == "cuda" else "int8"
            logger.info("⏳ Whisper 'small' yükleniyor...")
            self._whisper = WhisperModel("small", device=self.device, compute_type=compute)
            logger.info("✅ Whisper hazır")
        return self._whisper

    def transcribe(self, audio_path: str) -> str:
        model = self._load_whisper()
        segments, _ = model.transcribe(audio_path, language="tr", beam_size=5)
        text = " ".join([s.text.strip() for s in segments])
        logger.info(f"📝 Transkript: {text[:80]}")
        return text.strip()

    def _load_tts(self):
        if self._tts_model is None:
            from TTS.tts.configs.xtts_config import XttsConfig
            from TTS.tts.models.xtts import Xtts

            logger.info(f"⏳ XTTS v2 yükleniyor: {XTTS_MODEL_PATH}")
            config = XttsConfig()
            config.load_json(os.path.join(XTTS_MODEL_PATH, "config.json"))

            model = Xtts.init_from_config(config)
            model.load_checkpoint(config, checkpoint_dir=XTTS_MODEL_PATH, eval=True)

            if self.device == "cuda":
                model.cuda()

            self._tts_model = model
            self._tts_config = config
            logger.info("✅ XTTS v2 hazır")

            if REFERENCE_WAV.exists():
                logger.info("🎤 Referans ses conditioning hesaplanıyor...")
                self._gpt_cond_latent, self._speaker_embedding = \
                    model.get_conditioning_latents(audio_path=[str(REFERENCE_WAV)])
                logger.info("✅ Ses klonlama hazır")

        return self._tts_model, self._tts_config

    def unload_tts(self):
        if self._tts_model is not None:
            del self._tts_model
            self._tts_model = None
            self._tts_config = None
            self._gpt_cond_latent = None
            self._speaker_embedding = None
            if self.device == "cuda":
                torch.cuda.empty_cache()
            logger.info("🗑️ XTTS v2 VRAM'dan kaldırıldı")

    def synthesize(self, text: str, output_filename: str = "output.wav") -> str:
        if not REFERENCE_WAV.exists():
            raise FileNotFoundError(
                f"Referans ses bulunamadı: {REFERENCE_WAV}\n"
                "Lütfen data/voice_samples/reference.wav dosyasını ekleyin."
            )

        output_path = str(OUTPUT_DIR / output_filename)
        chunks = self._split_text(text)
        model, config = self._load_tts()

        logger.info(f"🔊 {len(chunks)} parça sentezleniyor...")
        all_audio = []

        for i, chunk in enumerate(chunks):
            logger.info(f"  Parça {i+1}/{len(chunks)}: {chunk[:50]}...")
            out = model.inference(
                text=chunk,
                language="tr",
                gpt_cond_latent=self._gpt_cond_latent,
                speaker_embedding=self._speaker_embedding,
                temperature=0.7,
                length_penalty=1.0,
                repetition_penalty=10.0,
                top_k=50,
                top_p=0.85,
            )
            all_audio.append(np.array(out["wav"]))

        merged = np.concatenate(all_audio)
        sf.write(output_path, merged, 24000)
        logger.info(f"✅ Ses kaydedildi: {output_path}")
        return output_path

    def _split_text(self, text: str, max_chars: int = 250) -> list:
        if len(text) <= max_chars:
            return [text]
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        chunks, current = [], ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(current) + len(sent) < max_chars:
                current += sent + ". "
            else:
                if current:
                    chunks.append(current.strip())
                current = sent + ". "
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text[:max_chars]]

    def synthesize_sentence(self, text: str, filename: str) -> str:
        """Tek cümleyi sentezler, dosya yolunu döner."""
        if len(text.strip()) < 5:
            return ""
        if not REFERENCE_WAV.exists():
            raise FileNotFoundError(f"Referans ses bulunamadı: {REFERENCE_WAV}")

        output_path = str(OUTPUT_DIR / filename)
        model, config = self._load_tts()

        out = model.inference(
            text=text,
            language="tr",
            gpt_cond_latent=self._gpt_cond_latent,
            speaker_embedding=self._speaker_embedding,
            temperature=0.7,
            length_penalty=1.0,
            repetition_penalty=10.0,
            top_k=50,
            top_p=0.85,
        )
        sf.write(output_path, np.array(out["wav"]), 24000)
        logger.info(f"✅ Cümle sesi: {filename}")
        return output_path

    def split_into_sentences(self, text: str) -> list:
        """Metni akıllıca cümlelere böler."""
        import re
        text = re.sub(
            r'\b(Hz|Dr|Prof|Yrd|Doç|Müh|s\.a\.v|r\.a|k\.s)\.',
            lambda m: m.group().replace('.', '@@'),
            text
        )
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.replace('@@', '.') for s in sentences]
        result = []
        buffer = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            buffer = (buffer + " " + s).strip() if buffer else s
            if len(buffer) >= 30:
                result.append(buffer)
                buffer = ""
        if buffer:
            result.append(buffer)
        return result if result else [text]

    def cleanup_old_audio(self, max_files: int = 50):
        """Eski cümle ses dosyalarını temizler."""
        files = sorted(
            OUTPUT_DIR.glob("sentence_*.wav"),
            key=lambda f: f.stat().st_mtime
        )
        while len(files) > max_files:
            files[0].unlink()
            files = files[1:]


voice_service = VoiceService()