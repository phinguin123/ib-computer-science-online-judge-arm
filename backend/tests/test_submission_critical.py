from datetime import timedelta
from unittest import mock

from django.utils.timezone import now

from utils.api.tests import APITestCase
from utils.shortcuts import rand_str
from contest.models import Contest, ContestRuleType
from submission.models import Submission
from problem.models import Problem, ProblemTag, ProblemRuleType


class SubmissionCriticalTests(APITestCase):
    """
    Critical submission scenarios focused on permissions, visibility, and contest rules.
    """

    def setUp(self):
        self.submission_url = self.reverse("submission_api")
        self.admin = self.create_admin("admin_user", "admin123")
        self.user = self.create_user("regular_user", "pass123")
        self.other_user = self.create_user("other_user", "pass123", login=False)

        # Ensure session has an IP so submission creation doesn't crash on missing key
        session = self.client.session
        session["ip"] = "127.0.0.1"
        session.save()

    # Helpers
    def _create_problem(self, *, languages=None, visible=True, contest=None):
        if languages is None:
            languages = ["Python3"]

        problem_data = {
            "_id": f"TEST-{rand_str(6)}",
            "title": "Critical Submission Problem",
            "description": "<p>desc</p>",
            "input_description": "input",
            "output_description": "output",
            "time_limit": 1000,
            "memory_limit": 256,
            "difficulty": "Level 1",
            "visible": visible,
            "languages": languages,
            "template": {},
            "samples": [{"input": "1", "output": "2"}],
            "spj": False,
            "spj_language": None,
            "spj_code": None,
            "test_case_id": rand_str(32),
            "test_case_score": [{"input_name": "1.in", "output_name": "1.out", "score": 0}],
            "rule_type": ProblemRuleType.ACM,
            "created_by": self.admin,
        }
        if contest:
            problem_data["contest"] = contest

        problem = Problem.objects.create(**problem_data)
        tag = ProblemTag.objects.create(name="critical")
        problem.tags.add(tag)
        return problem

    # 1. Non-Existent Problem
    @mock.patch("submission.views.oj.judge_task.send")
    def test_submit_to_nonexistent_problem_returns_not_found(self, judge_task):
        response = self.client.post(
            self.submission_url,
            data={"problem_id": 99999, "language": "Python3", "code": "print('hi')"},
        )
        self.assertFailed(response, "Problem not exist")
        self.assertIn(response.status_code, (404, 200))
        judge_task.assert_not_called()

    # 2. Disallowed Language
    @mock.patch("submission.views.oj.judge_task.send")
    def test_submit_with_disallowed_language_rejected(self, judge_task):
        problem = self._create_problem(languages=["Python3"])  # Only Python3 allowed

        response = self.client.post(
            self.submission_url,
            data={"problem_id": problem.id, "language": "C++", "code": "int main(){return 0;}"},
        )
        self.assertFailed(response, "C++ is not allowed in the problem")
        judge_task.assert_not_called()

    # 3. Invisible Problem
    @mock.patch("submission.views.oj.judge_task.send")
    def test_submit_to_invisible_problem_forbidden(self, judge_task):
        problem = self._create_problem(visible=False)

        response = self.client.post(
            self.submission_url,
            data={"problem_id": problem.id, "language": "Python3", "code": "print('hi')"},
        )
        self.assertFailed(response, "Problem not exist")
        self.assertIn(response.status_code, (403, 404, 200))
        judge_task.assert_not_called()

    # 4. Ended Contest
    @mock.patch("submission.views.oj.judge_task.send")
    def test_submit_to_recently_ended_contest(self, judge_task):
        contest = Contest.objects.create(
            title="Ended Contest",
            description="ended",
            start_time=now() - timedelta(hours=2),
            end_time=now() - timedelta(minutes=1),
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin,
        )
        problem = self._create_problem(contest=contest)

        response = self.client.post(
            self.submission_url,
            data={
                "problem_id": problem.id,
                "contest_id": contest.id,
                "language": "Python3",
                "code": "print('contest')",
            },
        )
        self.assertFailed(response, "The contest have ended")
        self.assertIn(response.status_code, (403, 404, 200))
        judge_task.assert_not_called()

    # 5. Permission Check
    def test_viewing_other_user_private_submission_denied(self):
        problem = self._create_problem()
        submission = Submission.objects.create(
            problem=problem,
            user_id=self.other_user.id,
            username=self.other_user.username,
            code="secret",
            language="Python3",
            shared=False,
        )

        response = self.client.get(self.submission_url, data={"id": submission.id})
        self.assertFailed(response, "No permission for this submission")
        self.assertIn(response.status_code, (403, 404, 200))

    # 6. Share During Contest
    def test_sharing_submission_during_active_contest_blocked(self):
        contest = Contest.objects.create(
            title="Running Contest",
            description="running",
            start_time=now() - timedelta(minutes=5),
            end_time=now() + timedelta(minutes=55),
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin,
        )
        problem = self._create_problem(contest=contest)
        submission = Submission.objects.create(
            problem=problem,
            contest=contest,
            user_id=self.user.id,
            username=self.user.username,
            code="code",
            language="Python3",
        )

        response = self.client.put(self.submission_url, data={"id": submission.id, "shared": True})
        self.assertFailed(response, "Can not share submission now")
        self.assertIn(response.status_code, (403, 404, 200))
