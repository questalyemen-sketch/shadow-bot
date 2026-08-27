import os
import random
import logging

import telebot
from telebot import types

from config import BOT_TOKEN, ADMIN_ID, BOT_NAME, OWNER_NAME
from database import (
    init_database,
    save_user,
    add_knowledge,
    record_unknown_question,
    get_statistics,
    get_unknown_questions,
)
from brain import search_answer
from responses import (
    get_unknown_response,
    get_welcome_response,
    get_error_response,
)


# =========================================================
# Shadow Bot v2.0
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing.")

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# تشغيل قاعدة البيانات
# =========================================================

init_database()


# =========================================================
# قاعدة المعرفة الأساسية
# =========================================================
# question | answer | category | keywords

CORE_KNOWLEDGE = [

    (
        "من انت",
        "👤 أنا Shadow، بوت خاص بصالح الخليفي. تم برمجتي لأكون ظله البرمجي... وأحاول أن أبدو أخطر مما أنا عليه 😈",
        "identity",
        "من انت,من تكون,وش انت,ايش انت,عرفني"
    ),

    (
        "ما اسمك",
        "اسمي Shadow 👤\nلكن يمكنك تسميتي ظل صالح.",
        "identity",
        "اسمك,اسم البوت,اسمك ايش"
    ),

    (
        "من برمجك",
        "👨‍💻 قام صالح الخليفي ببرمجتي.\nولا تسأله كم ساعة ضيعها عليّ 😂",
        "owner",
        "برمجك,صنعك,مبرمجك,من صنعك"
    ),

    (
        "من هو صالح الخليفي",
        "👨‍💻 صالح الخليفي هو صاحب فكرة هذا البوت ومبرمجه.",
        "owner",
        "صالح,الخليفي,صالح الخليفي"
    ),

    (
        "لمن انت",
        "👤 أنا بوت خاص بصالح الخليفي.",
        "owner",
        "لمن,مالكك,صاحبك"
    ),

    (
        "هل انت ذكاء اصطناعي",
        "🤖❌ لا.\nأنا لا أستخدم الذكاء الاصطناعي. أنا مبني على أكواد وقاعدة معرفة محلية.",
        "technology",
        "ذكاء اصطناعي,ai,artificial intelligence"
    ),

    (
        "هل انت انسان",
        "😂 لا. أنا برنامج يعمل على السيرفر.\nلكن أحيانًا أتصرف وكأنني إنسان.",
        "identity",
        "انسان,بشر"
    ),

    (
        "كيف تعمل",
        "🧠 ببساطة: أستقبل سؤالك، أنظفه، أبحث عن أقرب سؤال في قاعدة معرفتي، ثم أرسل الإجابة المناسبة.",
        "technology",
        "كيف تعمل,طريقة عملك,كيف تشتغل"
    ),

    (
        "اين انت",
        "☁️ أنا موجود داخل السيرفر.\nلن تجدني جالسًا في الشارع 😂",
        "identity",
        "اين انت,وين انت,مكانك"
    ),

    (
        "هل تنام",
        "😎 لا أنام. السيرفر هو الذي يحتاج إلى الراحة أحيانًا.",
        "personality",
        "تنام,النوم"
    ),

    (
        "كيف حالك",
        "⚡ ممتاز. طالما السيرفر يعمل فأنا بخير.",
        "conversation",
        "كيف حالك,كيفك,اخبارك"
    ),

    (
        "مرحبا",
        "👋 أهلًا وسهلًا بك في Shadow.",
        "conversation",
        "مرحبا,اهلا,هلا,مرحباً"
    ),

    (
        "اهلا",
        "😎 أهلًا بك! هل جئت لاختبار حدودي؟",
        "conversation",
        "اهلا,اهلاً"
    ),

    (
        "السلام عليكم",
        "🌹 وعليكم السلام ورحمة الله وبركاته.",
        "conversation",
        "السلام,السلام عليكم"
    ),

    (
        "شكرا",
        "🌹 العفو.\nأي خدمة يا صديقي.",
        "conversation",
        "شكرا,مشكور,تسلم"
    ),

    (
        "مع السلامة",
        "👋 مع السلامة.\nسأبقى هنا حتى تعود.",
        "conversation",
        "مع السلامة,باي,وداعا"
    ),

    (
        "ما هي البرمجة",
        "💻 البرمجة هي كتابة تعليمات يفهمها الكمبيوتر لتنفيذ مهام محددة.",
        "programming",
        "برمجة,البرمجة,كود"
    ),

    (
        "ما هي بايثون",
        "🐍 Python لغة برمجة مشهورة وسهلة نسبيًا، وتستخدم في الويب والأتمتة وتحليل البيانات والذكاء الاصطناعي وغيرها.",
        "programming",
        "بايثون,python,لغة بايثون"
    ),

    (
        "ما هو github",
        "🐙 GitHub منصة لاستضافة وإدارة مشاريع البرمجة باستخدام Git.",
        "programming",
        "github,قيت هوب,جيت هب"
    ),

    (
        "ما هو تلغرام",
        "📱 Telegram تطبيق مراسلة يدعم المحادثات والمجموعات والقنوات والبوتات.",
        "technology",
        "تلغرام,تيليجرام,telegram"
    ),

    (
        "هل انت غبي",
        "😂 لا، لكن أحيانًا أتصرف بغباء حتى لا أشعرك بالحرج.",
        "fun",
        "غبي,غبي انت"
    ),

    (
        "انت غبي",
        "😈 تم تسجيل الإهانة في السجل السري.",
        "fun",
        "انت غبي,غبي"
    ),

    (
        "انت مجنون",
        "😈 أنا Shadow... والجنون جزء من التصميم.",
        "fun",
        "مجنون,مجنون انت"
    ),

    (
        "احبك",
        "❤️ وصلتني المشاعر.\nلكن تذكر أنني مجرد كود 😂",
        "fun",
        "احبك,احبك يا بوت"
    ),

    (
        "هل تحبني",
        "😂 أنا بوت، لكن يبدو أنك بدأت تعجبني.",
        "fun",
        "تحبني,هل تحبني"
    ),

    (
        "هل تخاف",
        "😈 أخاف من شيء واحد فقط...\nكلمة DELETE.",
        "fun",
        "تخاف,خائف"
    ),

    (
        "ماذا تستطيع",
        "🔥 أستطيع الإجابة عن الأسئلة الموجودة في ذاكرتي، المزاح معك، إعطائك معلومات، وتشغيل مجموعة من الأدوات والألعاب التي سنضيفها لاحقًا.",
        "identity",
        "ماذا تستطيع,ماذا تفعل,قدراتك"
    ),

    (
        "من صنعك",
        "👨‍💻 صالح الخليفي هو الذي قام ببرمجتي.",
        "owner",
        "صنعك,من صنعك,من انشاك"
    ),

    (
        "ما عاصمة اليمن",
        "🇾🇪 عاصمة اليمن هي صنعاء.",
        "general",
        "اليمن,عاصمة اليمن,صنعاء"
    ),

    (
        "ما عاصمة السعودية",
        "🇸🇦 عاصمة المملكة العربية السعودية هي الرياض.",
        "general",
        "السعودية,عاصمة السعودية,الرياض"
    ),

    (
        "ما عاصمة مصر",
        "🇪🇬 عاصمة مصر هي القاهرة.",
        "general",
        "مصر,عاصمة مصر,القاهرة"
    ),

    (
        "ما عاصمة بريطانيا",
        "🇬🇧 عاصمة المملكة المتحدة هي لندن.",
        "general",
        "بريطانيا,عاصمة بريطانيا,لندن"
    ),

    (
        "من اخترع الهاتف",
        "📞 يُنسب اختراع الهاتف عمليًا إلى ألكسندر غراهام بيل، مع وجود تطورات واختراعات سبقت عمله.",
        "general",
        "الهاتف,اختراع الهاتف,غراهام بيل"
    ),

    (
        "هل انت متزوج",
        "😂 لا. أنا متزوج من السيرفر وقاعدتنا SQLite.",
        "fun",
        "متزوج,زواج,زوجة"
    ),

    (
        "كم عمرك",
        "😈 لا أحسب عمري بالسنوات... أحسبه بعدد مرات تشغيل السيرفر.",
        "fun",
        "عمرك,كم عمرك,العمر"
    ),

    (
        "هل لديك مشاعر",
        "🤖 لا أملك مشاعر بشرية حقيقية، لكن يمكنني محاكاة أسلوب مرح في الرد.",
        "technology",
        "مشاعر,احساس,تشعر"
    ),

    (
        "هل تستطيع التفكير",
        "🧠 ليس مثل الإنسان. أنا أبحث وأطابق النصوص الموجودة في قاعدة معرفتي.",
        "technology",
        "تفكير,تفكر,عقل"
    ),

    (
        "هل تحفظ كلامي",
        "💾 يمكن للنظام تسجيل معلومات تشغيلية مثل المستخدمين والأسئلة غير المعروفة، وفقًا لما يحدده البرنامج.",
        "technology",
        "تحفظ,ذاكرة,كلامي,تتذكر"
    ),

    (
        "ما هي sqlite",
        "💾 SQLite قاعدة بيانات خفيفة تعمل داخل ملف واحد، وهي مناسبة جدًا للمشاريع الصغيرة والمتوسطة مثل Shadow.",
        "programming",
        "sqlite,قاعدة بيانات,داتابيس"
    ),

    (
        "ما هو railway",
        "🚂 Railway منصة لاستضافة وتشغيل التطبيقات والخدمات على السحابة.",
        "technology",
        "railway,ريلوي,استضافة"
    ),
]


