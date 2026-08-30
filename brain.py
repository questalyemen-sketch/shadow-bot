# =========================================================
# SHADOW BRAIN V2 🧠
# Advanced Arabic Knowledge Search Engine
# =========================================================

import re
import random
from difflib import SequenceMatcher

from database import get_all_knowledge


# =========================================================
# Configuration
# =========================================================

MIN_SCORE = 0.50
EXACT_SCORE = 1.0

QUESTION_WEIGHT = 0.70
KEYWORD_WEIGHT = 0.30

# عدد المرشحين الذين نطبق عليهم المقارنة الثقيلة
MAX_DEEP_CANDIDATES = 80


# =========================================================
# Arabic Normalization
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower().strip()

    # -----------------------------------------------------
    # إزالة التشكيل
    # -----------------------------------------------------

    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670]",
        "",
        text
    )

    # -----------------------------------------------------
    # إزالة التطويل
    # -----------------------------------------------------

    text = text.replace("ـ", "")

    # -----------------------------------------------------
    # توحيد الحروف العربية
    # -----------------------------------------------------

    replacements = {

        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",

        "ة": "ه",

        "ى": "ي",

        "ؤ": "و",

        "ئ": "ي",

    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # -----------------------------------------------------
    # كلمات عامية شائعة
    # -----------------------------------------------------

    colloquial = {

        "ايش": "ماذا",
        "إيش": "ماذا",

        "اش": "ماذا",
        "وش": "ماذا",
        "شو": "ماذا",
        "شنو": "ماذا",

        "ليش": "لماذا",
        "ليه": "لماذا",
        "لشو": "لماذا",

        "مين": "من",
        "منو": "من",

        "وين": "اين",
        "فين": "اين",

        "متى": "متى",

        "كيفك": "كيف حالك",
        "شلونك": "كيف حالك",
        "شخبارك": "كيف حالك",

        "هاذي": "هذه",
        "هذي": "هذه",
        "هذا": "هذا",

        "ابغى": "اريد",
        "ابي": "اريد",
        "بغيت": "اريد",

        "مو": "ليس",
        "مش": "ليس",

        "عندي": "لدي",
        "عندك": "لديك",

    }

    for old, new in colloquial.items():

        text = re.sub(
            rf"(?<!\w){re.escape(old)}(?!\w)",
            new,
            text
        )

    # -----------------------------------------------------
    # تقليل تكرار الحروف
    #
    # مثال:
    # مااااااااا -> ما
    # حلووووو -> حلو
    # -----------------------------------------------------

    text = re.sub(
        r"(.)\1{2,}",
        r"\1\1",
        text
    )

    # -----------------------------------------------------
    # إزالة الرموز
    # -----------------------------------------------------

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text
    )

    # -----------------------------------------------------
    # تنظيف المسافات
    # -----------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =========================================================
# Stop Words
# =========================================================

STOP_WORDS = {

    "هل",
    "هو",
    "هي",

    "انا",
    "أنت",
    "انت",
    "انتي",
    "نحن",

    "يا",

    "من",
    "ما",
    "ماذا",

    "كيف",
    "اين",
    "متى",
    "لماذا",

    "في",
    "من",
    "على",
    "عن",

    "الى",
    "إلى",

    "لي",
    "لك",
    "له",
    "لها",

    "هذا",
    "هذه",

    "ذلك",
    "تلك",

    "هل",
    "قد",
    "لقد",

    "ان",
    "أن",

    "او",
    "أو",

    "ثم",

}


# =========================================================
# Tokenization
# =========================================================

def words(text):

    text = normalize_text(text)

    if not text:
        return set()

    return {
        word
        for word in text.split()
        if len(word) > 1
        and word not in STOP_WORDS
    }


# =========================================================
# Character Similarity
# =========================================================

def character_similarity(a, b):

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    if a in b or b in a:
        return 0.92

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


# =========================================================
# Word Similarity
# =========================================================

def word_similarity(a, b):

    wa = words(a)
    wb = words(b)

    if not wa or not wb:
        return 0.0

    intersection = len(wa & wb)

    if intersection == 0:
        return 0.0

    union = len(wa | wb)

    if union == 0:
        return 0.0

    jaccard = intersection / union

    # نسبة الكلمات المشتركة بالنسبة لسؤال المستخدم
    user_coverage = intersection / len(wa)

    # نعطي أهمية أعلى لتغطية سؤال المستخدم
    return (
        jaccard * 0.45
        +
        user_coverage * 0.55
    )


# =========================================================
# Main Similarity
# =========================================================

def similarity(a, b):

    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    # -----------------------------------------------------
    # تطابق كامل
    # -----------------------------------------------------

    if a == b:
        return EXACT_SCORE

    # -----------------------------------------------------
    # احتواء
    # -----------------------------------------------------

    if a in b or b in a:
        return 0.92

    # -----------------------------------------------------
    # تشابه الكلمات
    # -----------------------------------------------------

    word_score = word_similarity(
        a,
        b
    )

    # -----------------------------------------------------
    # تشابه الحروف
    # -----------------------------------------------------

    char_score = character_similarity(
        a,
        b
    )

    # -----------------------------------------------------
    # النتيجة النهائية
    # -----------------------------------------------------

    score = (
        char_score * 0.55
        +
        word_score * 0.45
    )

    return round(
        score,
        4
    )


# =========================================================
# Keyword Similarity
# =========================================================

