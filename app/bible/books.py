"""Bible book catalogue, translation registry and API mappings."""


BIBLE_BOOKS = [
    {"name": "Genesis", "chapters": 50, "slug": "genesis"},
    {"name": "Exodus", "chapters": 40, "slug": "exodus"},
    {"name": "Leviticus", "chapters": 27, "slug": "leviticus"},
    {"name": "Numbers", "chapters": 36, "slug": "numbers"},
    {"name": "Deuteronomy", "chapters": 34, "slug": "deuteronomy"},
    {"name": "Joshua", "chapters": 24, "slug": "joshua"},
    {"name": "Judges", "chapters": 21, "slug": "judges"},
    {"name": "Ruth", "chapters": 4, "slug": "ruth"},
    {"name": "1 Samuel", "chapters": 31, "slug": "1-samuel"},
    {"name": "2 Samuel", "chapters": 24, "slug": "2-samuel"},
    {"name": "1 Kings", "chapters": 22, "slug": "1-kings"},
    {"name": "2 Kings", "chapters": 25, "slug": "2-kings"},
    {"name": "1 Chronicles", "chapters": 29, "slug": "1-chronicles"},
    {"name": "2 Chronicles", "chapters": 36, "slug": "2-chronicles"},
    {"name": "Ezra", "chapters": 10, "slug": "ezra"},
    {"name": "Nehemiah", "chapters": 13, "slug": "nehemiah"},
    {"name": "Esther", "chapters": 10, "slug": "esther"},
    {"name": "Job", "chapters": 42, "slug": "job"},
    {"name": "Psalms", "chapters": 150, "slug": "psalms"},
    {"name": "Proverbs", "chapters": 31, "slug": "proverbs"},
    {"name": "Ecclesiastes", "chapters": 12, "slug": "ecclesiastes"},
    {"name": "Song of Solomon", "chapters": 8, "slug": "song-of-solomon"},
    {"name": "Isaiah", "chapters": 66, "slug": "isaiah"},
    {"name": "Jeremiah", "chapters": 52, "slug": "jeremiah"},
    {"name": "Lamentations", "chapters": 5, "slug": "lamentations"},
    {"name": "Ezekiel", "chapters": 48, "slug": "ezekiel"},
    {"name": "Daniel", "chapters": 12, "slug": "daniel"},
    {"name": "Hosea", "chapters": 14, "slug": "hosea"},
    {"name": "Joel", "chapters": 3, "slug": "joel"},
    {"name": "Amos", "chapters": 9, "slug": "amos"},
    {"name": "Obadiah", "chapters": 1, "slug": "obadiah"},
    {"name": "Jonah", "chapters": 4, "slug": "jonah"},
    {"name": "Micah", "chapters": 7, "slug": "micah"},
    {"name": "Nahum", "chapters": 3, "slug": "nahum"},
    {"name": "Habakkuk", "chapters": 3, "slug": "habakkuk"},
    {"name": "Zephaniah", "chapters": 3, "slug": "zephaniah"},
    {"name": "Haggai", "chapters": 2, "slug": "haggai"},
    {"name": "Zechariah", "chapters": 14, "slug": "zechariah"},
    {"name": "Malachi", "chapters": 4, "slug": "malachi"},
    {"name": "Matthew", "chapters": 28, "slug": "matthew"},
    {"name": "Mark", "chapters": 16, "slug": "mark"},
    {"name": "Luke", "chapters": 24, "slug": "luke"},
    {"name": "John", "chapters": 21, "slug": "john"},
    {"name": "Acts", "chapters": 28, "slug": "acts"},
    {"name": "Romans", "chapters": 16, "slug": "romans"},
    {"name": "1 Corinthians", "chapters": 16, "slug": "1-corinthians"},
    {"name": "2 Corinthians", "chapters": 13, "slug": "2-corinthians"},
    {"name": "Galatians", "chapters": 6, "slug": "galatians"},
    {"name": "Ephesians", "chapters": 6, "slug": "ephesians"},
    {"name": "Philippians", "chapters": 4, "slug": "philippians"},
    {"name": "Colossians", "chapters": 4, "slug": "colossians"},
    {"name": "1 Thessalonians", "chapters": 5, "slug": "1-thessalonians"},
    {"name": "2 Thessalonians", "chapters": 3, "slug": "2-thessalonians"},
    {"name": "1 Timothy", "chapters": 6, "slug": "1-timothy"},
    {"name": "2 Timothy", "chapters": 4, "slug": "2-timothy"},
    {"name": "Titus", "chapters": 3, "slug": "titus"},
    {"name": "Philemon", "chapters": 1, "slug": "philemon"},
    {"name": "Hebrews", "chapters": 13, "slug": "hebrews"},
    {"name": "James", "chapters": 5, "slug": "james"},
    {"name": "1 Peter", "chapters": 5, "slug": "1-peter"},
    {"name": "2 Peter", "chapters": 3, "slug": "2-peter"},
    {"name": "1 John", "chapters": 5, "slug": "1-john"},
    {"name": "2 John", "chapters": 1, "slug": "2-john"},
    {"name": "3 John", "chapters": 1, "slug": "3-john"},
    {"name": "Jude", "chapters": 1, "slug": "jude"},
    {"name": "Revelation", "chapters": 22, "slug": "revelation"},
]

