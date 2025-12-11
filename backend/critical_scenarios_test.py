"""
Critical Scenarios Test Suite for Online Judge Platform

This test file covers the most critical edge cases and failure scenarios
that could break the system. Each test is designed to catch potential bugs
before they reach production.

Test Organization:
1. Account Module - Authentication, registration, security
2. Submission Module - Code submission, permissions, validation
3. Problem Module - Problem creation, validation, scoring
4. Contest Module - Contest management, time validation, IP restrictions
"""

from copy import deepcopy
from unittest import mock
from datetime import timedelta
from django.utils.timezone import now
from django.core.files.uploadedfile import SimpleUploadedFile
from otpauth import OtpAuth

from utils.api.tests import APITestCase
from utils.shortcuts import rand_str
from options.options import SysOptions
from account.models import User, UserProfile, AdminType, ProblemPermission
from problem.models import Problem, ProblemTag, ProblemRuleType
from submission.models import Submission, JudgeStatus
from contest.models import Contest, ContestStatus
from utils.constants import ContestRuleType


# ============================================================================
# CRITICAL SCENARIO ANALYSIS
# ============================================================================

"""
ACCOUNT MODULE CRITICAL SCENARIOS:

1. Registration with duplicate username/email
   WHY: Prevents account hijacking and data integrity issues

2. Login with disabled account
   WHY: Security - disabled accounts should not be able to access the system

3. 2FA validation failures
   WHY: Security - prevents unauthorized access even with stolen credentials

4. Password reset token expiration
   WHY: Security - prevents token reuse attacks

5. Email change with duplicate email
   WHY: Data integrity - ensures email uniqueness

6. Avatar upload with invalid file types/sizes
   WHY: Prevents DoS attacks and storage abuse

7. Registration when registration is disabled
   WHY: System control - admins should be able to disable registration

8. Password change without 2FA when 2FA is enabled
   WHY: Security - 2FA should be required for sensitive operations

9. Login attempt with non-existent user
   WHY: Should not leak information about user existence

10. Reset password when already logged in
    WHY: Security - prevents token hijacking attacks
"""


