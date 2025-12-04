from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db import models
from utils.models import JSONField
from utils.constants import TierConfig


class AdminType(object):
    REGULAR_USER = "Regular User"
    ADMIN = "Admin"
    SUPER_ADMIN = "Super Admin"


class ProblemPermission(object):
    NONE = "None"
    OWN = "Own"
    ALL = "All"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('admin_type', AdminType.REGULAR_USER)
        extra_fields.setdefault('problem_permission', ProblemPermission.NONE)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        # This is where we force the user to be a Super Admin
        extra_fields.setdefault('admin_type', AdminType.SUPER_ADMIN)
        extra_fields.setdefault('problem_permission', ProblemPermission.ALL)
        extra_fields.setdefault('open_api', True)

        if extra_fields.get('admin_type') != AdminType.SUPER_ADMIN:
            raise ValueError('Superuser must have admin_type=AdminType.SUPER_ADMIN.')

        return self._create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser):
    username = models.TextField(unique=True)
    email = models.TextField(null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    # One of UserType
    admin_type = models.TextField(default=AdminType.REGULAR_USER)
    problem_permission = models.TextField(default=ProblemPermission.NONE)
    reset_password_token = models.TextField(null=True)
    reset_password_token_expire_time = models.DateTimeField(null=True)
    # SSO auth token
    auth_token = models.TextField(null=True)
    two_factor_auth = models.BooleanField(default=False)
    tfa_token = models.TextField(null=True)
    session_keys = JSONField(default=list)
    # open api key
    open_api = models.BooleanField(default=False)
    open_api_appkey = models.TextField(null=True)
    is_disabled = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"] # Added email here so CLI asks for it

    objects = UserManager()

    def is_admin(self):
        return self.admin_type == AdminType.ADMIN

    def is_super_admin(self):
        return self.admin_type == AdminType.SUPER_ADMIN

    def is_admin_role(self):
        return self.admin_type in [AdminType.ADMIN, AdminType.SUPER_ADMIN]

    def can_mgmt_all_problem(self):
        return self.problem_permission == ProblemPermission.ALL

    def is_contest_admin(self, contest):
        return self.is_authenticated and (contest.created_by == self or self.admin_type == AdminType.SUPER_ADMIN)
    
    @property
    def is_staff(self):
        # Django Admin asks: "Is this user staff?"
        # We answer: "Yes, if they are an Admin or Super Admin."
        return self.admin_type in [AdminType.ADMIN, AdminType.SUPER_ADMIN]

    @property
    def is_superuser(self):
        # Django asks: "Is this a superuser?"
        # We answer: "Yes, if admin_type is Super Admin."
        return self.admin_type == AdminType.SUPER_ADMIN

    def has_perm(self, perm, obj=None):
        # Django asks: "Does this user have permission X?"
        # We answer: "Yes, if they are a superuser, they can do anything."
        return self.is_superuser

    def has_module_perms(self, app_label):
        # Django asks: "Can this user see this app?"
        # We answer: "Yes, if they are a superuser."
        return self.is_superuser

    class Meta:
        db_table = "user"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    acm_problems_status = JSONField(default=dict)
    # like acm_problems_status, merely add "score" field
    oi_problems_status = JSONField(default=dict)

    real_name = models.TextField(null=True)
    avatar = models.TextField(default=f"{settings.AVATAR_URI_PREFIX}/default.png")
    blog = models.URLField(null=True)
    mood = models.TextField(null=True)
    github = models.TextField(null=True)
    school = models.TextField(null=True)
    major = models.TextField(null=True)
    language = models.TextField(null=True)
    
    # for ACM
    accepted_number = models.IntegerField(default=0)
    
    # for OI & Leaderboard
    total_score = models.BigIntegerField(default=0)
    tier = models.TextField(default="Unranked")
    submission_number = models.IntegerField(default=0)

    def add_accepted_problem_number(self):
        self.accepted_number = models.F("accepted_number") + 1
        self.save()

    def add_submission_number(self):
        self.submission_number = models.F("submission_number") + 1
        self.save()

    def add_score(self, this_time_score, last_time_score=None):
        """
        This function is called when a user solves a problem.
        """
        last_time_score = last_time_score or 0
        
        # 1. Update the score in the database using F expression (safe for concurrency)
        self.total_score = models.F("total_score") - last_time_score + this_time_score
        self.save()
        
        # 2. We must refresh to get the actual integer value after the F() operation
        self.refresh_from_db()
        
        # 3. Calculate the new Tier
        self.update_tier()

    def update_tier(self):
        # LOGIC CHANGE:
        # If they haven't submitted anything yet, they are Unranked.
        if self.submission_number == 0:
            new_tier = "Unranked"
        else:
            new_tier = TierConfig.get_tier(self.total_score)
        
        if self.tier != new_tier:
            self.tier = new_tier
            self.save(update_fields=['tier'])

    def save(self, *args, **kwargs):
        if self.pk:
            # Check logic on every save
            if self.submission_number == 0:
                 self.tier = "Unranked"
            else:
                 # If admin manually sets score, we update tier
                 correct_tier = TierConfig.get_tier(self.total_score)
                 if self.tier != correct_tier:
                     self.tier = correct_tier
                
        super().save(*args, **kwargs)

    class Meta:
        db_table = "user_profile"