for i, book in enumerate(BIBLE_BOOKS):
    book['testament'] = 'Old' if i < 39 else 'New'

VERSION_LIST = [
    {"id": "en-kjv", "version": "King James Version (KJV)", "source": "bible_api", "popularity": 1},
    {"id": "en-niv", "version": "New International Version (NIV)", "source": "api_bible", "popularity": 2},
    {"id": "en-nkjv", "version": "New King James Version (NKJV)", "source": "api_bible", "popularity": 3},
    {"id": "en-amp", "version": "Amplified Bible (AMP)", "source": "api_bible_secondary", "popularity": 4},
    # {"id": "en-esv", "version": "English Standard Version (ESV)", "source": "bible_api", "popularity": 4},
    {"id": "en-nasb", "version": "New American Standard Bible (NASB)", "source": "api_bible_secondary", "popularity": 5},
    {"id": "en-csb", "version": "Christian Standard Bible (CSB)", "source": "api_bible_secondary", "popularity": 6},
    {"id": "en-nlt", "version": "New Living Translation (NLT)", "source": "api_bible", "popularity": 7},
    # {"id": "en-bsb", "version": "Berean Standard Bible (BSB)", "source": "bible_api", "popularity": 8},
    {"id": "en-web", "version": "World English Bible (WEB)", "source": "bible_api", "popularity": 9},
    # {"id": "en-nrsv", "version": "New Revised Standard Version (NRSV)", "source": "bible_api", "popularity": 10},
    # {"id": "en-rsv", "version": "Revised Standard Version (RSV)", "source": "bible_api", "popularity": 11},
    {"id": "en-asv", "version": "American Standard Version (ASV)", "source": "bible_api", "popularity": 12},
    {"id": "en-bbe", "version": "Bible in Basic English (BBE)", "source": "bible_api", "popularity": 13},
    {"id": "en-darby", "version": "Darby Bible", "source": "bible_api", "popularity": 14},
    {"id": "en-dra", "version": "Douay-Rheims (DRA)", "source": "bible_api", "popularity": 15},
    {"id": "fr-ls1910", "version": "Louis Segond 1910 (Français)", "source": "getbible", "popularity": 23},
    {"id": "yo-yoruba", "version": "Bíbélì Mímọ́ ní Èdè Yorùbá Òde-Òní (Yorùbá)", "source": "local", "popularity": 24},
    # {"id": "en-ylt", "version": "Young's Literal Translation (YLT)", "source": "bible_api", "popularity": 16},
    # {"id": "en-msg", "version": "The Message (MSG)", "source": "bible_api", "popularity": 18},
    # {"id": "en-net", "version": "NET Bible (NET)", "source": "bible_api", "popularity": 19},
    # {"id": "en-erv", "version": "Easy-to-Read Version (ERV)", "source": "bible_api", "popularity": 20},
    # {"id": "pt-almeida", "version": "João Ferreira de Almeida (Português)", "source": "bible_api", "popularity": 21},
    {"id": "ro-rccv", "version": "Cornilescu (Română)", "source": "bible_api", "popularity": 22},
    # {"id": "zh-cuv", "version": "Chinese Union Version (中文)", "source": "bible_api", "popularity": 23},
    # {"id": "cs-bkr", "version": "Bible Kralická (Čeština)", "source": "bible_api", "popularity": 24},
]

