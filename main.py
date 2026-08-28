# =========================================================
# SHADOW BOT
# Personal Knowledge Telegram Bot
# =========================================================

import os
import time
import logging
import random

import telebot
from telebot import types

from config import BOT_TOKEN, ADMIN_ID, BOT_NAME, OWNER_NAME

from database import (
    init_database,
    save_user,
    add_knowledge,
    get_all_knowledge,
    record_unknown_question,
    get_statistics,
    get_unknown_questions,
)

from brain import search_answer, normalize_text
from responses import (
    get_unknown_response,
    get_welcome_response,
    get_error_response,
)

from knowledge import get_knowledge


# =========================================================
# Logging
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("Shadow")


# =========================================================
# Bot
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN غير موجود في Railway Variables."
    )

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# =========================================================
# Database
# =========================================================

init_database()


# =========================================================
# Runtime states
# =========================================================

admin_states = {}

# عدد الأسئلة المجهولة المتتالية لكل مستخدم
unknown_streak = {}

# آخر سؤال مجهول لكل مستخدم
last_unknown_question = {}


# =========================================================
# Shadow unknown responses
# =========================================================

UNKNOWN_LEVEL_1 = [
    "🤔 هذا السؤال غير موجود في ذاكرتي حاليًا.",
    "🧠 لم أجد إجابة لهذا السؤال.",
    "😶 هذه المرة وجدتني بلا جواب.",
    "🕶️ هذا السؤال خرج قليلًا عن حدود ذاكرتي.",
]

UNKNOWN_LEVEL_2 = [
    "🕶️ يبدو أنك بدأت تختبر حدود Shadow.",
    "😈 سؤال آخر لا أعرفه؟ بدأت أشك أنك تتعمد إحراجي.",
    "🤔 أنت مصمم على العثور على نقطة ضعفي، أليس كذلك؟",
    "🧠 لم أعرفه... لكنني لاحظت إصرارك.",
]

UNKNOWN_LEVEL_3 = [
    "⚠️ نصيحة من Shadow: لا تكثر من الأسئلة التي لا أملك إجاباتها.",
    "😈 قلت لك إنني لا أعرف... لا تجعلني أرفع مستوى السخرية.",
    "🕶️ أنت تقترب من منطقة لا أنصحك بالإقامة فيها طويلًا.",
    "⚠️ يبدو أنك مصر على اختبار صبري.",
]

UNKNOWN_LEVEL_4 = [
    "😈 حسنًا... أنت لا تبحث عن إجابة، أنت تبحث عن مشاكل.",
    "🕶️ ما زلت مستمرًا؟ لديك إصرار غريب فعلًا.",
    "😂 أنا لا أعرف الإجابة، وأنت لا تعرف متى تتوقف. تعادل.",
    "😈 آخر تحذير ساخر: غيّر السؤال قبل أن تصبح أنت السؤال.",
]

UNKNOWN_LEVEL_5 = [
    "🕶️ واضح أنك قررت تحويل المحادثة إلى اختبار صبر رسمي.",
    "😈 ممتاز... لقد وصلت إلى مرحلة جعل Shadow يسخر منك بدلًا من السؤال.",
    "😂 يا رجل، حتى قاعدة البيانات بدأت تتساءل لماذا أنت مصر.",
    "⚠️ كفاية أسئلة مجهولة. أعطني شيئًا أعرفه.",
]


# =========================================================
# Helpers
# =========================================================

def is_admin(user_id):
    return int(user_id) == int(ADMIN_ID)


def safe_text(text):
    if not text:
        return ""

    return text.strip()


def get_unknown_reply(user_id, question):
    """
    إنشاء رد تدريجي عندما لا يعرف Shadow الإجابة.
    """

    normalized = normalize_text(question)

    previous = last_unknown_question.get(user_id)

    # إذا كرر نفس السؤال، زد مستوى الإصرار
    if previous == normalized:
        unknown_streak[user_id] = (
            unknown_streak.get(user_id, 0) + 1
        )
    else:
        # سؤال مجهول جديد
        unknown_streak[user_id] = (
            unknown_streak.get(user_id, 0) + 1
        )

    last_unknown_question[user_id] = normalized

    level = unknown_streak[user_id]

    if level <= 1:
        return random.choice(UNKNOWN_LEVEL_1)

    if level == 2:
        return random.choice(UNKNOWN_LEVEL_2)

    if level == 3:
        return random.choice(UNKNOWN_LEVEL_3)

    if level == 4:
        return random.choice(UNKNOWN_LEVEL_4)

    return random.choice(UNKNOWN_LEVEL_5)


