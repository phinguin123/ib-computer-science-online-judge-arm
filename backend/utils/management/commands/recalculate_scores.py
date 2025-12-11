"""
Management command to recalculate user scores based on current problem point values.

This implements retroactive scoring: when problem point values change (due to more solves),
all users who solved those problems get their scores updated to reflect the current values.

Usage:
    python manage.py recalculate_scores
    python manage.py recalculate_scores --dry-run  # Preview changes without saving
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from account.models import UserProfile
from problem.models import Problem
from submission.models import JudgeStatus
from utils.scoring import calculate_problem_points


class Command(BaseCommand):
    help = 'Recalculate all user scores based on current problem point values (retroactive scoring)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each user',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Starting score recalculation...'))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        total_users = 0
        updated_users = 0
        total_score_delta = 0
        
        # Get all user profiles
        profiles = UserProfile.objects.select_related('user').all()
        
        with transaction.atomic():
            for profile in profiles:
                total_users += 1
                old_score = profile.total_score
                
                # Recalculate score from all solved problems
                new_score = 0
                solved_problems = []
                
                # Check ACM problems
                acm_problems = profile.acm_problems_status.get("problems", {})
                for problem_id, problem_data in acm_problems.items():
                    # Status can be stored as int or string in user profile
                    status = problem_data.get("status")
                    if status == JudgeStatus.ACCEPTED or status == str(JudgeStatus.ACCEPTED):
                        try:
                            problem = Problem.objects.get(id=int(problem_id))
                            current_points = problem.get_current_points()
                            new_score += current_points
                            solved_problems.append({
                                'id': problem_id,
                                '_id': problem_data.get('_id', 'N/A'),
                                'points': current_points
                            })
                        except (Problem.DoesNotExist, ValueError):
                            # Problem might have been deleted or ID is invalid
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(f'  Problem {problem_id} not found for user {profile.user.username}')
                                )
                
                # Check OI problems
                oi_problems = profile.oi_problems_status.get("problems", {})
                for problem_id, problem_data in oi_problems.items():
                    # Status can be stored as int or string in user profile
                    status = problem_data.get("status")
                    if status == JudgeStatus.ACCEPTED or status == str(JudgeStatus.ACCEPTED):
                        try:
                            problem = Problem.objects.get(id=int(problem_id))
                            # For OI, check if it's fully accepted (score matches problem points)
                            # If fully accepted, use dynamic scoring; otherwise keep partial score
                            stored_score = problem_data.get("score", 0)
                            problem_total = sum([tc.get("score", 0) for tc in problem.test_case_score])
                            
                            if stored_score >= problem_total:
                                # Fully accepted - use dynamic scoring
                                current_points = problem.get_current_points()
                                new_score += current_points
                                solved_problems.append({
                                    'id': problem_id,
                                    '_id': problem_data.get('_id', 'N/A'),
                                    'points': current_points
                                })
                            else:
                                # Partial score - keep as is
                                new_score += stored_score
                        except (Problem.DoesNotExist, ValueError):
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(f'  Problem {problem_id} not found for user {profile.user.username}')
                                )
                
                # Update if score changed
                if new_score != old_score:
                    updated_users += 1
                    score_delta = new_score - old_score
                    total_score_delta += score_delta
                    
                    if verbose:
                        self.stdout.write(
                            f'User {profile.user.username}: {old_score} -> {new_score} (Δ{score_delta:+d})'
                        )
                        if solved_problems:
                            self.stdout.write(f'  Solved {len(solved_problems)} problems')
                    
                    if not dry_run:
                        # Persist new total_score, then update tier
                        profile.total_score = new_score
                        profile.save(update_fields=["total_score"])
                        profile.update_tier()  # recalculates and saves tier if needed
                
            if dry_run:
                # Rollback transaction in dry-run mode
                transaction.set_rollback(True)
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'Total users processed: {total_users}'))
        self.stdout.write(self.style.SUCCESS(f'Users with score changes: {updated_users}'))
        if updated_users > 0:
            self.stdout.write(self.style.SUCCESS(f'Total score delta: {total_score_delta:+d}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write(self.style.SUCCESS('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS('\nScore recalculation completed!'))

