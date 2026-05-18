"""Fetch real-world test photos for M0 dry-run extension.

Sources (license-cleared, research/testing use):
- Wikimedia Commons (CC0 / CC-BY / Public Domain)
- Picsum Photos (https://picsum.photos, Unsplash-backed CC0-equivalent)

⚠️ This still does NOT replace the user-photo final M0 verdict
(see docs/07-algo-spec.md §6.1). Public-domain photos differ from
"phone photo of my own cat / lover / scenery" in subject distribution
and processing (most are professional photography).

Each fetched image gets a sidecar .meta.json with provenance.

Output:
  samples/<category>/<i>.jpg
  samples/<category>/<i>.meta.json

Wikimedia rate-limit policy:
  - Use iiurlwidth=1200 thumbnail (cheaper than original)
  - Hard floor 1.0s between requests, retry 429/503 with exponential backoff
  - Single User-Agent identifying contact (compliance)
"""
from __future__ import annotations

import argparse
import io
import json
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"

USER_AGENT = (
    "pindou-feasibility-bot/0.1 (research; https://github.com/Fu0000/ai-pin-dou)"
)
WM_API = "https://commons.wikimedia.org/w/api.php"

CATEGORIES = {
    "cat": ["Domestic_cats", "Cats_lying_down", "Tabby_cats"],
    "face": [
        "Portrait_photographs_of_women",
        "Portrait_photographs",
    ],
    "pet": ["Puppies", "Rabbits", "Hamsters"],
    "scene": [],  # use Picsum (more reliable than Wikimedia for landscapes)
}

PER_CATEGORY = 15
WIKI_PAGE_SAMPLE = 200


# ----------------- HTTP with retry + throttle -----------------

_LAST_REQ_AT: float = 0.0
MIN_INTERVAL_S = 1.0  # Wikimedia recommends ≤ 1 req/s for unauth bots


def _throttle() -> None:
    global _LAST_REQ_AT
    now = time.time()
    delta = now - _LAST_REQ_AT
    if delta < MIN_INTERVAL_S:
        time.sleep(MIN_INTERVAL_S - delta)
    _LAST_REQ_AT = time.time()