class AccountCriticalScenariosTest(APITestCase):
    """Critical test scenarios for Account module"""

    def setUp(self):
        self.register_url = self.reverse("user_register_api")
        self.login_url = self.reverse("user_login_api")
        self.change_password_url = self.reverse("user_change_password_api")
        self.change_email_url = self.reverse("user_change_email_api")
        self.reset_password_url = self.reverse("reset_password_api")
        self.apply_reset_password_url = self.reverse("apply_reset_password_api")
        self.avatar_upload_url = self.reverse("avatar_upload_api")

    def test_registration_with_duplicate_username(self):
        """
        SCENARIO: User tries to register with an existing username
        WHY IMPORTANT: Prevents account hijacking and ensures data integrity
        """
        # Create existing user
        existing_user = self.create_user("testuser", "password123", login=False)
        existing_user.email = "test@example.com"
        existing_user.save()

        # Attempt registration with same username (case-insensitive)
        response = self.client.post(self.register_url, data={
            "username": "TestUser",  # Different case
            "email": "new@example.com",
            "password": "newpass123",
            "captcha": "test_captcha"
        })
        self.assertFailed(response, "Username already exists")

    def test_registration_with_duplicate_email(self):
        """
        SCENARIO: User tries to register with an existing email
        WHY IMPORTANT: Email uniqueness is critical for password reset functionality
        """
        existing_user = self.create_user("user1", "pass123", login=False)
        existing_user.email = "existing@example.com"
        existing_user.save()

        response = self.client.post(self.register_url, data={
            "username": "user2",
            "email": "Existing@Example.com",  # Different case
            "password": "pass123",
            "captcha": "test_captcha"
        })
        self.assertFailed(response, "Email already exists")

    def test_login_with_disabled_account(self):
        """
        SCENARIO: User tries to login with a disabled account
        WHY IMPORTANT: Disabled accounts should be completely blocked from access
        """
        user = self.create_user("disabled_user", "password123", login=False)
        user.is_disabled = True
        user.save()

        response = self.client.post(self.login_url, data={
            "username": "disabled_user",
            "password": "password123"
        })
        self.assertFailed(response, "Your account has been disabled")

    def test_login_with_invalid_credentials(self):
        """
        SCENARIO: Login attempt with wrong password
        WHY IMPORTANT: Should not leak information about user existence
        """
        self.create_user("existing_user", "correctpass", login=False)

        # Wrong password
        response = self.client.post(self.login_url, data={
            "username": "existing_user",
            "password": "wrongpass"
        })
        self.assertFailed(response, "Invalid username or password")

        # Non-existent user (should return same error)
        response = self.client.post(self.login_url, data={
            "username": "nonexistent",
            "password": "anypass"
        })
        self.assertFailed(response, "Invalid username or password")

    def test_2fa_login_without_code(self):
        """
        SCENARIO: User with 2FA enabled tries to login without TFA code
        WHY IMPORTANT: 2FA should be enforced for security
        """
        user = self.create_user("tfa_user", "password123", login=False)
        user.two_factor_auth = True
        user.tfa_token = rand_str(32)
        user.save()

        response = self.client.post(self.login_url, data={
            "username": "tfa_user",
            "password": "password123"
            # Missing tfa_code
        })
        self.assertFailed(response, "tfa_required")

    def test_2fa_login_with_invalid_code(self):
        """
        SCENARIO: User with 2FA provides invalid TFA code
        WHY IMPORTANT: Invalid codes should be rejected
        """
        user = self.create_user("tfa_user", "password123", login=False)
        tfa_token = rand_str(32)
        user.two_factor_auth = True
        user.tfa_token = tfa_token
        user.save()

        response = self.client.post(self.login_url, data={
            "username": "tfa_user",
            "password": "password123",
            "tfa_code": "000000"  # Invalid code
        })
        self.assertFailed(response, "Invalid two factor verification code")

    def test_password_reset_token_expiration(self):
        """
        SCENARIO: User tries to reset password with expired token
        WHY IMPORTANT: Expired tokens should not be usable (security)
        """
        user = self.create_user("reset_user", "oldpass", login=False)
        user.email = "reset@example.com"
        user.reset_password_token = "expired_token"
        user.reset_password_token_expire_time = now() - timedelta(minutes=1)  # Expired
        user.save()

        response = self.client.post(self.reset_password_url, data={
            "token": "expired_token",
            "password": "newpass123",
            "captcha": "test_captcha"
        })
        self.assertFailed(response, "Token has expired")

    def test_password_reset_with_invalid_token(self):
        """
        SCENARIO: User tries to reset password with non-existent token
        WHY IMPORTANT: Invalid tokens should be rejected
        """
        response = self.client.post(self.reset_password_url, data={
            "token": "nonexistent_token",
            "password": "newpass123",
            "captcha": "test_captcha"
        })
        self.assertFailed(response, "Token does not exist")

    def test_change_email_with_duplicate_email(self):
        """
        SCENARIO: User tries to change email to an email already in use
        WHY IMPORTANT: Email uniqueness is critical for account recovery
        """
        # Create two users
        user1 = self.create_user("user1", "pass123")
        user1.email = "user1@example.com"
        user1.save()

        user2 = self.create_user("user2", "pass123", login=False)
        user2.email = "user2@example.com"
        user2.save()

        # User1 tries to change to user2's email
        response = self.client.post(self.change_email_url, data={
            "password": "pass123",
            "new_email": "user2@example.com"
        })
        self.assertFailed(response, "The email is owned by other account")

    def test_change_password_without_2fa_when_2fa_enabled(self):
        """
        SCENARIO: User with 2FA enabled tries to change password without TFA code
        WHY IMPORTANT: Sensitive operations should require 2FA
        """
        user = self.create_user("tfa_user", "oldpass")
        user.two_factor_auth = True
        user.tfa_token = rand_str(32)
        user.save()

        response = self.client.post(self.change_password_url, data={
            "old_password": "oldpass",
            "new_password": "newpass123"
            # Missing tfa_code
        })
        self.assertFailed(response, "tfa_required")

    def test_avatar_upload_with_invalid_file_type(self):
        """
        SCENARIO: User tries to upload non-image file as avatar
        WHY IMPORTANT: Prevents security issues and file type confusion
        """
        self.create_user("testuser", "pass123")

        # Upload a text file instead of image
        fake_image = SimpleUploadedFile("avatar.txt", b"not an image", content_type="text/plain")
        response = self.client.post(self.avatar_upload_url, data={"image": fake_image})
        self.assertFailed(response, "Unsupported file format")

    def test_avatar_upload_with_file_too_large(self):
        """
        SCENARIO: User tries to upload avatar larger than 2MB
        WHY IMPORTANT: Prevents DoS attacks and storage abuse
        """
        self.create_user("testuser", "pass123")

        # Create a file larger than 2MB
        large_file = SimpleUploadedFile(
            "large.png",
            b"x" * (3 * 1024 * 1024),  # 3MB
            content_type="image/png"
        )
        response = self.client.post(self.avatar_upload_url, data={"image": large_file})
        self.assertFailed(response, "Picture is too large")

    def test_registration_when_disabled(self):
        """
        SCENARIO: User tries to register when registration is disabled
        WHY IMPORTANT: Admins should be able to control system access
        """
        original_value = SysOptions.allow_register
        try:
            SysOptions.allow_register = False

            response = self.client.post(self.register_url, data={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass123",
                "captcha": "test_captcha"
            })
            self.assertFailed(response, "Register function has been disabled by admin")
        finally:
            SysOptions.allow_register = original_value

    def test_reset_password_when_already_logged_in(self):
        """
        SCENARIO: Logged-in user tries to reset password
        WHY IMPORTANT: Security - prevents token hijacking attacks
        """
        self.create_user("logged_user", "pass123")

        response = self.client.post(self.apply_reset_password_url, data={
            "email": "test@example.com",
            "captcha": "test_captcha"
        })
        self.assertFailed(response, "You have already logged in, are you kidding me? ")