def reset_unknown_streak(user_id):
    unknown_streak[user_id] = 0
    last_unknown_question.pop(user_id, None)


# =========================================================
# Knowledge Seeder
# =========================================================

def seed_knowledge():
    """
    تحميل المعرفة الموجودة في knowledge.py
    إلى SQLite بدون تكرار الأسئلة.
    """

    existing = get_all_knowledge()

    existing_questions = {
        normalize_text(row["question"])
        for row in existing
    }

    added = 0

    for item in get_knowledge():

        question = safe_text(
            item.get("question", "")
        )

        answer = safe_text(
            item.get("answer", "")
        )

        category = item.get(
            "category",
            "general"
        )

        keywords = item.get(
            "keywords",
            ""
        )

        if not question or not answer:
            continue

        normalized_question = normalize_text(
            question
        )

        if normalized_question in existing_questions:
            continue

        try:
            add_knowledge(
                question=question,
                answer=answer,
                category=category,
                keywords=keywords
            )

            existing_questions.add(
                normalized_question
            )

            added += 1

        except Exception as e:
            logger.error(
                "Knowledge error: %s",
                e
            )

    logger.info(
        "Knowledge loaded. Added: %s",
        added
    )


# تحميل المعرفة عند تشغيل البوت
seed_knowledge()


# =========================================================
# Main Menu
# =========================================================

def main_menu(user_id):

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "👤 من أنا؟",
            callback_data="who"
        ),
        types.InlineKeyboardButton(
            "⚡ ماذا تستطيع؟",
            callback_data="abilities"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🧠 كيف تعمل؟",
            callback_data="how"
        ),
        types.InlineKeyboardButton(
            "👨‍💻 من برمجك؟",
            callback_data="owner"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🎲 اختبر Shadow",
            callback_data="test"
        )
    )

    if is_admin(user_id):
        keyboard.add(
            types.InlineKeyboardButton(
                "👑 Shadow Control Center",
                callback_data="admin"
            )
        )

    return keyboard


# =========================================================
# Admin Menu
# =========================================================

def admin_menu():

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "➕ ADD",
            callback_data="admin_add"
        ),
        types.InlineKeyboardButton(
            "📊 الإحصائيات",
            callback_data="admin_stats"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❓ الأسئلة المجهولة",
            callback_data="admin_unknown"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="back_main"
        )
    )

    return keyboard


# =========================================================
# /start
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    try:
        save_user(message.from_user)

        reset_unknown_streak(
            message.from_user.id
        )

        text = (
            f"👤 <b>مرحبًا بك في {BOT_NAME}</b>\n\n"
            f"أنا Shadow، بوت خاص بـ "
            f"<b>{OWNER_NAME}</b>.\n\n"
            "🧠 لدي قاعدة معرفة خاصة بي.\n"
            "😈 اسألني أي شيء يخطر في بالك.\n\n"
            "لكن تذكر...\n"
            "<i>ليس كل سؤال ستجد له إجابة.</i>"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_menu(
                message.from_user.id
            )
        )

    except Exception as e:
        logger.exception(e)

        bot.send_message(
            message.chat.id,
            get_error_response()
        )


# =========================================================
# /help
# =========================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    save_user(message.from_user)

    text = (
        "🕶️ <b>Shadow Help</b>\n\n"
        "أرسل لي أي سؤال وسأبحث عنه داخل ذاكرتي.\n\n"
        "الأوامر:\n"
        "• /start — تشغيل Shadow\n"
        "• /help — المساعدة\n"
    )

    if is_admin(message.from_user.id):

        text += (
            "\n👑 <b>أوامر المدير:</b>\n"
            "• /admin — لوحة التحكم\n"
            "• /add — تعليم Shadow\n"
            "• /stats — الإحصائيات\n"
            "• /unknown — الأسئلة المجهولة\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# /admin
# =========================================================

@bot.message_handler(commands=["admin"])
def admin_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "🚫 هذه المنطقة ليست لك."
        )

        return

    bot.send_message(
        message.chat.id,
        (
            "👑 <b>Shadow Control Center</b>\n\n"
            f"مرحبًا يا {message.from_user.first_name}.\n"
            "هذه لوحة التحكم الأساسية."
        ),
        reply_markup=admin_menu()
    )


# =========================================================
# /stats
# =========================================================

@bot.message_handler(commands=["stats"])
def stats_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "🚫 هذا الأمر للمدير فقط."
        )

        return

    send_statistics(
        message.chat.id
    )


