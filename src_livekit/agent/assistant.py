import json
import logging
import os
import sys
import asyncio
import aiohttp
import re
from typing import AsyncIterable, Optional, Dict, Any
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    UserStateChangedEvent,
    RunContext,
    function_tool,
    metrics,
    CloseEvent,
)

from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

from ..configs import agent_config
from ..tools.info_lookup import load_all_docs, find_relevant_info

logger = logging.getLogger("voice-assistant")
load_dotenv()

conf_api_base_url = os.environ.get("CONF_API_BASE_URL")
robot_service_host = os.environ.get("ROBOT_SERVICE__HOST")

class WakeupAgent(Agent):
    """Agent specialized for wake word detection using Vosk (self-hosted STT)"""
    
    def __init__(self) -> None:

        self.wake_words = agent_config.wakeup_words

        super().__init__(
            instructions=agent_config.wakeup_agent_instructions,
            stt=openai.STT(language=agent_config.wakeup_agent_language),  # use a openai compatible STT locally otherwise it takes openai service. 
            tts=openai.TTS(voice=agent_config.voice),
        )

    async def on_enter(self):
        logger.info("WakeupAgent activated - listening for wake words")
        self.session.say("Hello There! Please say the wake word when you're ready.")

    def stt_node(
        self,
        audio: AsyncIterable[str],
        model_settings: Optional[dict] = None
    ) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(audio, model_settings)

        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text.lower()
                    logger.info(f"WakeupAgent received transcript: '{transcript}'")

                    cleaned_transcript = re.sub(r'[^\w\s]', '', transcript)
                    cleaned_transcript = ' '.join(cleaned_transcript.split())
                    logger.info(f"Cleaned transcript: '{cleaned_transcript}'")

                    wake_word_found = False
                    for wake_word in self.wake_words:
                        if wake_word in cleaned_transcript:
                            logger.info(f"Wake word detected: '{wake_word}' - switching to ConversationalAgent")
                            wake_word_found = True
                            
                            content_after_wake_word = cleaned_transcript.split(wake_word, 1)[-1].strip()
                            
                            self.session.update_agent(ConversationalAgent(
                                initial_query=content_after_wake_word,
                            ))
                            return
                    
                    if not wake_word_found:
                        logger.debug(f"No wake word found in: '{cleaned_transcript}' - ignoring")
                        continue
                
                if not (hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT"):
                    yield event

        return process_stream()


class ConversationalAgent(Agent):
    """Agent specialized for conversation handling using OpenAI realtime model"""
    
    def __init__(self, initial_query: str = "") -> None:
        self.initial_query = initial_query
        
        super().__init__(
            instructions=agent_config.conversational_agent_instructions,
            llm=openai.realtime.RealtimeModel(voice=agent_config.voice),
            tts=openai.TTS(voice=agent_config.voice),
        )

    @function_tool(raw_schema=agent_config.tools[0])
    async def get_wso2_info(self, raw_arguments: Dict[str, Any], ctx: RunContext) -> str:
        """Get information about specific WSO2 products."""
        topic = raw_arguments.get("topic", "")
        logger.info(f"Looking up WSO2 info for topic: {topic}")
        
        docs = load_all_docs()
        return find_relevant_info(topic, docs)

    @function_tool(raw_schema=agent_config.tools[1])
    async def get_wso2con_speakers(self, raw_arguments: Dict[str, Any], ctx: RunContext) -> str:
        """Fetch information about WSO2Con speakers."""
        try:
            logger.info("Fetching WSO2Con speakers info via HTTP")
            base_url = conf_api_base_url
            if not base_url.startswith(('http://', 'https://')):
                base_url = f"http://{base_url}"
            
            url = f"{base_url}/speakers"
            logger.info(f"Making request to: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"WSO2Con speakers: {data}"
                    else:
                        error_data = await response.json()
                        return f"Speakers fetch failed: {error_data.get('error', 'Unknown error')}"
        except asyncio.TimeoutError:
            return "Request timed out for speakers info"
        except Exception as e:
            logger.exception(f"Exception during get_wso2con_speakers: URL was {url}")
            return f"Failed to fetch speakers: {e}"

    @function_tool(raw_schema=agent_config.tools[2])
    async def get_wso2con_agenda(self, raw_arguments: Dict[str, Any], ctx: RunContext) -> str:
        """Fetch agenda details for WSO2Con sessions."""
        try:
            logger.info("Fetching WSO2Con agenda info via HTTP")
            base_url = conf_api_base_url
            if not base_url.startswith(('http://', 'https://')):
                base_url = f"http://{base_url}"
            
            url = f"{base_url}/agenda"
            logger.info(f"Making request to: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"WSO2Con agenda: {data}"
                    else:
                        error_data = await response.json()
                        return f"Agenda fetch failed: {error_data.get('error', 'Unknown error')}"
        except asyncio.TimeoutError:
            return "Request timed out for agenda info"
        except Exception as e:
            logger.exception(f"Exception during get_wso2con_agenda: URL was {url}")
            return f"Failed to fetch agenda: {e}"

    @function_tool(raw_schema=agent_config.tools[3])
    async def take_photo(self, raw_arguments: Dict[str, Any], ctx: RunContext) -> str:
        """Command the Unitree Go2 robot to take a photo."""
        try:
            logger.info("Handling Go2 action via HTTP: take_photo")
            base_url = robot_service_host
            if not base_url.startswith(('http://', 'https://')):
                base_url = f"http://{base_url}"
            
            url = f"{base_url}/take_photo"
            logger.info(f"Making request to: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"Photo taken successfully! {data.get('status', '')}"
                    else:
                        error_data = await response.json()
                        return f"Failed to take photo: {error_data.get('error', 'Unknown error')}"
        except asyncio.TimeoutError:
            return "Request timed out for photo"
        except Exception as e:
            logger.exception(f"Exception during take_photo: URL was {url}")
            return f"Failed to take photo: {e}"

    @function_tool(raw_schema=agent_config.tools[4])
    async def control_go2(self, raw_arguments: Dict[str, Any], ctx: RunContext) -> str:
        """Send an action command to the Unitree Go2 robot."""
        action = raw_arguments.get("action", "")
        api_timeout = 60
        logger.info(f"Handling Go2 action via HTTP: {action}")
        
        base_url = robot_service_host
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"http://{base_url}"
        
        url = f"{base_url}/action/{action.lower()}"
        logger.info(f"Making request to: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=api_timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return f"Action '{action}' completed successfully! {data.get('status', '')}"
                    else:
                        error_data = await response.json()
                        return f"Action '{action}' failed: {error_data.get('error', 'Unknown error')}"
        except asyncio.TimeoutError:
            return f"Request timed out for action '{action}'"
        except Exception as e:
            logger.exception(f"Exception during control_go2 action: {action} URL was {url}")
            return f"Failed to perform '{action}': {e}"

    async def on_enter(self):
        logger.info("ConversationalAgent activated")
        await self.session.say("Hello! I'm Go2, your W S O 2 Con assistant robot. How can I help you today?")

    async def on_user_turn_completed(self, turn_ctx, new_message=None):
        result = await super().on_user_turn_completed(turn_ctx, new_message)
        logger.info("Turn completed - staying in conversation mode")
        return result

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    # proc.userdata["face_recognition"] = FaceRecognition.load() Future Integration for Face Recognition by Realsense Camera

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        turn_detection=EnglishModel(),
        resume_false_interruption=agent_config.resume_false_interruption,
        false_interruption_timeout=agent_config.false_interruption_timeout,
        min_interruption_duration=agent_config.min_interruption_duration,
        user_away_timeout=float(agent_config.user_away_timeout_seconds),  
    )
    
    @session.on("close")
    def on_close(ev: CloseEvent):
        """This function is called when the session is closed, for any reason."""
        logger.info(f"Agent session closed, reason: {ev.reason}")
        if os.name != 'nt':
            os.system('stty sane')
    
    usage_collector = metrics.UsageCollector()
    inactivity_task: asyncio.Task | None = None

    async def handle_inactivity():
        """Handle inactivity by switching back to WakeupAgent"""
        logger.info("User has been inactive for 30 seconds - switching back to WakeupAgent")
        
        try:
            current_agent = session._agent
            
            if isinstance(current_agent, ConversationalAgent):
                logger.info("Switching from ConversationalAgent to WakeupAgent due to inactivity")
                await session.say("Going back to listening for wake words.")
                
                await asyncio.sleep(2)
                
                session.update_agent(WakeupAgent())
            else:
                logger.debug("Already in WakeupAgent, no switch needed")
                
        except Exception as e:
            logger.error(f"Error during inactivity handling: {e}")

    @session.on("user_state_changed")
    def _user_state_changed(ev: UserStateChangedEvent):
        nonlocal inactivity_task
        logger.info(f"User state changed to: {ev.new_state}")

        current_agent = session._agent

        if ev.new_state == "away":
            if inactivity_task is None and isinstance(current_agent, ConversationalAgent):
                logger.info("User went away - starting inactivity task")
                inactivity_task = asyncio.create_task(handle_inactivity())
            return

        if inactivity_task is not None:
            logger.info("User is active again - cancelling inactivity task")
            inactivity_task.cancel()
            inactivity_task = None

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    await session.start(
        agent=WakeupAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(audio_sample_rate=agent_config.input_sample_rate),
        room_output_options=RoomOutputOptions(audio_sample_rate=agent_config.output_sample_rate),
    )