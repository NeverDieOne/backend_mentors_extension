import datetime
import locale
import re

import requests
from bs4 import BeautifulSoup


def get_study_days(url: str, days: int = 7) -> int:
    study_days = 0
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    logtable = soup.select_one('.logtable')
    blocks = logtable.select('.mt-4 .mb-4')

    locale.setlocale(
        category=locale.LC_ALL,
        locale=''
    )

    today = datetime.date.today()
    study_days = 0
    for block in blocks:
        raw = block.select_one('.align-items-center').text
        pattern = re.compile(r'\s+')
        day_info = re.sub(pattern, ' ', raw).strip()

        date = ' '.join(day_info.split(' ')[:4])
        date = datetime.datetime.strptime(date, u'%d %B %Y г.').date()

        if (today - date).days >= days:
            break

        is_study = '+' in day_info.split(' ')[-1].strip()
        if is_study:
            study_days += 1

    return study_days
