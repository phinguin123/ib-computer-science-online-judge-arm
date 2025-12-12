from django.core.management import call_command
from django.test import TestCase

from account.models import User, UserProfile
from problem.models import (
    Problem,
    ProblemDifficulty,
    ProblemIOMode,
    ProblemRuleType,
)
from submission.models import JudgeStatus


class DynamicScoringRippleEffectTest(TestCase):
    """
    Verifies Option B (dynamic scoring) ripple effect:
    when another user solves a problem and its current value drops,
    previously awarded users also see their total_score drop after
    running the recalculation command.
    """

    def setUp(self):
        self.author = User.objects.create_user(
            username="author", email="author@test.com", password="pass"
        )

        self.problem = Problem.objects.create(
            _id="1001",
            title="Hard Problem",
            contest=None,
            is_public=True,
            description="desc",
            input_description="in",
            output_description="out",
            samples=[],
            test_case_id="1",
            test_case_score=[],
            hint="",
            languages=[],
            template={},
            created_by=self.author,
            time_limit=1000,
            memory_limit=256,
            io_mode={"io_mode": ProblemIOMode.standard, "input": "in", "output": "out"},
            spj=False,
            rule_type=ProblemRuleType.ACM,
            visible=True,
            difficulty=ProblemDifficulty.LEVEL_4,
            total_score=0,
            submission_number=0,
            accepted_number=0,
            statistic_info={},
            share_submission=False,
            source="",
        )

        # First solver: User A
        self.user_a = User.objects.create_user(
            username="user_a", email="a@test.com", password="pass"
        )
        self.profile_a = UserProfile.objects.create(user=self.user_a)

        # Second solver: User B
        self.user_b = User.objects.create_user(
            username="user_b", email="b@test.com", password="pass"
        )
        self.profile_b = UserProfile.objects.create(user=self.user_b)

    def test_ripple_effect_after_recalculation(self):
        # User A solves first; problem has 1 accepted
        self.problem.accepted_number = 1
        self.problem.save(update_fields=["accepted_number"])
        first_value = self.problem.get_current_points()
        self.profile_a.acm_problems_status = {
            "problems": {
                str(self.problem.id): {
                    "status": JudgeStatus.ACCEPTED,
                    "score": first_value,
                    "_id": self.problem._id,
                }
            }
        }
        self.profile_a.total_score = first_value
        self.profile_a.save(update_fields=["acm_problems_status", "total_score"])

        # User B solves second; problem value decays with 2 accepted
        self.problem.accepted_number = 2
        self.problem.save(update_fields=["accepted_number"])
        second_value = self.problem.get_current_points()
        self.profile_b.acm_problems_status = {
            "problems": {
                str(self.problem.id): {
                    "status": JudgeStatus.ACCEPTED,
                    "score": second_value,
                    "_id": self.problem._id,
                }
            }
        }
        self.profile_b.total_score = second_value
        self.profile_b.save(update_fields=["acm_problems_status", "total_score"])

        # Recalculate all scores using current problem values
        call_command("recalculate_scores")

        self.profile_a.refresh_from_db()
        self.profile_b.refresh_from_db()

        # With dynamic scoring, User A should now match the new (lower) value
        self.assertEqual(
            self.profile_a.total_score,
            second_value,
            "User A score did not drop after decay; ripple effect missing.",
        )
        self.assertEqual(
            self.profile_b.total_score,
            second_value,
            "User B score should reflect current problem value.",
        )


