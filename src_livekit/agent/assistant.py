import json
import logging
import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import AsyncIterable, Optional
import re
import asyncio

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    metrics,
    UserStateChangedEvent,
)

from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

from ..configs import agent_config

logger = logging.getLogger("voice-assistant")
load_dotenv()

class WakeupAgent(Agent):
    """Agent specialized for wake word detection using Self Hosted STT or Just by OpenAI"""
    
    def __init__(self) -> None:

        self.wake_words = agent_config.wakeup_words

        super().__init__(
            instructions=agent_config.wakeup_agent_instructions,
            stt=openai.STT(),  # use a openai compatible STT locally. 
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
    """Agent specialized for conversation handling using OpenAI STT for accuracy"""
    
    def __init__(self, initial_query: str = "") -> None:

        self.initial_query = initial_query
        
        super().__init__(
            instructions=agent_config.conversational_agent_instructions,
            # stt=openai.STT(), 
            llm=openai.realtime.RealtimeModel(voice=agent_config.voice),
            tts=openai.TTS(voice=agent_config.voice),  
            tools=agent_config.tools,
        )

    async def on_enter(self):
        logger.info("ConversationalAgent activated")
        #logger.info(f"User identified as: {self.user_name}") #Future Integration with Face Recognition
    

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

    usage_collector = metrics.UsageCollector()
    inactivity_task: asyncio.Task | None = None

    async def handle_inactivity():
        """Handle inactivity by switching back to WakeupAgent"""
        logger.info(f"User has been inactive for {agent_config.user_away_timeout_seconds} seconds - switching back to WakeupAgent")
        
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