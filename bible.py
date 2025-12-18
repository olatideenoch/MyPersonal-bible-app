import requests

# api_key = "LrTbundpMQy8C_uRuO1W6"
# headers = {
#     "api-key": api_key
# }
# params = {
#     "language": "en"
# }
# api_endpoint = f"https://rest.api.bible/v1/bibles/"

# response = requests.get(api_endpoint, headers=headers, params=params)
# response.raise_for_status()
# data = response.json()
# print(data)
# # for bibles in data:
# #     bible_name = bibles["data"][0]["language"]["name"]
# #     print(bible_name)

bible_books = [
    # Old Testament
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "1 Kings",
    "2 Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalms",
    "Proverbs",
    "Ecclesiastes",
    "Song of Solomon",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",

    # New Testament
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation"
]
# book_name = "john"
# selected_chapter = 3
# version = "en-t4t"
url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/bibles.json"
response = requests.get(url)
data = response.json()
versions = data
for version in versions:
    all_version = version["id"]
    print(all_version)
# for verse in verses:
#     print(verse["verse"] + ". " + verse["text"])
# if response.status_code == 200:
#     for verse in verses:
#         verse_number = verse.get("verse")
#         verse_text = verse.get("text")
#         print(f"{verse_number}. {verse_text}")
# else:
#     print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
# query = "love"
# url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-t4t/search/{query}.json"
# response = requests.get(url)
# data = response.json()
# for result in data["data"]:
#     print(f"{result['chapter']}:{result['verse']}. {result['text']}")
# search_results = data["data"]
# for result in search_results:
#     print(result)

# Fetch once at startup