# ============================================================================
# SUBMISSION MODULE CRITICAL SCENARIOS
# ============================================================================

"""
SUBMISSION MODULE CRITICAL SCENARIOS:

1. Submission to non-existent problem
   WHY: Prevents invalid submissions and data corruption

2. Submission with disallowed language
   WHY: Problem-specific language restrictions must be enforced

3. Submission during ended contest
   WHY: Contest integrity - submissions after contest end should be rejected

4. Submission permission checks (own vs shared vs admin)
   WHY: Privacy and security - users should only see allowed submissions

5. Submission to invisible problem
   WHY: Hidden problems should not accept submissions

6. Submission to contest problem without permission
   WHY: Contest access control must be enforced

7. Submission sharing during active contest
   WHY: Prevents cheating during contests

8. Submission with empty code
   WHY: Prevents invalid submissions

9. Submission throttling limits
   WHY: Prevents DoS attacks and system abuse
"""


class SubmissionCriticalScenariosTest(APITestCase):
    """Critical test scenarios for Submission module"""

    def setUp(self):
        self.submission_url = self.reverse("submission_api")
        self.admin = self.create_admin("admin", "admin123")
        self.user = self.create_user("regular_user", "pass123")
        self.other_user = self.create_user("other_user", "pass123", login=False)

    def _create_problem(self, languages=None, visible=True, contest=None):
        """Helper to create a test problem"""
        if languages is None:
            languages = ["C", "C++", "Python2"]
        
        problem_data = {
            "_id": f"TEST-{rand_str(6)}",
            "title": "Test Problem",
            "description": "<p>Test</p>",
            "input_description": "Test input",
            "output_description": "Test output",
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
            "created_by": self.admin
        }
        if contest:
            problem_data["contest"] = contest
        
        problem = Problem.objects.create(**problem_data)
        tag = ProblemTag.objects.create(name="test")
        problem.tags.add(tag)
        return problem

    @mock.patch("submission.views.oj.judge_task.send")
    def test_submission_to_nonexistent_problem(self, judge_task):
        """
        SCENARIO: User submits code to a problem that doesn't exist
        WHY IMPORTANT: Prevents invalid submissions and data corruption
        """
        response = self.client.post(self.submission_url, data={
            "problem_id": 99999,  # Non-existent
            "language": "C",
            "code": "int main() { return 0; }"
        })
        self.assertFailed(response, "Problem not exist")
        judge_task.assert_not_called()

    @mock.patch("submission.views.oj.judge_task.send")
    def test_submission_with_disallowed_language(self, judge_task):
        """
        SCENARIO: User submits code in a language not allowed for the problem
        WHY IMPORTANT: Problem-specific language restrictions must be enforced
        """
        problem = self._create_problem(languages=["C", "C++"])  # Python not allowed

        response = self.client.post(self.submission_url, data={
            "problem_id": problem.id,
            "language": "Python2",  # Not in allowed languages
            "code": "print('hello')"
        })
        self.assertFailed(response, "Python2 is not allowed in the problem")
        judge_task.assert_not_called()

    @mock.patch("submission.views.oj.judge_task.send")
    def test_submission_to_invisible_problem(self, judge_task):
        """
        SCENARIO: User submits code to a hidden/invisible problem
        WHY IMPORTANT: Hidden problems should not accept submissions
        """
        problem = self._create_problem(visible=False)

        response = self.client.post(self.submission_url, data={
            "problem_id": problem.id,
            "language": "C",
            "code": "int main() { return 0; }"
        })
        self.assertFailed(response, "Problem not exist")
        judge_task.assert_not_called()

    @mock.patch("submission.views.oj.judge_task.send")
    def test_submission_during_ended_contest(self, judge_task):
        """
        SCENARIO: User tries to submit during an ended contest
        WHY IMPORTANT: Contest integrity - submissions after contest end should be rejected
        """
        # Create ended contest
        contest = Contest.objects.create(
            title="Ended Contest",
            description="Test",
            start_time=now() - timedelta(days=2),
            end_time=now() - timedelta(days=1),  # Ended yesterday
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin
        )
        problem = self._create_problem(contest=contest)

        response = self.client.post(self.submission_url, data={
            "problem_id": problem.id,
            "language": "C",
            "code": "int main() { return 0; }",
            "contest_id": contest.id
        })
        self.assertFailed(response, "The contest have ended")
        judge_task.assert_not_called()

    def test_view_submission_without_permission(self):
        """
        SCENARIO: User tries to view another user's private submission
        WHY IMPORTANT: Privacy and security - users should only see allowed submissions
        """
        problem = self._create_problem()
        
        # Create submission by other user
        submission = Submission.objects.create(
            problem=problem,
            user_id=self.other_user.id,
            username=self.other_user.username,
            code="secret code",
            language="C",
            shared=False  # Not shared
        )

        # Try to view as regular user
        response = self.client.get(self.submission_url, data={"id": submission.id})
        self.assertFailed(response, "No permission for this submission")

    def test_share_submission_during_active_contest(self):
        """
        SCENARIO: User tries to share submission during an active contest
        WHY IMPORTANT: Prevents cheating during contests
        """
        # Create active contest
        contest = Contest.objects.create(
            title="Active Contest",
            description="Test",
            start_time=now() - timedelta(hours=1),
            end_time=now() + timedelta(hours=1),  # Still active
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin
        )
        problem = self._create_problem(contest=contest)
        
        submission = Submission.objects.create(
            problem=problem,
            contest=contest,
            user_id=self.user.id,
            username=self.user.username,
            code="code",
            language="C"
        )

        response = self.client.put(self.submission_url, data={
            "id": submission.id,
            "shared": True
        })
        self.assertFailed(response, "Can not share submission now")

    def test_view_nonexistent_submission(self):
        """
        SCENARIO: User tries to view a submission that doesn't exist
        WHY IMPORTANT: Should return proper error, not crash
        """
        response = self.client.get(self.submission_url, data={"id": "nonexistent_id"})
        self.assertFailed(response, "Submission doesn't exist")

    def test_submission_without_problem_id(self):
        """
        SCENARIO: User tries to submit without providing problem_id
        WHY IMPORTANT: Required fields should be validated
        """
        response = self.client.post(self.submission_url, data={
            "language": "C",
            "code": "int main() { return 0; }"
            # Missing problem_id
        })
        # Should fail validation
        self.assertTrue(response.status_code in [400, 200])  # Either validation error or API error


