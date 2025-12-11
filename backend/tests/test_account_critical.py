from datetime import timedelta
from unittest import mock

from django.utils.timezone import now
from django.core.files.uploadedfile import SimpleUploadedFile

from utils.api.tests import APITestCase, APIClient
from utils.shortcuts import rand_str
from options.options import SysOptions
from account.models import User


class AccountCriticalTests(APITestCase):
    """
    Critical account scenarios focusing on security and data integrity.
    """

    def setUp(self):
        self.client = APIClient()
        self.register_url = self.reverse("user_register_api")
        self.login_url = self.reverse("user_login_api")
        self.change_password_url = self.reverse("user_change_password_api")
        self.change_email_url = self.reverse("user_change_email_api")
        self.reset_password_url = self.reverse("reset_password_api")
        self.apply_reset_password_url = self.reverse("apply_reset_password_api")
        self.avatar_upload_url = self.reverse("avatar_upload_api")

    # -------- Helpers --------
    def _enable_2fa(self, user):
        user.two_factor_auth = True
        user.tfa_token = rand_str(32)
        user.save()
        return user.tfa_token

    def _create_registered_user(self, username="user1", email="user1@example.com"):
        user = self.create_user(username, "pass123", login=False)
        user.email = email
        user.save()
        return user

    # -------- Registration Duplicate (username/email) --------
    @mock.patch("utils.captcha.Captcha.check", return_value=True)
    def test_registration_duplicate_username(self, _):
        first_payload = {
            "username": "dupuser",
            "email": "first@example.com",
            "password": "pass123",
            "captcha": "abcd",
        }
        second_payload = {
            "username": "dupuser",  # duplicate username
            "email": "second@example.com",
            "password": "pass123",
            "captcha": "abcd",
        }
        self.assertSuccess(self.client.post(self.register_url, data=first_payload))
        resp = self.client.post(self.register_url, data=second_payload)
        self.assertFailed(resp, "Username already exists")

    @mock.patch("utils.captcha.Captcha.check", return_value=True)
    def test_registration_duplicate_email(self, _):
        first_payload = {
            "username": "dupuser1",
            "email": "same@example.com",
            "password": "pass123",
            "captcha": "abcd",
        }
        second_payload = {
            "username": "dupuser2",
            "email": "same@example.com",  # duplicate email
            "password": "pass123",
            "captcha": "abcd",
        }
        self.assertSuccess(self.client.post(self.register_url, data=first_payload))
        resp = self.client.post(self.register_url, data=second_payload)
        self.assertFailed(resp, "Email already exists")

    # -------- Login Disabled --------
    def test_login_disabled_account(self):
        user = self._create_registered_user("disabled_user", "disabled@example.com")
        user.is_disabled = True
        user.save()
        resp = self.client.post(self.login_url, data={"username": user.username, "password": "pass123"})
        self.assertDictEqual(resp.data, {"error": "error", "data": "Your account has been disabled"})
        self.assertIn(resp.status_code, (200, 401, 403))

    # -------- 2FA Failures --------
    def test_login_2fa_without_code(self):
        user = self._create_registered_user("tfa_user", "tfa@example.com")
        self._enable_2fa(user)
        resp = self.client.post(self.login_url, data={"username": user.username, "password": "pass123"})
        self.assertFailed(resp, "tfa_required")

    def test_login_2fa_wrong_code(self):
        user = self._create_registered_user("tfa_user2", "tfa2@example.com")
        token = self._enable_2fa(user)
        wrong_code = "000000" if len(token) else "000000"
        resp = self.client.post(
            self.login_url,
            data={"username": user.username, "password": "pass123", "tfa_code": wrong_code},
        )
        self.assertFailed(resp, "Invalid two factor verification code")

    # -------- Token Expiration --------
    @mock.patch("utils.captcha.Captcha.check", return_value=True)
    def test_password_reset_token_expired(self, _):
        user = self._create_registered_user("reset_user", "reset@example.com")
        user.reset_password_token = "expired_token"
        user.reset_password_token_expire_time = now() - timedelta(minutes=1)
        user.save()

        resp = self.client.post(
            self.reset_password_url,
            data={"token": "expired_token", "password": "newpass123", "captcha": "abcd"},
        )
        self.assertFailed(resp, "Token has expired")

    # -------- Email Change Duplicate --------
    def test_email_change_duplicate(self):
        user_a = self._create_registered_user("user_a", "a@example.com")
        user_b = self._create_registered_user("user_b", "b@example.com")
        self.client.login(username=user_a.username, password="pass123")

        resp = self.client.post(
            self.change_email_url,
            data={"password": "pass123", "new_email": user_b.email},
        )
        self.assertFailed(resp, "The email is owned by other account")

    # -------- Avatar Upload Validation --------
    def test_avatar_upload_invalid_type(self):
        self.create_user("avatar_user", "pass123")
        bad_file = SimpleUploadedFile("malware.exe", b"FAKEEXE", content_type="application/octet-stream")
        resp = self.client.post(self.avatar_upload_url, data={"image": bad_file}, format="multipart")
        self.assertFailed(resp, "Unsupported file format")

    def test_avatar_upload_too_large(self):
        self.create_user("avatar_user2", "pass123")
        big_bytes = b"x" * (50 * 1024 * 1024)  # 50MB
        big_file = SimpleUploadedFile("big.png", big_bytes, content_type="image/png")
        resp = self.client.post(self.avatar_upload_url, data={"image": big_file}, format="multipart")
        self.assertFailed(resp, "Picture is too large")

    # -------- Registration Disabled --------
    @mock.patch("utils.captcha.Captcha.check", return_value=True)
    def test_registration_disabled_by_config(self, _):
        original = SysOptions.allow_register
        try:
            SysOptions.allow_register = False
            resp = self.client.post(
                self.register_url,
                data={"username": "blocked", "email": "blocked@example.com", "password": "pass123", "captcha": "abcd"},
            )
            self.assertFailed(resp, "Register function has been disabled by admin")
        finally:
            SysOptions.allow_register = original

    # -------- Password Change Requires 2FA --------
    def test_password_change_requires_2fa(self):
        user = self._create_registered_user("pw_user", "pw@example.com")
        self.client.login(username=user.username, password="pass123")
        self._enable_2fa(user)

        resp = self.client.post(
            self.change_password_url,
            data={"old_password": "pass123", "new_password": "newpass123"},
        )
        self.assertFailed(resp, "tfa_required")

    # -------- Reset Password While Logged In --------
    @mock.patch("utils.captcha.Captcha.check", return_value=True)
    def test_reset_password_while_logged_in(self, _):
        user = self._create_registered_user("logged_in", "logged@example.com")
        self.client.login(username=user.username, password="pass123")
        resp = self.client.post(
            self.apply_reset_password_url,
            data={"email": "logged@example.com", "captcha": "abcd"},
        )
        self.assertFailed(resp, "You have already logged in, are you kidding me? ")

