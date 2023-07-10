import requests
from typing import Any
from datetime import date


class MentorsAPI:
    base_url = 'https://mentors.dvmn.org/api/v1'

    def __init__(
        self,
        login: str,
        password: str
    ) -> None:
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.session.auth = (self.login, self.password)

    def get_mentor_orders(self, mentor_uuid: str) -> dict[Any, Any]:
        response = self.session.get(
            f'{self.base_url}/mentors/{mentor_uuid}/orders/'
        )
        response.raise_for_status()
        return response.json()['results']
    
    def get_order(self, order_uuid: str) -> dict[Any, Any]:
        response = self.session.get(
            f'{self.base_url}/orders/{order_uuid}/'
        )
        response.raise_for_status()
        return response.json()

    def get_weekly_plan(self, plan_uuid: str) -> dict[Any, Any]:
        response = self.session.get(
            f'{self.base_url}/weekly-plans/{plan_uuid}/'
        )
        response.raise_for_status()
        return response.json()

    def close_note(self, note_uuid: str) -> None:
        response = self.session.patch(
            f'{self.base_url}/notes/{note_uuid}/',
            json={'is_hidden': True}
        )
        response.raise_for_status()

    def add_note(
        self,
        student_uuid: str,
        comment: str,
        is_hidden: bool = False
    ) -> None:
        response = self.session.post(
            f'{self.base_url}/notes/',
            json={
                'student': student_uuid,
                'content': comment,
                'is_hidden': is_hidden
            }
        )
        response.raise_for_status()

    def get_weekly_plans(
        self,
        order_uuid: str | None = None,
        student_uuid: str | None = None,
        dvmn_username: str | None = None,
    ) -> list[dict[Any, Any]]:
        params = {
            'order_uuid': order_uuid,
            'student_uuid': student_uuid,
            'username_to_dvmn_org': dvmn_username,
        }
        response = self.session.get(
            f'{self.base_url}/weekly-plans/',
            params=params
        )
        response.raise_for_status()
        return response.json()['results']

    def get_study_program_tasks(self, order_uuid: str) -> list[dict[Any, Any]]:
        resposne = self.session.get(
            f'{self.base_url}/orders/{order_uuid}/study-program-tasks/'
        )
        resposne.raise_for_status()
        return resposne.json()

    def get_study_program_by_order_uuid(
        self,
        order_uuid: str
    ) -> list[dict[Any, Any]]:
        response = self.session.get(
            f'{self.base_url}/orders/{order_uuid}/study-program-tasks/'
        )
        response.raise_for_status()
        return response.json()

    def create_weekly_plan(
        self,
        order_uuid: str,
        task_uuid: str,
        task_time: str,
    ) -> str:
        body = {
            "order": order_uuid,
            "status_from_mentor": "preparing",
            "general_tasks": [{
                "execution_time": task_time,
                "parent_task_uuid": task_uuid
            }],
            "individual_tasks": [],
            "subtasks": []
        }

        response = self.session.post(
            f'{self.base_url}/weekly-plans/',
            json=body
        )
        response.raise_for_status()
        return response.json()['uuid']

    def give_weekly_plan(
        self,
        order_uuid: str,
        task_uuid: str,
        task_time: str,
        plan_uuid: str,
    ) -> None:
        body = {
            "order": order_uuid,
            "status_from_mentor": "issued_by",
            "general_tasks": [{
                "execution_time": task_time,
                "parent_task_uuid": task_uuid
            }],
            "individual_tasks": [],
            "subtasks": []
        }
        response = self.session.put(
            f'{self.base_url}/weekly-plans/{plan_uuid}/', json=body
        )
        response.raise_for_status()

    def create_gist(self, plan_uuid: str) -> None:
        body = {'uuid': plan_uuid}
        response = self.session.post(
            f'{self.base_url}/gists-create/', json=body
        )
        response.raise_for_status()

    def update_gist(self, plan_uuid: str) -> None:
        body = {'uuid': plan_uuid}
        response = self.session.patch(
            f'{self.base_url}/gists-update/', json=body
        )
        response.raise_for_status()

    def send_report(self, plan_uuid: str, text: str) -> dict[Any, Any]:
        body = {
            "weeklyplan_uuid": plan_uuid,
            "student_comment": text,
            "sent_by_student_for_review_at": str(date.today())
        }
        response = self.session.post(f'{self.base_url}/reports/', json=body)
        response.raise_for_status()
        return response.json()
