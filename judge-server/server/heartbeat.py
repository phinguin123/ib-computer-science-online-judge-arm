#!/usr/bin/env python3
"""Background process to send periodic heartbeats to the backend"""
import os
import time
import sys

# Add the current directory to the path so we can import server modules
sys.path.insert(0, os.path.dirname(__file__))

from service import JudgeService
from utils import logger

def main():
    if os.environ.get("DISABLE_HEARTBEAT"):
        return
    
    backend_url = os.environ.get("BACKEND_URL")
    service_url = os.environ.get("SERVICE_URL")
    
    if not backend_url or not service_url:
        logger.warning("BACKEND_URL or SERVICE_URL not set, heartbeat disabled")
        return
    
    try:
        service = JudgeService()
        
        # Send initial heartbeat after a short delay
        time.sleep(2)
        
        while True:
            try:
                service.heartbeat()
                logger.debug("Heartbeat sent successfully")
            except Exception as e:
                logger.exception(f"Heartbeat failed: {e}")
            # Send heartbeat every 5 seconds (backend checks every 6 seconds, 5s gives a safe buffer)
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Heartbeat worker stopped")
    except Exception as e:
        logger.exception(f"Failed to start heartbeat worker: {e}")

if __name__ == "__main__":
    main()

