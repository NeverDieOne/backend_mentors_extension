from typing import Any

from mentors import MentorsAPI


def parse_order(api: MentorsAPI, order: dict[Any, Any]) -> dict[Any, Any]:
    student = order['student']
    profile = student['profile']
    notes = student['notes']
    comments = [
        n for n in notes
        if not n['is_hidden'] and '$:' in n['content']
    ]

    student_tg = profile['telegram_username']
    dvmn_link = profile['username_to_dvmn_org']

    comment_text = None
    if comments:
        comment = comments[0]
        api.close_note(comment['uuid'])
        comment_text = comment['content'].split('$: ')[-1]

    weekly_plan_uuid = order['weekly_plan']['uuid']
    weekly_plan = api.get_weekly_plan(weekly_plan_uuid)
    gist = weekly_plan['gist_url']

    return {
        student_tg: {
            'gist': gist,
            'comment': comment_text,
            'dvmn_link': dvmn_link
        }
    }