from __future__ import annotations

import logging
import sys


def configure_logging() -> None:
    """Configure concise structured-ish logs for local and Docker runs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

