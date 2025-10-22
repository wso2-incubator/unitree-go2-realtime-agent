# Realtime Voice Agent for Robots (WSO2Con / Unitree Go2 Example)

A real-time voice agent for robots, built for the Unitree Go2 Edu and runnable on the Jetson expansion module. The agent integrates LiveKit with OpenAI-compatible STT, LLM, and TTS endpoints (either OpenAI’s Realtime API or locally hosted OpenAI-compatible services). Example local components include optimized STT, small open-source LLMs, and open TTS endpoints served via FastAPI — these can be added by setting base URLs in the config (e.g., LLM(base_url=<ip>)). Jetson Orin NX 16GB is sufficient when not running ROS for autonomous navigation.

Refer to LiveKit agents documentation for agent-specific details: https://docs.livekit.io/agents/

A real-time voice agent for the Unitree Go2 Edu, runnable on the Jetson expansion module. Current development uses OpenAI services as follows:
- OpenAI STT for wake-word detection,
- OpenAI Realtime API for conversation,
- OpenAI TTS for predefined audio generation.

Because the intended deployment target is an NVIDIA Jetson Orin NX (16GB), these cloud services can be replaced by locally-hosted, OpenAI-compatible endpoints to avoid latency. To use a local model, expose an OpenAI-compatible FastAPI endpoint and set its base_url in the assistant config (example):
```py
# example usage in configs/agent_config.py
stt = openai.STT(base_url="http://192.168.1.10:8000")
llm = openai.Realtime(base_url="http://192.168.1.11:8000")
tts = openai.TTS(base_url="http://192.168.1.12:8000")
```
Note: the highly optimized models used during development are tuned for NVIDIA GPUs and are not publicly available.

## Features

- Real-time speech interaction with STT, LLM, and TTS (local or cloud)
- Modular persona and tool configuration (see configs/agent_config.py)
- Uses streaming Realtime APIs supported by LiveKit
- Extensible for different robots, events, and conference scenarios
- Wake-word detection and conversational session switching

## Requirements

- Linux (tested)
- uv (for running scripts)
- LiveKit Server (use `livekit-server --dev` for development)
- Python 3.10+

## Installation

1. Install LiveKit CLI and start a local server:
   ```bash
   curl -sSL https://get.livekit.io | bash
   livekit-server --dev
   ```

2. In another terminal, download prepackaged files used by the agent:
   ```bash
   uv run main-livekit.py download-files
   ```

## Usage

1. Copy `.env.example` to `.env` and set your OpenAI-compatible API keys / endpoints.
2. Configure the agent persona, tools and endpoints in `configs/agent_config.py`.
3. Run the mock Conference Service (WSO2Con example):
   ```bash
   uv run tools/conference_service.py
   ```
4. (Optional) Configure and start the Unitree Go2 control service — see the Robot Control section below.
5. Start the LiveKit agent console:
   ```bash
   uv run main-livekit.py console
   ```

Controls:
- Speak the configured wake word when the agent indicates "Listening for wake words".
- To quit the LiveKit console mode use Ctrl+C (the in-app "Q" quit is not functional when running in console mode).

## Customization

- Persona & instructions: edit `configs/agent_config.py`.
- Tools: add/modify tool definitions in `configs/agent_config.py` and implement tool handlers in `tools/`.
- Event data: place markdown or data files in `data/` for lookups.
- Mock APIs: `tools/conference_service.py` contains a WSO2Con mock agenda and speaker endpoints.


## File Structure

unitree-go2-realtime-agent/
├── .env.example                 # Example environment variables file
├── .env                         # Environment variables file (user-specific)
├── .gitignore                   # Git ignore rules
├── LICENSE                      # Apache 2.0 license file
├── [README.md]                  # This README file
├── [issue_template.md]          # Issue template for GitHub
├── [main-livekit.py]            # Main entry point for LiveKit agent
├── [pull_request_template.md]   # Pull request template for GitHub
├── [pyproject.toml]             # Project configuration (dependencies, etc.)
├── data/                        # Markdown files for WSO2 product information
├── robot_controller/            # Unitree Go2 robot control service
└── src_livekit/                 # LiveKit agent source code
    ├── agent/
    │   └── [assistant.py]       # Main agent implementation
    ├── configs/
    │   └── [agent_config.py]    # Agent configuration (persona, tools, endpoints)
    └── tools/
        ├── [conference_service.py] # Mock conference service implementation
        └── [info_lookup.py]     # Tool for looking up WSO2 product info

# Unitree Go2 Control Service(for robot control) - Python 3.11.9 recommended


This is a concurrency-safe Flask server implementation for the Unitree Go2 Python SDK. It has been tested on the Unitree Go2 Edu version. The server can be run from an external computer (with the network interface configured appropriately), directly on the Jetson module (using network interface `eth0`), or in test mode (without a Unitree Go2 robot).

## Setup (Run as separate terminal)

### 1. Install the Unitree SDK
If you encounter issues, refer to the [Unitree SDK website](https://github.com/unitreerobotics/unitree_sdk2_python).

```bash
cd robot_controller
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
python -m venv .venv
source .venv/bin/activate
pip3 install -e .
cd ..
```

### 2. Install requirements

```bash
pip3 install -r requirements.txt
```


### 3. Start the Robot Control Service

```bash
python3 control_service.py <network_interface>
# Example: python3 control_service.py eth0
# Or for test mode: python3 control_service.py test
```

### 4. Start the Conference Service
```bash
python conference_service.py
```

### FAQ
**Q1: Error when running `pip3 install -e .`:**
```
Could not locate cyclonedds. Try to set CYCLONEDDS_HOME or CMAKE_PREFIX_PATH
```
This error means the cyclonedds path could not be found. First, compile and install cyclonedds:

```bash
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x 
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
```

Then, set `CYCLONEDDS_HOME` and install the SDK:

```bash
cd ~/unitree_sdk2_python
export CYCLONEDDS_HOME="~/cyclonedds/install"
pip3 install -e .
```

## License

Apache 2.0 — see `LICENSE` file.

# Credits

- This project is built on an example from LiveKit's [Realtime Voice Agent](https://github.com/livekit/agents/tree/main/examples).

## Roadmap (short)
- Add Intel/NVidia RealSense-based realtime face detection and pose stream integration.
- Per-speaker voice recognition (speaker ID model) and speaker-specific personalization.
- Local small LLM fallback for offline/low-latency scenarios.
- ROS integration for autonomous navigation + voice-assisted commands.
- On-device optimized wake-word detector with lower-power model variants.
- Implement a virtual avatar based UI server for visual feedback during conversations.