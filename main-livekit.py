import logging
import os
import signal
import sys
from src_livekit.agent.assistant import entrypoint, prewarm
from livekit import agents

logger = logging.getLogger("app")

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully exit and restore terminal."""
    logger.info("Ctrl+C detected, shutting down and restoring terminal...")
    if os.name != 'nt':
        os.system('stty sane') 
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))