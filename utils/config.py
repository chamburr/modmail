import os

from dotenv import load_dotenv


class Config:
    def __init__(self):
        pass

    def __getattr__(self, attr):
        return os.getenv(attr)

    def load(self):
        load_dotenv(override=True)
        return self
