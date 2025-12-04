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
    LOW = "Low"
    MID = "Mid"
    HIGH = "High"


class TierConfig:
    # (Threshold Score, Tier Name)
    # The logic checks from TOP to BOTTOM.
    # The first threshold your score beats is your tier.
    THRESHOLDS = [
        (5000, "Master"),       # 5000+ = Master (Shiny Hologram!)
        
        (4500, "Diamond 1"),
        (4000, "Diamond 2"),
        (3500, "Diamond 3"),
        (3000, "Diamond 4"),
        
        (2500, "Platinum 1"),
        (2250, "Platinum 2"),
        (2000, "Platinum 3"),
        (1750, "Platinum 4"),
        
        (1500, "Gold 1"),
        (1250, "Gold 2"),
        (1000, "Gold 3"),
        (800,  "Gold 4"),
        
        (600,  "Silver 1"),
        (450,  "Silver 2"),
        (300,  "Silver 3"),
        (150,  "Silver 4"),
        
        (100,  "Bronze 1"),
        (60,   "Bronze 2"),
        (30,   "Bronze 3"),
        (0,    "Bronze 4"),    # Everyone starts here
    ]

    @staticmethod
    def get_tier(score):
        """
        Input: Integer (e.g. 1550)
        Output: String (e.g. "Gold 1")
        """
        # Handle negative scores (if you implement penalties later)
        if score < 0:
            return "Bronze 4"
            
        for threshold, tier_name in TierConfig.THRESHOLDS:
            if score >= threshold:
                return tier_name
                
        # Fallback (shouldn't happen if 0 is in the list)
        return "Bronze 4"


CONTEST_PASSWORD_SESSION_KEY = "contest_password"
