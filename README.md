
# Realtime Voice Agent for Robots (WSO2Con/Unitree Go2 Example)


A real-time, voice agent that can be run on robots. This was specifically made for the Unitree Go 2 Edu, and can run natively on the Jetson Expansion module. The voice agent is built using OpenAI’s Realtime API, with a Textual TUI and modular tool integration. This project is easily customizable for any event, robot, or use case, and includes WSO2Con-specific mock data for demonstration.


## Features

- Real-time transcription and voice response on a Textual Interface (TUI)
- Modular, customizable tools and persona config (see `config.py`)
- Uses OpenAI's streaming Realtime API
- Easily extensible for any robot, event, or conference


## Requirements

- Python 3.9+ (Python 3.11.9 recommended)
- MacOS: `brew install portaudio ffmpeg`
- Ubuntu: `sudo apt install portaudio19-dev python3-pyaudio`
- Environment variable: `OPENAI_API_KEY` (see `.env.example`)


## Installation

```bash
git clone <this-repo-url>
cd <repo-folder>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


## Usage

1. Copy `.env.example` to `.env` and fill in your OpenAI API key.
2. Edit `config.py` to set your agent's persona, event, and tool configuration.
3. Run the Conference Service in `tools/` (Run `python conference_service.py` for WSO2Con mock example).
4. Setup the Unitree Go2 SDK Server (Optional - Refer to instructions below)
5. Run the app:

```bash
python main.py
```

**Controls:**
- Press `K` to start/stop recording (push-to-talk)
- Press `Q` to quit

## Customization

- **Persona & Instructions:** Edit `config.py` to set the agent's name, event, and instructions.
- **Tools:** Add or modify tools in `config.py` and implement their logic in `tools/`.
- **Event Data:** Place markdown or data files in `data/` for info lookup.
- **Mock Conference API:** See `tools/con_api.py` for a WSO2Con mock agenda and speaker API.


## File Structure

- `main.py` — App entry point
- `audio_util.py` — Audio streaming utilities
- `tools/` — Info lookup and event API helpers (see `conference_service.py` for mock WSO2Con)
- `data/` — Static markdown data
- `styles/cli.css` — Custom styling for the TUI
- `.env.example` — Sample environment config

# Unitree Go2 SDK Flask Server (for robot control) - Python 3.11.9 recommended


This is a concurrency-safe Flask server implementation for the Unitree Go2 Python SDK. It has been tested on the Unitree Go2 Edu version. The server can be run from an external computer (with the network interface configured appropriately), directly on the Jetson module (using network interface `eth0`), or in test mode (without a Unitree Go2 robot).

## Setup (Run as separate terminal)

### 1. Install the Unitree SDK
If you encounter issues, refer to the [Unitree SDK website](https://github.com/unitreerobotics/unitree_sdk2_python).

```bash
cd sdk_controller
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


### 3. Start the Flask SDK Server

```bash
python3 sdk_server.py <network_interface>
# Example: python3 sdk_server.py eth0
# Or for test mode: python3 sdk_server.py test
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

MIT — see `LICENSE` file.


# Credits

- This project is built on an example from OpenAI: https://github.com/openai/openai-python/blob/main/examples/realtime/push_to_talk_app.py