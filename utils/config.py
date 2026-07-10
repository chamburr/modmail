from __future__ import annotations

import os

from dotenv import load_dotenv


class Config:
    def __init__(self) -> None:
        pass

    def __getattr__(self, attr: str) -> str | None:
        variable = os.getenv(attr)
        if variable == "":
            return None
        return variable

    def load(self) -> Config:
        load_dotenv(override=True)
        return self
