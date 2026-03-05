import base64
import array
from collections import deque
import difflib
import io
import json
import math
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from mss import mss
from PIL import Image
from openai import OpenAI


@dataclass
class Settings:
    provider: str
    model_name: str
    frame_interval_seconds: float
    max_output_tokens: int
    monitor_index: int
    jpeg_quality: int
    max_width: int
    companion_tone: str
    ollama_base_url: str
    voice_enabled: bool
    voice_gender: str
    voice_name_hint: str
    voice_backend: str
    voice_rate: int
    voice_volume: float
    speak_every_n_comments: int
    min_novelty_ratio: float
    allow_silent: bool
    heartbeat_seconds: float
    use_agent_names: bool
    name_mention_cooldown: int
    repetition_window: int
    speak_on_events_only: bool
    kill_banner_hint_enabled: bool
    kill_banner_conf_threshold: float
    use_context_memory: bool
    repetition_similarity_threshold: float
    voice_input_enabled: bool
    always_listen: bool
    ptt_key: str
    vosk_model_path: str
    vad_silence_seconds: float
    vad_rms_threshold: int
    min_voice_words: int
    min_voice_chars: int


def load_settings() -> Settings:
    load_dotenv()

    provider = os.getenv("PROVIDER", "openai").strip().lower()
    model_name = os.getenv("MODEL_NAME", "gpt-4.1-mini")
    frame_interval_seconds = float(os.getenv("FRAME_INTERVAL_SECONDS", "3"))
    max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "120"))
    monitor_index = int(os.getenv("MONITOR_INDEX", "1"))
    jpeg_quality = int(os.getenv("JPEG_QUALITY", "70"))
    max_width = int(os.getenv("MAX_WIDTH", "1280"))
    companion_tone = os.getenv("COMPANION_TONE", "hype").strip().lower()
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    voice_enabled = os.getenv("VOICE_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
    voice_gender = os.getenv("VOICE_GENDER", "female").strip().lower()
    voice_name_hint = os.getenv("VOICE_NAME_HINT", "").strip()
    voice_backend = os.getenv("VOICE_BACKEND", "powershell").strip().lower()
    voice_rate = int(os.getenv("VOICE_RATE", "185"))
    voice_volume = float(os.getenv("VOICE_VOLUME", "1.0"))
    speak_every_n_comments = max(1, int(os.getenv("SPEAK_EVERY_N_COMMENTS", "1")))
    min_novelty_ratio = float(os.getenv("MIN_NOVELTY_RATIO", "0.86"))
    allow_silent = os.getenv("ALLOW_SILENT", "false").strip().lower() in {"1", "true", "yes", "on"}
    heartbeat_seconds = float(os.getenv("HEARTBEAT_SECONDS", "6"))
    use_agent_names = os.getenv("USE_AGENT_NAMES", "false").strip().lower() in {"1", "true", "yes", "on"}
    name_mention_cooldown = max(0, int(os.getenv("NAME_MENTION_COOLDOWN", "5")))
    repetition_window = max(3, int(os.getenv("REPETITION_WINDOW", "8")))
    speak_on_events_only = os.getenv("SPEAK_ON_EVENTS_ONLY", "false").strip().lower() in {"1", "true", "yes", "on"}
    kill_banner_hint_enabled = os.getenv("KILL_BANNER_HINT_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
    kill_banner_conf_threshold = float(os.getenv("KILL_BANNER_CONF_THRESHOLD", "0.30"))
    use_context_memory = os.getenv("USE_CONTEXT_MEMORY", "false").strip().lower() in {"1", "true", "yes", "on"}
    repetition_similarity_threshold = float(os.getenv("REPETITION_SIMILARITY_THRESHOLD", "0.78"))
    voice_input_enabled = os.getenv("VOICE_INPUT_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    always_listen = os.getenv("ALWAYS_LISTEN", "false").strip().lower() in {"1", "true", "yes", "on"}
    ptt_key = os.getenv("PTT_KEY", "f8").strip().lower()
    vosk_model_path = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15").strip()
    vad_silence_seconds = float(os.getenv("VAD_SILENCE_SECONDS", "0.9"))
    vad_rms_threshold = int(os.getenv("VAD_RMS_THRESHOLD", "450"))
    min_voice_words = max(1, int(os.getenv("MIN_VOICE_WORDS", "2")))
    min_voice_chars = max(3, int(os.getenv("MIN_VOICE_CHARS", "6")))

    return Settings(
        provider=provider,
        model_name=model_name,
        frame_interval_seconds=frame_interval_seconds,
        max_output_tokens=max_output_tokens,
        monitor_index=monitor_index,
        jpeg_quality=jpeg_quality,
        max_width=max_width,
        companion_tone=companion_tone,
        ollama_base_url=ollama_base_url,
        voice_enabled=voice_enabled,
        voice_gender=voice_gender,
        voice_name_hint=voice_name_hint,
        voice_backend=voice_backend,
        voice_rate=voice_rate,
        voice_volume=voice_volume,
        speak_every_n_comments=speak_every_n_comments,
        min_novelty_ratio=min_novelty_ratio,
        allow_silent=allow_silent,
        heartbeat_seconds=heartbeat_seconds,
        use_agent_names=use_agent_names,
        name_mention_cooldown=name_mention_cooldown,
        repetition_window=repetition_window,
        speak_on_events_only=speak_on_events_only,
        kill_banner_hint_enabled=kill_banner_hint_enabled,
        kill_banner_conf_threshold=kill_banner_conf_threshold,
        use_context_memory=use_context_memory,
        repetition_similarity_threshold=repetition_similarity_threshold,
        voice_input_enabled=voice_input_enabled,
        always_listen=always_listen,
        ptt_key=ptt_key,
        vosk_model_path=vosk_model_path,
        vad_silence_seconds=vad_silence_seconds,
        vad_rms_threshold=vad_rms_threshold,
        min_voice_words=min_voice_words,
        min_voice_chars=min_voice_chars,
    )


def capture_frame_data(
    monitor_index: int,
    max_width: int,
    jpeg_quality: int,
) -> tuple[str, Image.Image]:
    with mss() as sct:
        monitors = sct.monitors
        if monitor_index < 1 or monitor_index >= len(monitors):
            raise ValueError(
                f"Invalid monitor index {monitor_index}. Available monitor indexes: 1..{len(monitors) - 1}."
            )

        shot = sct.grab(monitors[monitor_index])

    image = Image.frombytes("RGB", shot.size, shot.rgb)

    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_size = (max_width, int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8"), image


class PushToTalkInput:
    def __init__(
        self,
        enabled: bool,
        always_listen: bool,
        ptt_key: str,
        model_path: str,
        vad_silence_seconds: float,
        vad_rms_threshold: int,
        min_voice_words: int,
        min_voice_chars: int,
        sample_rate: int = 16000,
    ) -> None:
        self.enabled = enabled
        self.always_listen = always_listen
        self.ptt_key = ptt_key
        self.model_path = model_path
        self.vad_silence_seconds = max(0.3, vad_silence_seconds)
        self.vad_rms_threshold = max(50, vad_rms_threshold)
        self.min_voice_words = max(1, min_voice_words)
        self.min_voice_chars = max(3, min_voice_chars)
        self.sample_rate = sample_rate
        self._lock = threading.Lock()
        self._pressed = False
        self._chunks: list[bytes] = []
        self._latest_text = ""
        self._pending_audio: queue.Queue[bytes | None] = queue.Queue(maxsize=3)
        self._last_voice_time = 0.0
        self._always_chunks: list[bytes] = []
        self._stream = None
        self._listener = None
        self._stt_thread: threading.Thread | None = None
        self._ready = False
        self._model = None
        self._vosk_kaldi_recognizer = None

    def start(self) -> None:
        if not self.enabled:
            return
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model, SetLogLevel
            from pynput import keyboard as pynput_keyboard
        except Exception as exc:
            print(f"Voice input disabled: missing dependency ({exc})")
            self.enabled = False
            return

        if not os.path.isdir(self.model_path):
            print(f"Voice input disabled: Vosk model path not found ({self.model_path})")
            self.enabled = False
            return

        try:
            SetLogLevel(-1)
            self._model = Model(self.model_path)
            self._vosk_kaldi_recognizer = KaldiRecognizer
            self._stt_thread = threading.Thread(target=self._stt_loop, daemon=True)
            self._stt_thread.start()

            def audio_callback(indata, frames, time_info, status) -> None:
                _ = frames, time_info, status
                raw = bytes(indata)
                with self._lock:
                    if self.always_listen:
                        now = time.time()
                        rms = self._rms16le(raw)
                        if rms >= self.vad_rms_threshold:
                            self._always_chunks.append(raw)
                            self._last_voice_time = now
                        else:
                            if self._always_chunks:
                                self._always_chunks.append(raw)
                                if (now - self._last_voice_time) >= self.vad_silence_seconds:
                                    self._enqueue_audio(b"".join(self._always_chunks))
                                    self._always_chunks = []
                    elif self._pressed:
                        self._chunks.append(raw)

            self._stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                channels=1,
                dtype="int16",
                callback=audio_callback,
            )
            self._stream.start()

            def on_press(key) -> None:
                if not self._is_target_key(key):
                    return
                with self._lock:
                    if self._pressed:
                        return
                    self._pressed = True
                    self._chunks = []
                print("[ptt] listening...")

            def on_release(key) -> None:
                if not self._is_target_key(key):
                    return
                with self._lock:
                    if not self._pressed:
                        return
                    self._pressed = False
                    audio_bytes = b"".join(self._chunks)
                    self._chunks = []
                self._enqueue_audio(audio_bytes)

            if not self.always_listen:
                self._listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
                self._listener.daemon = True
                self._listener.start()
            self._ready = True
        except Exception as exc:
            print(f"Voice input disabled: init failed ({exc})")
            self.enabled = False

    def _enqueue_audio(self, audio_bytes: bytes) -> None:
        if not audio_bytes:
            return
        if self._pending_audio.full():
            try:
                _ = self._pending_audio.get_nowait()
            except queue.Empty:
                pass
        try:
            self._pending_audio.put_nowait(audio_bytes)
        except queue.Full:
            pass

    @staticmethod
    def _rms16le(raw: bytes) -> float:
        if not raw:
            return 0.0
        samples = array.array("h")
        samples.frombytes(raw)
        if not samples:
            return 0.0
        total = 0.0
        for s in samples:
            total += float(s) * float(s)
        return (total / len(samples)) ** 0.5

    def _stt_loop(self) -> None:
        while True:
            item = self._pending_audio.get()
            if item is None:
                return
            text = self._transcribe_bytes(item)
            text = self._clean_transcript(text)
            if not self._is_useful_transcript(text):
                continue
            if text:
                with self._lock:
                    self._latest_text = text
                if self.always_listen:
                    print(f"[mic] heard: {text}")
                else:
                    print(f"[ptt] heard: {text}")

    def _clean_transcript(self, text: str) -> str:
        return " ".join(text.strip().split())

    def _is_useful_transcript(self, text: str) -> bool:
        if not text or len(text) < self.min_voice_chars:
            return False
        tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
        if len(tokens) >= self.min_voice_words:
            return True
        one_word_whitelist = {"help", "stop", "pause", "resume", "yes", "no", "okay", "ok"}
        return len(tokens) == 1 and tokens[0] in one_word_whitelist

    def _is_target_key(self, key) -> bool:
        target = self.ptt_key.lower()
        char = getattr(key, "char", None)
        if char and len(target) == 1:
            return char.lower() == target
        key_str = str(key).lower()
        return key_str in {target, f"key.{target}"}

    def _transcribe_bytes(self, audio_bytes: bytes) -> str:
        if not audio_bytes or not self._model or not self._vosk_kaldi_recognizer:
            return ""
        try:
            recognizer = self._vosk_kaldi_recognizer(self._model, self.sample_rate)
            chunk_size = 8000
            for i in range(0, len(audio_bytes), chunk_size):
                recognizer.AcceptWaveform(audio_bytes[i:i + chunk_size])
            final = json.loads(recognizer.FinalResult())
            return (final.get("text") or "").strip()
        except Exception:
            return ""

    def pop_latest_text(self) -> str:
        with self._lock:
            text = self._latest_text
            self._latest_text = ""
        return text

    def stop(self) -> None:
        try:
            self._pending_audio.put_nowait(None)
        except Exception:
            pass
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        if self._stt_thread is not None:
            self._stt_thread.join(timeout=1.0)

    @property
    def ready(self) -> bool:
        return self._ready and self.enabled


class TerminalChatInput:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._latest_text = ""
        self._commands: queue.Queue[tuple[str, str]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if not self.enabled:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                line = input().strip()
            except EOFError:
                return
            except Exception:
                return

            if not line:
                continue
            if line.lower() in {"/help", "help"}:
                print(
                    "[chat] /say <msg> | /tone hype|coach|chill | /silent on|off | "
                    "/speak <n> | /status"
                )
                continue
            if line.lower().startswith("/say "):
                self._latest_text = line[5:].strip()
                print(f"[chat] queued: {self._latest_text}")
                continue
            if line.lower().startswith("/tone "):
                self._commands.put(("tone", line[6:].strip().lower()))
                continue
            if line.lower().startswith("/silent "):
                self._commands.put(("silent", line[8:].strip().lower()))
                continue
            if line.lower().startswith("/speak "):
                self._commands.put(("speak", line[7:].strip()))
                continue
            if line.lower() == "/status":
                self._commands.put(("status", ""))
                continue

            # Plain text is treated like /say
            self._latest_text = line
            print(f"[chat] queued: {self._latest_text}")

    def pop_latest_text(self) -> str:
        text = self._latest_text
        self._latest_text = ""
        return text

    def pop_commands(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        while True:
            try:
                out.append(self._commands.get_nowait())
            except queue.Empty:
                break
        return out

    def stop(self) -> None:
        self._stop.set()


def build_prompt(
    previous_summary: str,
    last_comment: str,
    companion_tone: str,
    allow_silent: bool,
    kill_banner_hint: bool,
    latest_user_message: str,
) -> str:
    if companion_tone == "coach":
        style_line = "Tone: calm coach, concise callouts, supportive and practical."
    elif companion_tone == "chill":
        style_line = "Tone: relaxed friend, light energy, natural reactions."
    else:
        style_line = "Tone: hype best-friend energy, short punchy reactions."
    silence_rule = (
        "If there is no meaningful change, no notable threat/opportunity, or no useful new update compared with the previous comment, "
        "respond with exactly: SILENT. "
        if allow_silent
        else "Always provide one useful short live line, even if the situation is stable. "
    )

    return "".join(
        [
            "You are an AI companion describing what is visible on the current screen. ",
            "Talk directly to the user in second person ('you'). ",
            "Infer what is likely happening from this frame only. ",
            silence_rule,
            "Otherwise provide exactly one short sentence (max 14 words). ",
            "Use mostly second-person reactions like: 'Nice, you organized that clearly.' ",
            "Only use agent/character names if clearly visible in this frame's UI/kill-feed/nameplate text. ",
            "If uncertain, say what you can see instead of guessing genre/game. ",
            "Sound human and conversational, like live friend commentary. ",
            "Good examples: 'Nice layout, this looks clean.', 'You have a lot open right now.', 'Good progress, keep going.' ",
            "Vary wording and avoid repeating recent phrases. ",
            "Avoid certainties when unclear; use probabilistic language like likely/maybe. ",
            "Focus on actionable or entertaining observations relevant to whatever is on screen. ",
            "Do not force event callouts unless they are obvious from the frame. ",
            (
                f"Latest user voice message: {latest_user_message}. "
                "You MUST directly respond to that message first in second person. "
                "Do not ignore it. Then optionally add one brief screen observation. "
                if latest_user_message
                else ""
            ),
            f"{style_line}\n\n",
            f"Recent context: {previous_summary or 'No prior context yet.'}\n",
            f"Previous comment: {last_comment or 'None yet.'}",
        ]
    )


def request_commentary(
    client: OpenAI,
    model_name: str,
    previous_summary: str,
    last_comment: str,
    companion_tone: str,
    allow_silent: bool,
    kill_banner_hint: bool,
    latest_user_message: str,
    frame_base64: str,
    max_output_tokens: int,
) -> str:
    prompt = build_prompt(
        previous_summary,
        last_comment,
        companion_tone,
        allow_silent,
        kill_banner_hint,
        latest_user_message,
    )

    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{frame_base64}",
                    },
                ],
            }
        ],
        max_output_tokens=max_output_tokens,
    )

    text = (response.output_text or "").strip()
    return normalize_comment(text)


