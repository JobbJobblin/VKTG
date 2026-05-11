from dataclasses import dataclass


@dataclass
class LoggerConfig:
    MAIN_LOG_NAME: str = "ADL_MAIN"
    IS_DEBUG: bool = False
    LOG_DIR: str = "log"
