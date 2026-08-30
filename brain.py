# =========================================================
# SHADOW BRAIN 🧠
# Smart Arabic Knowledge Search Engine
# =========================================================

import re
import random
from difflib import SequenceMatcher

from database import get_all_knowledge


# =========================================================
# Arabic Normalization
# =========================================================

ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

NON_TEXT = re.compile(
    r"[^\w\s\u0600-\u06FF]"
)

MULTI_SPACE = re.compile(
    r"\s+"
)


def normalize_text(text):
    """
    توحيد النص العربي والإنجليزي.

    الهدف:
    جعل الصيغ المختلفة للسؤال أقرب لبعضها.
    """

    if text is None:
        return ""

    text = str(text).lower().strip()

    if not text:
        return ""

    # -----------------------------------------------------
    # إزالة التشكيل
    # -----------------------------------------------------

    text = ARABIC_DIACRITICS.sub("", text)

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

        "ى": "ي",

        "ؤ": "و",
        "ئ": "ي",

        "ة": "ه",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # -----------------------------------------------------
    # توحيد بعض الصيغ العامية
    # -----------------------------------------------------

    slang = {
        "ايش": "ماذا",
        "إيش": "ماذا",
        "وش": "ماذا",
        "شو": "ماذا",

        "ليش": "لماذا",
        "ليه": "لماذا",
        "ليشـ": "لماذا",

        "مين": "من",

        "وين": "اين",
        "وينك": "اين",

        "متى": "متى",

        "كيفك": "كيف حالك",
        "شخبارك": "كيف حالك",
        "شلونك": "كيف حالك",

        "انتو": "انتم",
        "انتمو": "انتم",

        "انا": "انا",
        "إنا": "انا",
    }

    for old, new in slang.items():
        text = text.replace(old, new)

    # -----------------------------------------------------
    # تنظيف الرموز
    # -----------------------------------------------------

    text = NON_TEXT.sub(" ", text)

    # -----------------------------------------------------
    # إزالة المسافات الزائدة
    # -----------------------------------------------------

    text = MULTI_SPACE.sub(" ", text).strip()

    return text


# =========================================================
# Backward Compatibility
# =========================================================

def normalize(text):
    """
    توافق مع الإصدارات القديمة.
    """

    return normalize_text(text)


# =========================================================
# Stop Words
# =========================================================

STOP_WORDS = {
    "هل",
    "هو",
    "هي",
    "هم",
    "هن",
    "انا",
    "انت",
    "انتي",
    "انتم",
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
    "الي",
    "الى",
    "لي",
    "لك",
    "له",
    "لها",
    "مع",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "هو",
    "هي",
}


# =========================================================
# Tokenization
# =========================================================

def words(text):
    """
    استخراج الكلمات المهمة من النص.
    """

    text = normalize_text(text)

    if not text:
        return set()

    result = set()

    for word in text.split():

        if len(word) <= 1:
            continue

        if word in STOP_WORDS:
            continue

        result.add(word)

    return result


# =========================================================
# Light Arabic Stemming
# =========================================================

PREFIXES = (
    "وال",
    "بال",
    "كال",
    "لل",
    "ال",
    "و",
    "ف",
    "ب",
    "ك",
    "ل",
)


SUFFIXES = (
    "يات",
    "ية",
    "ات",
    "ون",
    "ين",
    "ان",
    "ها",
    "هم",
    "هن",
    "كما",
    "كم",
    "نا",
    "ني",
    "ه",
    "ك",
    "ي",
    "ة",
)


def light_stem(word):
    """
    اشتقاق عربي خفيف.
    لا يحاول تحليل الكلمة صرفيًا بالكامل.
    """

    word = normalize_text(word)

    if len(word) <= 3:
        return word

    # إزالة بادئة واحدة
    for prefix in PREFIXES:

        if word.startswith(prefix):

            remaining = word[len(prefix):]

            if len(remaining) >= 3:
                word = remaining
                break

    # إزالة لاحقة واحدة
    for suffix in SUFFIXES:

        if word.endswith(suffix):

            remaining = word[:-len(suffix)]

            if len(remaining) >= 3:
                word = remaining
                break

    return word


def stem_words(text):
    """
    استخراج الكلمات بعد الاشتقاق الخفيف.
    """

    result = set()

    for word in words(text):

        stem = light_stem(word)

        if stem:
            result.add(stem)

    return result


# =========================================================
# Sequence Similarity
# =========================================================

def sequence_similarity(a, b):

    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

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

    intersection = wa & wb

    if not intersection:
        return 0.0

    union = wa | wb

    return len(intersection) / len(union)


# =========================================================
# Stem Similarity
# =========================================================

def stem_similarity(a, b):

    wa = stem_words(a)
    wb = stem_words(b)

    if not wa or not wb:
        return 0.0

    intersection = wa & wb

    if not intersection:
        return 0.0

    union = wa | wb

    return len(intersection) / len(union)


# =========================================================
# Main Similarity Engine
# =========================================================

def similarity(a, b):
    """
    حساب درجة التشابه بين سؤالين.

    النتيجة:
        0.0 = لا يوجد تشابه
        1.0 = تطابق كامل
    """

    a = normalize_text(a)
    b = normalize_text(b)

    if not a or not b:
        return 0.0

    # تطابق كامل
    if a == b:
        return 1.0

    # احتواء كامل
    if a in b or b in a:
        return 0.94

    seq = sequence_similarity(a, b)

    word = word_similarity(a, b)

    stem = stem_similarity(a, b)

    score = (
        seq * 0.40
        +
        word * 0.35
        +
        stem * 0.25
    )

    return min(score, 1.0)


