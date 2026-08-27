import re
import random
from difflib import SequenceMatcher

from database import get_all_knowledge


# =========================================================
# Arabic Text Engine
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.lower().strip()

    # إزالة التشكيل
    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670]",
        "",
        text
    )

    # توحيد الحروف
    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # كلمات عامية شائعة
    text = text.replace("ايش", "ماذا")
    text = text.replace("وش", "ماذا")
    text = text.replace("شو", "ماذا")
    text = text.replace("كيفك", "كيف حالك")
    text = text.replace("مين", "من")
    text = text.replace("وين", "اين")

    # إزالة الرموز
    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text
    )

    # مسافات
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =========================================================
# كلمات السؤال
# =========================================================

STOP_WORDS = {
    "هل",
    "هو",
    "هي",
    "انا",
    "انت",
    "انت",
    "يا",
    "من",
    "ما",
    "ماذا",
    "كيف",
    "اين",
    "متى",
    "لماذا",
    "في",
    "على",
    "عن",
    "لي",
    "لك"
}


def words(text):

    text = normalize_text(text)

    return {
        word
        for word in text.split()
        if len(word) > 1 and word not in STOP_WORDS
    }


# =========================================================
# تشابه النصوص
# =========================================================

def similarity(a, b):

    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0

    # تطابق كامل
    if a == b:
        return 1.0

    # أحدهما يحتوي الآخر
    if a in b or b in a:
        return 0.92

    # تشابه نصي
    sequence_score = SequenceMatcher(
        None,
        a,
        b
    ).ratio()

    # تشابه الكلمات
    wa = words(a)
    wb = words(b)

    if wa and wb:

        intersection = len(wa & wb)
        union = len(wa | wb)

        word_score = intersection / union

    else:
        word_score = 0

    # النتيجة النهائية
    return (
        sequence_score * 0.55
        +
        word_score * 0.45
    )


# =========================================================
# البحث في قاعدة المعرفة
# =========================================================

def search_answer(user_text):

    normalized_user = normalize_text(user_text)

    if not normalized_user:
        return None

    knowledge = get_all_knowledge()

    if not knowledge:
        return None

    candidates = []

    for item in knowledge:

        question = item["question"]
        keywords = item["keywords"] or ""

        score_question = similarity(
            normalized_user,
            question
        )

        score_keywords = 0

        if keywords:

            keyword_list = [
                normalize_text(x)
                for x in keywords.split(",")
            ]

            user_words = words(normalized_user)

            matches = sum(
                1
                for keyword in keyword_list
                if keyword in user_words
                or keyword in normalized_user
            )

            if keyword_list:
                score_keywords = (
                    matches / len(keyword_list)
                )

        score = (
            score_question * 0.75
            +
            score_keywords * 0.25
        )

        candidates.append(
            (score, item)
        )

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not candidates:
        return None

    best_score, best_item = candidates[0]

    # حد أدنى للتطابق
    if best_score < 0.48:
        return None

    return best_item["answer"]


# =========================================================
# البحث عن عدة نتائج
# =========================================================

def search_candidates(
    user_text,
    limit=5
):

    knowledge = get_all_knowledge()

    results = []

    for item in knowledge:

        score = similarity(
            user_text,
            item["question"]
        )

        results.append(
            (score, item)
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:limit]


# =========================================================
# اختيار رد عشوائي
# =========================================================

def random_answer(answers):

    if not answers:
        return None

    return random.choice(answers)