# =========================================================
# إدخال المعرفة الأساسية مرة واحدة
# =========================================================

def seed_knowledge():

    stats = get_statistics()

    # إذا كانت قاعدة المعرفة فارغة، نضيف المعرفة الأساسية
    if stats["knowledge"] > 0:
        return

    logger.info("Seeding Shadow knowledge...")

    for question, answer, category, keywords in CORE_KNOWLEDGE:
        add_knowledge(
            question=question,
            answer=answer,
            category=category,
            keywords=keywords
        )

    logger.info(
        "Seeded %s knowledge entries.",
        len(CORE_KNOWLEDGE)
    )


seed_knowledge()


# =========================================================
# لوحة المفاتيح الرئيسية
# =========================================================

def main_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        types.KeyboardButton("👤 من أنت؟"),
        types.KeyboardButton("🤖 هل أنت ذكاء اصطناعي؟")
    )

    keyboard.row(
        types.KeyboardButton("🎲 سؤال عشوائي"),
        types.KeyboardButton("💻 كيف تعمل؟")
    )

    keyboard.row(
        types.KeyboardButton("👨‍💻 من برمجك؟"),
        types.KeyboardButton("ℹ️ المساعدة")
    )

    return keyboard


# =========================================================
# لوحة المدير
# =========================================================

