import requests
import json
import re
import os
from typing import Set, List
from datetime import datetime

class DictionaryGenerator:
    def __init__(self):
        self.min_word_length = 3  # Changed to 3 as requested
        self.max_word_length = 8
        self.valid_words: Set[str] = set()
    
    def fetch_word_list(self) -> List[str]:
        """Fetch words from frequency-based source for highest quality"""
        frequency_url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_50k.txt"
        
        all_words = []
        
        try:
            response = requests.get(frequency_url, timeout=30)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    # Split by space and take the first part (the word)
                    parts = line.strip().split()
                    if len(parts) >= 2:  # Ensure we have both word and frequency
                        word = parts[0].upper()
                        frequency = int(parts[1])
                        
                        # Only include words with reasonable frequency (filter out very rare words)
                        if frequency >= 1000:  # Minimum frequency threshold
                            all_words.append(word)
            
            print(f"Loaded {len(all_words)} frequency-based words")
            
        except Exception as e:
            print(f"Failed to load from frequency source: {e}")
            # Fallback to a basic word list if frequency source fails
            try:
                fallback_url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa.txt"
                response = requests.get(fallback_url, timeout=30)
                fallback_words = [line.strip().upper() for line in response.text.strip().split('\n') 
                                if line.strip() and len(line.strip()) >= 3]
                all_words.extend(fallback_words)
                print(f"Used fallback source with {len(fallback_words)} words")
            except:
                print("All sources failed")
        
        return all_words
    
    def is_common_word_pattern(self, word: str) -> bool:
        """Check if word follows common English patterns"""
        # Common English endings that indicate real words
        common_endings = [
            'ING', 'ION', 'TION', 'SION', 'NESS', 'MENT', 'ABLE', 'IBLE', 
            'FUL', 'LESS', 'LY', 'ED', 'ER', 'EST', 'AL', 'IC', 'OUS', 'IVE'
        ]
        
        # Common prefixes
        common_prefixes = [
            'UN', 'RE', 'IN', 'DIS', 'EN', 'NON', 'OVER', 'MIS', 'SUB', 
            'PRE', 'INTER', 'FORE', 'DE', 'TRANS', 'SUPER', 'SEMI', 'ANTI'
        ]
        
        # Check for common patterns
        has_common_ending = any(word.endswith(ending) for ending in common_endings)
        has_common_prefix = any(word.startswith(prefix) for prefix in common_prefixes)
        
        # Short words are usually common if they made it to our sources
        is_short = len(word) <= 5
        
        return has_common_ending or has_common_prefix or is_short
    
    def is_valid_word(self, word: str) -> bool:
        """Enhanced word validation focusing on commonly known words"""
        if not word or len(word) < self.min_word_length or len(word) > self.max_word_length:
            return False
        
        if not word.isalpha() or not word.isupper():
            return False
        
        # Filter out very uncommon letter combinations
        uncommon_patterns = [
            r'^[BCDFGHJKLMNPQRSTVWXYZ]{5,}$',  # Too many consonants in a row
            r'^[XZ][^AEIOU]',  # X or Z followed by consonant (very rare)
            r'QU[^AEIOU]',  # QU not followed by vowel
            r'(.)\1{3,}',  # More than 3 repeated characters
            r'[BCDFGHJKLMNPQRSTVWXYZ]{4,}',  # 4+ consonants in a row anywhere
            r'^[AEIOU]{3,}',  # 3+ vowels at start
        ]
        
        for pattern in uncommon_patterns:
            if re.search(pattern, word):
                return False
        
        # Additional filters for very obscure words
        # Skip words with rare letter combinations
        rare_combinations = ['CWM', 'CWR', 'GYP', 'HMM', 'PHY', 'PSY', 'RHY', 'SHM', 'THM']
        if any(combo in word for combo in rare_combinations) and len(word) > 5:
            return False
        
        return True
    
    def filter_words(self, words: List[str]) -> List[str]:
        """Filter words based on game requirements and common usage"""
        filtered_words = []
        
        for word in words:
            if self.is_valid_word(word):
                filtered_words.append(word)
        
        # Since words are already in frequency order, we keep that order
        # Add curated essential words at the end to fill any gaps
        curated_words = self.get_curated_common_words()
        
        # Combine but avoid duplicates while preserving frequency order
        seen = set(filtered_words)
        for word in curated_words:
            if word not in seen:
                filtered_words.append(word)
                seen.add(word)
        
        print(f"Filtered to {len(filtered_words)} words from {len(words)} original words")
        print(f"Words are ordered by frequency (most common first)")
        
        return filtered_words
    
    def get_curated_common_words(self) -> List[str]:
        """Add a curated list of definitely valid common words"""
        # Essential words that should definitely be in any word game
        essential_words = [
            # 3-letter words
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER", "WAS", "ONE", "OUR",
            "OUT", "DAY", "GET", "HAS", "HIM", "HIS", "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "SEE",
            "TWO", "WHO", "BOY", "DID", "CAR", "EAT", "END", "FAR", "FUN", "GOT", "GUN", "HOT", "JOB",
            "LET", "LOT", "MAN", "MAP", "MOM", "RUN", "SUN", "TOP", "TRY", "USE", "WAR", "WAY", "WIN",
            "BAD", "BAG", "BAT", "BED", "BIG", "BOX", "BUS", "BUY", "CAT", "CUP", "CUT", "DOG", "EGG",
            "EYE", "FLY", "FOX", "HAT", "HIT", "ICE", "KEY", "KID", "LAW", "LEG", "LIE", "LOG", "LOW",
            "MAD", "NET", "OIL", "PAN", "PEN", "PET", "PIE", "PIG", "POT", "RED", "ROW", "SAD", "SAT",
            "SKY", "TEA", "TOY", "VAN", "WET", "YES", "ZOO", "ARM", "ART", "ASK", "BAY", "BIT", "COW",
            "CRY", "EAR", "FAN", "FEW", "FIG", "FIT", "FOG", "GAP", "GAS", "GOD", "HAD", "HAM", "HEN",
            "HID", "JAM", "LAD", "LAP", "LAY", "LID", "LIP", "MUD", "NUT", "ODD", "OWN", "PAY", "POP",
            "RAG", "RAT", "RID", "RUG", "SIN", "SIT", "SIX", "TAX", "TEN", "TIE", "TIP", "WIG", "WIN",
            
            # 4-letter words
            "THAT", "WITH", "HAVE", "THIS", "WILL", "YOUR", "FROM", "THEY", "KNOW", "WANT", "BEEN",
            "GOOD", "MUCH", "SOME", "TIME", "VERY", "WHEN", "COME", "HERE", "JUST", "LIKE", "LONG",
            "MAKE", "MANY", "OVER", "SUCH", "TAKE", "THAN", "THEM", "WELL", "WERE", "WHAT", "WORD",
            "WORK", "YEAR", "BACK", "CALL", "CAME", "EACH", "EVEN", "FIND", "GIVE", "HAND", "HIGH",
            "KEEP", "LAST", "LEFT", "LIFE", "LIVE", "LOOK", "MADE", "MOVE", "NAME", "NEED", "NEXT",
            "OPEN", "PART", "PLAY", "SAID", "SAME", "SEEM", "SHOW", "SIDE", "TELL", "TURN", "USED",
            "WAYS", "WEEK", "WENT", "ABLE", "BOOK", "DOES", "FACT", "FEEL", "FOUR", "FREE", "GAVE",
            "GOES", "HELP", "HOME", "IDEA", "INTO", "KIND", "KNEW", "LATE", "LESS", "LINE", "LIST",
            "LOVE", "MIND", "MOST", "NEAR", "ONCE", "ONLY", "REAL", "ROOM", "SEEN", "SURE", "TALK",
            "TREE", "UPON", "WALK", "WALL", "WIFE", "WIND", "WISH", "BLUE", "CLUB", "COLD", "COOL",
            "DOOR", "DUCK", "DUCK", "FACE", "FAST", "FISH", "GIRL", "GOLD", "HAIR", "HALF", "HALL",
            "HEAD", "HEAR", "HELD", "HOPE", "HOUR", "JUMP", "KEEP", "KING", "LAND", "LEAD", "LOSE",
            "MAIN", "MILK", "MOON", "NOTE", "PAIN", "PICK", "PLAN", "POOL", "POOR", "PULL", "PUSH",
            "RACE", "RAIN", "READ", "RICH", "ROCK", "ROLE", "ROLL", "RULE", "SAFE", "SALE", "SAVE",
            "SEAT", "SELL", "SEND", "SHOP", "SHUT", "SICK", "SIGN", "SING", "SIZE", "SKIN", "SLOW",
            "SNOW", "SOFT", "SOLD", "SONG", "SORT", "STAY", "STEP", "STOP", "SWIM", "TALL", "TEAM",
            "TOLD", "TOOL", "TOWN", "TRIP", "TRUE", "TURN", "TWIN", "TYPE", "VIEW", "WAIT", "WAKE",
            "WARM", "WASH", "WAVE", "WEAR", "WEEK", "WEST", "WIDE", "WILD", "WINE", "WISE", "WOOD",
            "YARD", "ZERO", "ZONE",
            
            # 5+ letter words (most common)
            "ABOUT", "AFTER", "AGAIN", "AGAINST", "ALONE", "ALONG", "AMONG", "ANGRY", "APART", "APPLE",
            "ARGUE", "AROUND", "ARRIVE", "BASIC", "BEACH", "BEGAN", "BEGIN", "BEING", "BELOW", "BIRTH",
            "BLACK", "BLOOD", "BOARD", "BOUND", "BRAIN", "BREAD", "BREAK", "BRING", "BROAD", "BROKE",
            "BROWN", "BUILD", "CARRY", "CATCH", "CAUSE", "CHAIN", "CHAIR", "CHEAP", "CHECK", "CHEST",
            "CHILD", "CHINA", "CHOSE", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLIMB", "CLOCK", "CLOSE",
            "CLOUD", "COACH", "COAST", "COULD", "COUNT", "COURT", "COVER", "CROWD", "DANCE", "DEATH",
            "DOING", "DOUBT", "DOZEN", "DRAMA", "DRANK", "DREAM", "DRESS", "DRINK", "DRIVE", "DROVE",
            "EARLY", "EARTH", "ENEMY", "ENJOY", "ENTER", "EQUAL", "ERROR", "EVENT", "EVERY", "EXACT",
            "EXIST", "EXTRA", "FAITH", "FALSE", "FAULT", "FIELD", "FIFTH", "FIFTY", "FIGHT", "FINAL",
            "FIRST", "FLOOR", "FOCUS", "FORCE", "FORTH", "FORTY", "FOUND", "FRAME", "FRESH", "FRONT",
            "FRUIT", "FULLY", "FUNNY", "GLASS", "GRACE", "GRADE", "GRAND", "GRANT", "GRASS", "GREAT",
            "GREEN", "GROSS", "GROUP", "GROWN", "GUARD", "GUESS", "GUEST", "GUIDE", "HAPPY", "HEARD",
            "HEART", "HEAVY", "HORSE", "HOTEL", "HOUSE", "HUMAN", "HURRY", "IMAGE", "INDEX", "INNER",
            "INPUT", "ISSUE", "JAPAN", "JOINT", "JUDGE", "KNIFE", "KNOCK", "KNOWN", "LABEL", "LARGE",
            "LASER", "LATER", "LAUGH", "LAYER", "LEARN", "LEASE", "LEAST", "LEAVE", "LEGAL", "LEVEL",
            "LIGHT", "LIMIT", "LIVED", "LOCAL", "LOOSE", "LOWER", "LUCKY", "LUNCH", "LYING", "MAGIC",
            "MAJOR", "MAKER", "MARCH", "MATCH", "MAYBE", "MAYOR", "MEANT", "METAL", "MIGHT", "MINOR",
            "MINUS", "MIXED", "MODEL", "MONEY", "MONTH", "MORAL", "MOTOR", "MOUNT", "MOUSE", "MOUTH",
            "MOVED", "MOVIE", "MUSIC", "NEEDS", "NEVER", "NEWLY", "NIGHT", "NOISE", "NORTH", "NOTED",
            "NOVEL", "NURSE", "OCCUR", "OCEAN", "OFFER", "OFTEN", "ORDER", "OTHER", "OUGHT", "PAINT",
            "PANEL", "PAPER", "PARTY", "PEACE", "PHONE", "PHOTO", "PIANO", "PIECE", "PILOT", "PITCH",
            "PLACE", "PLAIN", "PLANE", "PLANT", "PLATE", "POINT", "POUND", "POWER", "PRESS", "PRICE",
            "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE", "PROOF", "PROUD", "PROVE", "QUEEN", "QUICK",
            "QUIET", "QUITE", "RADIO", "RAISE", "RANGE", "RAPID", "RATIO", "REACH", "READY", "REFER",
            "RELAX", "RIDER", "RIGHT", "RIVAL", "RIVER", "ROBOT", "ROGER", "ROMAN", "ROUGH", "ROUND",
            "ROUTE", "ROYAL", "RURAL", "SCALE", "SCENE", "SCOPE", "SCORE", "SENSE", "SERVE", "SEVEN",
            "SHALL", "SHAPE", "SHARE", "SHARP", "SHEET", "SHELF", "SHELL", "SHIFT", "SHINE", "SHIRT",
            "SHOCK", "SHOOT", "SHORT", "SHOWN", "SIGHT", "SILLY", "SINCE", "SIXTH", "SIXTY", "SIZED",
            "SKILL", "SLEEP", "SLIDE", "SMALL", "SMART", "SMILE", "SMOKE", "SNAKE", "SOLID", "SOLVE",
            "SORRY", "SOUND", "SOUTH", "SPACE", "SPARE", "SPEAK", "SPEED", "SPEND", "SPENT", "SPLIT",
            "SPOKE", "SPORT", "STAFF", "STAGE", "STAKE", "STAND", "START", "STATE", "STEAM", "STEEL",
            "STICK", "STILL", "STOCK", "STONE", "STOOD", "STORE", "STORM", "STORY", "STRIP", "STUCK",
            "STUDY", "STUFF", "STYLE", "SUGAR", "SUPER", "SWEET", "SWIFT", "SWING", "TABLE", "TAKEN",
            "TASTE", "TAXES", "TEACH", "TERMS", "TERRY", "THANK", "THEFT", "THEIR", "THEME", "THERE",
            "THESE", "THICK", "THING", "THINK", "THIRD", "THOSE", "THREE", "THREW", "THROW", "THUMB",
            "TIGHT", "TIRED", "TITLE", "TODAY", "TOPIC", "TOTAL", "TOUCH", "TOUGH", "TOWER", "TRACK",
            "TRADE", "TRAIN", "TREAT", "TREND", "TRIAL", "TRIBE", "TRICK", "TRIED", "TRIES", "TRULY",
            "TRUNK", "TRUST", "TRUTH", "TWICE", "UNCLE", "UNDER", "UNION", "UNITY", "UNTIL", "UPPER",
            "URBAN", "USAGE", "USUAL", "VALUE", "VIDEO", "VIRUS", "VISIT", "VITAL", "VOICE", "WASTE",
            "WATCH", "WATER", "WHEEL", "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WHOSE", "WOMAN",
            "WOMEN", "WORLD", "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WRITE", "WRONG", "WROTE",
            "YOUNG", "YOUTH"
        ]
        
        return [word.upper() for word in essential_words if self.min_word_length <= len(word) <= self.max_word_length]
    
    def generate_trie_structure(self, words: List[str]) -> dict:
        """Convert word list to trie structure for efficient lookup"""
        trie = {}
        for word in words:
            current = trie
            for char in word:
                if char not in current:
                    current[char] = {}
                current = current[char]
            current['$'] = True  # End of word marker
        return trie
    
    def save_dictionary(self, words: List[str], output_path: str):
        """Save both word list and trie structure"""
        dictionary_data = {
            "version": "2.0",
            "word_count": len(words),
            "words": words,
            "trie": self.generate_trie_structure(words),
            "metadata": {
                "min_length": self.min_word_length,
                "max_length": self.max_word_length,
                "generated_at": str(datetime.now()),
                "sources": "FrequencyWords 50K list (frequency-ordered) + essential words",
                "description": "High-quality dictionary for word games, focusing on commonly known words"
            }
        }
        
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w') as f:
            json.dump(dictionary_data, f, separators=(',', ':'))
        
        print(f"Dictionary saved to {output_path}")
        print(f"Total words: {len(words)}")
        
        # Show distribution by length
        length_dist = {}
        for word in words:
            length = len(word)
            length_dist[length] = length_dist.get(length, 0) + 1
        
        print("Words by length:")
        for length in sorted(length_dist.keys()):
            print(f"  {length} letters: {length_dist[length]} words")

if __name__ == "__main__":
    generator = DictionaryGenerator()
    words = generator.fetch_word_list()
    filtered_words = generator.filter_words(words)
    generator.save_dictionary(filtered_words, "public/database.json")