import logging
import sys

def configure_human_readable_logging():
    # 1. Establish the clean, human-scannable format string blueprint
    LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s -> %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=logging.DEBUG, # Retain your target application insights
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        force=True, # Ensures override control if initialized earlier by libraries
        stream=sys.stdout
    )
    
    # 2. Drop specific network-level protocol noisy modules down to WARNING
    noisy_protocols = ["hpack", "httpx", "httpcore", "urllib3.connectionpool", "watchfiles"]
    for logger_name in noisy_protocols:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
        
    # 3. Streamline AI orchestration telemetry down to INFO to avoid raw curl dumps
    logging.getLogger("LiteLLM").setLevel(logging.INFO)
    logging.getLogger("litellm").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.INFO)

# Keep the old name for backwards compatibility or explicitly export the new one
setup_logging = configure_human_readable_logging
