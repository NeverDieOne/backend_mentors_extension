from datetime import date
from textwrap import dedent

import uvicorn
from fastapi import Depends, FastAPI, Query
from telethon import TelegramClient

from dependencies import mentor_api, telegram_client
from get_study_days import get_study_days
from mentors import MentorsAPI
from plans import parse_order
from settings import settings


async def send_user_in_academic_leave(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
    date_from: date = Query(description='Старт академа'),
    date_to: date  = Query(description='Конец академа'),
    reason: str | None = Query(default=None, description='Причина')
) -> None:

    order = mentor_api.get_order(order_uuid)
    dvmn_profile = order['student']['profile']['username_to_dvmn_org']
    tg_profile = order['student']['profile']['telegram_username']

    text = f'''
    #академ

    Dvmn: {dvmn_profile}, tg: {tg_profile}
    {date_from.strftime('%d %m %Y г.')} - {date_to.strftime('%d %m %Y г.')}
    {reason}
    '''

    await client.send_message(
        entity=settings.mentors_chat,
        message=dedent(text),
        link_preview=False,
    )


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


async def send_plan(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
) -> None:
    order = mentor_api.get_order(order_uuid)
    user_tg = order['student']['profile']['telegram_username']

    plan_info = parse_order(mentor_api, order)[user_tg]
    
    gist = plan_info['gist']
    comment = plan_info['comment']

    message_with_gist = await client.get_messages(
        user_tg, 1, search=gist
    )
    if message_with_gist:
        print(f'Ученику: {user_tg} уже был выдан план с таким гистом.')
        return

    text = dedent(f"""\
    #ЕженедельныйПлан

    Приветосий :)
    Держи планчик на новую неделю:
    {gist}

    """)

    if comment:
        text += dedent(f"""\
        {'-' * 5}

        {comment}
        """)

    await client.send_message(user_tg, text, link_preview=False)


async def send_plans(
    client: TelegramClient = Depends(telegram_client),
    mentor_api: MentorsAPI = Depends(mentor_api),
    mentor_uuid: str = Query(description='UUID ментора'),
) -> None:
    orders = mentor_api.get_mentor_orders(mentor_uuid)
    messages = {}
    for order in orders:
        if not order['is_active'] or not order['weekly_plan']:
            continue
        messages.update(parse_order(mentor_api, order))
    
    for tag, info in messages.items():
        message_with_gist = await client.get_messages(
            tag, 1, search=info['gist']
        )
        if message_with_gist:
            print(f'Ученику: {tag} уже был выдан план с таким гистом.')
            continue
            
        text = dedent(f"""\
            #ЕженедельныйПлан

            Приветосий :)
            Держи планчик на новую неделю:
            {info['gist']}

            """)

        if comment := info.get('comment'):
            text += dedent(f"""\
            {'-' * 5}

            {comment}
            """)
        
        await client.send_message(tag, text, link_preview=False)


async def get_dvmn_study_days(
    mentor_api: MentorsAPI = Depends(mentor_api),
    order_uuid: str = Query(description='UUID заказа'),
) -> int:

    order = mentor_api.get_order(order_uuid)
    dvmn_profile = order['student']['profile']['username_to_dvmn_org']
    study_days = get_study_days(f'https://dvmn.org/user/{dvmn_profile}/history/')
    return int(study_days)


def main():
    app = FastAPI()

    app.add_api_route(
        path='/academic_leave/',
        endpoint=send_user_in_academic_leave,
        methods=['POST'],
        description='Отправить ученика в академ',
    )

    app.add_api_route(
        path='/internship/',
        endpoint=send_user_in_internship,
        methods=['POST'],
        description='Отправить ученика на стажировку',
    )

    app.add_api_route(
        path='/send_plan/',
        endpoint=send_plan,
        methods=['POST'],
        description='Отправить план'
    )

    app.add_api_route(
        path='/send_plans/',
        endpoint=send_plans,
        methods=['POST'],
        description='Отправить планы всем ученикам'
    )

    app.add_api_route(
        path='/get_study_days/',
        endpoint=get_dvmn_study_days,
        methods=['GET'],
        description='Получить кол-во дней, которые занимался ученик'
    )

    uvicorn.run(app)


if __name__ == '__main__':
    main()
