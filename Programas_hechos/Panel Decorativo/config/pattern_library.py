import json
import os


LIBRARY_FILE = "pattern_library.json"


class PatternLibrary:

    def __init__(self):
        self.patterns = {}
        self.load()

    def load(self):

        if not os.path.exists(LIBRARY_FILE):
            self.patterns = {}
            return

        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            self.patterns = json.load(f)

    def save(self):

        with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
            json.dump(
                self.patterns,
                f,
                indent=4,
                ensure_ascii=False,
            )

    def add_pattern(self, name, file_path, step_x, step_y, restricted=False, restricted_reason=""):

        entry = {
            "type": "dxf",
            "file_path": file_path,
            "step_x": step_x,
            "step_y": step_y,
        }

        if restricted:
            entry["restricted"] = True
            entry["restricted_reason"] = restricted_reason or "Contiene entidades no soportadas"
        else:
            # Explicitly store False so the field is present and unambiguous.
            # Existing patterns loaded from JSON that lack this field are treated
            # as restricted=False by the UI (default), so omitting it for
            # backwards-compat is also safe, but being explicit avoids confusion.
            entry["restricted"] = False
            entry["restricted_reason"] = ""

        self.patterns[name] = entry
        self.save()

    def delete_pattern(self, name):

        if name in self.patterns:
            del self.patterns[name]
            self.save()

    def get_names(self):
        return list(self.patterns.keys())

    def get_pattern(self, name):
        return self.patterns[name]