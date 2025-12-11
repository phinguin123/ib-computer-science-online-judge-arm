"""
Hybrid Dynamic Scoring System for Online Judge Platform

This module implements:
1. 5-Level Difficulty Configuration with Base/Max Points
2. Logarithmic Decay Scoring Formula
3. User Rank Determination
"""

from typing import Dict, Tuple


class DifficultyConfig:
    """
    Configuration for 5 difficulty levels.
    Each level has a Base (Floor) and Max (Ceiling) point value.
    """
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"
    LEVEL_4 = "Level 4"
    LEVEL_5 = "Level 5"
    
    # Difficulty configuration: (Base Points, Max Points, Decay Factor)
    # Decay Factor: Lower = faster decay, Higher = slower decay
    CONFIG: Dict[str, Tuple[int, int, int]] = {
        LEVEL_1: (5, 30, 50),      # Easy: Slow decay (many solves expected)
        LEVEL_2: (20, 80, 50),     # Easy-Medium: Slow decay
        LEVEL_3: (50, 200, 30),    # Medium: Moderate decay
        LEVEL_4: (150, 500, 15),   # Hard: Faster decay
        LEVEL_5: (300, 1200, 10),  # Very Hard: Fastest decay
    }
    
    @classmethod
    def get_base_points(cls, difficulty_level: str) -> int:
        """Get the base (floor) points for a difficulty level."""
        return cls.CONFIG.get(difficulty_level, (5, 30, 50))[0]
    
    @classmethod
    def get_max_points(cls, difficulty_level: str) -> int:
        """Get the max (ceiling) points for a difficulty level."""
        return cls.CONFIG.get(difficulty_level, (5, 30, 50))[1]
    
    @classmethod
    def get_decay_factor(cls, difficulty_level: str) -> int:
        """Get the decay factor for a difficulty level."""
        return cls.CONFIG.get(difficulty_level, (5, 30, 50))[2]
    
    @classmethod
    def is_valid_difficulty(cls, difficulty_level: str) -> bool:
        """Check if a difficulty level is valid."""
        return difficulty_level in cls.CONFIG


def calculate_problem_points(difficulty_level: str, solve_count: int) -> int:
    """
    Calculate the current points for a problem using logarithmic decay.
    
    Formula: CurrentScore = MinScore + (MaxScore - MinScore) / (1 + (SolveCount / DecayFactor))
    
    Args:
        difficulty_level: One of DifficultyConfig.LEVEL_1 through LEVEL_5
        solve_count: Number of users who have solved this problem (accepted_number)
    
    Returns:
        Current point value for the problem (rounded to nearest integer)
    """
    if not DifficultyConfig.is_valid_difficulty(difficulty_level):
        # Fallback to Level 1 if invalid difficulty
        difficulty_level = DifficultyConfig.LEVEL_1
    
    base_points = DifficultyConfig.get_base_points(difficulty_level)
    max_points = DifficultyConfig.get_max_points(difficulty_level)
    decay_factor = DifficultyConfig.get_decay_factor(difficulty_level)
    
    # Logarithmic decay formula
    if solve_count == 0:
        # No solves yet, return max points
        current_score = max_points
    else:
        # Apply decay formula
        score_range = max_points - base_points
        decay_ratio = 1 + (solve_count / decay_factor)
        current_score = base_points + (score_range / decay_ratio)
    
    # Round to nearest integer
    return int(round(current_score))


def get_user_rank(total_points: int) -> str:
    """
    Determine user rank based on total points.
    
    Args:
        total_points: User's total accumulated points
    
    Returns:
        Rank name as string (e.g., "Master", "Diamond 1", "Bronze 4", "Unranked")
    """
    from utils.constants import TierConfig
    return TierConfig.get_tier(total_points)

