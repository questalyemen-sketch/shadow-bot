# =========================================================
# SHADOW BRAIN V3
# Intent Engine + Smart Knowledge Search
# =========================================================

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
    # توحيد بعض الحروف/الأشكال
    # -----------------------------------------------------

    text = text.replace("ـ", "")

    # -----------------------------------------------------
    # كلمات عامية شائعة
    # -----------------------------------------------------

    slang = {
        "ايش": "ماذا",
        "اي": "ماذا",
        "وش": "ماذا",
        "شو": "ماذا",
        "شنو": "ماذا",
        "اش": "ماذا",
        "اشو": "ماذا",

        "مين": "من",
        "منو": "من",

        "وين": "اين",
        "فين": "اين",

        "متى": "متى",

        "ليش": "لماذا",
        "ليه": "لماذا",
        "لشو": "لماذا",

        "كيفك": "كيف حالك",
        "شخبارك": "كيف حالك",
        "اخبارك": "كيف حالك",
    }

    for old, new in slang.items():

        text = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            text
        )

    # -----------------------------------------------------
    # إزالة الرموز والإيموجي
    # -----------------------------------------------------

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text
    )

    # -----------------------------------------------------
    # إزالة المسافات الزائدة
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
    "انت",
    "انتي",
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
    "لك",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "انا",
    "لدي",
    "عندي",
    "يمكن",
    "هل",
}


# =========================================================
# Words
# =========================================================

def words(text):

    text = normalize_text(text)

    return {
        word
        for word in text.split()
        if len(word) > 1
        and word not in STOP_WORDS
    }


# =========================================================
# Intent Engine
# =========================================================

INTENT_PATTERNS = {

    "greeting": [
        "مرحبا",
        "اهلا",
        "السلام عليكم",
        "سلام عليكم",
        "هلا",
        "هاي",
        "هيلو",
        "صباح الخير",
        "مساء الخير",
        "كيف حالك",
        "كيفك",
    ],

    "identity": [
        "من انت",
        "من هو شادو",
        "من هو shadow",
        "من تكون",
        "ما اسمك",
        "اسمك ايش",
        "اسمك ماذا",
        "ما هو shadow",
        "ماهو shadow",
        "من هذا البوت",
        "من انت يا shadow",
    ],

    "abilities": [
        "ماذا تستطيع",
        "ماذا تستطيع ان تفعل",
        "ماذا تفعل",
        "ما الذي تستطيع",
        "ما هي قدراتك",
        "ما قدراتك",
        "ما الذي يمكنك فعله",
        "ايش تقدر",
        "وش تقدر",
        "وش تسوي",
        "ايش تسوي",
        "ماذا يمكنك",
        "ما الذي يمكنك",
    ],

    "how_work": [
        "كيف تعمل",
        "كيف تشتغل",
        "كيف يعمل shadow",
        "كيف يعمل البوت",
        "كيف تفكر",
        "كيف تبحث",
        "كيف تجيب",
        "كيف تعرف الاجابة",
        "كيف تجد الاجابة",
        "طريقة عملك",
        "كيف تعمل يا shadow",
    ],

    "owner": [
        "من برمجك",
        "من صنعك",
        "من طورك",
        "من انشاك",
        "من هو مبرمجك",
        "من صاحبك",
        "من مالكك",
        "من صاحب shadow",
        "من يملكك",
    ],

    "memory": [
        "هل لديك ذاكرة",
        "هل عندك ذاكرة",
        "هل تتذكر",
        "هل تملك ذاكرة",
        "اين ذاكرتك",
        "كيف تحفظ المعلومات",
        "هل تحفظ الاسئلة",
        "هل تتعلم",
        "هل يمكنك التعلم",
    ],

    "thanks": [
        "شكرا",
        "شكرا لك",
        "مشكور",
        "مشكورة",
        "تسلم",
        "يعطيك العافية",
        "بارك الله فيك",
        "ممتاز",
        "رائع",
    ],

    "help": [
        "ساعدني",
        "المساعدة",
        "كيف استخدمك",
        "كيف استخدم البوت",
        "ما هي الاوامر",
        "الاوامر",
        "ماذا افعل",
    ],

    "test": [
        "اختبر نفسك",
        "اختبار",
        "اختبر shadow",
        "اختبار shadow",
        "هل تستطيع الاجابة",
    ],
}


def detect_intent(text):

    normalized = normalize_text(text)

    if not normalized:
        return "unknown"

    # -----------------------------------------------------
    # تطابق مباشر
    # -----------------------------------------------------

    for intent, patterns in INTENT_PATTERNS.items():

        for pattern in patterns:

            normalized_pattern = normalize_text(
                pattern
            )

            if normalized == normalized_pattern:
                return intent

    # -----------------------------------------------------
    # تطابق احتوائي
    # -----------------------------------------------------

    for intent, patterns in INTENT_PATTERNS.items():

        for pattern in patterns:

            normalized_pattern = normalize_text(
                pattern
            )

            if normalized_pattern in normalized:
                return intent

    # -----------------------------------------------------
    # تشابه تقريبي
    # -----------------------------------------------------

    best_intent = "unknown"
    best_score = 0.0

    for intent, patterns in INTENT_PATTERNS.items():

        for pattern in patterns:

            score = SequenceMatcher(
                None,
                normalized,
                normalize_text(pattern)
            ).ratio()

            if score > best_score:

                best_score = score
                best_intent = intent

    if best_score >= 0.78:
        return best_intent

    return "unknown"


