import logging
from app.core.log_safety import configure


def test_transport_children_do_not_propagate_to_root():
    captured=[]
    class Capture(logging.Handler):
        def emit(self,record):captured.append(record.getMessage())
    root=logging.getLogger();handler=Capture();root.addHandler(handler)
    try:
        configure()
        logging.getLogger("httpx.child").error("synthetic_sensitive_diagnostic")
        logging.getLogger("uvicorn.access").error("synthetic_callback_code")
        assert captured==[]
    finally:root.removeHandler(handler)
