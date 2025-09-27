import json, pathlib
from extractors.keywords_mslearn import KeywordsMSLearn
from extractors.base import merge_into, ensure_dir

OUT = pathlib.Path("out/spec.json")

FRESH = {
    "comment": "generated from Microsoft Learn (and friends)",
    "keywords": [], "types": [], "functions": [], "semantics": [], "operators": []
}

def load_spec(path: pathlib.Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return dict(FRESH)  # fresh copy
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # file exists but is garbage → don’t die
        return dict(FRESH)

def save_spec(path: pathlib.Path, spec: dict):
    ensure_dir(path.parent)
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def main():
    spec = load_spec(OUT)

    extractors = [
        KeywordsMSLearn(),
    ]

    for ex in extractors:
        print(f"[run] {ex.name}")
        data = ex.run()
        merge_into(spec, ex.target_key, data)

    save_spec(OUT, spec)
    print(f"[ok] wrote {OUT}")

if __name__ == "__main__":
    main()
