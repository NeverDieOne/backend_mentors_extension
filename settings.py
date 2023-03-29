from pydantic import BaseSettings


class Settings(BaseSettings):
    tg_api_id: str
    tg_api_hash: str

    mentors_chat: int = -1001649457872
    mentors_head_chat: int = 424079888

    mentor_username: str
    mentor_password: str


    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
