import sqlite3
from datetime import datetime

from config import DATABASE_NAME


# =========================================================
# Database
# =========================================================

def get_connection():
    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# إنشاء الجداول
# =========================================================

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    # المستخدمون
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            first_seen TEXT,
            last_seen TEXT,
            message_count INTEGER DEFAULT 0
        )
    """)

    # الأسئلة والإجابات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            keywords TEXT DEFAULT '',
            created_at TEXT
        )
    """)

    # الأسئلة التي لم يعرفها البوت
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unknown_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            first_seen TEXT,
            last_seen TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# حفظ / تحديث المستخدم
# =========================================================

def save_user(user):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user.id,)
    )

    exists = cursor.fetchone()

    if exists:

        cursor.execute("""
            UPDATE users
            SET username = ?,
                first_name = ?,
                last_name = ?,
                last_seen = ?,
                message_count = message_count + 1
            WHERE user_id = ?
        """, (
            user.username,
            user.first_name,
            user.last_name,
            now,
            user.id
        ))

    else:

        cursor.execute("""
            INSERT INTO users (
                user_id,
                username,
                first_name,
                last_name,
                first_seen,
                last_seen,
                message_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            now,
            now,
            1
        ))

    conn.commit()
    conn.close()


# =========================================================
# إضافة معرفة
# =========================================================

def add_knowledge(
    question,
    answer,
    category="general",
    keywords=""
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO knowledge (
            question,
            answer,
            category,
            keywords,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        question,
        answer,
        category,
        keywords,
        datetime.utcnow().isoformat()
    ))

    conn.commit()

    knowledge_id = cursor.lastrowid

    conn.close()

    return knowledge_id


# =========================================================
# جلب المعرفة
# =========================================================

def get_all_knowledge():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM knowledge
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# =========================================================
# تسجيل سؤال مجهول
# =========================================================

def record_unknown_question(
    user_id,
    question
):

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute("""
        SELECT id
        FROM unknown_questions
        WHERE question = ?
    """, (question,))

    row = cursor.fetchone()

    if row:

        cursor.execute("""
            UPDATE unknown_questions
            SET count = count + 1,
                last_seen = ?
            WHERE id = ?
        """, (
            now,
            row["id"]
        ))

    else:

        cursor.execute("""
            INSERT INTO unknown_questions (
                user_id,
                question,
                count,
                first_seen,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            question,
            1,
            now,
            now
        ))

    conn.commit()
    conn.close()


# =========================================================
# الإحصائيات
# =========================================================

def get_statistics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS count FROM users"
    )
    users = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COUNT(*) AS count FROM knowledge"
    )
    knowledge = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COUNT(*) AS count FROM unknown_questions"
    )
    unknown = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COALESCE(SUM(message_count), 0) AS count FROM users"
    )
    messages = cursor.fetchone()["count"]

    conn.close()

    return {
        "users": users,
        "knowledge": knowledge,
        "unknown": unknown,
        "messages": messages
    }


# =========================================================
# الأسئلة المجهولة
# =========================================================

def get_unknown_questions(limit=20):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM unknown_questions
        ORDER BY count DESC, last_seen DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows