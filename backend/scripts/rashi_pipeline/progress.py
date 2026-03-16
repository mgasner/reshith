"""
Live progress monitor for the Rashi enrichment pipeline.
Usage: python -m scripts.rashi_pipeline.progress
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[3] / "frontend/public/data/hebrew/rashi"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "data/rashi_enriched"
LOG_FILE   = Path("/tmp/rashi_pipeline.log")

BARS = "▁▂▃▄▅▆▇█"


def bar(v: float, lo: float, hi: float) -> str:
    if hi <= lo:
        return BARS[0]
    return BARS[int((v - lo) / (hi - lo + 1e-9) * 7)]


def progress_bar(done: int, total: int, width: int = 36) -> str:
    pct = done / total if total else 0
    filled = int(pct * width)
    return "█" * filled + "░" * (width - filled)


def parse_log() -> list[dict]:
    """Return list of completed chapters with timing from the log."""
    if not LOG_FILE.exists():
        return []
    chapters = []
    start_time = start_info = None
    for line in LOG_FILE.read_text().splitlines():
        m = re.search(r"(\d\d:\d\d:\d\d).*\[(\w+)\] chapter (\d+)/\d+ \((\d+) verses\)", line)
        if m:
            start_time = datetime.strptime(m.group(1), "%H:%M:%S")
            start_info = (m.group(2), int(m.group(3)), int(m.group(4)))
        m2 = re.search(r"(\d\d:\d\d:\d\d).*wrote", line)
        if m2 and start_time and start_info:
            secs = (datetime.strptime(m2.group(1), "%H:%M:%S") - start_time).seconds
            book, ch, verses = start_info
            chapters.append({"book": book, "ch": ch, "verses": verses, "secs": secs,
                              "spv": secs / verses if verses else 0})
            start_time = None
    return chapters


def load_corpus() -> dict[str, int]:
    """Return {book: total_chapters}."""
    return {p.stem: len(json.loads(p.read_text())) for p in sorted(SOURCE_DIR.glob("*.json"))}


def count_done(book: str) -> int:
    d = OUTPUT_DIR / book
    return len(list(d.glob("ch*.json"))) if d.exists() else 0


def fmt_duration(secs: float) -> str:
    secs = int(secs)
    h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


def render(corpus: dict[str, int], chapters: list[dict]) -> str:
    total_ch = sum(corpus.values())
    done_ch  = sum(count_done(b) for b in corpus)
    remaining_ch = total_ch - done_ch

    spvs  = [c["spv"]  for c in chapters] or [0]
    spcs  = [c["secs"] for c in chapters] or [0]
    lo_v, hi_v = min(spvs), max(spvs)
    lo_c, hi_c = min(spcs), max(spcs)

    # Rolling 5-chapter averages
    recent = chapters[-5:] or chapters
    avg_spv = sum(c["spv"]  for c in recent) / len(recent)
    avg_spc = sum(c["secs"] for c in recent) / len(recent)
    eta_secs = avg_spc * remaining_ch

    # Sparklines (last 30)
    tail = chapters[-30:]
    spark_v = "".join(bar(c["spv"],  lo_v, hi_v) for c in tail)
    spark_c = "".join(bar(c["secs"], lo_c, hi_c) for c in tail)

    pct = done_ch / total_ch if total_ch else 0
    overall = progress_bar(done_ch, total_ch, 40)

    lines = [
        "",
        f"  Rashi pipeline  {datetime.now().strftime('%H:%M:%S')}",
        "",
        f"  [{overall}]  {pct*100:.1f}%",
        f"  {done_ch} / {total_ch} chapters   ETA {fmt_duration(eta_secs)}",
        "",
        f"  sec/verse  (lo={lo_v:.1f} hi={hi_v:.1f})   5-ch avg {avg_spv:.1f}s",
        f"  {spark_v}",
        "",
        f"  sec/chapter  (lo={lo_c} hi={hi_c})   5-ch avg {avg_spc:.0f}s",
        f"  {spark_c}",
        "",
    ]

    # Per-book summary (show active + done books)
    for book, total in corpus.items():
        done = count_done(book)
        if done == 0:
            continue
        bbar = progress_bar(done, total, 12)
        check = "✓" if done == total else f"{done}/{total}"
        lines.append(f"  {book:>4}  [{bbar}]  {check}")

    # Show next few pending books
    pending = [b for b, t in corpus.items() if count_done(b) == 0]
    if pending:
        lines.append(f"  … {len(pending)} books pending: {', '.join(pending[:6])}" +
                     (" …" if len(pending) > 6 else ""))

    lines.append("")
    return "\n".join(lines)


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def main() -> None:
    corpus = load_corpus()
    try:
        while True:
            chapters = parse_log()
            clear_screen()
            print(render(corpus, chapters))
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
