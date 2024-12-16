import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


MyWay = Path(__file__).resolve()
DOTENV = Path(MyWay.parents[0] / ".env")
print(f'DOTENV = {DOTENV}')

class Settings(BaseSettings):

    VK_TOKEN: SecretStr
    GROUP_ID_MINUS: SecretStr
    GROUP_ID: SecretStr
    TG_TOKEN: SecretStr
    CHANNEL_ID: SecretStr
    MSG_THREAD: SecretStr

    model_config = SettingsConfigDict(
        extra= "allow",
        env_file=DOTENV,
        env_file_encoding='utf-8',
    )

config = Settings()