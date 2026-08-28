import sqlite3
import random
from config import DATABASE_NAME


# =========================================================
# SHADOW PATIENCE SYSTEM 😈
# =========================================================

def get_connection():
    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_patience():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patience (
            user_id INTEGER PRIMARY KEY,
            unknown_count INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_patience(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT unknown_count
        FROM patience
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return 0

    return row["unknown_count"]


def increase_patience(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO patience (user_id, unknown_count)
        VALUES (?, 1)
        ON CONFLICT(user_id)
        DO UPDATE SET unknown_count = unknown_count + 1
    """, (user_id,))

    conn.commit()

    cursor.execute("""
        SELECT unknown_count
        FROM patience
        WHERE user_id = ?
    """, (user_id,))

    count = cursor.fetchone()["unknown_count"]

    conn.close()

    return count


def reset_patience(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM patience
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


# =========================================================
# SHADOW RESPONSES
# =========================================================

LEVEL_1 = [
    "🤔 هذا السؤال لم أجده في ذاكرتي.",
    "😶 لا أملك جوابًا لهذا السؤال حتى الآن.",
    "🧠 يبدو أنك وجدت شيئًا لم أتعلمه بعد.",
    "👤 Shadow لا يعرف كل شيء... حتى الآن."
]


LEVEL_2 = [
    "😈 سؤال آخر لا أعرفه؟ أنت بدأت تختبر ذاكرتي.",
    "😂 يبدو أنك مصر على البحث عن نقاط ضعفي.",
    "🕶️ لم أعرفه أيضًا... لكن لا تتحمس كثيرًا.",
    "😏 سؤال جيد، لكنه خارج حدود ذاكرتي.",
    "🤨 أنت تبحث عن سؤال لا أعرفه وكأنك في مهمة سرية."
]


LEVEL_3 = [
    "⚠️ تحذير: كثرة الأسئلة المجهولة بدأت تستهلك صبر Shadow.",
    "😈 قلت لك إنني لا أعرف... لماذا تصر؟",
    "🕶️ نصيحة ودية: توقف عن اختبار حدود ذاكرتي.",
    "⚠️ Shadow بدأ يفقد صبره قليلًا.",
    "😏 أنت الآن تختبر النظام أكثر مما تختبر معلوماتي."
]


LEVEL_4 = [
    "😈 آخر تحذير تقريبًا... لا تجعلني أبدأ بالسخرية منك.",
    "🕶️ أنت تعرف أنني لا أعرف السؤال، ومع ذلك تستمر؟ مثير للاهتمام.",
    "⚠️ صبري البرمجي له حدود أيضًا.",
    "😈 يبدو أنك قررت أن تجعلني أندم على إعطائك صندوق الأسئلة.",
    "😂 هل هذه محادثة أم تحقيق رسمي مع Shadow؟"
]


LEVEL_5 = [
    "☠️ كفى. أنت لا تبحث عن إجابة، أنت تبحث عن أعصابي.",
    "😈 واضح أنك قررت اختبار صبري بدل اختبار معرفتي.",
    "🕶️ توقف قليلًا... حتى الظل يحتاج إلى استراحة من أسئلتك.",
    "😂 إذا كان هدفك إحراجي، فقد نجحت. الآن ارحم ذاكرتي.",
    "☠️ السؤال الخامس عشر الذي لا أعرفه... هل تريد مني اختراع الإجابة من العدم؟"
]


def get_patience_response(count):

    if count <= 2:
        pool = LEVEL_1

    elif count <= 5:
        pool = LEVEL_2

    elif count <= 8:
        pool = LEVEL_3

    elif count <= 11:
        pool = LEVEL_4

    else:
        pool = LEVEL_5

    return random.choice(pool)


def handle_unknown(user_id):

    count = increase_patience(user_id)

    response = get_patience_response(count)

    return response, count