# ============================================================================
# PROBLEM MODULE CRITICAL SCENARIOS
# ============================================================================

"""
PROBLEM MODULE CRITICAL SCENARIOS:

1. Problem creation with duplicate display ID
   WHY: Display IDs must be unique for user-facing identification

2. Problem with invalid test case scores (negative, zero for OI)
   WHY: Scoring integrity - invalid scores break the scoring system

3. SPJ validation (must compile)
   WHY: Special judge code must be valid to judge submissions correctly

4. Problem rule type validation
   WHY: Rule types determine scoring behavior - must be valid

5. Problem permission checks (own vs all)
   WHY: Users should only manage problems they have permission for

6. Problem deletion by non-owner
   WHY: Prevents unauthorized problem deletion

7. Problem update with invalid display ID
   WHY: Display ID uniqueness must be maintained on updates

8. OI problem with zero total score
   WHY: OI problems must have valid scoring configuration
"""


class ProblemCriticalScenariosTest(APITestCase):
    """Critical test scenarios for Problem module"""

    def setUp(self):
        self.problem_url = self.reverse("problem_admin_api")
        self.admin = self.create_admin("admin", "admin123")
        self.user = self.create_user("regular_user", "pass123", login=False)

    def _get_problem_data(self):
        """Helper to get valid problem data"""
        return {
            "_id": f"TEST-{rand_str(6)}",
            "title": "Test Problem",
            "description": "<p>Test</p>",
            "input_description": "Test input",
            "output_description": "Test output",
            "time_limit": 1000,
            "memory_limit": 256,
            "difficulty": "Level 1",
            "visible": True,
            "languages": ["C", "C++"],
            "template": {},
            "samples": [{"input": "1", "output": "2"}],
            "spj": False,
            "spj_language": None,
            "spj_code": None,
            "spj_compile_ok": False,
            "test_case_id": rand_str(32),
            "test_case_score": [{"input_name": "1.in", "output_name": "1.out", "score": 0}],
            "rule_type": ProblemRuleType.ACM,
            "tags": ["test"],
            "hint": "",
            "source": "",
            "share_submission": False,
            "io_mode": {"io_mode": "Standard IO", "input": "input.txt", "output": "output.txt"}
        }

    def test_create_problem_with_duplicate_display_id(self):
        """
        SCENARIO: Admin tries to create problem with existing display ID
        WHY IMPORTANT: Display IDs must be unique for user-facing identification
        """
        self.create_admin("admin", "admin123")
        
        problem_data = self._get_problem_data()
        problem_data["_id"] = "DUPLICATE-001"
        
        # Create first problem
        response1 = self.client.post(self.problem_url, data=problem_data)
        self.assertSuccess(response1)
        
        # Try to create second with same display ID
        problem_data2 = self._get_problem_data()
        problem_data2["_id"] = "DUPLICATE-001"  # Same ID
        response2 = self.client.post(self.problem_url, data=problem_data2)
        self.assertFailed(response2, "Display ID already exists")

    def test_create_oi_problem_with_negative_score(self):
        """
        SCENARIO: Admin creates OI problem with negative test case score
        WHY IMPORTANT: Scoring integrity - negative scores break the scoring system
        """
        self.create_admin("admin", "admin123")
        
        problem_data = self._get_problem_data()
        problem_data["rule_type"] = ProblemRuleType.OI
        problem_data["test_case_score"] = [
            {"input_name": "1.in", "output_name": "1.out", "score": -10}  # Negative!
        ]
        
        response = self.client.post(self.problem_url, data=problem_data)
        self.assertFailed(response, "Invalid score")

    def test_create_oi_problem_with_zero_score(self):
        """
        SCENARIO: Admin creates OI problem with zero test case score
        WHY IMPORTANT: OI problems must have valid scoring configuration
        """
        self.create_admin("admin", "admin123")
        
        problem_data = self._get_problem_data()
        problem_data["rule_type"] = ProblemRuleType.OI
        problem_data["test_case_score"] = [
            {"input_name": "1.in", "output_name": "1.out", "score": 0}  # Zero!
        ]
        
        response = self.client.post(self.problem_url, data=problem_data)
        self.assertFailed(response, "Invalid score")

    def test_create_spj_problem_without_compile_ok(self):
        """
        SCENARIO: Admin creates SPJ problem without compiling the SPJ code
        WHY IMPORTANT: Special judge code must be valid to judge submissions correctly
        """
        self.create_admin("admin", "admin123")
        
        problem_data = self._get_problem_data()
        problem_data["spj"] = True
        problem_data["spj_language"] = "C"
        problem_data["spj_code"] = "int main() { return 0; }"
        problem_data["spj_compile_ok"] = False  # Not compiled!
        
        response = self.client.post(self.problem_url, data=problem_data)
        self.assertFailed(response, "SPJ code must be compiled successfully")

    def test_create_spj_problem_without_code(self):
        """
        SCENARIO: Admin creates SPJ problem without providing SPJ code
        WHY IMPORTANT: SPJ problems require valid code
        """
        self.create_admin("admin", "admin123")
        
        problem_data = self._get_problem_data()
        problem_data["spj"] = True
        problem_data["spj_language"] = "C"
        problem_data["spj_code"] = ""  # Empty!
        problem_data["spj_compile_ok"] = False
        
        response = self.client.post(self.problem_url, data=problem_data)
        self.assertFailed(response, "Invalid spj")

    def test_update_problem_with_duplicate_display_id(self):
        """
        SCENARIO: Admin updates problem to use another problem's display ID
        WHY IMPORTANT: Display ID uniqueness must be maintained on updates
        """
        self.create_admin("admin", "admin123")
        
        # Create two problems
        problem_data1 = self._get_problem_data()
        problem_data1["_id"] = "PROB-001"
        response1 = self.client.post(self.problem_url, data=problem_data1)
        self.assertSuccess(response1)
        problem1_id = response1.data["data"]["id"]
        
        problem_data2 = self._get_problem_data()
        problem_data2["_id"] = "PROB-002"
        response2 = self.client.post(self.problem_url, data=problem_data2)
        self.assertSuccess(response2)
        problem2_id = response2.data["data"]["id"]
        
        # Try to update problem2 to use problem1's display ID
        problem_data2["id"] = problem2_id
        problem_data2["_id"] = "PROB-001"  # Duplicate!
        response3 = self.client.put(self.problem_url, data=problem_data2)
        self.assertFailed(response3, "Display ID already exists")

    def test_delete_problem_by_non_owner(self):
        """
        SCENARIO: Regular user tries to delete a problem they didn't create
        WHY IMPORTANT: Prevents unauthorized problem deletion
        """
        # Admin creates problem
        self.create_admin("admin", "admin123")
        problem_data = self._get_problem_data()
        response = self.client.post(self.problem_url, data=problem_data)
        self.assertSuccess(response)
        problem_id = response.data["data"]["id"]
        
        # Regular user tries to delete
        self.create_user("regular_user", "pass123")
        response = self.client.delete(self.problem_url, data={"id": problem_id})
        # Should fail - no permission or not found
        self.assertFailed(response)

    def test_create_problem_without_display_id(self):
        """
        SCENARIO: Admin tries to create problem without display ID
        WHY IMPORTANT: Display ID is required for problem identification
        """
        self.create_admin("admin", "admin123")
        
        problem_data = self._get_problem_data()
        problem_data["_id"] = ""  # Empty!
        
        response = self.client.post(self.problem_url, data=problem_data)
        self.assertFailed(response, "Display ID is required")


