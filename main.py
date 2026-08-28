# =========================================================
# SHADOW BOT 👤
# Personal Knowledge Telegram Bot
# =========================================================

import time
import logging
import random

import telebot
from telebot import types

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    BOT_NAME,
    OWNER_NAME
)

from database import (
    init_database,
    save_user,
    add_knowledge,
    get_all_knowledge,
    record_unknown_question,
    get_statistics,
    get_unknown_questions,
)

from brain import (
    search_answer,
    normalize_text
)

from responses import (
    get_unknown_response,
    get_welcome_response,
    get_error_response,
)

from knowledge import get_knowledge

from patience import (
    init_patience,
    handle_unknown,
    reset_patience,
    get_patience,
)


# =========================================================
# Logging
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("Shadow")


# =========================================================
# Bot Configuration
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
# Database Initialization
# =========================================================

init_database()
init_patience()


# =========================================================
# Runtime States
# =========================================================

admin_states = {}


# =========================================================
# Helpers
# =========================================================

def is_admin(user_id):
    """
    التحقق من أن المستخدم هو المدير.
    """

    try:
        return int(user_id) == int(ADMIN_ID)

    except Exception:
        return False


def safe_text(text):
    """
    تنظيف النص.
    """

    if not text:
        return ""

    return text.strip()


# =========================================================
# Knowledge Seeder
# =========================================================

def seed_knowledge():
    """
    تحميل المعرفة الموجودة في knowledge.py
    إلى SQLite بدون تكرار.
    """

    try:

        existing = get_all_knowledge()

        existing_questions = {
            normalize_text(row["question"])
            for row in existing
        }

        added = 0

        knowledge_items = get_knowledge()

        for item in knowledge_items:

            if not isinstance(item, dict):
                continue

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
                    "Knowledge item error: %s",
                    e
                )

        logger.info(
            "Knowledge loaded successfully. Added: %s",
            added
        )

    except Exception as e:

        logger.exception(
            "Knowledge loading failed: %s",
            e
        )


# =========================================================
# Load Knowledge
# =========================================================

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

        user_id = message.from_user.id

        save_user(
            message.from_user
        )

        reset_patience(
            user_id
        )

        text = (

            f"👤 <b>مرحبًا بك في {BOT_NAME}</b>\n\n"

            f"أنا Shadow، بوت خاص بـ "
            f"<b>{OWNER_NAME}</b>.\n\n"

            "🧠 لدي قاعدة معرفة خاصة بي.\n"
            "😈 اسألني ما يخطر في بالك.\n\n"

            "لكن تذكر...\n"

            "<i>"
            "ليس كل سؤال ستجد له إجابة."
            "</i>"

        )

        bot.send_message(

            message.chat.id,

            text,

            reply_markup=main_menu(
                user_id
            )

        )

    except Exception as e:

        logger.exception(
            "Start error: %s",
            e
        )

        bot.send_message(

            message.chat.id,

            get_error_response()

        )


# =========================================================
# /help
# =========================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    try:

        save_user(
            message.from_user
        )

        text = (

            "🕶️ <b>Shadow Help</b>\n\n"

            "أرسل لي أي سؤال.\n"
            "سأبحث عن الإجابة داخل ذاكرتي.\n\n"

            "<b>الأوامر:</b>\n"

            "• /start — تشغيل Shadow\n"
            "• /help — المساعدة\n"

        )

        if is_admin(
            message.from_user.id
        ):

            text += (

                "\n👑 <b>أوامر المدير:</b>\n"

                "• /admin — لوحة التحكم\n"
                "• /add — تعليم Shadow\n"
                "• /stats — الإحصائيات\n"
                "• /unknown — الأسئلة المجهولة\n"
                "• /cancel — إلغاء التعليم\n"

            )

        bot.send_message(
            message.chat.id,
            text
        )

    except Exception as e:

        logger.exception(
            "Help error: %s",
            e
        )


# =========================================================
# /admin
# =========================================================

@bot.message_handler(commands=["admin"])
def admin_command(message):

    try:

        save_user(
            message.from_user
        )

        user_id = message.from_user.id

        if not is_admin(user_id):

            bot.send_message(

                message.chat.id,

                "🚫 هذه المنطقة ليست لك."

            )

            return

        bot.send_message(

            message.chat.id,

            (
                "👑 <b>Shadow Control Center</b>\n\n"

                f"مرحبًا يا "
                f"{message.from_user.first_name}.\n\n"

                "هذه لوحة التحكم الأساسية.\n"
                "اختر العملية التي تريد تنفيذها."
            ),

            reply_markup=admin_menu()

        )

    except Exception as e:

        logger.exception(
            "Admin error: %s",
            e
        )


