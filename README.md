# AI companion

AI companion that watches your screen and comments in real time

## Overview
This repository contains the implementation, configuration, and supporting assets for this project.

## Features
- Core project functionality (see source files for detailed modules)

## Tech Stack
- Python

## Project Structure
- `docs/`

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## Configuration
Create a `.env` file (or equivalent) and configure keys like:

- `OPENAI_API_KEY`
- `PROVIDER`
- `OLLAMA_BASE_URL`
- `MONITOR_INDEX`
- `VOICE_ENABLED`
- `VOICE_GENDER`
- `VOICE_NAME_HINT`
- `VOICE_RATE`
- `VOICE_VOLUME`
- `HEARTBEAT_SECONDS`
- `VOICE_BACKEND`
- `NAME_MENTION_COOLDOWN`
- `USE_AGENT_NAMES`
- `SPEAK_ON_EVENTS_ONLY`
- `KILL_BANNER_CONF_THRESHOLD`
- `COMPANION_TONE`
- `KILL_BANNER_HINT_ENABLED`
- `USE_CONTEXT_MEMORY`
- `REPETITION_SIMILARITY_THRESHOLD`
- `FRAME_INTERVAL_SECONDS`

## Contributing
Contributions are welcome. Please open an issue for major changes before submitting a PR.

## License
Add your project license details here.

---

## Legacy Notes

# AI companion

AI companion that watches your screen and comments in real time

## Overview
This repository contains the implementation, configuration, and supporting assets for this project.

## Features
- Core project functionality (see source files for detailed modules)

## Tech Stack
- Python

## Project Structure
- `docs/`

## Quick Start
```bash
pip install -r requirements.txt
python main.py
```

## Configuration
Create a `.env` file (or equivalent) and configure keys like:

- `OPENAI_API_KEY`
- `PROVIDER`
- `OLLAMA_BASE_URL`
- `MONITOR_INDEX`
- `VOICE_ENABLED`
- `VOICE_GENDER`
- `VOICE_NAME_HINT`
- `VOICE_RATE`
- `VOICE_VOLUME`
- `HEARTBEAT_SECONDS`
- `VOICE_BACKEND`
- `NAME_MENTION_COOLDOWN`
- `USE_AGENT_NAMES`
- `SPEAK_ON_EVENTS_ONLY`
- `KILL_BANNER_CONF_THRESHOLD`
- `COMPANION_TONE`
- `KILL_BANNER_HINT_ENABLED`
- `USE_CONTEXT_MEMORY`
- `REPETITION_SIMILARITY_THRESHOLD`
- `FRAME_INTERVAL_SECONDS`

## Contributing
Contributions are welcome. Please open an issue for major changes before submitting a PR.

## License
Add your project license details here.

---

## Legacy Notes

# AI Companion (Gameplay Watcher)

This app watches your game screen and generates live commentary with optional voice output.

## Local unlimited-cost path (recommended)
Use Ollama with a local vision model so there is no per-request API billing.

1. Install Ollama: `https://ollama.com/download`
2. Pull a vision model:
   ```bash
   ollama pull qwen2.5vl:3b
   ```
3. Start Ollama server (if not auto-running):
   ```bash
   ollama serve
   ```
4. In `.env` set:
   - `PROVIDER=ollama`
   - `MODEL_NAME=qwen2.5vl:3b`

## Setup
1. Create and activate your virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and tune values.

## Run
```bash
python main.py
```

## Smart comments
The model can now stay quiet. If nothing meaningful changed, it returns `SILENT` and the app does not print/speak.
Repeated near-duplicate comments are also suppressed using `MIN_NOVELTY_RATIO`.
Set `COMPANION_TONE=hype` for human-like energetic lines such as quick praise/callouts.
Agent names are disabled by default for cleaner second-person commentary.

## Voice settings
- `VOICE_ENABLED=true`
- `VOICE_GENDER=female` (or `male`)
- `VOICE_NAME_HINT=zira` (optional, strongly recommended on Windows)
- `VOICE_RATE=185`
- `VOICE_VOLUME=1.0`
- `SPEAK_EVERY_N_COMMENTS=1`
- `MIN_NOVELTY_RATIO=0.86` (higher = fewer repeated comments)

## Push-To-Talk Input
- `VOICE_INPUT_ENABLED=true`
- `PTT_KEY=f8` (hold this key while speaking)
- `VOSK_MODEL_PATH=models/vosk-model-small-en-us-0.15`
- Download a Vosk model and place it in the path above: https://alphacephei.com/vosk/models

## Live Text Chat
While `main.py` is running, type in the same terminal:
- `/say <message>`: send a text message to the companion
- `/tone hype|coach|chill`: switch tone live
- `/silent on|off`: toggle silent mode live
- `/speak <n>`: speak every `n` comments
- `/status`: print current runtime chat/tone settings
- plain text (without `/say`) is treated as a message

## Key settings
- `PROVIDER=openai|ollama`
- `MODEL_NAME=<model name>`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `FRAME_INTERVAL_SECONDS=1`
- `COMPANION_TONE=hype|coach|chill`
- `USE_AGENT_NAMES=false` (recommended)
- `NAME_MENTION_COOLDOWN=5` (when names are enabled)

## Notes
- 1-second loop is best effort; slower hardware/model means lower effective rate.
- For lower latency, reduce `MAX_WIDTH` and `JPEG_QUALITY`.

## Overview
AI companion that watches your screen and comments in real time

## Tech Stack
- Python

## Quick Start
```bash
pip install -r requirements.txt
```

## Project Structure
- `docs/`

## Contributing
Contributions are welcome. Open an issue or submit a pull request.
