"""Disable URL/body-bearing transport diagnostics. App events use a safe schema."""
import logging


def configure():
    for name in ("uvicorn.access","httpx","httpcore","urllib3","requests_oauthlib","oauthlib","google.auth.transport.requests","googleapiclient"):
        logger=logging.getLogger(name)
        # Child loggers propagate through this handler without emitting raw data.
        logger.handlers=[logging.NullHandler()]
        logger.propagate=False
        logger.disabled=True