def send_statistics(chat_id):

    stats = get_statistics()

    text = (
        "📊 <b>Shadow Statistics</b>\n\n"
        f"👥 المستخدمون: <b>{stats['users']}</b>\n"
        f"🧠 المعرفة: <b>{stats['knowledge']}</b>\n"
        f"❓ الأسئلة المجهولة: <b>{stats['unknown']}</b>\n"
        f"💬 الرسائل: <b>{stats['messages']}</b>"
    )

    bot.send_message(
        chat_id,
        text
    )


# =========================================================
# /unknown
# =========================================================

@bot.message_handler(commands=["unknown"])
def unknown_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "🚫 هذا الأمر للمدير فقط."
        )

        return

    send_unknown_questions(
        message.chat.id
    )


def send_unknown_questions(chat_id):

    rows = get_unknown_questions(
        limit=20
    )

    if not rows:

        bot.send_message(
            chat_id,
            "✅ لا توجد أسئلة مجهولة حتى الآن."
        )

        return

    text = "❓ <b>أكثر الأسئلة المجهولة:</b>\n\n"

    for index, row in enumerate(
        rows,
        start=1
    ):

        question = row["question"]
        count = row["count"]

        text += (
            f"{index}. "
            f"<b>{question}</b>\n"
            f"   🔁 {count} مرة\n\n"
        )

    bot.send_message(
        chat_id,
        text
    )


# =========================================================
# /add
# =========================================================

@bot.message_handler(commands=["add"])
def add_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "🚫 التعليم متاح لصاحب Shadow فقط."
        )

        return

    admin_states[
        message.from_user.id
    ] = {
        "state": "question"
    }

    bot.send_message(
        message.chat.id,
        (
            "➕ <b>تعليم Shadow</b>\n\n"
            "أرسل الآن السؤال الذي تريد تعليمي إياه.\n\n"
            "مثال:\n"
            "<code>ما لون Shadow المفضل؟</code>\n\n"
            "للإلغاء أرسل:\n"
            "<code>/cancel</code>"
        )
    )


# =========================================================
# /cancel
# =========================================================

@bot.message_handler(commands=["cancel"])
def cancel_command(message):

    user_id = message.from_user.id

    if not is_admin(user_id):
        return

    admin_states.pop(
        user_id,
        None
    )

    bot.send_message(
        message.chat.id,
        "❌ تم إلغاء عملية التعليم."
    )


# =========================================================
# Admin state handler
# =========================================================

def handle_admin_state(message):

    user_id = message.from_user.id

    state_data = admin_states.get(
        user_id
    )

    if not state_data:
        return False

    state = state_data.get(
        "state"
    )

    text = safe_text(
        message.text
    )

    if not text:
        return True

    # ---------------------------------------------
    # Question
    # ---------------------------------------------

    if state == "question":

        state_data["question"] = text
        state_data["state"] = "answer"

        bot.send_message(
            message.chat.id,
            (
                "✅ تم حفظ السؤال.\n\n"
                "💬 الآن أرسل الإجابة التي تريد أن أتعلمها."
            )
        )

        return True

    # ---------------------------------------------
    # Answer
    # ---------------------------------------------

    if state == "answer":

        question = state_data.get(
            "question"
        )

        answer = text

        try:

            # منع التكرار البسيط
            existing = get_all_knowledge()

            normalized_question = normalize_text(
                question
            )

            already_exists = any(
                normalize_text(
                    row["question"]
                ) == normalized_question
                for row in existing
            )

            if already_exists:

                bot.send_message(
                    message.chat.id,
                    (
                        "⚠️ هذا السؤال موجود "
                        "بالفعل في ذاكرة Shadow."
                    )
                )

            else:

                add_knowledge(
                    question=question,
                    answer=answer,
                    category="admin",
                    keywords=""
                )

                bot.send_message(
                    message.chat.id,
                    (
                        "🧠 <b>تم التعليم بنجاح!</b>\n\n"
                        f"❓ {question}\n\n"
                        f"💬 {answer}"
                    )
                )

        except Exception as e:

            logger.exception(e)

            bot.send_message(
                message.chat.id,
                get_error_response()
            )

        admin_states.pop(
            user_id,
            None
        )

        return True

    return False