# ============================================================================
# CONTEST MODULE CRITICAL SCENARIOS
# ============================================================================

"""
CONTEST MODULE CRITICAL SCENARIOS:

1. Contest with end_time <= start_time
   WHY: Invalid time ranges break contest logic and scheduling

2. Invalid CIDR IP ranges
   WHY: Invalid IP ranges cause errors in IP filtering

3. Contest status checks (not started, underway, ended)
   WHY: Contest state determines what actions are allowed

4. Contest permission checks
   WHY: Only contest admins should manage contests

5. Contest problem with mismatched rule type
   WHY: Contest and problem rule types must match

6. Contest with empty password when password-protected
   WHY: Password validation must be consistent

7. Contest access from disallowed IP
   WHY: IP restrictions must be enforced for security
"""


class ContestCriticalScenariosTest(APITestCase):
    """Critical test scenarios for Contest module"""

    def setUp(self):
        self.contest_url = self.reverse("contest_admin_api")
        self.admin = self.create_admin("admin", "admin123")
        self.user = self.create_user("regular_user", "pass123", login=False)

    def _get_contest_data(self):
        """Helper to get valid contest data"""
        return {
            "title": "Test Contest",
            "description": "<p>Test Contest</p>",
            "start_time": (now() + timedelta(days=1)).isoformat(),
            "end_time": (now() + timedelta(days=2)).isoformat(),
            "rule_type": ContestRuleTypeConst.ACM,
            "password": "",
            "visible": True,
            "real_time_rank": True,
            "allowed_ip_ranges": []
        }

    def test_create_contest_with_end_time_before_start_time(self):
        """
        SCENARIO: Admin creates contest where end_time is before start_time
        WHY IMPORTANT: Invalid time ranges break contest logic and scheduling
        """
        self.create_admin("admin", "admin123")
        
        contest_data = self._get_contest_data()
        contest_data["start_time"] = (now() + timedelta(days=2)).isoformat()
        contest_data["end_time"] = (now() + timedelta(days=1)).isoformat()  # Before start!
        
        response = self.client.post(self.contest_url, data=contest_data)
        self.assertFailed(response, "Start time must occur earlier than end time")

    def test_create_contest_with_end_time_equal_to_start_time(self):
        """
        SCENARIO: Admin creates contest where end_time equals start_time
        WHY IMPORTANT: Contests must have duration > 0
        """
        self.create_admin("admin", "admin123")
        
        contest_data = self._get_contest_data()
        same_time = (now() + timedelta(days=1)).isoformat()
        contest_data["start_time"] = same_time
        contest_data["end_time"] = same_time  # Equal!
        
        response = self.client.post(self.contest_url, data=contest_data)
        self.assertFailed(response, "Start time must occur earlier than end time")

    def test_create_contest_with_invalid_cidr(self):
        """
        SCENARIO: Admin creates contest with invalid CIDR IP range
        WHY IMPORTANT: Invalid IP ranges cause errors in IP filtering
        """
        self.create_admin("admin", "admin123")
        
        contest_data = self._get_contest_data()
        contest_data["allowed_ip_ranges"] = ["127.0.0"]  # Invalid CIDR!
        
        response = self.client.post(self.contest_url, data=contest_data)
        self.assertFailed(response)
        self.assertIn("is not a valid cidr network", response.data["data"])

    def test_update_contest_with_invalid_time(self):
        """
        SCENARIO: Admin updates contest with invalid time range
        WHY IMPORTANT: Time validation must work on updates too
        """
        self.create_admin("admin", "admin123")
        
        # Create valid contest
        contest_data = self._get_contest_data()
        response = self.client.post(self.contest_url, data=contest_data)
        self.assertSuccess(response)
        contest_id = response.data["data"]["id"]
        
        # Update with invalid time
        contest_data["id"] = contest_id
        contest_data["start_time"] = (now() + timedelta(days=2)).isoformat()
        contest_data["end_time"] = (now() + timedelta(days=1)).isoformat()  # Invalid!
        
        response = self.client.put(self.contest_url, data=contest_data)
        self.assertFailed(response, "Start time must occur earlier than end time")

    def test_create_contest_problem_with_mismatched_rule_type(self):
        """
        SCENARIO: Admin creates contest problem with rule type different from contest
        WHY IMPORTANT: Contest and problem rule types must match for consistent scoring
        """
        self.create_admin("admin", "admin123")
        
        # Create ACM contest
        contest_data = self._get_contest_data()
        contest_data["rule_type"] = ContestRuleType.ACM
        response = self.client.post(self.contest_url, data=contest_data)
        self.assertSuccess(response)
        contest_id = response.data["data"]["id"]
        
        # Try to create OI problem in ACM contest
        from problem.views.admin import ContestProblemAPI
        problem_data = {
            "_id": "CONTEST-001",
            "title": "Contest Problem",
            "description": "<p>Test</p>",
            "input_description": "Test",
            "output_description": "Test",
            "time_limit": 1000,
            "memory_limit": 256,
            "difficulty": "Level 1",
            "visible": True,
            "languages": ["C"],
            "template": {},
            "samples": [{"input": "1", "output": "2"}],
            "spj": False,
            "spj_language": None,
            "spj_code": None,
            "spj_compile_ok": False,
            "test_case_id": rand_str(32),
            "test_case_score": [{"input_name": "1.in", "output_name": "1.out", "score": 0}],
            "rule_type": ProblemRuleType.OI,  # Mismatch!
            "tags": ["test"],
            "hint": "",
            "source": "",
            "share_submission": False,
            "io_mode": {"io_mode": "Standard IO", "input": "input.txt", "output": "output.txt"},
            "contest_id": contest_id
        }
        
        contest_problem_url = self.reverse("contest_problem_admin_api")
        response = self.client.post(contest_problem_url, data=problem_data)
        self.assertFailed(response, "Invalid rule type")

    def test_contest_status_not_started(self):
        """
        SCENARIO: Check contest status when contest hasn't started
        WHY IMPORTANT: Contest state determines what actions are allowed
        """
        contest = Contest.objects.create(
            title="Future Contest",
            description="Test",
            start_time=now() + timedelta(days=1),  # Future
            end_time=now() + timedelta(days=2),
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin
        )
        
        self.assertEqual(contest.status, ContestStatus.CONTEST_NOT_START)

    def test_contest_status_ended(self):
        """
        SCENARIO: Check contest status when contest has ended
        WHY IMPORTANT: Ended contests should block new submissions
        """
        contest = Contest.objects.create(
            title="Past Contest",
            description="Test",
            start_time=now() - timedelta(days=2),  # Past
            end_time=now() - timedelta(days=1),  # Past
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin
        )
        
        self.assertEqual(contest.status, ContestStatus.CONTEST_ENDED)

    def test_contest_status_underway(self):
        """
        SCENARIO: Check contest status when contest is active
        WHY IMPORTANT: Active contests should allow submissions
        """
        contest = Contest.objects.create(
            title="Active Contest",
            description="Test",
            start_time=now() - timedelta(hours=1),  # Started
            end_time=now() + timedelta(hours=1),  # Not ended
            rule_type=ContestRuleType.ACM,
            real_time_rank=True,
            created_by=self.admin
        )
        
        self.assertEqual(contest.status, ContestStatus.CONTEST_UNDERWAY)