# =========================================================
# Keyword Matching
# =========================================================

def keyword_similarity(user_text, keywords):

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

    # دعم:
    # ,
    # ،
    # ;
    # /
    # |
    keyword_list = re.split(
        r"[,،;/|]+",
        str(keywords)
    )

    normalized_keywords = []

    for keyword in keyword_list:

        keyword = normalize_text(
            keyword
        )

        if keyword:
            normalized_keywords.append(
                keyword
            )

    if not normalized_keywords:
        return 0.0

    matches = 0

    for keyword in normalized_keywords:

        keyword_words = words(
            keyword
        )

        # الكلمة المفتاحية نفسها
        if keyword in user_words:
            matches += 1
            continue

        # إذا كانت عبارة
        if keyword in user_normalized:
            matches += 1
            continue

        # مقارنة كلمات المفتاح
        if keyword_words:

            if keyword_words & user_words:
                matches += 0.5

    score = matches / len(
        normalized_keywords
    )

    return min(score, 1.0)


# =========================================================
# Candidate Score
# =========================================================

def score_candidate(user_text, item):

    question = item["question"]

    keywords = item["keywords"] or ""

    normalized_user = normalize_text(
        user_text
    )

    normalized_question = normalize_text(
        question
    )

    # -----------------------------------------------------
    # Exact Match
    # -----------------------------------------------------

    if normalized_user == normalized_question:
        return 1.0

    # -----------------------------------------------------
    # Phrase Match
    # -----------------------------------------------------

    if (
        normalized_user in normalized_question
        or
        normalized_question in normalized_user
    ):
        return 0.96

    # -----------------------------------------------------
    # Question similarity
    # -----------------------------------------------------

    question_score = similarity(
        normalized_user,
        normalized_question
    )

    # -----------------------------------------------------
    # Keyword similarity
    # -----------------------------------------------------

    keyword_score = keyword_similarity(
        normalized_user,
        keywords
    )

    # -----------------------------------------------------
    # Final score
    # -----------------------------------------------------

    final_score = (
        question_score * 0.78
        +
        keyword_score * 0.22
    )

    # -----------------------------------------------------
    # Bonus للكلمات المشتركة
    # -----------------------------------------------------

    user_words = words(
        normalized_user
    )

    question_words = words(
        normalized_question
    )

    if user_words and question_words:

        common = user_words & question_words

        if common:

            coverage = (
                len(common)
                /
                len(user_words)
            )

            if coverage >= 0.80:

                final_score += 0.08

            elif coverage >= 0.60:

                final_score += 0.04

    return min(
        final_score,
        0.99
    )


# =========================================================
# Search Answer
# =========================================================

def search_answer(user_text):
    """
    البحث عن أفضل إجابة.

    هذه هي الدالة التي يستخدمها main.py.
    """

    if not user_text:
        return None

    user_text = str(
        user_text
    ).strip()

    if not user_text:
        return None

    normalized_user = normalize_text(
        user_text
    )

    if not normalized_user:
        return None

    # =====================================================
    # تحميل المعرفة
    # =====================================================

    try:

        knowledge = get_all_knowledge()

    except Exception:

        return None

    if not knowledge:
        return None

    # =====================================================
    # المرحلة 1
    # Exact normalized match
    # =====================================================

    for item in knowledge:

        question = item["question"]

        if normalize_text(
            question
        ) == normalized_user:

            return item["answer"]

    # =====================================================
    # المرحلة 2
    # Compact match
    # =====================================================

    compact_user = normalized_user.replace(
        " ",
        ""
    )

    if compact_user:

        for item in knowledge:

            compact_question = normalize_text(
                item["question"]
            ).replace(
                " ",
                ""
            )

            if compact_question == compact_user:

                return item["answer"]

    # =====================================================
    # المرحلة 3
    # Scoring
    # =====================================================

    best_item = None

    best_score = 0.0

    for item in knowledge:

        try:

            score = score_candidate(
                user_text,
                item
            )

        except Exception:

            continue

        if score > best_score:

            best_score = score

            best_item = item

    # =====================================================
    # لا توجد نتيجة
    # =====================================================

    if best_item is None:
        return None

    # =====================================================
    # Confidence Threshold
    # =====================================================

    user_word_count = len(
        words(user_text)
    )

    # سؤال قصير جدًا
    if user_word_count <= 1:

        threshold = 0.78

    # سؤال قصير
    elif user_word_count <= 2:

        threshold = 0.68

    # سؤال متوسط
    elif user_word_count <= 4:

        threshold = 0.55

    # سؤال طويل
    else:

        threshold = 0.48

    if best_score < threshold:

        return None

    return best_item["answer"]


# =========================================================
# Search Candidates
# =========================================================

def search_candidates(
    user_text,
    limit=5
):
    """
    إرجاع أفضل النتائج مع درجاتها.

    مفيدة للاختبار والتطوير مستقبلًا.
    """

    if not user_text:
        return []

    try:

        knowledge = get_all_knowledge()

    except Exception:

        return []

    results = []

    for item in knowledge:

        try:

            score = score_candidate(
                user_text,
                item
            )

            results.append(
                (
                    score,
                    item
                )
            )

        except Exception:

            continue

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:limit]


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

def brain_test(question):

    """
    أداة اختبار بسيطة.

    مثال:

        brain_test("من انت")

    ترجع:
        {
            "answer": "...",
            "score": ...
        }
    """

    candidates = search_candidates(
        question,
        limit=1
    )

    if not candidates:
        return {
            "answer": None,
            "score": 0.0,
            "question": None
        }

    score, item = candidates[0]

    return {
        "answer": item["answer"],
        "score": round(score, 4),
        "question": item["question"]
    }