import logging
import os
from src_livekit.agent.assistant import entrypoint, prewarm
from livekit import agents

logger = logging.getLogger("app")

if __name__ == '__main__':
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))