def request_commentary_ollama(
    base_url: str,
    model_name: str,
    previous_summary: str,
    last_comment: str,
    companion_tone: str,
    allow_silent: bool,
    kill_banner_hint: bool,
    latest_user_message: str,
    frame_base64: str,
) -> str:
    prompt = build_prompt(
        previous_summary,
        last_comment,
        companion_tone,
        allow_silent,
        kill_banner_hint,
        latest_user_message,
    )
    payload = {
        "model": model_name,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [frame_base64],
            }
        ],
    }
    request = urllib.request.Request(
        url=f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach Ollama at {base_url}. Is `ollama serve` running? ({exc})") from exc

    parsed = json.loads(raw)
    message = parsed.get("message", {})
    text = (message.get("content") or "").strip()
    return normalize_comment(text)


def normalize_comment(text: str) -> str:
    if not text:
        return "SILENT"

    compact = " ".join(text.split()).strip()
    upper = compact.upper().strip(".! ")
    if upper in {"SILENT", "[SILENT]", "(SILENT)", "NO COMMENT", "NONE"}:
        return "SILENT"
    return compact


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def is_direct_reply_to_user(comment: str, user_message: str) -> bool:
    c = comment.lower()
    u = user_message.lower().strip()
    if any(phrase in c for phrase in ("you said", "you asked", "about your", "i think", "i'd say", "i would say")):
        return True
    c_tokens = set(_tokenize(comment))
    u_tokens = [t for t in _tokenize(user_message) if len(t) >= 4]
    overlap = sum(1 for t in u_tokens if t in c_tokens)
    if comment.strip().endswith("?") and u_tokens:
        # Avoid counting near-echoed questions as valid "answers".
        echo_ratio = difflib.SequenceMatcher(None, c, u).ratio()
        if echo_ratio >= 0.55:
            return False
    return overlap >= 2


def build_direct_user_reply(user_message: str) -> str:
    msg = user_message.strip()
    lower = msg.lower()
    if "project" in lower:
        return "About your project, it looks solid so far. Keep iterating and testing frequently."
    if "what do you think" in lower:
        return "I think you're on the right track. Keep going, your setup looks good."
    if "help" in lower:
        return "I can help. Tell me the exact part you want to improve right now."
    if "why" in lower:
        return "Good question. Say it again with detail and I’ll answer clearly."
    if "how" in lower:
        return "I can walk you through it step by step. Ask the exact how-to."
    short = " ".join(msg.split())[:80]
    return f"I heard you: '{short}'. Keep going, you're making progress."


AGENT_NAMES = (
    "astra", "breach", "brimstone", "chamber", "clove", "cypher", "deadlock", "fade", "gekko",
    "harbor", "iso", "jett", "kayo", "killjoy", "neon", "omen", "phoenix", "raze", "reyna",
    "sage", "skye", "sova", "tejo", "viper", "vyse", "waylay", "yoru",
)


def contains_agent_name(text: str) -> bool:
    lower = text.lower()
    return any(re.search(rf"\b{name}\b", lower) for name in AGENT_NAMES)


def sanitize_agent_names(text: str, use_agent_names: bool) -> str:
    if text == "SILENT":
        return text
    if use_agent_names:
        return text

    sanitized = text
    for name in AGENT_NAMES:
        sanitized = re.sub(rf"\b{name}\b", "enemy", sanitized, flags=re.IGNORECASE)

    sanitized = re.sub(r"\benemy,?\s+enemy\b", "enemy", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s{2,}", " ", sanitized).strip(" ,")
    return sanitized or "Nice one, keep it up."


def is_repetitive_comment(new_comment: str, last_comment: str, min_novelty_ratio: float) -> bool:
    if new_comment == "SILENT":
        return True
    if not last_comment:
        return False
    similarity = difflib.SequenceMatcher(None, new_comment.lower(), last_comment.lower()).ratio()
    return similarity >= min_novelty_ratio


def is_repetitive_against_history(new_comment: str, recent_comments: deque[str], min_novelty_ratio: float) -> bool:
    if new_comment == "SILENT":
        return True
    candidate = new_comment.lower().strip()
    for prior in recent_comments:
        ratio = difflib.SequenceMatcher(None, candidate, prior.lower().strip()).ratio()
        if ratio >= min_novelty_ratio:
            return True
    return False


def normalize_for_repeat_check(text: str) -> str:
    return " ".join(text.lower().replace("’", "'").split())


def is_hard_repeat(new_comment: str, recent_comments: deque[str], similarity_threshold: float) -> bool:
    if not recent_comments:
        return False
    candidate = normalize_for_repeat_check(new_comment)
    for prior in recent_comments:
        prior_norm = normalize_for_repeat_check(prior)
        if candidate == prior_norm:
            return True
        if difflib.SequenceMatcher(None, candidate, prior_norm).ratio() >= similarity_threshold:
            return True
    return False


def is_kill_comment(comment: str) -> bool:
    text = comment.lower()
    kill_terms = (
        "kill", "killed", "elim", "eliminat", "headshot", "frag", "pick",
        "double", "triple", "quadra", "ace", "clutch",
    )
    return any(term in text for term in kill_terms)


def is_death_comment(comment: str) -> bool:
    text = comment.lower()
    death_terms = (
        "you died", "you are dead", "you got killed", "you were killed", "you got picked",
        "death", "eliminated", "got eliminated", "downed", "you went down",
    )
    return any(term in text for term in death_terms)


def is_event_comment(comment: str) -> bool:
    return is_kill_comment(comment) or is_death_comment(comment)


def detect_kill_banner_score(image: Image.Image) -> float:
    width, height = image.size
    left = int(width * 0.38)
    right = int(width * 0.62)
    top = int(height * 0.72)
    bottom = int(height * 0.98)
    roi = image.crop((left, top, right, bottom)).convert("RGB")

    # Keep detector work bounded for speed.
    if roi.width > 260:
        scale = 260.0 / roi.width
        roi = roi.resize((260, max(1, int(roi.height * scale))), Image.Resampling.BILINEAR)

    pixels = roi.load()
    rw, rh = roi.size
    center_candidates = [
        (rw // 2, int(rh * 0.45)),
        (rw // 2, int(rh * 0.52)),
        (rw // 2, int(rh * 0.60)),
        (int(rw * 0.48), int(rh * 0.52)),
        (int(rw * 0.52), int(rh * 0.52)),
    ]
    outer_radii = [int(min(rw, rh) * k) for k in (0.19, 0.22, 0.25)]
    inner_radii = [int(min(rw, rh) * k) for k in (0.13, 0.15)]

    best = 0.0
    for cx, cy in center_candidates:
        for r_out in outer_radii:
            orange_hits = 0
            samples = 0
            for deg in range(0, 360, 12):
                rad = math.radians(deg)
                x = int(cx + math.cos(rad) * r_out)
                y = int(cy + math.sin(rad) * r_out)
                if x < 0 or y < 0 or x >= rw or y >= rh:
                    continue
                samples += 1
                r, g, b = pixels[x, y]
                if r >= 170 and 70 <= g <= 210 and b <= 170 and (r - b) >= 35:
                    orange_hits += 1
            if samples == 0:
                continue
            orange_ratio = orange_hits / samples

            white_best = 0.0
            for r_in in inner_radii:
                white_hits = 0
                white_samples = 0
                for deg in range(0, 360, 15):
                    rad = math.radians(deg)
                    x = int(cx + math.cos(rad) * r_in)
                    y = int(cy + math.sin(rad) * r_in)
                    if x < 0 or y < 0 or x >= rw or y >= rh:
                        continue
                    white_samples += 1
                    pr, pg, pb = pixels[x, y]
                    if pr >= 165 and pg >= 165 and pb >= 165:
                        white_hits += 1
                if white_samples > 0:
                    white_best = max(white_best, white_hits / white_samples)

            score = 0.62 * orange_ratio + 0.38 * white_best
            if score > best:
                best = score

    return best


def generate_kill_callout(index: int) -> str:
    _ = index
    lines = [
        "Nice kill, keep the pressure up.",
        "Huge pick, you're winning these duels.",
        "Clean frag, your timing was perfect.",
        "Great elimination, keep pushing space.",
        "Big kill, your crosshair placement paid off.",
        "Beautiful headshot, you snapped that.",
        "Strong pick, you opened the map.",
        "Great shot, you punished that peek.",
        "Massive kill, momentum is yours.",
        "Excellent finish, keep that confidence.",
        "That was crisp, you're locked in.",
        "Perfect punish, you read that swing.",
    ]
    return random.choice(lines)


def fallback_comment(index: int) -> str:
    lines = [
        "Nice flow, you’re making steady progress.",
        "Clean setup, this looks organized.",
        "Good focus, keep that momentum.",
        "You’re managing this well, keep going.",
        "Solid pacing, you're staying on track.",
        "Nice structure, your screen looks tidy.",
        "Good rhythm, keep building on this.",
        "You’re doing well, keep refining it.",
        "Clean execution, that’s coming together.",
        "Good control, you’re handling this smoothly.",
        "Nice progress, keep the same energy.",
        "You’re locked in, keep moving forward.",
    ]
    return lines[index % len(lines)]


def update_summary(existing_summary: str, new_comment: str, limit: int = 400) -> str:
    merged = f"{existing_summary} {new_comment}".strip()
    if len(merged) <= limit:
        return merged
    return merged[-limit:]


class VoiceSpeaker:
    def __init__(
        self,
        enabled: bool,
        rate: int,
        volume: float,
        gender: str,
        name_hint: str,
        backend: str,
    ) -> None:
        self.enabled = enabled
        self.rate = rate
        self.volume = max(0.0, min(1.0, volume))
        self.gender = gender
        self.name_hint = name_hint.lower()
        self.backend = backend
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=1)
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._ensure_running()

    def _ensure_running(self) -> None:
        if not self.enabled:
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while self.enabled:
            text = self._queue.get()
            if text is None:
                return
            try:
                self._speak_text(text)
            except Exception as exc:
                print(f"Voice playback error: {exc}")

    def _speak_text(self, text: str) -> None:
        # Windows PowerShell SpeechSynthesizer is more stable than long-lived pyttsx3 loops.
        if self.backend == "powershell" and sys.platform.startswith("win"):
            try:
                self._speak_with_powershell(text)
            except Exception:
                self._speak_with_pyttsx3(text)
            return
        self._speak_with_pyttsx3(text)

    def _speak_with_powershell(self, text: str) -> None:
        normalized = (
            text.replace("’", "'")
            .replace("“", "\"")
            .replace("”", "\"")
            .replace("—", "-")
            .replace("–", "-")
        )
        safe_text = normalized.replace("'", "''")
        safe_hint = self.name_hint.replace("'", "''")
        gender_token = "Female" if self.gender == "female" else "Male"
        sapi_rate = int(max(-10, min(10, round((self.rate - 180) / 8))))
        sapi_volume = int(max(0, min(100, round(self.volume * 100))))
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$synth=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$voices=$synth.GetInstalledVoices()|ForEach-Object{$_.VoiceInfo};"
            "$selected=$null;"
            f"if('{safe_hint}' -ne ''){{$selected=$voices|Where-Object{{$_.Name -like '*{safe_hint}*'}}|Select-Object -First 1;}}"
            f"if(-not $selected){{$selected=$voices|Where-Object{{$_.Gender -eq '{gender_token}'}}|Select-Object -First 1;}}"
            "if($selected){$synth.SelectVoice($selected.Name)};"
            f"$synth.Rate={sapi_rate};$synth.Volume={sapi_volume};"
            f"$synth.Speak('{safe_text}');"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=25,
        )

    def _speak_with_pyttsx3(self, text: str) -> None:
        import pyttsx3
        engine = pyttsx3.init()
        self._configure_voice(engine)
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)
        engine.say(text)
        engine.runAndWait()
        try:
            engine.stop()
        except Exception:
            pass

    def _configure_voice(self, engine) -> None:
        voices = engine.getProperty("voices") or []
        if not voices:
            return

        if self.name_hint:
            for voice in voices:
                name = (getattr(voice, "name", "") or "").lower()
                if self.name_hint in name:
                    engine.setProperty("voice", voice.id)
                    return

        if self.gender == "female":
            female_tokens = ("female", "zira", "hazel", "susan", "aria", "eva", "sara", "jenny")
            for voice in voices:
                blob = f"{getattr(voice, 'name', '')} {getattr(voice, 'id', '')}".lower()
                if any(token in blob for token in female_tokens):
                    engine.setProperty("voice", voice.id)
                    return

        if self.gender == "male":
            male_tokens = ("male", "david", "mark", "james", "guy")
            for voice in voices:
                blob = f"{getattr(voice, 'name', '')} {getattr(voice, 'id', '')}".lower()
                if any(token in blob for token in male_tokens):
                    engine.setProperty("voice", voice.id)
                    return

    def say(self, text: str) -> None:
        if not self.enabled or not text:
            return
        self._ensure_running()

        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass

        try:
            self._queue.put_nowait(text)
        except queue.Full:
            pass

    def stop(self) -> None:
        if not self.enabled:
            return
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            try:
                _ = self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(None)
        if self._thread is not None:
            self._thread.join(timeout=1.5)


def run() -> None:
    settings = load_settings()
    # Always start each run as a fresh session with no carried context.
    settings.use_context_memory = False
    api_key = os.getenv("OPENAI_API_KEY")

    if settings.provider not in {"openai", "ollama"}:
        print("Invalid PROVIDER. Use 'openai' or 'ollama'.")
        sys.exit(1)

    if settings.provider == "openai":
        if not api_key:
            print("Missing OPENAI_API_KEY. Copy .env.example to .env and set your key.")
            sys.exit(1)
        client = OpenAI(api_key=api_key)
    else:
        client = None

    summary = ""
    last_comment = ""
    speaker = VoiceSpeaker(
        enabled=settings.voice_enabled,
        rate=settings.voice_rate,
        volume=settings.voice_volume,
        gender=settings.voice_gender,
        name_hint=settings.voice_name_hint,
        backend=settings.voice_backend,
    )
    speaker.start()
    ptt = PushToTalkInput(
        enabled=settings.voice_input_enabled,
        always_listen=settings.always_listen,
        ptt_key=settings.ptt_key,
        model_path=settings.vosk_model_path,
        vad_silence_seconds=settings.vad_silence_seconds,
        vad_rms_threshold=settings.vad_rms_threshold,
        min_voice_words=settings.min_voice_words,
        min_voice_chars=settings.min_voice_chars,
    )
    ptt.start()
    chat = TerminalChatInput(enabled=True)
    chat.start()
    comment_count = 0
    forced_count = 0
    name_cooldown_remaining = 0
    recent_comments: deque[str] = deque(maxlen=settings.repetition_window)
    last_output_time = time.time()

    print("AI Companion started. Press Ctrl+C to stop.")
    print(
        f"Provider: {settings.provider} | Model: {settings.model_name} | "
        f"Monitor: {settings.monitor_index} | Every: {settings.frame_interval_seconds}s"
    )
    if settings.provider == "ollama":
        print(f"Ollama URL: {settings.ollama_base_url}")
    print(f"Allow silent: {settings.allow_silent} | Heartbeat: every {settings.heartbeat_seconds}s")
    print(f"Use agent names: {settings.use_agent_names} | Name cooldown: {settings.name_mention_cooldown}")
    print(f"Speak on events only: {settings.speak_on_events_only}")
    print(f"Use context memory: {settings.use_context_memory}")
    print("[chat] type /help for live chat commands")
    if ptt.ready:
        if settings.always_listen:
            print(
                "Voice input: on (always listening) | "
                f"VAD silence: {settings.vad_silence_seconds}s | threshold: {settings.vad_rms_threshold}"
            )
        else:
            print(f"Voice input: on (push-to-talk `{settings.ptt_key}`)")
    else:
        print("Voice input: off")
    if settings.voice_enabled:
        print(
            f"Voice: on ({settings.voice_gender}/{settings.voice_backend}) | "
            f"Rate: {settings.voice_rate} | Volume: {settings.voice_volume} | "
            f"Speak every {settings.speak_every_n_comments} comment(s)"
        )
    else:
        print("Voice: off")

    try:
        while True:
            started = time.time()

            try:
                frame_base64, frame_image = capture_frame_data(
                    monitor_index=settings.monitor_index,
                    max_width=settings.max_width,
                    jpeg_quality=settings.jpeg_quality,
                )
                kill_banner_score = detect_kill_banner_score(frame_image) if settings.kill_banner_hint_enabled else 0.0
                kill_banner_hint = kill_banner_score >= settings.kill_banner_conf_threshold
                for command, value in chat.pop_commands():
                    if command == "tone" and value in {"hype", "coach", "chill"}:
                        settings.companion_tone = value
                        print(f"[chat] tone set to {settings.companion_tone}")
                    elif command == "silent" and value in {"on", "off"}:
                        settings.allow_silent = value == "on"
                        print(f"[chat] allow_silent set to {settings.allow_silent}")
                    elif command == "speak":
                        try:
                            n = max(1, int(value))
                            settings.speak_every_n_comments = n
                            print(f"[chat] speak_every_n_comments set to {n}")
                        except ValueError:
                            print("[chat] invalid /speak value; use integer >= 1")
                    elif command == "status":
                        print(
                            f"[chat] tone={settings.companion_tone} "
                            f"allow_silent={settings.allow_silent} "
                            f"speak_every={settings.speak_every_n_comments}"
                        )
                latest_chat_message = chat.pop_latest_text()
                latest_voice_message = ptt.pop_latest_text()
                latest_user_message = latest_chat_message or latest_voice_message

                if settings.provider == "openai":
                    comment = request_commentary(
                        client=client,
                        model_name=settings.model_name,
                        previous_summary=summary,
                        last_comment=last_comment,
                        companion_tone=settings.companion_tone,
                        allow_silent=settings.allow_silent,
                        kill_banner_hint=kill_banner_hint,
                        latest_user_message=latest_user_message,
                        frame_base64=frame_base64,
                        max_output_tokens=settings.max_output_tokens,
                    )
                else:
                    comment = request_commentary_ollama(
                        base_url=settings.ollama_base_url,
                        model_name=settings.model_name,
                        previous_summary=summary,
                        last_comment=last_comment,
                        companion_tone=settings.companion_tone,
                        allow_silent=settings.allow_silent,
                        kill_banner_hint=kill_banner_hint,
                        latest_user_message=latest_user_message,
                        frame_base64=frame_base64,
                    )

                if latest_user_message:
                    if comment == "SILENT" or not is_direct_reply_to_user(comment, latest_user_message):
                        comment = build_direct_user_reply(latest_user_message)

                if is_repetitive_comment(comment, last_comment, settings.min_novelty_ratio) or is_repetitive_against_history(
                    comment, recent_comments, settings.min_novelty_ratio
                ):
                    if not is_kill_comment(comment):
                        comment = "SILENT" if settings.allow_silent else fallback_comment(forced_count)

                if is_hard_repeat(comment, recent_comments, settings.repetition_similarity_threshold):
                    if not is_kill_comment(comment):
                        comment = "SILENT" if settings.allow_silent else fallback_comment(forced_count + 3)

                if comment != "SILENT":
                    if contains_agent_name(comment):
                        if (not settings.use_agent_names) or name_cooldown_remaining > 0:
                            comment = sanitize_agent_names(comment, use_agent_names=False)
                        else:
                            name_cooldown_remaining = settings.name_mention_cooldown
                    else:
                        if name_cooldown_remaining > 0:
                            name_cooldown_remaining -= 1

                    forced_count += 1
                    summary = update_summary(summary, comment)
                    if not settings.use_context_memory:
                        summary = ""
                    last_comment = comment
                    recent_comments.append(comment)
                    comment_count += 1
                    stamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{stamp}] {comment}")
                    last_output_time = time.time()
                    should_speak = (comment_count % settings.speak_every_n_comments == 0)
                    if settings.speak_on_events_only:
                        should_speak = is_event_comment(comment)
                    if should_speak:
                        speaker.say(comment)
                else:
                    now = time.time()
                    if settings.heartbeat_seconds > 0 and (now - last_output_time) >= settings.heartbeat_seconds:
                        stamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{stamp}] ...watching")
                        last_output_time = now

            except Exception as exc:
                stamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{stamp}] error: {exc}")

            elapsed = time.time() - started
            time.sleep(max(0, settings.frame_interval_seconds - elapsed))

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        chat.stop()
        ptt.stop()
        speaker.stop()


if __name__ == "__main__":
    run()
