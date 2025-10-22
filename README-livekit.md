# Realtime Voice Agent for Robots (WSO2Con/Unitree Go2 Example)

A real-time voice agent that can be run on robots. This was specifically made for the Unitree Go2 Edu and can run natively on the Jetson Expansion module. The voice agent is built using OpenAI’s Realtime API, STT, LLM, TTS services that LiveKit supports, or any local hosted OpenAI-compatible services. For example (STT: Optimized Whisper for realtime performance by myself—it is not publicly available due to its value in realtime needs; LLM as open-source models under 2B; TTS as open-source TTS; all are FastAPI-based OpenAI-compatible endpoints). Then we can easily add with LLM(base_url=<ip>) likewise. Jetson Orin NX 16GB is enough if not using ROS for autonomous navigation. This project is easily customizable for any event, robot, or use case, and includes WSO2Con-specific mock data for demonstration. A very advanced voice agent can be built with local models and run on the robot itself. Please refer to [LiveKit documentation](https://docs.livekit.io/agents/) for more details.

## Features

- Real-time performance with fully locally hosted STT, LLM, TTS, or any OpenAI-compatible services.
- Modular, customizable tools and persona config (see [`configs/agent_config.py`](configs/agent_config.py)).
- Uses OpenAI's streaming Realtime API or any services LiveKit supports.
- Easily extensible for any robot, event, or conference.
- Supports wake word detection and conversational switching.

## Requirements

- Tested on Linux.
- UV (for dependency management).
- LiveKit Server (run via `livekit-server --dev` for development).
- Python 3.10+.

## Installation

1. Install LiveKit CLI and server:
   ```bash
   curl -sSL https://get.livekit.io | bash
   livekit-server --dev
   ```

2. In another terminal, download the necessary files and run the console:
   ```bash
   uv run main-livekit.py download-files
   uv run main-livekit.py console
   ```

## Usage

1. Copy `.env.example` to `.env` and fill in your OpenAI API key.
2. Edit `agent_config.py` to set your agent's persona, event, and tool configuration.
3. Run the Conference Service in `tools/` (Run `python conference_service.py` for WSO2Con mock example).
4. Setup the Unitree Go2 Control Service (Optional - Refer to instructions below)
5. Run the app:

   ```bash
   uv run main-livekit.py console
   ```

**Controls:**
Say the wakeup word after it say Listening for wake words

## Customization

- **Persona & Instructions:** Edit `agent_config.py` to set the agent's name, event, and instructions.
- **Tools:** Add or modify tools in `agent_config.py` and implement their logic in `tools/`.
- **Event Data:** Place markdown or data files in `data/` for info lookup.
- **Mock Conference API:** See `tools/conference_service.py` for a WSO2Con mock agenda and speaker API.


## File Structure


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

- This project is built on an example from OpenAI: https://github.com/openai/openai-python/blob/main/examples/realtime/push_to_talk_app.py