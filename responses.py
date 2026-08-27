# =========================================================
# Shadow Personality
# =========================================================

PERSONALITY_RESPONSES = {

    "unknown": [
        "🤔 هذا السؤال لم أتعلم إجابته بعد.",
        "😶 سؤال قوي... لكنك وجدت ثغرة في ذاكرتي.",
        "🧠 لم أجد جوابًا مناسبًا لهذا السؤال.",
        "👤 Shadow لا يعرف كل شيء... حتى الآن.",
        "😈 هذا السؤال سأحتفظ به في قائمة الأسئلة التي تحتاج إلى دراسة.",
        "😂 ضبطتني! لا أعرف الإجابة."
    ],

    "thinking": [
        "🔎 لحظة... أبحث في ذاكرتي.",
        "🧠 دعني أفتش بين أكوادي...",
        "👤 Shadow يفكر... بطريقة لا تشبه تفكير البشر 😂"
    ],

    "welcome": [
        "👤 أهلًا بك في Shadow.",
        "😈 مرحبًا بك... حاول أن تسأل سؤالًا لا أعرفه.",
        "🔥 أهلًا! هل جئت لاختبار حدودي؟",
        "🧠 مرحبًا بك في ذاكرة Shadow."
    ],

    "error": [
        "⚠️ حدث خطأ صغير... حتى الظلال تتعثر أحيانًا.",
        "😵 حدث شيء لم يعجبني في السيرفر.",
        "⚠️ يبدو أن هناك مشكلة تقنية. جرّب مرة أخرى."
    ]
}


def get_unknown_response():
    import random
    return random.choice(
        PERSONALITY_RESPONSES["unknown"]
    )


def get_welcome_response():
    import random
    return random.choice(
        PERSONALITY_RESPONSES["welcome"]
    )


def get_error_response():
    import random
    return random.choice(
        PERSONALITY_RESPONSES["error"]
    )