def keyword_similarity(
    user_text,
    keywords
):

    if not keywords:
        return 0.0

    user_normalized = normalize_text(
        user_text
    )

    user_words = words(
        user_normalized
    )

    if not user_words:
        return 0.0

    keyword_list = []

    for keyword in keywords.split(","):

        keyword = normalize_text(
            keyword
        )

        if keyword:
            keyword_list.append(
                keyword
            )

    if not keyword_list:
        return 0.0

    matches = 0

    for keyword in keyword_list:

        if (
            keyword in user_words
            or keyword in user_normalized
        ):
            matches += 1

    return matches / len(keyword_list)


# =========================================================
# Fast Candidate Score
# =========================================================

def fast_score(
    user_text,
    question
):

    user_normalized = normalize_text(
        user_text
    )

    question_normalized = normalize_text(
        question
    )

    if not user_normalized or not question_normalized:
        return 0.0

    # تطابق مباشر
    if user_normalized == question_normalized:
        return 1.0

    # احتواء
    if (
        user_normalized in question_normalized
        or question_normalized in user_normalized
    ):
        return 0.92

    user_words = words(
        user_normalized
    )

    question_words = words(
        question_normalized
    )

    if not user_words or not question_words:
        return 0.0

    intersection = len(
        user_words & question_words
    )

    if intersection == 0:
        return 0.0

    coverage = (
        intersection
        /
        len(user_words)
    )

    question_coverage = (
        intersection
        /
        len(question_words)
    )

    return (
        coverage * 0.65
        +
        question_coverage * 0.35
    )


# =========================================================
# Search Answer
# =========================================================

def search_answer(user_text):

    normalized_user = normalize_text(
        user_text
    )

    if not normalized_user:
        return None

    knowledge = get_all_knowledge()

    if not knowledge:
        return None

    # =====================================================
    # المرحلة الأولى:
    # البحث عن تطابق كامل
    # =====================================================

    for item in knowledge:

        question = item["question"]

        normalized_question = normalize_text(
            question
        )

        if normalized_user == normalized_question:

            return item["answer"]

    # =====================================================
    # المرحلة الثانية:
    # إنشاء مرشحين سريعًا
    # =====================================================

    candidates = []

    for item in knowledge:

        question = item["question"]

        score = fast_score(
            normalized_user,
            question
        )

        if score > 0:

            candidates.append(
                (score, item)
            )

    # =====================================================
    # إذا لم توجد مرشحات
    # =====================================================

    if not candidates:
        return None

    # =====================================================
    # ترتيب المرشحين
    # =====================================================

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # نأخذ عددًا محدودًا للمقارنة العميقة
    candidates = candidates[
        :MAX_DEEP_CANDIDATES
    ]

    # =====================================================
    # المرحلة الثالثة:
    # المقارنة الدقيقة
    # =====================================================

    deep_candidates = []

    for _, item in candidates:

        question = item["question"]

        keywords = item["keywords"] or ""

        question_score = similarity(
            normalized_user,
            question
        )

        keyword_score = keyword_similarity(
            normalized_user,
            keywords
        )

        final_score = (
            question_score
            * QUESTION_WEIGHT
            +
            keyword_score
            * KEYWORD_WEIGHT
        )

        deep_candidates.append(
            (
                final_score,
                item
            )
        )

    # =====================================================
    # ترتيب النتائج النهائية
    # =====================================================

    deep_candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not deep_candidates:
        return None

    best_score, best_item = (
        deep_candidates[0]
    )

    # =====================================================
    # حماية من الإجابات الخاطئة
    # =====================================================

    if best_score < MIN_SCORE:

        return None

    return best_item["answer"]


# =========================================================
# Search Candidates
# =========================================================

def search_candidates(
    user_text,
    limit=5
):

    if not user_text:
        return []

    knowledge = get_all_knowledge()

    if not knowledge:
        return []

    candidates = []

    normalized_user = normalize_text(
        user_text
    )

    # -----------------------------------------------------
    # البحث السريع
    # -----------------------------------------------------

    for item in knowledge:

        question = item["question"]

        score = fast_score(
            normalized_user,
            question
        )

        if score > 0:

            candidates.append(
                (score, item)
            )

    # -----------------------------------------------------
    # ترتيب
    # -----------------------------------------------------

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # -----------------------------------------------------
    # تحسين أفضل النتائج
    # -----------------------------------------------------

    results = []

    for _, item in candidates[:limit * 3]:

        score = similarity(
            normalized_user,
            item["question"]
        )

        results.append(
            (
                score,
                item
            )
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:limit]


# =========================================================
# Find Best Match
# =========================================================

def find_best_match(user_text):

    results = search_candidates(
        user_text,
        limit=1
    )

    if not results:
        return None

    score, item = results[0]

    if score < MIN_SCORE:
        return None

    return item


# =========================================================
# Get Best Score
# =========================================================

def get_best_score(user_text):

    results = search_candidates(
        user_text,
        limit=1
    )

    if not results:
        return 0.0

    return results[0][0]


# =========================================================
# Random Answer
# =========================================================

def random_answer(answers):

    if not answers:
        return None

    return random.choice(
        answers
    )


# =========================================================
# Brain Test
# =========================================================

def test_brain(question):

    answer = search_answer(
        question
    )

    if answer:
        return {
            "found": True,
            "answer": answer,
            "score": get_best_score(
                question
            )
        }

    return {
        "found": False,
        "answer": None,
        "score": get_best_score(
            question
        )
    }