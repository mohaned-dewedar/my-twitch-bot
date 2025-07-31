import json

with open("data/smite_gods_extended.json", "r") as file:
    data = json.load(file)


# Remove the last ability for each god
for god in data["gods"]:
    if god["abilities"]:
        god["abilities"].pop()

# To display or use the modified data
with open("data/smite_gods_modified.json", "w") as file:
    json.dump(data, file, indent=2)