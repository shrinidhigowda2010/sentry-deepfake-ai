"""Safe temporary file helpers with guaranteed cleanup."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable, Optional

from sentrydeepfake.config import STORE_UPLOADS, TEMP_DIR
from sentrydeepfake.utils.logging_config import get_logger

logger = get_logger(__name__)


def new_session_dir(prefix: str = "session") -> Path:
    path = TEMP_DIR / f"{prefix}_{uuid.uuid4().hex[:12]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_path(path: Optional[Path]) -> None:
    if path is None:
        return
    try:
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir() and not STORE_UPLOADS:
            shutil.rmtree(path, ignore_errors=True)
    except OSError as exc:
        logger.warning("cleanup_failed path=%s err=%s", path.name, type(exc).__name__)


@contextmanager
def temporary_upload(
    data: bytes,
    suffix: str,
    session_dir: Optional[Path] = None,
) -> Generator[Path, None, None]:
    """Write upload bytes to a temp file and clean up afterwards."""
    base = session_dir or new_session_dir("upload")
    base.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(suffix=suffix, dir=base)
    path = Path(name)
    try:
        with open(fd, "wb") as fh:
            fh.write(data)
        yield path
    finally:
        if not STORE_UPLOADS:
            cleanup_path(path)
            if session_dir is None:
                cleanup_path(base)


def cleanup_many(paths: Iterable[Optional[Path]]) -> None:
    for p in paths:
        cleanup_path(p)
