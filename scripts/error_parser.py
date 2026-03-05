import json
import os
from collections import defaultdict

data = defaultdict(int)
counter = 0
interesting_files = []
for file in os.listdir("../debug_data"):
    interesting = True
    if "error_log" in file:
        with open(f"../debug_data/{file}", "r", encoding="utf-8") as f:
            counter += 1
            lines = f.readlines()
            if len(lines) == 0:
                interesting = False
            for line in lines:
                if line.strip() == "":
                    continue
                if "traceback object" in line:
                    data["traceback"] += 1
                else:
                    data[line] += 1
                if "JSONDecodeError: Expecting value: line 1 column 1" in line:
                    interesting = False
            if interesting:
                interesting_files.append(file)
print(f"total files: {counter}")
print(json.dumps(data, indent=4))
print("\n".join(interesting_files))