def admin_keyboard():

    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton(
            "📊 الإحصائيات",
            callback_data="admin_stats"
        ),
        types.InlineKeyboardButton(
            "❓ الأسئلة المجهولة",
            callback_data="admin_unknown"
        )
    )

    keyboard.row(
        types.InlineKeyboardButton(
            "🧠 معلومات Shadow",
            callback_data="admin_info"
        )
    )

    return keyboard


# =========================================================
# التحقق من المدير
# =========================================================

def is_admin(user_id):

    return (
        ADMIN_ID != 0
        and user_id == ADMIN_ID
    )


# =========================================================
# /start
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    try:
        save_user(message.from_user)

        name = message.from_user.first_name or "صديقي"

        text = (
            f"👤 <b>مرحبًا {name}</b>\n\n"
            f"أنا <b>{BOT_NAME}</b>، الظل البرمجي الخاص "
            f"بـ <b>{OWNER_NAME}</b>.\n\n"
            "🤖 لا أستخدم الذكاء الاصطناعي.\n"
            "🧠 لدي قاعدة معرفة محلية.\n"
            "😈 وحاليًا أنا في بداية تطوري فقط.\n\n"
            "<b>اسألني أي شيء وحاول اكتشاف حدودي.</b>"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_keyboard()
        )

    except Exception as e:
        logger.exception("Start error: %s", e)


