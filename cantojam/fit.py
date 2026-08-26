"""Repair lyrics against a melody that is already written.

`check` says which syllables fight the tune. That is the diagnosis. This is the
treatment: for every clash it names what could stand there instead, drawn from
what Cantopop lyricists actually wrote and constrained by the notes on both
sides, so a fix at one seam cannot quietly break the next one.

A whole phrase lifted from the corpus is a safer suggestion than a single
character, because the phrase was written as a unit and the character was not.
The corpus cannot tell the two apart on its own: its n-grams are raw sequences,
so 舊日 and the boundary-crossing 日你 look alike by frequency and score the
same PMI. Rather than pretend to a filter that does not work, phrase swaps are
offered first and single characters are labelled as needing your judgement.
"""

from .check import check, parse_melody
from .jyutping import Lexicon, tone_of
from .lexicon import Lexicon as WordList
from .model import ToneModel

# A clash sits between two syllables. Replacing the phrase that spans it is
# tried first, then the wider phrase around it, then either character alone.
WINDOWS = ((-1, 2), (-1, 3), (0, 2), (-1, 1), (0, 1))


def repairs(text, melody, keep_rhyme=True, min_count=2, limit=6,
            allow_unusual=False, lexicon=None, words=None, model=None,
            overrides=None):
    """Every clash in the line, each with what would fit instead.

    keep_rhyme  a swap touching the last syllable must keep the line's rime,
                because that is usually load bearing across the verse
    min_count   how often a candidate appears in the corpus; 1 admits hapaxes
    limit       options per bucket, phrases and single characters counted apart
    """
    model = model or ToneModel()
    lexicon = lexicon or Lexicon(overrides)
    words = words or WordList()

    pitches = parse_melody(melody)
    result = check(text, pitches, lexicon=lexicon, model=model)
    rows = result["rows"]
    tones = [row["tone"] for row in rows]
    here = [row["char"] for row in rows]
    last = len(rows) - 1
    rime = rows[last]["jyutping"] if rows and rows[last]["jyutping"] else None

    def reading_note(entry):
        """Which characters must take a reading other than the default.

        A candidate is admitted on the tones the corpus sang it with, but the
        checker reads a polyphone with its most frequent reading. 爲何 is
        offered as wai4 ho4 while 爲 defaults to wai6, and that one-tone
        difference is the difference between the line fitting and not. Roughly
        one suggestion in fifty, so worth naming rather than dropping.
        """
        pinned = []
        for char, syllable in zip(entry["w"], entry["j"].split()):
            if tone_of(syllable) != tone_of(lexicon.lookup(char) or ""):
                pinned.append(f"{char}={syllable}")
        return pinned

    problems = []
    for row in rows:
        if not (row["violation"] or row["unusual"]):
            continue
        phrases, singles, seen = [], [], set()
        for offset, length in WINDOWS:
            start = row["index"] + offset
            if start < 0 or start + length > len(rows):
                continue
            was = "".join(here[start:start + length])
            filters = {"min_count": min_count}
            if keep_rhyme and rime and start + length > last:
                filters["rimes_with"] = rime
            for entry in words.fitting(pitches, tones, start, length,
                                       model=model,
                                       allow_unusual=allow_unusual, **filters):
                key = (start, entry["w"])
                if entry["w"] == was or key in seen:
                    continue
                seen.add(key)
                (singles if length == 1 else phrases).append({
                    "start": start, "length": length, "replaces": was,
                    "word": entry["w"], "jyutping": entry["j"],
                    "tones": entry["t"], "rime": entry["r"],
                    "count": entry["n"], "pin": reading_note(entry),
                    "line": "".join(here[:start]) + entry["w"]
                            + "".join(here[start + length:]),
                })
        # Least of the line disturbed first, then the most idiomatic.
        phrases.sort(key=lambda o: (o["length"], -o["count"]))
        singles.sort(key=lambda o: -o["count"])
        problems.append({
            "index": row["index"],
            "kind": "violation" if row["violation"] else "unusual",
            "message": row.get("message", ""),
            "phrases": phrases[:limit], "singles": singles[:limit],
            "phrase_total": len(phrases), "single_total": len(singles),
        })

    return {"check": result, "problems": problems,
            "clean": not problems, "line": text}


def _lines(options, total, limit, note=None):
    out = []
    if note:
        out.append(f"    {note}")
    for option in options:
        out.append(f"    {option['replaces']} -> {option['word']:<5} "
                   f"{option['jyutping']:<21} tones {option['tones']:<4} "
                   f"-{option['rime']:<5} {option['count']}x")
        pin = f"   sing {' '.join(option['pin'])}" if option["pin"] else ""
        out.append(f"        {option['line']}{pin}")
    if total > limit:
        out.append(f"    ... {total - limit} more, raise --limit")
    return out


def render(report):
    """The report as text, for the terminal."""
    result = report["check"]
    out = []
    if result["length_mismatch"]:
        out.append(f"warning: {result['syllables']} sung syllables but "
                   f"{result['notes']} notes. Line these up first, or every "
                   f"clash below is off by one.")

    for row in result["rows"]:
        mark = "X" if row["violation"] else "?" if row["unusual"] else " "
        interval = row.get("interval")
        step = f"{interval:+3d}" if interval is not None else "  ."
        out.append(f" {mark} {row['char']}  {row['jyutping'] or '?':<8} "
                   f"{row['note'] or '-':<4} {step}")

    if report["clean"]:
        out.append("\nnothing to fix. The lyrics already sit on this melody.")
        return "\n".join(out)

    for problem in report["problems"]:
        out.append(f"\n{'X' if problem['kind'] == 'violation' else '?'} "
                   f"{problem['message']}")
        if not (problem["phrases"] or problem["singles"]):
            out.append("    nothing in the corpus fits here. Try "
                       "--allow-unusual, --min-count 1, --no-keep-rhyme, "
                       "or move the note instead.")
            continue
        limit = len(problem["phrases"])
        out += _lines(problem["phrases"], problem["phrase_total"], limit,
                      "phrases the corpus wrote as a unit:")
        if problem["singles"]:
            out += _lines(problem["singles"], problem["single_total"],
                          len(problem["singles"]),
                          "single characters that fit the notes, sense is "
                          "yours to judge:")
    return "\n".join(out)
