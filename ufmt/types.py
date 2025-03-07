# Copyright 2022 Amethyst Reese, Tim Hatch
# Licensed under the MIT license

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

from black import Mode as BlackConfig
from typing_extensions import Protocol
from usort import Config as UsortConfig

STDIN = Path("-")

Encoding = str
FileContent = bytes
Newline = bytes

BlackConfigFactory = Callable[[Path], BlackConfig]
UsortConfigFactory = Callable[[Path], UsortConfig]


@dataclass
class Options:
    debug: bool = False
    quiet: bool = False


class Processor(Protocol):
    def __call__(
        self,
        path: Path,
        content: FileContent,
        *,
        encoding: Encoding = "utf-8",
    ) -> FileContent:  # pragma: nocover
        """
        Process bytes before or after formatting and return the updated file content.
        """
        ...


class SkipFormatting(Exception):
    """Raise this exception in a pre/post processor to skip formatting a file."""


@dataclass
class Result:
    """
    Basic metadata results from formatting files.
    """

    path: Path
    changed: bool = False
    written: bool = False
    skipped: Union[bool, str] = False
    diff: Optional[str] = None
    error: Optional[Exception] = None
    before: bytes = b""  # only set if return_content=True
    after: bytes = b""  # only set if return_content=True
