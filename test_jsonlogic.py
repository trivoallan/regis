import sys

from json_logic import jsonLogic


class NamedList(list):
    def __init__(self, data):
        super().__init__(data)
        self._keys = {}
        for item in data:
            if isinstance(item, dict):
                if "slug" in item:
                    self._keys[item["slug"]] = item
                if "name" in item:
                    # also normalized
                    norm = item["name"].lower().replace(" ", "_")
                    self._keys[norm] = item

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(key)
        if isinstance(key, str):
            try:
                idx = int(key)
                return super().__getitem__(idx)
            except ValueError:
                pass
            if key in self._keys:
                return self._keys[key]
        return super().__getitem__(key)

data = {
    "playbooks": [
        {
            "pages": NamedList([
                {
                    "slug": "compliance",
                    "title": "Compliance",
                    "sections": NamedList([
                        {
                            "name": "Mandatory Requirements",
                            "score": 95
                        }
                    ])
                }
            ])
        }
    ]
}

cond1 = {"var": "playbooks.0.pages.0.sections.0.score"}
cond2 = {"var": "playbooks.0.pages.compliance.sections.mandatory_requirements.score"}

try:
    print("cond1:", jsonLogic(cond1, data))
    print("cond2:", jsonLogic(cond2, data))
except Exception as e:
    print("error:", e)
