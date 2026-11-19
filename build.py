import json
from pathlib import Path
from voyage import experiment

ROOT = Path(__file__).resolve().parent


def render():
    template = (ROOT / "explorer.html").read_text(encoding="utf-8")
    payload = json.dumps(experiment(), separators=(",", ":"), allow_nan=False)
    return template.replace("<!-- REPORT -->", payload)


if __name__ == "__main__":
    (ROOT / "index.html").write_text(render(), encoding="utf-8", newline="\n")
