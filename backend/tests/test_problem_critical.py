from unittest import mock

from options.options import SysOptions
from problem.models import Problem, ProblemDifficulty, ProblemIOMode, ProblemRuleType
from utils.api.tests import APITestCase
from utils.shortcuts import rand_str


class ProblemCriticalTests(APITestCase):
    """
    Critical scenarios for problem management covering duplicate IDs, validation, and permissions.
    """

    def setUp(self):
        self.problem_admin_url = self.reverse("problem_admin_api")
        self.compile_spj_url = self.reverse("compile_spj")
        self.admin = self.create_admin("admin_user", "admin123")
        self.admin_other = self.create_admin("other_admin", "admin123", login=False)
        self.user = self.create_user("regular_user", "user123", login=False)

    # -------- Helpers --------
    def _base_payload(self, display_id, *, rule_type=ProblemRuleType.ACM, spj=False):
        spj_lang = SysOptions.spj_language_names[0] if SysOptions.spj_language_names else None
        test_case_score = (
            [{"input_name": "1.in", "output_name": "1.out", "score": 10}]
            if rule_type == ProblemRuleType.OI
            else []
        )

        payload = {
            "_id": display_id,
            "title": f"Problem {display_id}",
            "description": "<p>desc</p>",
            "input_description": "input",
            "output_description": "output",
            "samples": [{"input": "1", "output": "2"}],
            "test_case_id": rand_str(24),
            "test_case_score": test_case_score,
            "time_limit": 1000,
            "memory_limit": 256,
            "languages": ["Python3"],
            "template": {"Python3": "print('hi')"},
            "rule_type": rule_type,
            "io_mode": {
                "io_mode": ProblemIOMode.standard,
                "input": "input.txt",
                "output": "output.txt",
            },
            "spj": spj,
            "visible": True,
            "difficulty": ProblemDifficulty.LEVEL_1,
            "tags": ["critical"],
            "hint": "",
            "source": "",
            "share_submission": False,
        }

        if spj:
            payload["spj_language"] = spj_lang
            payload["spj_code"] = "int main(){}"
            payload["spj_compile_ok"] = True
        else:
            payload["spj_language"] = None
            payload["spj_code"] = None
            payload["spj_compile_ok"] = False

        return payload

    def _create_problem(self, display_id, creator=None, *, rule_type=ProblemRuleType.ACM):
        base = self._base_payload(display_id, rule_type=rule_type)
        creator = creator or self.admin
        problem = Problem.objects.create(
            _id=base["_id"],
            title=base["title"],
            description=base["description"],
            input_description=base["input_description"],
            output_description=base["output_description"],
            samples=base["samples"],
            test_case_id=base["test_case_id"],
            test_case_score=base["test_case_score"],
            time_limit=base["time_limit"],
            memory_limit=base["memory_limit"],
            languages=base["languages"],
            template=base["template"],
            rule_type=base["rule_type"],
            created_by=creator,
            difficulty=base["difficulty"],
            io_mode=base["io_mode"],
            hint=base["hint"],
            source=base["source"],
            visible=base["visible"],
            share_submission=base["share_submission"],
        )
        return problem

    # -------- Duplicate Display ID on Create --------
    def test_create_duplicate_display_id_rejected(self):
        self._create_problem(display_id="100", creator=self.admin)
        duplicate_payload = self._base_payload("100")

        response = self.client.post(self.problem_admin_url, data=duplicate_payload, format="json")

        self.assertFailed(response, "Display ID already exists")

    # -------- Invalid Test Case Score --------
    def test_negative_test_case_score_rejected(self):
        payload = self._base_payload("NEG", rule_type=ProblemRuleType.OI)
        payload["test_case_score"] = [{"input_name": "1.in", "output_name": "1.out", "score": -10}]

        response = self.client.post(self.problem_admin_url, data=payload, format="json")

        self.assertFailed(response)
        self.assertIn("Ensure this value is greater than or equal to 0", response.data["data"])

    # -------- SPJ Validation --------
    @mock.patch("judge.dispatcher.SPJCompiler.compile_spj", return_value="Compile Error")
    def test_spj_compile_failure_bubbles_up(self, compile_spj):
        spj_language = SysOptions.spj_language_names[0] if SysOptions.spj_language_names else "C++"
        response = self.client.post(
            self.compile_spj_url,
            data={"spj_language": spj_language, "spj_code": "int main(){return 0;}"},  # bad code mocked
            format="json",
        )

        self.assertFailed(response, "Compile Error")
        compile_spj.assert_called_once()

    # -------- Permission Checks --------
    def test_regular_user_cannot_delete_problem(self):
        problem = self._create_problem(display_id="DEL-USER")
        self.client.logout()
        self.client.login(username=self.user.username, password="user123")

        response = self.client.delete(f"{self.problem_admin_url}?id={problem.id}")

        # Regular users should be rejected before permission checks; backend returns login-required for admin-only endpoints
        self.assertEqual(response.data["error"], "login-required")
        self.assertIn(response.status_code, (200, 403))

    # -------- Deletion by Non-Owner Admin --------
    def test_admin_cannot_delete_others_problem(self):
        problem = self._create_problem(display_id="DEL-OTHER", creator=self.admin_other)
        self.client.logout()
        self.client.login(username=self.admin.username, password="admin123")

        response = self.client.delete(f"{self.problem_admin_url}?id={problem.id}")

        self.assertFailed(response, "Problem does not exist")

    # -------- Update Duplicate Display ID --------
    def test_update_duplicate_display_id_rejected(self):
        problem_a = self._create_problem(display_id="UP-1")
        problem_b = self._create_problem(display_id="UP-2")

        update_payload = self._base_payload(display_id=problem_a._id)
        update_payload["id"] = problem_b.id

        response = self.client.put(self.problem_admin_url, data=update_payload, format="json")

        self.assertFailed(response, "Display ID already exists")
