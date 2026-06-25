import logging
import sys
import os
import structlog

def configure_human_readable_logging():
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 1. Standard python logging config
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout,
    )
    
    # 2. Drop specific network-level protocol noisy modules down to WARNING
    noisy_protocols = ["hpack", "httpx", "httpcore", "urllib3.connectionpool", "watchfiles"]
    for logger_name in noisy_protocols:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
        
    # 3. Streamline AI orchestration telemetry down to INFO
    logging.getLogger("LiteLLM").setLevel(logging.INFO)
    logging.getLogger("litellm").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    # 4. Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

setup_logging = configure_human_readable_logging
