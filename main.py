from textwrap import dedent

import uvicorn
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from telethon import TelegramClient

from authorization import auth_router, AuthError
from dependencies import DependencyError, mentor_api, telegram_client
from get_study_days import get_study_days
from mentors import MentorsAPI
from plans import parse_order
from settings import settings


async def catch_exception_middleware(request: Request, err) -> JSONResponse:
    return JSONResponse(
        content={'message': 'Не получается создать клиент телеграма. Проверьте токен.'},
        status_code=400
    )


async def catch_auth_exception_middleware(request: Request, err) -> JSONResponse:
    return JSONResponse(
        content={'message': 'Что-то пошло не так. Проверьте запросы в Network'},
        status_code=400
    )


async def send_user_in_academic_leave(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
    splitter: str = Query(default='ac:',description='Метка академа')
) -> None:
    order = mentor_api.get_order(order_uuid)
    student = order['student']
    
    dvmn_profile = student['profile']['username_to_dvmn_org']
    tg_profile = student['profile']['telegram_username']
    
    notes = student['notes']
    comment = next((
        n for n in notes
        if not n['is_hidden'] and splitter in n['content']
    ), None)

    if not comment:
        return JSONResponse(
            content={'message': f'Нет заметки об академе с разделителем {splitter}'},
            status_code=400
        )

    comment_text = comment['content'].split('ac: ')[-1]

    text = f'''
    #академ

    Dvmn: {dvmn_profile}, tg: {tg_profile}
    {comment_text}
    '''

    await client.send_message(
        entity=settings.mentors_chat,
        message=dedent(text),
        link_preview=False,
    )
    return {'message': 'Сообщение отправлено в чат менторов'}


async def send_user_in_internship(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
) -> None:
    order = mentor_api.get_order(order_uuid)
    dvmn_profile = order['student']['profile']['username_to_dvmn_org']
    tg_profile = order['student']['profile']['telegram_username']

    text = f'''
    #стажировка

    Добавь, плз, этого ученика в очередь на стажировку
    Dvmn: {dvmn_profile}, tg: {tg_profile}
    '''

    await client.send_message(
        entity=settings.mentors_head_chat,
        message=dedent(text),
        link_preview=False,
    )
    return {'message': 'Сообщение успешно отправлено главе менторов'}


async def send_plan(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
    template: str = Query(description='Шаблон сообщения')
) -> dict[str, str]:
    order = mentor_api.get_order(order_uuid)
    user_tg = order['student']['profile']['telegram_username']

    try:
        plan_info = parse_order(mentor_api, order)[user_tg]
    except Exception:
        return JSONResponse(
            content={'message': 'Что-то не так с планом'},
            status_code=400
        )
    
    gist = plan_info['gist']
    comment = plan_info['comment']

    message_with_gist = await client.get_messages(
        user_tg, 1, search=gist
    )
    if message_with_gist:
        return JSONResponse(
            content={'message': 'План уже был выдан'},
            status_code=400
        )

    text = template.replace('{gist}', gist)
    if comment:
        text = text.replace('{comment}', comment)

    await client.send_message(user_tg, text, link_preview=False)
    return {'message': 'План был успешно отправлен'}


async def send_plans(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    mentor_uuid: str = Query(description='UUID ментора'),
    template: str = Query(description='Шаблон сообщения')
) -> None:
    orders = mentor_api.get_mentor_orders(mentor_uuid)
    messages = {}
    for order in orders:
        if not order['is_active'] or not order['weekly_plan']:
            continue
        messages.update(parse_order(mentor_api, order))
    
    res_messages = []
    for tag, info in messages.items():
        message_with_gist = await client.get_messages(
            tag, 1, search=info['gist']
        )
        if message_with_gist:
            res_messages.append({
                'status': 'warning',
                'order_id': info['order_id'],
                'message': f'План с этим гистом уже был выдан.'
            })
            continue
            
        text = template.replace('{gist}', info['gist'])
        if comment := info.get('comment'):
            text = template.replace('{comment}', comment)
        
        try:
            await client.send_message(tag, text, link_preview=False)
            res_messages.append({
                'status': 'ok',
                'order_id': info['order_id'],
                'message': 'План успешно выдан.'
            })
        except Exception:
            res_messages.append({
                'status': 'error',
                'order_id': info['order_id'],
                'message': f'План не отправлен, ошибка.'
            })
            continue


    return {'messages': res_messages}


async def get_dvmn_study_days(
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
) -> dict[str, str]:

    order = mentor_api.get_order(order_uuid)
    dvmn_profile = order['student']['profile']['username_to_dvmn_org']
    try:
        study_days = get_study_days(f'https://dvmn.org/user/{dvmn_profile}/history/')
        return {'message': study_days}
    except Exception:
        return JSONResponse(
            content={'message': '¯\_(ツ)_/¯'},
            status_code=400
        )


def main():
    app = FastAPI()

    app.add_exception_handler(DependencyError, catch_exception_middleware)
    app.add_exception_handler(AuthError, catch_auth_exception_middleware)

    app.add_api_route(
        path='/academic_leave/',
        endpoint=send_user_in_academic_leave,
        methods=['POST'],
        description='Отправить ученика в академ',
        tags=['Mentors']
    )

    app.add_api_route(
        path='/internship/',
        endpoint=send_user_in_internship,
        methods=['POST'],
        description='Отправить ученика на стажировку',
        tags=['Mentors']
    )

    app.add_api_route(
        path='/send_plan/',
        endpoint=send_plan,
        methods=['POST'],
        description='Отправить план',
        tags=['Mentors']
    )

    app.add_api_route(
        path='/send_plans/',
        endpoint=send_plans,
        methods=['POST'],
        description='Отправить планы всем ученикам',
        tags=['Mentors']
    )

    app.add_api_route(
        path='/get_study_days/',
        endpoint=get_dvmn_study_days,
        methods=['GET'],
        description='Получить кол-во дней, которые занимался ученик',
        tags=['Mentors']
    )

    app.include_router(auth_router)

    origins = ['*']

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=['*'],
        allow_headers=['*'],
        allow_credentials=True,
    )

    uvicorn.run(app)


if __name__ == '__main__':
    main()