API_BIBLE_BOOKS = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM",
    "Deuteronomy": "DEU", "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT",
    "1 Samuel": "1SA", "2 Samuel": "2SA", "1 Kings": "1KI", "2 Kings": "2KI",
    "1 Chronicles": "1CH", "2 Chronicles": "2CH", "Ezra": "EZR", "Nehemiah": "NEH",
    "Esther": "EST", "Job": "JOB", "Psalms": "PSA", "Proverbs": "PRO",
    "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA", "Jeremiah": "JER",
    "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN", "Hosea": "HOS",
    "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
    "Micah": "MIC", "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP",
    "Haggai": "HAG", "Zechariah": "ZEC", "Malachi": "MAL", "Matthew": "MAT",
    "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO", "Galatians": "GAL",
    "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL", "1 Thessalonians": "1TH",
    "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI", "Titus": "TIT",
    "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
    "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN",
    "Jude": "JUD", "Revelation": "REV"
}

API_BIBLE_VERSIONS = {
    "en-nkjv": "63097d2a0a2f7db3-01",
    "en-niv": "78a9f6124f344018-01",
    "en-nlt": "d6e14a625393b4da-01",
}

API_BIBLE_VERSIONS_SECONDARY = {
    "en-csb": "a556c5305ee15c3f-01",
    "en-amp": "a81b73293d3080c9-01",
    "en-nasb": "a761ca71e0b3ddcf-01",
}

BIBLEAPI_TRANSLATIONS = {
    "en-kjv": "kjv",
    "en-bsb": "bsb",
    "en-web": "web",
    "en-asv": "asv",
    "en-bbe": "bbe",
    "en-darby": "darby",
    "en-dra": "dra",
    "en-ylt": "ylt",
    "en-esv": "esv",
    "en-nasb": "nasb",
    "en-csb": "csb",
    "en-nlt": "nlt",
    "en-niv": "niv",
    "en-nkjv": "nkjv",
    "en-nrsv": "nrsv",
    "en-rsv": "rsv",
    "en-amp": "amp",
    "en-msg": "msg",
    "en-net": "net",
    "en-erv": "erv",
    "pt-almeida": "almeida",
    "ro-rccv": "rccv",
    "zh-cuv": "cuv",
    "cs-bkr": "bkr",
}

GETBIBLE_TRANSLATIONS = {
    "fr-ls1910": "ls1910",
}

def get_book_by_slug(slug: str):
    """Get book by slug"""
    slug_lower = slug.lower()
    for book in BIBLE_BOOKS:
        if book['slug'] == slug_lower:
            return book
    return None

def get_book_by_name(name: str):
    """Get book by name"""
    name_lower = name.lower()
    for book in BIBLE_BOOKS:
        if book['name'].lower() == name_lower:
            return book
    return None

def get_version_name(version_id: str) -> str:
    """Get human-friendly version name"""
    return next((v['version'] for v in VERSION_LIST if v['id'] == version_id), version_id)

def get_version_source(version_id: str) -> str:
    """Get API source for a version"""
    return next((v.get('source', 'bible_api') for v in VERSION_LIST if v['id'] == version_id), 'bible_api')
