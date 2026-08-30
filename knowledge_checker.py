#!/usr/bin/env python3
"""Check proposed knowledge entries for duplicates and answer conflicts.

This tool is intentionally separate from the bot runtime. It never writes to
SQLite and never changes knowledge.py. Use it before importing new knowledge.
"""

import argparse
import importlib.util
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

STOP_WORDS = {
    "هل", "هو", "هي", "انا", "انت", "يا", "من", "ما", "ماذا", "كيف",
    "اين", "متى", "لماذا", "في", "على", "عن", "لي", "لك", "هذا", "هذه",
    "ذلك", "تلك", "الى", "منذ", "مع", "او", "و", "ب", "ل"
}
REPLACEMENTS = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه",
    "ى": "ي", "ؤ": "و", "ئ": "ي"
}
DIACRITICS = re.compile(r"[\\u0610-\\u061A\\u064B-\\u065F\\u0670]")
NON_TEXT = re.compile(r"[^\\w\\s\\u0600-\\u06FF]", re.UNICODE)
SPACES = re.compile(r"\\s+")


def normalize_text(value):
    text = str(value or "").lower().strip()
    text = DIACRITICS.sub("", text)
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    text = NON_TEXT.sub(" ", text)
    return SPACES.sub(" ", text).strip()


def words(value):
    return {
        word for word in normalize_text(value).split()
        if len(word) > 1 and word not in STOP_WORDS
    }


def similarity(left, right):
    left = normalize_text(left)
    right = normalize_text(right)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if left in right or right in left:
        return 0.92
    sequence_score = SequenceMatcher(None, left, right).ratio()
    left_words = words(left)
    right_words = words(right)
    word_score = (len(left_words & right_words) / len(left_words | right_words)) if left_words and right_words else 0.0
    return sequence_score * 0.55 + word_score * 0.45