# =========================================================
# Intent Keywords
# =========================================================

INTENT_KEYWORDS = {

    "greeting": {
        "مرحبا",
        "اهلا",
        "سلام",
        "هلا",
        "هاي",
        "صباح",
        "مساء",
        "حال",
    },

    "identity": {
        "انت",
        "اسم",
        "shadow",
        "شادو",
        "بوت",
        "تكون",
    },

    "abilities": {
        "تستطيع",
        "تقدر",
        "تفعل",
        "تسوي",
        "قدرات",
        "يمكنك",
    },

    "how_work": {
        "تعمل",
        "تشتغل",
        "تفكر",
        "تبحث",
        "تجيب",
        "اجابة",
        "ذاكرة",
    },

    "owner": {
        "برمجك",
        "صنعك",
        "طورك",
        "انشاك",
        "مبرمج",
        "صاحب",
        "مالك",
    },

    "memory": {
        "ذاكرة",
        "تتذكر",
        "تحفظ",
        "تعلم",
        "تتعلم",
    },

    "thanks": {
        "شكرا",
        "مشكور",
        "تسلم",
        "ممتاز",
        "رائع",
    },

    "help": {
        "ساعدني",
        "مساعدة",
        "اوامر",
        "استخدم",
    },
}


# =========================================================
# Text Similarity
# =========================================================

def similarity(a, b):

    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    # تطابق كامل
    if a == b:
        return 1.0

    # أحد النصين يحتوي الآخر
    if a in b or b in a:
        return 0.92

    # تشابه النص
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

        if union:
            word_score = intersection / union
        else:
            word_score = 0.0

    else:

        word_score = 0.0

    return (
        sequence_score * 0.55
        +
        word_score * 0.45
    )


# =========================================================
# Keyword Similarity
# =========================================================

def keyword_score(user_text, keywords):

    if not keywords:
        return 0.0

    user_normalized = normalize_text(
        user_text
    )

    user_words = words(
        user_normalized
    )

    keyword_list = [

        normalize_text(keyword.strip())

        for keyword in keywords.split(",")

        if keyword.strip()
    ]

    if not keyword_list:
        return 0.0

    matches = 0

    for keyword in keyword_list:

        if not keyword:
            continue

        if keyword in user_words:

            matches += 1

        elif keyword in user_normalized:

            matches += 1

    return matches / len(keyword_list)


# =========================================================
# Intent Score
# =========================================================

def intent_score(user_text, question):

    user_intent = detect_intent(
        user_text
    )

    question_intent = detect_intent(
        question
    )

    if user_intent == "unknown":
        return 0.0

    if user_intent == question_intent:
        return 1.0

    return 0.0


# =========================================================
# Advanced Candidate Score
# =========================================================

def calculate_score(user_text, item):

    question = item["question"]

    keywords = item["keywords"] or ""

    # -----------------------------------------------------
    # السؤال
    # -----------------------------------------------------

    question_score = similarity(
        user_text,
        question
    )

    # -----------------------------------------------------
    # الكلمات المفتاحية
    # -----------------------------------------------------

    keywords_score = keyword_score(
        user_text,
        keywords
    )

    # -----------------------------------------------------
    # النية
    # -----------------------------------------------------

    intent_match = intent_score(
        user_text,
        question
    )

    # -----------------------------------------------------
    # النتيجة الأساسية
    # -----------------------------------------------------

    score = (

        question_score * 0.60

        +

        keywords_score * 0.20

        +

        intent_match * 0.20

    )

    return score


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

    candidates = []

    for item in knowledge:

        score = calculate_score(
            normalized_user,
            item
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

    # -----------------------------------------------------
    # تطابق قوي جدًا
    # -----------------------------------------------------

    if best_score >= 0.75:

        return best_item["answer"]

    # -----------------------------------------------------
    # تطابق متوسط مع نية واضحة
    # -----------------------------------------------------

    if best_score >= 0.60:

        user_intent = detect_intent(
            normalized_user
        )

        if user_intent != "unknown":

            return best_item["answer"]

    # -----------------------------------------------------
    # تطابق عادي
    # -----------------------------------------------------

    if best_score >= 0.48:

        return best_item["answer"]

    return None


# =========================================================
# Search Candidates
# =========================================================

def search_candidates(
    user_text,
    limit=5
):

    knowledge = get_all_knowledge()

    if not knowledge:
        return []

    results = []

    for item in knowledge:

        score = calculate_score(
            user_text,
            item
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
# Find Best Candidate
# =========================================================

def get_best_candidate(user_text):

    candidates = search_candidates(
        user_text,
        limit=1
    )

    if not candidates:
        return None

    score, item = candidates[0]

    return {
        "score": score,
        "question": item["question"],
        "answer": item["answer"],
        "category": item["category"],
        "keywords": item["keywords"],
    }


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
# Brain Diagnostics
# =========================================================

def analyze_question(user_text):

    """
    أداة تشخيصية لمعرفة كيف يرى Shadow السؤال.
    """

    intent = detect_intent(
        user_text
    )

    candidates = search_candidates(
        user_text,
        limit=3
    )

    return {
        "text": user_text,
        "normalized": normalize_text(
            user_text
        ),
        "intent": intent,
        "candidates": candidates,
    }