# =========================================================
# Callback Queries
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callback_handler(call):

    try:

        user_id = call.from_user.id

        bot.answer_callback_query(
            call.id
        )

        # -----------------------------------------
        # Main buttons
        # -----------------------------------------

        if call.data == "who":

            answer = search_answer(
                "من انت"
            )

            bot.send_message(
                call.message.chat.id,
                answer or get_unknown_response()
            )

            return

        if call.data == "abilities":

            answer = search_answer(
                "ماذا تستطيع ان تفعل"
            )

            bot.send_message(
                call.message.chat.id,
                answer or get_unknown_response()
            )

            return

        if call.data == "how":

            answer = search_answer(
                "كيف تعمل"
            )

            bot.send_message(
                call.message.chat.id,
                answer or get_unknown_response()
            )

            return

        if call.data == "owner":

            answer = search_answer(
                "من برمجك"
            )

            bot.send_message(
                call.message.chat.id,
                answer or (
                    "👨‍💻 صالح الخليفي."
                )
            )

            return

        if call.data == "test":

            questions = [
                "من انت",
                "ماذا تستطيع ان تفعل",
                "هل انت ذكاء اصطناعي",
                "هل لديك ذاكرة",
                "من برمجك",
                "هل انت مجنون",
            ]

            question = random.choice(
                questions
            )

            bot.send_message(
                call.message.chat.id,
                (
                    "🎲 <b>اختبار Shadow</b>\n\n"
                    f"جرّب سؤالي:\n"
                    f"❓ <i>{question}</i>"
                )
            )

            return

        # -----------------------------------------
        # Admin
        # -----------------------------------------

        if call.data == "admin":

            if not is_admin(user_id):

                bot.send_message(
                    call.message.chat.id,
                    "🚫 ممنوع."
                )

                return

            bot.send_message(
                call.message.chat.id,
                (
                    "👑 <b>Shadow Control Center</b>\n\n"
                    "اختر العملية:"
                ),
                reply_markup=admin_menu()
            )

            return

        if call.data == "admin_add":

            if not is_admin(user_id):
                return

            admin_states[user_id] = {
                "state": "question"
            }

            bot.send_message(
                call.message.chat.id,
                (
                    "➕ <b>ADD Knowledge</b>\n\n"
                    "أرسل السؤال الآن.\n\n"
                    "أرسل /cancel للإلغاء."
                )
            )

            return

        if call.data == "admin_stats":

            if not is_admin(user_id):
                return

            send_statistics(
                call.message.chat.id
            )

            return

        if call.data == "admin_unknown":

            if not is_admin(user_id):
                return

            send_unknown_questions(
                call.message.chat.id
            )

            return

        if call.data == "back_main":

            bot.send_message(
                call.message.chat.id,
                "👤 القائمة الرئيسية:",
                reply_markup=main_menu(
                    user_id
                )
            )

            return

    except Exception as e:

        logger.exception(
            "Callback error: %s",
            e
        )


# =========================================================
# Text Messages
# =========================================================

@bot.message_handler(
    content_types=["text"]
)
def text_handler(message):

    try:

        user_id = message.from_user.id

        save_user(
            message.from_user
        )

        text = safe_text(
            message.text
        )

        if not text:
            return

        # -----------------------------------------
        # Cancel
        # -----------------------------------------

        if text == "/cancel":

            if is_admin(user_id):

                admin_states.pop(
                    user_id,
                    None
                )

                bot.send_message(
                    message.chat.id,
                    "❌ تم الإلغاء."
                )

            return

        # -----------------------------------------
        # Admin teaching state
        # -----------------------------------------

        if is_admin(user_id):

            if user_id in admin_states:

                handled = handle_admin_state(
                    message
                )

                if handled:
                    return

        # -----------------------------------------
        # Search knowledge
        # -----------------------------------------

        answer = search_answer(
            text
        )

        if answer:

            reset_unknown_streak(
                user_id
            )

            bot.send_message(
                message.chat.id,
                answer
            )

            return

        # -----------------------------------------
        # Unknown question
        # -----------------------------------------

        record_unknown_question(
            user_id,
            text
        )

        reply = get_unknown_reply(
            user_id,
            text
        )

        bot.send_message(
            message.chat.id,
            reply
        )

    except Exception as e:

        logger.exception(
            "Message error: %s",
            e
        )

        try:

            bot.send_message(
                message.chat.id,
                get_error_response()
            )

        except Exception:
            pass


# =========================================================
# Bot Info
# =========================================================

def print_startup_info():

    stats = get_statistics()

    logger.info("=" * 50)
    logger.info("SHADOW BOT STARTED")
    logger.info("Bot: %s", BOT_NAME)
    logger.info("Owner: %s", OWNER_NAME)
    logger.info(
        "Knowledge: %s",
        stats["knowledge"]
    )
    logger.info(
        "Users: %s",
        stats["users"]
    )
    logger.info("=" * 50)


# =========================================================
# Polling
# =========================================================

def run_bot():

    print_startup_info()

    while True:

        try:

            logger.info(
                "Starting Telegram polling..."
            )

            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )

        except Exception as e:

            logger.exception(
                "Polling crashed: %s",
                e
            )

            logger.info(
                "Restarting in 5 seconds..."
            )

            time.sleep(5)


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    run_bot()