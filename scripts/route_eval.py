"""Deterministic skill-routing eval (no model calls, safe for CI).

Approximates how an agent picks a skill from its description using stemmed TF-IDF.
It cannot judge semantics, but it catches the two common trigger bugs:
  * a description missing the words people actually say (skill never fires)
  * a description so broad that it outranks the right skill (wrong skill fires)

Cases live in evals/routing.json:
  [{"skill": "tdd",
    "positive": ["prompt that should pick this skill", ...],
    "negative": [{"prompt": "...", "owner": "other-skill"}]}]

Usage: python -m scripts.route_eval [--min-rank1 90] [--max-overlap 0.55] [repo_root]
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

from .frontmatter import parse

STOP = set(
    "a an and are as at be by do does for from has have how i in into is it its of on or our "
    "so that the their then there these this to use used using want we what when where which "
    "while will with you your should can need needs not no any all also than too very just "
    "me my help please make get".split()
)
SUFFIXES = ("ization", "ations", "ation", "ingly", "ing", "edly", "ed", "ies", "es", "ly", "s")
TOP_K = 3


def stem(word: str) -> str:
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            word = word[: -len(suf)] + ("y" if suf == "ies" else "")
            break
    # Fold a trailing silent "e" so "replace" and "replacing" share a stem.
    return word[:-1] if len(word) > 4 and word.endswith("e") else word


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(w) for w in words if w not in STOP and len(w) > 1]


def load_catalog(root: Path) -> dict[str, list[str]]:
    docs: dict[str, list[str]] = {}
    for path in sorted((root / ".agents" / "skills").glob("*/SKILL.md")):
        meta = parse(path.read_text()).meta
        name = meta["name"]
        # The name is a strong signal in real routers; count it twice.
        docs[name] = tokenize(name.replace("-", " ")) * 2 + tokenize(meta["description"])
    return docs


class Index:
    def __init__(self, docs: dict[str, list[str]]):
        self.docs = docs
        n = len(docs)
        df: Counter[str] = Counter()
        for toks in docs.values():
            df.update(set(toks))
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = {name: self._vec(toks) for name, toks in docs.items()}

    def _vec(self, toks: list[str]) -> dict[str, float]:
        tf = Counter(toks)
        vec = {t: (1 + math.log(c)) * self.idf.get(t, 0.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def rank(self, prompt: str) -> list[tuple[str, float]]:
        q = self._vec([t for t in tokenize(prompt) if t in self.idf])
        scores = {
            name: sum(w * vec.get(t, 0.0) for t, w in q.items()) for name, vec in self.vecs.items()
        }
        return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

    def overlap(self, a: str, b: str) -> float:
        va, vb = self.vecs[a], self.vecs[b]
        return sum(w * vb.get(t, 0.0) for t, w in va.items())


def evaluate(root: Path, max_overlap: float) -> dict:
    index = Index(load_catalog(root))
    cases = json.loads((root / "evals" / "routing.json").read_text())
    known = set(index.docs)
    problems: list[str] = []
    pos_total = pos_rank1 = pos_topk = 0
    neg_total = neg_ok = 0
    covered: set[str] = set()

    for case in cases:
        skill = case["skill"]
        covered.add(skill)
        if skill not in known:
            problems.append(f"case for unknown skill: {skill}")
            continue
        for prompt in case["positive"]:
            ranked = [n for n, _ in index.rank(prompt)]
            pos_total += 1
            pos_rank1 += ranked[0] == skill
            hit = skill in ranked[:TOP_K]
            pos_topk += hit
            if not hit:
                problems.append(
                    f"miss: {skill} not in top {TOP_K} for {prompt!r} (got {ranked[:TOP_K]})"
                )
        for neg in case.get("negative", []):
            ranked = [n for n, _ in index.rank(neg["prompt"])]
            neg_total += 1
            ok = ranked[0] != skill and (
                neg["owner"] not in known or ranked.index(neg["owner"]) < ranked.index(skill)
            )
            neg_ok += ok
            if not ok:
                problems.append(f"false positive: {skill} wrongly wins {neg['prompt']!r}")

    for missing in sorted(known - covered):
        problems.append(f"no routing cases for skill: {missing}")

    names = sorted(known)
    collisions = [
        (a, b, round(index.overlap(a, b), 2))
        for i, a in enumerate(names)
        for b in names[i + 1 :]
        if index.overlap(a, b) > max_overlap
    ]
    for a, b, score in collisions:
        problems.append(f"description overlap {score}: {a} <-> {b}")

    return {
        "positives": pos_total,
        "rank1": pos_rank1,
        "topk": pos_topk,
        "negatives": neg_total,
        "negatives_ok": neg_ok,
        "problems": problems,
    }


def main(argv: list[str]) -> int:
    args = argv[1:]
    min_rank1, max_overlap = 90.0, 0.55
    for flag in ("--min-rank1", "--max-overlap"):
        if flag in args:
            i = args.index(flag)
            value = float(args[i + 1])
            if flag == "--min-rank1":
                min_rank1 = value
            else:
                max_overlap = value
            del args[i : i + 2]
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    result = evaluate(root, max_overlap)
    pos = result["positives"] or 1
    rank1 = 100 * result["rank1"] / pos
    topk = 100 * result["topk"] / pos
    print(
        f"routing: {result['positives']} positive prompts, rank-1 {rank1:.1f}%, "
        f"top-{TOP_K} {topk:.1f}%; negatives {result['negatives_ok']}/{result['negatives']}"
    )
    for problem in result["problems"]:
        print(f"  {problem}", file=sys.stderr)
    failed = rank1 < min_rank1 or topk < 100 or bool(result["problems"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
