from fastapi.routing import APIRouter
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.utils import parse_phone

from settings import settings


auth_router = APIRouter(prefix='/auth', tags=['Auth'])
sessions = {}


class Verification(BaseModel):
    phone_number: str


class GetSession(BaseModel):
    phone_number: str
    verification_code: str
    phone_code_hash: str
    password: str | None = None


class AuthError(Exception):
    pass


@auth_router.post('/verification_code')
async def get_verification_code(
    verification: Verification
) -> None:
    sessions[verification.phone_number] = StringSession()

    client = TelegramClient(
        session=sessions[verification.phone_number],
        api_id=settings.tg_api_id,
        api_hash=settings.tg_api_hash,
        system_version='Windows 11'
    )
    try:
        await client.connect()
        await client.send_code_request(verification.phone_number)
        return {
            'message': 'Код был успешно отправлен',
            'phone_code_hash': client._phone_code_hash.get(
                parse_phone(verification.phone_number)
            )
        }
    except Exception:
        raise AuthError('Не могу отправить код верификации')
    finally:
        await client.disconnect()


@auth_router.post('/session')
async def get_session(
    session: GetSession
) -> None:
    client = TelegramClient(
        session=sessions[session.phone_number],
        api_id=settings.tg_api_id,
        api_hash=settings.tg_api_hash,
        system_version='Windows 11'
    )

    try:
        await client.connect()
        await client.sign_in(
            phone=session.phone_number,
            code=session.verification_code,
            password=session.password,
            phone_code_hash=session.phone_code_hash
        )
        await client.start()
        del sessions[session.phone_number]

        return {
            'message': 'Вы успешно залогинились',
            'tg_session': client.session.save()
        }
    except Exception:
        raise AuthError('Не могу залогинить пользователя')
    finally:
        await client.disconnect()
