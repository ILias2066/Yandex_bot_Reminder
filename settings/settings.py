from dataclasses import dataclass
from environs import Env

@dataclass
class Bots:
    token_bot: str
    yandex_oauth_url: str
    client_id: str

@dataclass
class Settings:
    bots: Bots

def get_settings(path: str = ".env") -> Settings:
    env = Env()
    env.read_env(path)
    return Settings(
        bots=Bots(
            token_bot=env.str('TOKEN_ID'),
            yandex_oauth_url=env.str('YANDEX_OAUTH_URL'),
            client_id=env.str('CLIENT_ID'),
        )
    )


settings = get_settings()
