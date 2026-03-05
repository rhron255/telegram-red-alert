import json

with open(
    "../example_responses/alert_history_example.json",
    "r",
    encoding="utf-8",
) as f:
    data = json.load(f)

# print(data)

categories = {cat["title"]: cat["category"] for cat in data}

print(categories)

with open(
    "../alert_categories.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(categories, f, ensure_ascii=False, indent=4)
