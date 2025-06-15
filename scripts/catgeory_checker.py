import json

with open(
    "/Users/rhron255/Documents/Code/TelegramRedAlert/telegram-red-alert/alert_history_example.json",
    "r",
) as f:
    data = json.load(f)

# print(data)

categories = {cat["title"]: cat["category"] for cat in data}

print(categories)

with open(
    "/Users/rhron255/Documents/Code/TelegramRedAlert/telegram-red-alert/alert_categories.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(categories, f, ensure_ascii=False, indent=4)