def load_source(path):
    module_path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("shadow_knowledge_source", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load source module: %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    getter = getattr(module, "get_knowledge", None)
    if not callable(getter):
        raise ValueError("Source file must define get_knowledge()")
    return list(getter())


def load_candidate(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("knowledge", data.get("items", data))
    if not isinstance(data, list):
        raise ValueError("Candidate JSON must be an array of knowledge objects")
    return data


def prepare(items, source_name):
    valid = []
    malformed = []
    for position, item in enumerate(items, 1):
        if not isinstance(item, dict):
            malformed.append({"source": source_name, "position": position, "reason": "not an object"})
            continue
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer:
            malformed.append({"source": source_name, "position": position, "reason": "question and answer are required"})
            continue
        valid.append({
            "source": source_name,
            "position": position,
            "question": question,
            "answer": answer,
            "question_key": normalize_text(question),
            "answer_key": normalize_text(answer),
            "tokens": words(question),
        })
    return valid, malformed


def build_index(items):
    token_index = defaultdict(set)
    trigram_index = defaultdict(set)
    for index, item in enumerate(items):
        for token in item["tokens"]:
            token_index[token].add(index)
        compact = item["question_key"].replace(" ", "")
        for start in range(max(0, len(compact) - 2)):
            trigram_index[compact[start:start + 3]].add(index)
    return token_index, trigram_index


def candidate_indexes(item, token_index, trigram_index, total):
    indexes = set()
    for token in item["tokens"]:
        indexes.update(token_index.get(token, ()))
    compact = item["question_key"].replace(" ", "")
    for start in range(max(0, len(compact) - 2)):
        indexes.update(trigram_index.get(compact[start:start + 3], ()))
    if not indexes and not item["tokens"] and total <= 1000:
        indexes.update(range(total))
    return indexes


def classify(new_item, old_item, threshold):
    score = similarity(new_item["question"], old_item["question"])
    if score < threshold:
        return None
    same_answer = new_item["answer_key"] == old_item["answer_key"]
    if new_item["question_key"] == old_item["question_key"]:
        kind = "exact_duplicate" if same_answer else "exact_conflict"
    else:
        kind = "semantic_duplicate" if same_answer else "semantic_conflict"
    return {
        "type": kind,
        "score": round(score, 4),
        "new": {"source": new_item["source"], "position": new_item["position"], "question": new_item["question"], "answer": new_item["answer"]},
        "existing": {"source": old_item["source"], "position": old_item["position"], "question": old_item["question"], "answer": old_item["answer"]},
    }


def check(existing, proposed, threshold):
    token_index, trigram_index = build_index(existing)
    results = []
    for item in proposed:
        possible = candidate_indexes(item, token_index, trigram_index, len(existing))
        matches = []
        for index in possible:
            match = classify(item, existing[index], threshold)
            if match:
                matches.append(match)
        if matches:
            matches.sort(key=lambda entry: entry["score"], reverse=True)
            results.append(matches[0])
        else:
            results.append({
                "type": "unique",
                "new": {"source": item["source"], "position": item["position"], "question": item["question"], "answer": item["answer"]},
            })
        index = len(existing)
        existing.append(item)
        for token in item["tokens"]:
            token_index[token].add(index)
        compact = item["question_key"].replace(" ", "")
        for start in range(max(0, len(compact) - 2)):
            trigram_index[compact[start:start + 3]].add(index)
    return results


def make_report(source_path, candidate_path, threshold):
    source_items, source_malformed = prepare(load_source(source_path), source_path)
    candidate_items, candidate_malformed = prepare(load_candidate(candidate_path), candidate_path)
    results = check(source_items[:], candidate_items, threshold)
    counts = defaultdict(int)
    for result in results:
        counts[result["type"]] += 1
    return {
        "source": source_path,
        "candidate": candidate_path,
        "semantic_threshold": threshold,
        "source_count": len(source_items),
        "candidate_count": len(candidate_items),
        "counts": dict(sorted(counts.items())),
        "malformed": source_malformed + candidate_malformed,
        "results": results,
    }


def print_summary(report):
    counts = report["counts"]
    print("Knowledge duplicate check")
    print("- Existing valid entries: %d" % report["source_count"])
    print("- Proposed valid entries: %d" % report["candidate_count"])
    print("- Semantic threshold: %.2f" % report["semantic_threshold"])
    for label in ("unique", "exact_duplicate", "semantic_duplicate", "exact_conflict", "semantic_conflict"):
        print("- %-19s %d" % (label + ":", counts.get(label, 0)))
    if report["malformed"]:
        print("- malformed:            %d" % len(report["malformed"]))
    conflicts = [entry for entry in report["results"] if "conflict" in entry["type"]]
    if conflicts:
        print("\\nConflicts requiring review:")
        for entry in conflicts[:20]:
            print("[%s | score %.3f] %s" % (entry["type"], entry["score"], entry["new"]["question"]))
            print("  existing: %s" % entry["existing"]["question"])
    print("\\nSafe to import: %s" % ("NO" if conflicts or report["malformed"] else "YES"))


def main():
    parser = argparse.ArgumentParser(description="Find duplicate and conflicting Shadow knowledge entries")
    parser.add_argument("--source", default="knowledge.py", help="Current knowledge.py path")
    parser.add_argument("--candidate", required=True, help="JSON file containing proposed entries")
    parser.add_argument("--threshold", type=float, default=0.78, help="Semantic match threshold (default: 0.78)")
    parser.add_argument("--json-out", help="Write the full machine-readable report to this path")
    args = parser.parse_args()
    if not 0.0 < args.threshold <= 1.0:
        parser.error("--threshold must be greater than 0 and at most 1")
    try:
        report = make_report(args.source, args.candidate, args.threshold)
    except Exception as error:
        print("Knowledge check failed: %s" % error, file=sys.stderr)
        return 2
    print_summary(report)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\\n")
    return 2 if report["malformed"] or any("conflict" in entry["type"] for entry in report["results"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