def _request(url: str, accept: str | None = None, timeout: int = 30) -> bytes:
    """HTTP GET with throttle + retry on 429/503."""
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    backoff = 5.0
    for attempt in range(5):
        _throttle()
        try:
            with urlopen(Request(url, headers=headers), timeout=timeout) as r:
                return r.read()
        except HTTPError as e:
            if e.code in (429, 503):
                wait = backoff * (2**attempt)
                print(f"    ⏳ {e.code} {url[:60]}... retry in {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if attempt < 4:
                print(f"    ⏳ retry {attempt + 1}: {e}", file=sys.stderr)
                time.sleep(backoff)
                continue
            raise
    raise RuntimeError(f"GET failed after retries: {url}")


def _http_json(url: str) -> dict:
    return json.loads(_request(url, accept="application/json"))


# ----------------- Wikimedia helpers -----------------


def _wikimedia_list_files(category: str, limit: int = WIKI_PAGE_SAMPLE) -> list[str]:
    titles: list[str] = []
    cont: str | None = None
    while len(titles) < limit:
        url = (
            f"{WM_API}?action=query&format=json"
            f"&list=categorymembers&cmtitle=Category:{quote(category)}"
            f"&cmtype=file&cmlimit=50"
        )
        if cont:
            url += f"&cmcontinue={quote(cont)}"
        data = _http_json(url)
        for m in data.get("query", {}).get("categorymembers", []):
            t = m["title"]
            if t.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                titles.append(t)
        nxt = data.get("continue", {}).get("cmcontinue")
        if not nxt:
            break
        cont = nxt
    return titles[:limit]


def _wikimedia_thumb_url(title: str, width: int = 1200) -> tuple[str | None, dict]:
    """Use iiurlwidth to get a thumb URL in one call (cheaper + cacheable)."""
    url = (
        f"{WM_API}?action=query&format=json"
        f"&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth={width}"
        f"&titles={quote(title)}"
    )
    try:
        data = _http_json(url)
    except Exception as e:
        print(f"    ! imageinfo {title}: {e}", file=sys.stderr)
        return None, {}
    pages = data.get("query", {}).get("pages", {})
    for _, p in pages.items():
        info = p.get("imageinfo")
        if info:
            i = info[0]
            return i.get("thumburl") or i.get("url"), i
    return None, {}


# ----------------- Save helpers -----------------


def _resize_save(raw: bytes, dest: Path, max_long_side: int = 1200) -> dict:
    img = Image.open(io.BytesIO(raw))
    img.load()
    img = img.convert("RGB")
    long_side = max(img.size)
    if long_side > max_long_side:
        ratio = max_long_side / long_side
        img = img.resize(
            (int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS
        )
    img.save(dest, "JPEG", quality=85, optimize=True)
    return {"width": img.width, "height": img.height}


# ----------------- Category fetchers -----------------


def fetch_wikimedia_for(category: str, n: int, seen: set[str]) -> list[Path]:
    cat_dir = SAMPLES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42 + sum(ord(c) for c in category))

    pool: list[str] = []
    for cat_name in CATEGORIES[category]:
        try:
            titles = _wikimedia_list_files(cat_name, limit=WIKI_PAGE_SAMPLE)
            print(f"  [{category}] +{len(titles)} from Commons:{cat_name}")
            pool.extend(titles)
        except Exception as e:
            print(f"  [{category}] failed to list {cat_name}: {e}", file=sys.stderr)
    rng.shuffle(pool)

    picks: list[Path] = []
    idx = 0
    for title in pool:
        if len(picks) >= n:
            break
        if title in seen:
            continue
        seen.add(title)

        thumb_url, info = _wikimedia_thumb_url(title)
        if not thumb_url or not info:
            continue
        w, h = info.get("width", 0), info.get("height", 0)
        if w < 600 or h < 600:
            continue
        if max(w, h) / max(1, min(w, h)) > 3:
            continue

        try:
            raw = _request(thumb_url)
        except Exception as e:
            print(f"    ! download {title[:50]}: {e}", file=sys.stderr)
            continue

        dest = cat_dir / f"{category}_{idx:02d}.jpg"
        try:
            saved = _resize_save(raw, dest)
        except Exception as e:
            print(f"    ! save {title[:50]}: {e}", file=sys.stderr)
            continue
        meta = {
            "source": "wikimedia_commons",
            "title": title,
            "thumb_url": thumb_url.split("?")[0],
            "original_url": info.get("url", "").split("?")[0],
            "license": info.get("extmetadata", {})
            .get("LicenseShortName", {})
            .get("value", "see page"),
            "page_url": info.get("descriptionurl", ""),
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "stored": saved,
        }
        with open(dest.with_suffix(".meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        picks.append(dest)
        print(f"  ✅ {dest.name}  <-  {title[:60]}")
        idx += 1

    return picks


def fetch_picsum_for(category: str, n: int, seed_base: int) -> list[Path]:
    cat_dir = SAMPLES_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    picks = []
    for i in range(n):
        seed = seed_base + i
        url = f"https://picsum.photos/seed/pindou-{category}-{seed}/1200/900"
        try:
            raw = _request(url)
        except Exception as e:
            print(f"    ! picsum {seed}: {e}", file=sys.stderr)
            continue
        dest = cat_dir / f"{category}_{i:02d}.jpg"
        saved = _resize_save(raw, dest)
        meta = {
            "source": "picsum_photos",
            "title": f"picsum-seed-{seed}",
            "url": url,
            "license": "Picsum is free to use; sourced from Unsplash.",
            "page_url": "https://picsum.photos",
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "stored": saved,
        }
        with open(dest.with_suffix(".meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        picks.append(dest)
        print(f"  ✅ {dest.name}  <-  picsum seed {seed}")
    return picks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-category", type=int, default=PER_CATEGORY)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if args.clean and SAMPLES_DIR.exists():
        import shutil

        shutil.rmtree(SAMPLES_DIR)
        print(f"cleaned {SAMPLES_DIR}")

    seen: set[str] = set()
    summary: dict[str, int] = {}
    for cat in ("cat", "face", "pet", "scene"):
        print(f"\n=== {cat} (target {args.per_category}) ===")
        if cat == "scene" or not CATEGORIES.get(cat):
            picks = fetch_picsum_for(cat, args.per_category, seed_base=10000)
        else:
            picks = fetch_wikimedia_for(cat, args.per_category, seen)
        summary[cat] = len(picks)

    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))
    total = sum(summary.values())
    print(f"total real photos: {total}")
    return 0 if total >= args.per_category * 4 * 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
