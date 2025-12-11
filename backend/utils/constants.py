class Choices:
    @classmethod
    def choices(cls):
        d = cls.__dict__
        return [d[item] for item in d.keys() if not item.startswith("__")]


class ContestType:
    PUBLIC_CONTEST = "Public"
    PASSWORD_PROTECTED_CONTEST = "Password Protected"


class ContestStatus:
    CONTEST_NOT_START = "1"
    CONTEST_ENDED = "-1"
    CONTEST_UNDERWAY = "0"


class ContestRuleType(Choices):
    ACM = "ACM"
    OI = "OI"


class CacheKey:
    waiting_queue = "waiting_queue"
    contest_rank_cache = "contest_rank_cache"
    website_config = "website_config"


class Difficulty(Choices):
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"
    LEVEL_4 = "Level 4"
    LEVEL_5 = "Level 5"
    
    # Legacy support - map old values to new levels
    LOW = "Level 1"
    MID = "Level 3"
    HIGH = "Level 5"


class TierConfig:
    # (Threshold Score, Tier Name)
    # The logic checks from TOP to BOTTOM.
    # The first threshold your score beats is your tier.
    # Updated thresholds per requirements
    THRESHOLDS = [
        (5005, "Master"),       # 5005+ = Master
        
        (4505, "Diamond 1"),
        (4005, "Diamond 2"),
        (3505, "Diamond 3"),
        (3005, "Diamond 4"),
        
        (2505, "Platinum 1"),
        (2255, "Platinum 2"),
        (2005, "Platinum 3"),
        (1755, "Platinum 4"),
        
        (1505, "Gold 1"),
        (1255, "Gold 2"),
        (1005, "Gold 3"),
        (805,  "Gold 4"),
        
        (605,  "Silver 1"),
        (455,  "Silver 2"),
        (305,  "Silver 3"),
        (155,  "Silver 4"),
        
        (105,  "Bronze 1"),
        (65,   "Bronze 2"),
        (35,   "Bronze 3"),
        (5,    "Bronze 4"),
        
        (0,    "Unranked"),     # 0 points = Unranked
    ]

    @staticmethod
    def get_tier(score):
        """
        Input: Integer (e.g. 1550)
        Output: String (e.g. "Gold 1")
        """
        # Handle negative scores
        if score < 0:
            return "Unranked"
        
        # If score is 0, return Unranked
        if score == 0:
            return "Unranked"
            
        for threshold, tier_name in TierConfig.THRESHOLDS:
            if score >= threshold:
                return tier_name
                
        # Fallback (shouldn't happen if 0 is in the list)
        return "Unranked"


CONTEST_PASSWORD_SESSION_KEY = "contest_password"