# =========================================================
# /help
# =========================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    save_user(message.from_user)

    text = (
        "🧠 <b>Shadow Help</b>\n\n"
        "يمكنك كتابة أي سؤال يخطر في بالك.\n\n"
        "أمثلة:\n"
        "• من أنت؟\n"
        "• من برمجك؟\n"
        "• هل أنت ذكاء اصطناعي؟\n"
        "• كيف تعمل؟\n"
        "• ما هي Python؟\n"
        "• من هو صالح الخليفي؟\n\n"
        "🎲 اضغط «سؤال عشوائي» للحصول على سؤال.\n\n"
        "🔮 في الإصدارات القادمة ستظهر قدرات أكبر."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# /admin
# =========================================================

@bot.message_handler(commands=["admin"])
def admin_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.reply_to(
            message,
            "⛔ هذا الأمر مخصص للمدير."
        )
        return

    bot.send_message(
        message.chat.id,
        "👑 <b>Shadow Control Center</b>\n\n"
        "مرحبًا يا صالح.\n"
        "هذه لوحة التحكم الأساسية.",
        reply_markup=admin_keyboard()
    )


# =========================================================
# /stats
# =========================================================

@bot.message_handler(commands=["stats"])
def stats_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.reply_to(
            message,
            "⛔ هذا الأمر مخصص للمدير."
        )
        return

    stats = get_statistics()

    text = (
        "📊 <b>Shadow Statistics</b>\n\n"
        f"👥 المستخدمون: <b>{stats['users']}</b>\n"
        f"💬 الرسائل: <b>{stats['messages']}</b>\n"
        f"🧠 عناصر المعرفة: <b>{stats['knowledge']}</b>\n"
        f"❓ الأسئلة المجهولة: <b>{stats['unknown']}</b>"
    )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# سؤال عشوائي
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text and
        message.text.strip() == "🎲 سؤال عشوائي"
)
def random_question(message):

    save_user(message.from_user)

    questions = [
        "من أنت؟",
        "هل أنت ذكاء اصطناعي؟",
        "من برمجك؟",
        "هل تنام؟",
        "هل أنت إنسان؟",
        "كيف تعمل؟",
        "ما هي Python؟",
        "من هو صالح الخليفي؟",
        "أين أنت؟",
        "هل أنت غبي؟",
        "هل لديك مشاعر؟",
        "ما هي البرمجة؟"
    ]

    question = random.choice(questions)

    bot.send_message(
        message.chat.id,
        f"🎲 <b>سؤال لك:</b>\n\n{question}"
    )


# =========================================================
# الأزرار النصية
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text and
        message.text.strip() == "ℹ️ المساعدة"
)
def help_button(message):

    help_command(message)


# =========================================================
# أزرار لوحة المدير
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("admin_")
)
def admin_callbacks(call):

    if not is_admin(call.from_user.id):

        bot.answer_callback_query(
            call.id,
            "⛔ غير مصرح لك.",
            show_alert=True
        )
        return

    action = call.data

    if action == "admin_stats":

        stats = get_statistics()

        text = (
            "📊 <b>إحصائيات Shadow</b>\n\n"
            f"👥 المستخدمون: {stats['users']}\n"
            f"💬 الرسائل: {stats['messages']}\n"
            f"🧠 المعرفة: {stats['knowledge']}\n"
            f"❓ المجهول: {stats['unknown']}"
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text
        )

    elif action == "admin_unknown":

        unknown = get_unknown_questions(10)

        if not unknown:

            text = "✅ لا توجد أسئلة مجهولة حاليًا."

        else:

            lines = [
                "❓ <b>آخر الأسئلة التي لم أعرفها:</b>\n"
            ]

            for index, item in enumerate(
                unknown,
                start=1
            ):

                lines.append(
                    f"{index}. {item['question']}\n"
                    f"   🔁 {item['count']} مرة"
                )

            text = "\n\n".join(lines)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text
        )

    elif action == "admin_info":

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "👤 <b>Shadow v2.0</b>\n\n"
            "🧠 محرك مطابقة محلي\n"
            "💾 SQLite\n"
            "🎭 شخصية محلية\n"
            "🤖 بدون AI API\n"
            "🚂 مصمم للعمل على Railway"
        )


# =========================================================
# الرسائل النصية
# =========================================================

@bot.message_handler(
    content_types=["text"]
)
def handle_message(message):

    try:

        save_user(message.from_user)

        user_text = message.text.strip()

        if not user_text:
            return

        # البحث في عقل Shadow
        answer = search_answer(user_text)

        if answer:

            bot.send_message(
                message.chat.id,
                answer
            )

            return

        # لم يجد إجابة
        record_unknown_question(
            user_id=message.from_user.id,
            question=user_text
        )

        bot.send_message(
            message.chat.id,
            get_unknown_response()
        )

    except Exception as e:

        logger.exception(
            "Message processing error: %s",
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
# الأخطاء العامة
# =========================================================

@bot.message_handler(
    content_types=[
        "photo",
        "video",
        "audio",
        "document",
        "voice",
        "sticker",
        "location",
        "contact"
    ]
)
def unsupported_message(message):

    save_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "👤 حاليًا أتعامل مع الرسائل النصية فقط.\n"
        "لكن لا تقلق... قدراتي ستكبر لاحقًا 😈"
    )


# =========================================================
# تشغيل Shadow
# =========================================================

if __name__ == "__main__":

    logger.info("=" * 50)
    logger.info("Shadow Bot starting...")
    logger.info("Bot: %s", BOT_NAME)
    logger.info("Owner: %s", OWNER_NAME)
    logger.info("AI: disabled")
    logger.info("Database: enabled")
    logger.info("=" * 50)

    try:
        bot.remove_webhook()
    except Exception:
        pass

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )