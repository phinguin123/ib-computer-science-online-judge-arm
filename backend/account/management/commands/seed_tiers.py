from django.core.management.base import BaseCommand
from account.models import User, UserProfile
from utils.constants import TierConfig
import random

class Command(BaseCommand):
    help = 'Generates dummy users for every tier level'

    def handle(self, *args, **options):
        self.stdout.write("Seeding users...")

        # Delete old test users first (optional, keeps it clean)
        User.objects.filter(username__startswith="player_").delete()

        # Get all the thresholds we defined in constants.py
        # We also want to test "Unranked" (0 submissions)
        scenarios = [
            ("player_unranked", 0, 0),
        ]

        # Add a player for every threshold in your config
        for threshold, tier_name in TierConfig.THRESHOLDS:
            # Create a username like 'player_gold_1'
            safe_name = tier_name.lower().replace(" ", "_")
            username = f"player_{safe_name}"
            # Give them the exact threshold score + 5 extra points
            score = threshold + 5
            scenarios.append((username, score, 10)) # 10 submissions

        for username, score, submissions in scenarios:
            # 1. Create the base User
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password("123456")
                user.email = f"{username}@example.com"
                user.save()

            # 2. Create or Get the Profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            
            # 3. Set the stats
            profile.submission_number = submissions
            profile.accepted_number = submissions
            profile.total_score = score
            
            # 4. Save (This triggers your logic to update the Tier string)
            profile.save()
            
            self.stdout.write(f"Created {username}: Score {score} -> Tier {profile.tier}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded users!'))