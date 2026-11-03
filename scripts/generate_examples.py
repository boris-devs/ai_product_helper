import argparse
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "examples" / "input"
OUTPUT_DIR = ROOT / "examples" / "output"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=args.base_url, timeout=180) as client:
        for path in sorted(INPUT_DIR.glob("*.json")):
            response = client.post(
                "/api/v1/cards",
                content=path.read_bytes(),
                headers={"Content-Type": "application/json"},
            )
            data = response.json()
            (OUTPUT_DIR / f"{path.stem}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if response.is_success:
                (OUTPUT_DIR / f"{path.stem}.md").write_text(data["markdown"], encoding="utf-8")
            print(f"{path.name}: HTTP {response.status_code}")


if __name__ == "__main__":
    main()
