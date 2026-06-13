import logging
import sys
import os

def configure_human_readable_logging():
    # 1. Establish the format
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # User approved JSON logging for production. 
    # Use python-json-logger if available, otherwise fallback.
    try:
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(log_format, datefmt=date_format)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logging.basicConfig(
            level=log_level,
            handlers=[handler],
            force=True
        )
    except ImportError:
        # Fallback if package isn't installed yet
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s | %(levelname)-7s | %(name)s -> %(message)s",
            datefmt=date_format,
            force=True,
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
