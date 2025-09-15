from __future__ import annotations

import os
import json
import base64
import asyncio
import logging
from typing import Any, cast

import dotenv
import aiohttp

from typing_extensions import override

from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Button, Static, RichLog
from textual.reactive import reactive
from textual.containers import Container
from textual.containers import Horizontal, Vertical

from openai import AsyncOpenAI, OpenAI
from openai.types.beta.realtime.session import Session
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection

from tools.info_lookup import load_all_docs, find_relevant_info
from tools.con_api import fetch_event_agenda, fetch_speaker_info

from utils.audio_util import CHANNELS, SAMPLE_RATE, AudioPlayerAsync

from agent_config import (
    instructions,
    tools,
    turn_detection,
    model,
    voice,
    timeout,
    echo_cancellation,
    input_audio_noise_reduction,
    input_audio_transcription,
    temperature
)

# Load environment variables from .env file
dotenv.load_dotenv(override=True)

class ToolUseIndicator(Static):
    """A widget that shows the current tool being used."""

    tool_name = reactive("")

    @override
    def render(self) -> str:
        return f"Using tool: {self.tool_name} with parameters {self.tool_parameters}" if self.tool_name else "No tool in use"


class SessionDisplay(Static):
    """A widget that shows the current session ID."""

    session_id = reactive("")

    @override
    def render(self) -> str:
        return f"Session ID: {self.session_id}" if self.session_id else "Connecting..."


class AudioStatusIndicator(Static):
    """A widget that shows the current audio recording status."""

    is_recording = reactive(False)

    @override
    def render(self) -> str:
        status = (
            "🔴 Started Session - Recording... (Press K to stop)" if self.is_recording else "⚪ Press K to start recording (Q to quit)"
        )
        return status


