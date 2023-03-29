from fastapi import Header, Query
from telethon import TelegramClient
from telethon.sessions import StringSession

from settings import settings
from mentors import MentorsAPI


async def telegram_client(
    session: str | None = Header()
) -> TelegramClient:
    client = TelegramClient(
        StringSession(session),
        api_id=settings.tg_api_id,
        api_hash=settings.tg_api_hash
    )

    try:
        await client.start()
        yield client
    finally:
        await client.disconnect()


async def mentor_api() -> MentorsAPI:
    print('Init mentor API')
    mentors_api = MentorsAPI(settings.mentor_username, settings.mentor_password)
    return mentors_api