# =========================================================
# /stats
# =========================================================

@bot.message_handler(commands=["stats"])
def stats_command(message):

    try:

        save_user(
            message.from_user
        )

        if not is_admin(
            message.from_user.id
        ):

            bot.send_message(

                message.chat.id,

                "🚫 هذا الأمر للمدير فقط."

            )

            return

        send_statistics(
            message.chat.id
        )

    except Exception as e:

        logger.exception(
            "Stats error: %s",
            e
        )


def send_statistics(chat_id):

    stats = get_statistics()

    text = (

        "📊 <b>Shadow Statistics</b>\n\n"

        f"👥 المستخدمون: "
        f"<b>{stats['users']}</b>\n"

        f"🧠 المعرفة: "
        f"<b>{stats['knowledge']}</b>\n"

        f"❓ الأسئلة المجهولة: "
        f"<b>{stats['unknown']}</b>\n"

        f"💬 الرسائل: "
        f"<b>{stats['messages']}</b>"

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

    try:

        save_user(
            message.from_user
        )

        if not is_admin(
            message.from_user.id
        ):

            bot.send_message(

                message.chat.id,

                "🚫 هذا الأمر للمدير فقط."

            )

            return

        send_unknown_questions(
            message.chat.id
        )

    except Exception as e:

        logger.exception(
            "Unknown command error: %s",
            e
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

    text = (
        "❓ <b>أكثر الأسئلة المجهولة:</b>\n\n"
    )

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

    try:

        save_user(
            message.from_user
        )

        user_id = message.from_user.id

        if not is_admin(user_id):

            bot.send_message(

                message.chat.id,

                "🚫 التعليم متاح لصاحب Shadow فقط."

            )

            return

        admin_states[user_id] = {

            "state": "question"

        }

        bot.send_message(

            message.chat.id,

            (
                "➕ <b>تعليم Shadow</b>\n\n"

                "أرسل الآن السؤال الذي تريد "
                "أن تعلمني إياه.\n\n"

                "مثال:\n"

                "<code>"
                "ما لون Shadow المفضل؟"
                "</code>\n\n"

                "للإلغاء:\n"

                "<code>/cancel</code>"
            )

        )

    except Exception as e:

        logger.exception(
            "Add error: %s",
            e
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
# Admin Teaching
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

    # =====================================================
    # Question
    # =====================================================

    if state == "question":

        state_data["question"] = text

        state_data["state"] = "answer"

        bot.send_message(

            message.chat.id,

            (
                "✅ تم حفظ السؤال.\n\n"

                "💬 الآن أرسل الإجابة "
                "التي تريد أن أتعلمها."
            )

        )

        return True

    # =====================================================
    # Answer
    # =====================================================

    if state == "answer":

        question = state_data.get(
            "question"
        )

        answer = text

        try:

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

                        f"❓ <b>السؤال:</b>\n"
                        f"{question}\n\n"

                        f"💬 <b>الإجابة:</b>\n"
                        f"{answer}"
                    )

                )

        except Exception as e:

            logger.exception(
                "Teaching error: %s",
                e
            )

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

        # =================================================
        # Who
        # =================================================

        if call.data == "who":

            answer = search_answer(
                "من انت"
            )

            if not answer:

                answer = (
                    f"👤 أنا {BOT_NAME}، "
                    f"بوت خاص بـ {OWNER_NAME}."
                )

            reset_patience(
                user_id
            )

            bot.send_message(

                call.message.chat.id,

                answer

            )

            return

        # =================================================
        # Abilities
        # =================================================

        if call.data == "abilities":

            answer = search_answer(
                "ماذا تستطيع ان تفعل"
            )

            if not answer:

                answer = (
                    "⚡ أستطيع فعل الكثير... "
                    "لكن لا تتوقع مني أن أخبرك "
                    "بكل أسراري دفعة واحدة. 😈"
                )

            reset_patience(
                user_id
            )

            bot.send_message(

                call.message.chat.id,

                answer

            )

            return

        # =================================================
        # How
        # =================================================

        if call.data == "how":

            answer = search_answer(
                "كيف تعمل"
            )

            if not answer:

                answer = (
                    "🧠 أعمل بقاعدة معرفة خاصة بي، "
                    "وأبحث عن السؤال الأقرب داخل "
                    "ذاكرتي."
                )

            reset_patience(
                user_id
            )

            bot.send_message(

                call.message.chat.id,

                answer

            )

            return

        # =================================================
        # Owner
        # =================================================

        if call.data == "owner":

            answer = search_answer(
                "من برمجك"
            )

            if not answer:

                answer = (
                    f"👨‍💻 قام ببرمجتي "
                    f"<b>{OWNER_NAME}</b>."
                )

            reset_patience(
                user_id
            )

            bot.send_message(

                call.message.chat.id,

                answer

            )

            return

        # =================================================
        # Test
        # =================================================

        if call.data == "test":

            questions = [

                "من أنت؟",

                "ماذا تستطيع أن تفعل؟",

                "هل أنت ذكاء اصطناعي؟",

                "هل لديك ذاكرة؟",

                "من برمجك؟",

                "هل أنت مجنون؟",

                "كيف تعمل؟",

                "هل تخاف من الأسئلة؟",

                "هل تستطيع أن تتعلم؟",

                "هل لديك أسرار؟"

            ]

            question = random.choice(
                questions
            )

            bot.send_message(

                call.message.chat.id,

                (
                    "🎲 <b>اختبار Shadow</b>\n\n"

                    "جرّب أن تسألني:\n\n"

                    f"❓ <i>{question}</i>\n\n"

                    "😈 ولنرَ ماذا سأجيب..."
                )

            return

        # =================================================
        # Admin Center
        # =================================================

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

        # =================================================
        # Admin Add
        # =================================================

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

                    "مثال:\n"

                    "<code>"
                    "ما هو لون Shadow المفضل؟"
                    "</code>\n\n"

                    "أرسل /cancel للإلغاء."
                )

            )

            return

        # =================================================
        # Admin Stats
        # =================================================

        if call.data == "admin_stats":

            if not is_admin(user_id):
                return

            send_statistics(
                call.message.chat.id
            )

            return

        # =================================================
        # Admin Unknown
        # =================================================

        if call.data == "admin_unknown":

            if not is_admin(user_id):
                return

            send_unknown_questions(
                call.message.chat.id
            )

            return

        # =================================================
        # Back
        # =================================================

        if call.data == "back_main":

            bot.send_message(

                call.message.chat.id,

                "👤 <b>القائمة الرئيسية:</b>",

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

        # =================================================
        # Cancel
        # =================================================

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

        # =================================================
        # Admin Teaching
        # =================================================

        if is_admin(user_id):

            if user_id in admin_states:

                handled = handle_admin_state(
                    message
                )

                if handled:
                    return

        # =================================================
        # Knowledge Search
        # =================================================

        answer = search_answer(
            text
        )

        if answer:

            # سؤال معروف = استعادة صبر Shadow
            reset_patience(
                user_id
            )

            bot.send_message(

                message.chat.id,

                answer

            )

            return

        # =================================================
        # Unknown Question
        # =================================================

        record_unknown_question(

            user_id,

            text

        )

        # =================================================
        # Patience System
        # =================================================

        reply, count = handle_unknown(
            user_id
        )

        # إضافة معلومات بسيطة حسب المستوى
        if count == 5:

            reply += (
                "\n\n⚠️ <i>"
                "ملاحظة: صبر Shadow بدأ ينفد."
                "</i>"
            )

        elif count == 10:

            reply += (
                "\n\n😈 <i>"
                "تحذير أخير تقريبًا..."
                "</i>"
            )

        elif count >= 15:

            reply += (
                "\n\n☠️ <i>"
                "لقد تجاوزت مرحلة اختبار "
                "المعرفة ودخلت مرحلة اختبار الصبر."
                "</i>"
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
# Bot Information
# =========================================================

def print_startup_info():

    stats = get_statistics()

    logger.info(
        "=" * 60
    )

    logger.info(
        "SHADOW BOT STARTED"
    )

    logger.info(
        "Bot: %s",
        BOT_NAME
    )

    logger.info(
        "Owner: %s",
        OWNER_NAME
    )

    logger.info(
        "Knowledge: %s",
        stats["knowledge"]
    )

    logger.info(
        "Users: %s",
        stats["users"]
    )

    logger.info(
        "Unknown Questions: %s",
        stats["unknown"]
    )

    logger.info(
        "=" * 60
    )


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