class RealtimeApp(App[None]):
    CSS_PATH = "./styles/cli.css"

    client: AsyncOpenAI
    should_send_audio: asyncio.Event
    audio_player: AudioPlayerAsync
    last_audio_item_id: str | None
    connection: AsyncRealtimeConnection | None
    session: Session | None
    connected: asyncio.Event

    def __init__(self) -> None:
        super().__init__()
        self.connection = None
        self.session = None
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.audio_player = AudioPlayerAsync()
        self.last_audio_item_id = None
        self.should_send_audio = asyncio.Event()
        self.connected = asyncio.Event()
        self.server_url = f"http://localhost:{os.getenv('SDK_CONTROLLER_PORT', 5051)}"

    @override
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container():
            with Horizontal(id="top-bar"):
                yield SessionDisplay(id="session-display")
                yield AudioStatusIndicator(id="status-indicator")

            yield ToolUseIndicator(id="tool-use-indicator")
            with Vertical(id="log-pane"):
                input_log = RichLog(id="input-log", wrap=True,
                                    highlight=True, markup=True)
                input_log.write("[b][green]INPUT[/green][/b]\n")
                yield input_log

                output_log = RichLog(
                    id="output-log", wrap=True, highlight=True, markup=True)
                output_log.write("[b][cyan]OUTPUT[/cyan][/b]\n")
                yield output_log

    async def on_mount(self) -> None:
        # add try except block to handle connection errors
        try:
            logging.info("Mounting RealtimeApp...")
            self.run_worker(self.handle_realtime_connection())
            logging.info("Starting audio player...")
            self.run_worker(self.send_mic_audio())
            logging.info("Starting session restart timer...")
            self.run_worker(self.session_restart_timer(timeout=timeout))
        except Exception as e:
            logging.info(f"Error during mount: {e}")
            self.query_one(RichLog).write(f"Error during mount: {e}")

    async def handle_realtime_connection(self) -> None:

        async with self.client.beta.realtime.connect(model=model) as conn:
            self.connection = conn
            self.connected.set()

            await conn.session.update(session={"turn_detection": turn_detection,
                                               "instructions": instructions,
                                               "input_audio_noise_reduction": input_audio_noise_reduction,
                                               "input_audio_transcription": input_audio_transcription,
                                               "temperature": temperature,
                                               "voice": voice,
                                               "tools": tools})

            acc_items: dict[str, Any] = {}
            input_items: dict[str, Any] = {}

            async for event in conn:
                if event.type == "session.created":
                    self.session = event.session
                    session_display = self.query_one(SessionDisplay)
                    assert event.session.id is not None
                    session_display.session_id = event.session.id
                    logging.info("Connnected to session ID: %s",
                                 event.session.id if event.session else "No session")
                    continue

                if event.type == "session.updated":
                    self.session = event.session
                    continue
                if event.type == "session.error" or event.type == "session.expired" or event.type == "session.timeout":
                    logging.info(f"Session error: {event.error} type: {event.type}")
                
                if event.type == "error":
                    logging.error(f"Error: {event.error}")

                if event.type == "conversation.item.input_audio_transcription.delta":
                    # This is the delta of the audio transcription
                    try:
                        text = input_items[event.item_id]
                        input_text = input_items[event.item_id].lower()

                    except KeyError:
                        input_items[event.item_id] = event.delta
                    else:
                        input_items[event.item_id] = text + event.delta

                    input_pane = self.query_one("#input-log", RichLog)
                    input_pane.clear()
                    # clear audio buffer
                    # self.audio_player.clear()
                    input_pane.write(input_items[event.item_id])
                    logging.info(f"Input transcription delta: {input_items[event.item_id]}")
                    continue

                if event.type == "response.done":

                    if echo_cancellation == True:
                        # If echo cancellation is on then the mic audio has stopped, and should be resumed after playback
                        self.run_worker(self.resume_mic_after_playback())
                    for output in event.response.output:
                        logging.info(f"Response output: {output}")
                        if output.type == "function_call":
                            name = output.name
                            args = json.loads(output.arguments)
                            call_id = output.call_id

                            tool_use_indicator = self.query_one(
                                ToolUseIndicator)
                            tool_use_indicator.tool_name = name
                            tool_use_indicator.tool_parameters = args

                            logging.info(
                                f"Function call: {name} with args: {args} and call_id: {call_id}")
                            logging.info(
                                args["topic"] if "topic" in args else "No topic in args")
                            logging.info(type(args))

                            # Dispatch to your handler
                            if name == "get_wso2_info":
                                result = await self.handle_wso2_info(args["topic"])
                            elif name == "get_wso2con_info":
                                result = await self.handle_wso2con_info(args["topic"])
                            elif name == "control_go2":
                                result = await self.handle_go2_action(args["action"])
                            elif name == "take_photo":
                                result = await self.handle_take_photo()
                            else:
                                result = "Function not recognized."

                            # # Send function output back to GPT
                            await conn.send({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": json.dumps({"result": result})
                                }
                            })

                            # Trigger the assistant to respond with audio
                            await conn.response.create()

                if event.type == "response.audio_transcript.delta":
                    try:
                        text = acc_items[event.item_id]
                        spoken_text = acc_items[event.item_id].lower()
                        logging.info(f"Spoken text: {spoken_text}")
                        if any(phrase in spoken_text for phrase in ["understood, i'll be silent"]):
                            logging.info(
                                "voice command: Stop talking received.")
                            conn = await self._get_connection()
                            # stop generating audio
                            await conn.send({"type": "response.cancel"})
                            self.audio_player.clear()                      # stop playing buffered audio

                    except KeyError:
                        acc_items[event.item_id] = event.delta
                    else:
                        acc_items[event.item_id] = text + event.delta

                    # Clear and update the entire content because RichLog otherwise treats each delta as a new line
                    output_pane = self.query_one("#output-log", RichLog)
                    output_pane.clear()
                    # clear audio buffer
                    # self.audio_player.clear()
                    output_pane.write(acc_items[event.item_id])
                    continue

                if event.type == "response.audio.delta":
                    if event.item_id != self.last_audio_item_id:
                        self.audio_player.reset_frame_count()
                        self.last_audio_item_id = event.item_id
                        
                        if echo_cancellation == True:
                            # If echo cancellation is on then the mic audio should be paused during playback
                            self.should_send_audio.clear()

                    bytes_data = base64.b64decode(event.delta)
                    self.audio_player.add_data(bytes_data)
                    continue

    async def session_restart_timer(self, timeout=25 * 60):

        while True:
            await asyncio.sleep(timeout)  # 25 minutes
            log = self.query_one(RichLog)
            log.clear()
            log.write("Restarting session before timeout...")

            self.connected.clear()
            self.run_worker(self.handle_realtime_connection())

    async def resume_mic_after_playback(self):
        # Wait until audio player finishes playback
        while not self.audio_player.is_idle():
            await asyncio.sleep(0.1)
        # check if human is detected
        # Resume mic input
        self.should_send_audio.set()
        logging.info("Audio playback finished, resuming mic.")

    async def _get_connection(self) -> AsyncRealtimeConnection:
        await self.connected.wait()
        assert self.connection is not None
        return self.connection

    async def send_mic_audio(self) -> None:
        import sounddevice as sd  # type: ignore

        sent_audio = False

        device_info = sd.query_devices()
        print(device_info)

        read_size = int(SAMPLE_RATE * 0.02)

        stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype="int16",
        )
        stream.start()

        status_indicator = self.query_one(AudioStatusIndicator)

        try:
            while True:
                if stream.read_available < read_size:
                    await asyncio.sleep(0)
                    continue

                await self.should_send_audio.wait()
                status_indicator.is_recording = True

                data, _ = stream.read(read_size)

                connection = await self._get_connection()
                if not sent_audio:
                    asyncio.create_task(connection.send(
                        {"type": "response.cancel"}))
                    sent_audio = True

                await connection.input_audio_buffer.append(audio=base64.b64encode(cast(Any, data)).decode("utf-8"))

                await asyncio.sleep(0)
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()

    async def on_key(self, event: events.Key) -> None:
        """Handle key press events."""
        if event.key == "enter":
            self.query_one(Button).press()
            return

        if event.key == "q":
            self.exit()
            return

        if event.key == "k":
            status_indicator = self.query_one(AudioStatusIndicator)
            if status_indicator.is_recording:
                self.should_send_audio.clear()
                status_indicator.is_recording = False

                if self.session and self.session.turn_detection is None:
                    # The default in the API is that the model will automatically detect when the user has
                    # stopped talking and then start responding itself.
                
                    # However if we're in manual `turn_detection` mode then we need to
                    # manually tell the model to commit the audio buffer and start responding.
                    conn = await self._get_connection()
                    await conn.input_audio_buffer.commit()
                    await conn.response.create()
            else:
                self.should_send_audio.set()
                status_indicator.is_recording = True

    async def handle_wso2_info(self, topic: str) -> str:
        docs = load_all_docs()
        return find_relevant_info(topic, docs)
        # return f"WSO2 info about '{topic}': This is a placeholder response."

    async def handle_wso2con_info(self, topic: str) -> str:
        # Use the mock con_api for agenda and speaker info
        if topic == "event_agenda":
            agenda = await fetch_event_agenda()
            return f"Agenda: {agenda}"
        elif topic == "speakers":
            speakers = await fetch_speaker_info()
            return f"Speakers: {speakers}"
        else:
            return f"No event info API is configured. You asked about '{topic}'."
        
    async def handle_take_photo(self) -> str:
        try:
            logging.info(f"Handling Go2 action via HTTP: take_photo")
            url = f"{self.server_url}/take_photo"
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"Photo succeeded: {data.get('result')}"
                    else:
                        error_data = await response.json()
                        return f"Photo failed: {error_data.get('error', 'Unknown error')}"
        except asyncio.TimeoutError:
            return f"Request timed out for photo'"
        except Exception as e:
            logging.exception("Exception during handle_go2_action")
            return f"Failed to take photo: {e}"
        
    async def handle_go2_action(self, action: str) -> str:
        api_timeout = 60
        logging.info(f"Handling Go2 action via HTTP: {action}")
        url = f"{self.server_url}/action/{action.lower()}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=api_timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"Action '{action}' succeeded: {data.get('result')}"
                    else:
                        error_data = await response.json()
                        return f"Action '{action}' failed: {error_data.get('error', 'Unknown error')}"
        except asyncio.TimeoutError:
            return f"Request timed out for action '{action}'"
        except Exception as e:
            logging.exception("Exception during handle_go2_action")
            return f"Failed to perform '{action}': {e}"

# Configure logging
logging.basicConfig(
    filename="main-debug.log",
    filemode='w',  # Overwrites the log file each run
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

if __name__ == "__main__":
    logging.info("Starting RealtimeApp")
    app = RealtimeApp()
    app.run()