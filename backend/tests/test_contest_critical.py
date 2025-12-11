from datetime import timedelta

from django.utils.timezone import now

from utils.api.tests import APITestCase
from utils.shortcuts import rand_str
from contest.models import Contest, ContestRuleType
from utils.constants import ContestStatus
from problem.models import ProblemRuleType


class ContestCriticalTests(APITestCase):
    """
    Critical contest scenarios covering validation, status, and permissions.
    """

    def setUp(self):
        self.client.defaults["CONTENT_TYPE"] = "application/json"
        self.admin = self.create_super_admin()
        self.regular_user = self.create_user("regular_user", "pass123", login=False)
        self.contest_url = self.reverse("contest_admin_api")
        self.contest_problem_url = self.reverse("contest_problem_admin_api")

    def _contest_payload(self):
        return {
            "title": "Critical Contest",
            "description": "<p>desc</p>",
            "start_time": (now() + timedelta(hours=1)).isoformat(),
            "end_time": (now() + timedelta(hours=2)).isoformat(),
            "rule_type": ContestRuleType.ACM,
            "password": "",
            "visible": True,
            "real_time_rank": True,
            "allowed_ip_ranges": [],
        }

    def _contest_problem_payload(self, contest_id, *, rule_type=ProblemRuleType.ACM):
        return {
            "_id": "CONTEST-1",
            "title": "Contest Problem",
            "description": "<p>desc</p>",
            "input_description": "input",
            "output_description": "output",
            "time_limit": 1000,
            "memory_limit": 256,
            "difficulty": "Level 1",
            "visible": True,
            "languages": ["Python3"],
            "template": {},
            "samples": [{"input": "1", "output": "2"}],
            "spj": False,
            "spj_language": None,
            "spj_code": None,
            "spj_compile_ok": False,
            "test_case_id": rand_str(24),
            "test_case_score": [{"input_name": "1.in", "output_name": "1.out", "score": 0}],
            "rule_type": rule_type,
            "tags": ["critical"],
            "hint": "",
            "source": "",
            "share_submission": False,
            "io_mode": {"io_mode": "Standard IO", "input": "input.txt", "output": "output.txt"},
            "contest_id": contest_id,
        }

    # -------- Validation --------
    def test_create_contest_rejects_end_before_start(self):
        payload = self._contest_payload()
        payload["start_time"] = (now() + timedelta(hours=2)).isoformat()
        payload["end_time"] = (now() + timedelta(hours=1)).isoformat()

        resp = self.client.post(self.contest_url, data=payload)

        self.assertFailed(resp, "Start time must occur earlier than end time")

    def test_create_contest_rejects_invalid_cidr(self):
        payload = self._contest_payload()
        payload["allowed_ip_ranges"] = ["999.999.999"]

        resp = self.client.post(self.contest_url, data=payload)

        self.assertFailed(resp)
        self.assertIn("is not a valid cidr network", resp.data["data"])

    # -------- Status checks --------
    def test_contest_status_not_started(self):
        contest = Contest.objects.create(
            title="Future",
            description="future",
            start_time=now() + timedelta(hours=3),
            end_time=now() + timedelta(hours=4),
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin,
        )

        self.assertEqual(contest.status, ContestStatus.CONTEST_NOT_START)

    def test_contest_status_ended(self):
        contest = Contest.objects.create(
            title="Past",
            description="past",
            start_time=now() - timedelta(hours=4),
            end_time=now() - timedelta(hours=3),
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin,
        )

        self.assertEqual(contest.status, ContestStatus.CONTEST_ENDED)

    def test_contest_status_underway(self):
        contest = Contest.objects.create(
            title="Running",
            description="running",
            start_time=now() - timedelta(hours=1),
            end_time=now() + timedelta(hours=1),
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin,
        )

        self.assertEqual(contest.status, ContestStatus.CONTEST_UNDERWAY)

    # -------- Rule checks --------
    def test_rule_mismatch_between_contest_and_problem(self):
        contest_resp = self.client.post(self.contest_url, data=self._contest_payload())
        self.assertSuccess(contest_resp)
        contest_id = contest_resp.data["data"]["id"]

        problem_payload = self._contest_problem_payload(contest_id, rule_type=ProblemRuleType.OI)
        resp = self.client.post(self.contest_problem_url, data=problem_payload)

        self.assertFailed(resp, "Invalid rule type")

    # -------- Permission checks --------
    def test_regular_user_cannot_edit_contest(self):
        contest_resp = self.client.post(self.contest_url, data=self._contest_payload())
        contest_id = contest_resp.data["data"]["id"]

        self.client.logout()
        self.client.login(username=self.regular_user.username, password="pass123")

        update_payload = self._contest_payload()
        update_payload.update(
            {
                "id": contest_id,
                "title": "Unauthorized Update",
            }
        )

        resp = self.client.put(self.contest_url, data=update_payload)

        self.assertFailed(resp)
        self.assertIn("login", resp.data["data"].lower())

