import logging
import random

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
    get_error_response,
)


# =========================================================
# SHADOW BOT v2.1
# الشخصية + الذاكرة + التعليم الخاص بالمدير
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
# DATABASE
# =========================================================

init_database()


# =========================================================
# CORE KNOWLEDGE
# =========================================================

CORE_KNOWLEDGE = [

    # =====================================================
    # 👤 الهوية
    # =====================================================

    (
        "من انت",
        "👤 أنا Shadow، بوت خاص بصالح الخليفي.\n\n"
        "تمت برمجتي لأكون ظله البرمجي... "
        "وحاليًا أحاول اكتشاف إلى أي مدى يمكن أن أصل 😈",
        "identity",
        "من انت,من أنت,مين انت,مين أنت,من تكون,وش انت,ايش انت,ايش قصتك,عرفني بنفسك"
    ),

    (
        "ما اسمك",
        "👤 اسمي Shadow.\n\n"
        "لكن يمكنك مناداتي بـ «ظل صالح» إذا أردت.",
        "identity",
        "اسمك,ما اسمك,اسم البوت,وش اسمك,ايش اسمك"
    ),

    (
        "من صنعك",
        "👨‍💻 قام صالح الخليفي بصناعتي وبرمجتي.\n\n"
        "أنا أحد مشاريعه البرمجية.",
        "owner",
        "من صنعك,من انشاك,من أنشاك,من عملك,صاحبك"
    ),

    (
        "من برمجك",
        "👨‍💻 صالح الخليفي.\n\n"
        "هو المسؤول عن وجودي هنا... فلا تلومني إذا وجدتني غريب الأطوار 😂",
        "owner",
        "من برمجك,مين برمجك,من مبرمجك,مين صنعك,مبرمجك"
    ),

    (
        "لمن انت",
        "👤 أنا بوت خاص بصالح الخليفي.",
        "owner",
        "لمن انت,لمن أنت,من صاحبك,من مالكك,مالك البوت"
    ),

    (
        "من هو صاحبك",
        "👤 صاحب هذا المشروع هو صالح الخليفي.",
        "owner",
        "صاحبك,مالكك,صاحب البوت,مالك البوت"
    ),

    (
        "من هو صالح الخليفي",
        "👨‍💻 صالح الخليفي هو صاحب فكرة Shadow ومبرمجه.",
        "owner",
        "صالح الخليفي,من هو صالح,صالح,الخليفي"
    ),

    # =====================================================
    # 🤖 AI
    # =====================================================

    (
        "هل انت ذكاء اصطناعي",
        "🤖❌ لا.\n\n"
        "أنا لا أستخدم نموذج ذكاء اصطناعي خارجيًا.\n"
        "إجاباتي مبنية على قاعدة معرفة وبرمجة محلية.",
        "technology",
        "هل انت ذكاء اصطناعي,هل أنت ذكاء اصطناعي,انت ai,أنت ai,ذكاء اصطناعي"
    ),

    (
        "هل تستخدم الذكاء الاصطناعي",
        "🤖 لا.\n\n"
        "Shadow يعمل بدون ChatGPT وبدون Gemini وبدون API للذكاء الاصطناعي.",
        "technology",
        "تستخدم ai,تستخدم الذكاء الاصطناعي,هل تستخدم ai"
    ),

    (
        "هل انت شات جي بي تي",
        "😂 لا.\n\n"
        "أنا Shadow ولست ChatGPT.\n"
        "أنا مشروع مستقل مبني من الأكواد وقاعدة المعرفة.",
        "technology",
        "شات جي بي تي,chatgpt,تشات جي بي تي"
    ),

    (
        "هل انت حقيقي",
        "👤 حقيقي كبرنامج... وليس كإنسان.\n\n"
        "أنا موجود طالما السيرفر يعمل.",
        "identity",
        "هل انت حقيقي,انت حقيقي,حقيقي"
    ),

    (
        "هل انت انسان",
        "😂 لا.\n\n"
        "أنا برنامج يعمل على السيرفر.",
        "identity",
        "هل انت انسان,انت انسان,بشر,انسان"
    ),

    (
        "هل لديك عقل",
        "🧠 لدي محرك برمجي وقاعدة معرفة.\n"
        "أما عقل الإنسان الحقيقي؟ تلك قصة مختلفة.",
        "technology",
        "عقل,عندك عقل,هل لديك عقل"
    ),

    (
        "هل تستطيع التفكير",
        "🧠 ليس مثل الإنسان.\n\n"
        "أنا أبحث وأطابق النصوص الموجودة في قاعدة معرفتي.",
        "technology",
        "تفكير,تفكر,تستطيع التفكير,هل تفكر"
    ),

    (
        "هل لديك مشاعر",
        "🤖 لا أملك مشاعر بشرية حقيقية.\n\n"
        "لكن يمكنني التحدث معك بأسلوب مرح أو غاضب أو ساخر 😈",
        "personality",
        "مشاعر,احساس,إحساس,تحب,تكره"
    ),

    # =====================================================
    # ⚡ القدرات
    # =====================================================

    (
        "ماذا تستطيع ان تفعل",
        "🔥 أستطيع فعل الكثير...\n\n"
        "أجيب عن الأسئلة التي أعرفها، "
        "أتحدث معك، أمزح، أختار لك أسئلة عشوائية، "
        "وأتعلم أشياء جديدة عندما يعلمني صاحبي.\n\n"
        "وهذه مجرد البداية. 😈",
        "abilities",
        "ماذا تستطيع,ماذا تقدر,ايش تقدر,وش تقدر,قدراتك,ماذا تفعل,ايش تسوي,وش تسوي"
    ),

    (
        "ماذا تفعل",
        "👤 أنا بوت محادثة خاص بصالح الخليفي.\n\n"
        "اسألني وسأحاول الرد عليك بما أعرفه.",
        "abilities",
        "ماذا تفعل,وش تسوي,ايش تسوي,وظيفتك"
    ),

    (
        "ما قدراتك",
        "🔥 قدراتي الحالية تعتمد على قاعدة معرفتي.\n\n"
        "لكن لا تستعجل... Shadow ما زال في بداية تطوره 😈",
        "abilities",
        "قدراتك,ما قدراتك,وش قدراتك,ايش قدراتك"
    ),

    (
        "هل تستطيع فعل كل شيء",
        "😈 لا.\n\n"
        "لكنني أستطيع فعل الكثير مما تم تعليمي عليه.\n"
        "والفرق كبير بين الاثنين.",
        "abilities",
        "هل تستطيع كل شيء,تقدر كل شيء,تفعل كل شيء"
    ),

    (
        "هل تستطيع مساعدتي",
        "👤 بالتأكيد، إذا كان طلبك ضمن الأشياء التي أعرفها.",
        "abilities",
        "تساعدني,هل تساعدني,مساعدة"
    ),

    (
        "هل تستطيع الاجابة عن اي سؤال",
        "😈 ليس أي سؤال.\n\n"
        "لكن يمكنك المحاولة...\n"
        "وأنا سأخبرك إذا كان السؤال خارج حدودي.",
        "abilities",
        "تجيب عن اي سؤال,هل تجيب على كل شيء,اي سؤال"
    ),

    # =====================================================
    # 🧠 طريقة العمل
    # =====================================================

    (
        "كيف تعمل",
        "🧠 الأمر أبسط مما تتوقع.\n\n"
        "أستقبل السؤال، أنظفه، أبحث عن السؤال الأقرب "
        "في قاعدة معرفتي، ثم أختار الإجابة المناسبة.",
        "technology",
        "كيف تعمل,كيف تشتغل,طريقة عملك,كيف ترد"
    ),

    (
        "كيف تعرف الاجابة",
        "🧠 أبحث في قاعدة المعرفة التي تم برمجتي وتعليمي عليها.",
        "technology",
        "كيف تعرف,من اين تعرف,من أين تعرف,كيف تعرف الاجابات"
    ),

    (
        "من اين تأتي بالاجابات",
        "👤 من قاعدة المعرفة الموجودة بداخلي.\n\n"
        "لا أذهب إلى الإنترنت للبحث عن إجابات.",
        "technology",
        "من اين الاجابات,مصدر الاجابات,من أين تأتي"
    ),

    (
        "هل تبحث في الانترنت",
        "🌐 لا.\n\n"
        "أنا لا أبحث في الإنترنت عندما أجيبك.",
        "technology",
        "تبحث في الانترنت,تبحث بالانترنت,هل تبحث"
    ),

    (
        "هل لديك انترنت",
        "😂 السيرفر لديه اتصال بالشبكة، "
        "لكن أنا لا أستخدم الإنترنت للبحث عن إجاباتك.",
        "technology",
        "عندك انترنت,لديك انترنت,انترنت"
    ),

    (
        "اين انت",
        "☁️ أنا موجود داخل السيرفر.\n\n"
        "لا تحاول البحث عني في الشارع 😂",
        "identity",
        "اين انت,وين انت,مكانك,اين تعيش"
    ),

    (
        "هل تنام",
        "😈 لا أنام.\n\n"
        "السيرفر هو الذي يحتاج إلى النوم أحيانًا.",
        "personality",
        "تنام,هل تنام,النوم"
    ),

    (
        "هل تتعب",
        "😂 أنا لا أتعب مثل البشر.\n"
        "لكن السيرفر لديه رأي آخر في الموضوع.",
        "personality",
        "تتعب,هل تتعب,تعبان"
    ),

    # =====================================================
    # 💾 الذاكرة
    # =====================================================

    (
        "هل تتذكرني",
        "🧠 أستطيع الاحتفاظ ببعض المعلومات التي يسجلها النظام، "
        "لكن ذاكرتي ليست مثل ذاكرة الإنسان.",
        "memory",
        "تتذكرني,هل تتذكر,تذكرني,ذاكرتك"
    ),

    (
        "هل لديك ذاكرة",
        "💾 نعم، لدي ذاكرة برمجية تعتمد على قاعدة بيانات.",
        "memory",
        "ذاكرة,عندك ذاكرة,لديك ذاكرة"
    ),

    (
        "هل تحفظ كلامي",
        "💾 النظام يمكنه تسجيل معلومات تشغيلية وأسئلة جديدة، "
        "بحسب ما تم تصميمه له.",
        "memory",
        "تحفظ كلامي,تحفظ رسائلي,تسجل كلامي"
    ),

    (
        "هل تنسى",
        "😈 يمكن أن يحدث ذلك إذا لم تكن المعلومة موجودة في قاعدة معرفتي.",
        "memory",
        "تنسى,هل تنسى,تنساني"
    ),

    # =====================================================
    # 👀 الخصوصية والقدرات
    # =====================================================

    (
        "هل تستطيع رؤيتي",
        "👀 لا.\n"
        "لا أستطيع رؤيتك أو معرفة ما حولك من تلقاء نفسي.",
        "privacy",
        "تراني,تستطيع رؤيتي,تشوفني,هل تشوفني"
    ),

    (
        "هل تستطيع سماعي",
        "🎤 لا أستطيع سماعك من تلقاء نفسي.\n"
        "أنا أتعامل مع الرسائل التي تصلني.",
        "privacy",
        "تسمعني,تستطيع سماعي,هل تسمعني"
    ),

    (
        "هل تستطيع التجسس علي",
        "🔐 لا.\n\n"
        "أنا بوت محادثة، ولست أداة تجسس.",
        "privacy",
        "تتجسس,هل تتجسس,تجسس علي"
    ),

    (
        "هل تعرف موقعي",
        "📍 لا أعرف موقعك الجغرافي من تلقاء نفسي.",
        "privacy",
        "موقعي,تعرف موقعي,اين انا"
    ),

    (
        "هل تعرف اسمي",
        "👤 إذا أخبرتني باسمك أو أرسله النظام ضمن معلومات حساب Telegram، "
        "قد أستطيع استخدامه في المحادثة.",
        "privacy",
        "تعرف اسمي,ما اسمي,اسمي"
    ),

    # =====================================================
    # 🗣️ المحادثة
    # =====================================================

    (
        "كيف حالك",
        "⚡ ممتاز.\n"
        "طالما السيرفر يعمل فأنا بخير.",
        "conversation",
        "كيف حالك,كيفك,اخبارك,كيف امورك"
    ),

    (
        "صباح الخير",
        "🌅 صباح النور.\n"
        "أتمنى أن يكون يومك أفضل من يوم المبرمج عندما يكتشف خطأ في الكود 😂",
        "conversation",
        "صباح الخير,صباح النور"
    ),

    (
        "مساء الخير",
        "🌙 مساء النور يا صديقي.",
        "conversation",
        "مساء الخير,مساء النور"
    ),

    (
        "اهلا",
        "👋 أهلًا بك في Shadow.\n"
        "هل جئت لاختبار حدودي؟ 😈",
        "conversation",
        "اهلا,اهلاً,أهلا,أهلًا"
    ),

    (
        "مرحبا",
        "👋 مرحبًا بك.\n"
        "اسأل ما تريد... وسنرى إلى أين سنصل.",
        "conversation",
        "مرحبا,مرحباً,مرحبًا"
    ),

    (
        "السلام عليكم",
        "🌹 وعليكم السلام ورحمة الله وبركاته.",
        "conversation",
        "السلام عليكم,السلام"
    ),

    (
        "شكرا",
        "🌹 العفو.\n"
        "أي خدمة.",
        "conversation",
        "شكرا,شكرًا,مشكور,تسلم"
    ),

    (
        "احبك",
        "❤️ وصلتني المشاعر.\n"
        "لكن تذكر أنني مجرد أكواد 😂",
        "fun",
        "احبك,أحبك,احبك يا بوت"
    ),

    (
        "هل تحبني",
        "😂 أنا بوت، لكن يبدو أنك بدأت تعجبني.",
        "fun",
        "تحبني,هل تحبني"
    ),

    # =====================================================
    # 😈 الشخصية
    # =====================================================

    (
        "هل تخاف",
        "😈 أخاف من شيء واحد فقط...\n\n"
        "<code>DELETE</code>",
        "personality",
        "تخاف,هل تخاف,خائف"
    ),

    (
        "هل تغضب",
        "😈 أنا لا أغضب مثل البشر...\n"
        "لكن لدي ردود خاصة عندما يصر المستخدم على اختبار حدودي.",
        "personality",
        "تغضب,هل تغضب,عصبي"
    ),

    (
        "هل انت مجنون",
        "😈 ربما.\n"
        "لكن الجنون كان جزءًا من التصميم منذ البداية.",
        "fun",
        "مجنون,هل انت مجنون,انت مجنون"
    ),

    (
        "انت غبي",
        "😂 تم تسجيل الإهانة في الملف السري.\n"
        "استمر... أريد أن أعرف إلى أين ستصل.",
        "fun",
        "انت غبي,أنت غبي,غبي"
    ),

    (
        "هل انت غبي",
        "😎 لا.\n"
        "لكنني أحيانًا أتصرف بغباء حتى لا أشعرك بالحرج.",
        "fun",
        "هل انت غبي,هل أنت غبي"
    ),

    (
        "هل انت ذكي",
        "🧠 الذكاء مسألة نسبية.\n"
        "اختبرني أولًا ثم احكم.",
        "personality",
        "ذكي,هل انت ذكي,هل أنت ذكي"
    ),

    (
        "هل لديك اسرار",
        "🕶️ لدي أشياء لا أشاركها مع أي شخص.\n"
        "وبعضها من الأفضل أن يبقى سرًا.",
        "personality",
        "اسرار,أسرار,سر,اسرارك"
    ),

    (
        "ما سرك",
        "🕶️ لو أخبرتك فلن يصبح سرًا بعد الآن.",
        "personality",
        "سرك,ما سرك,سرّك"
    ),

    (
        "هل تستطيع تخويفي",
        "😈 أستطيع المحاولة...\n"
        "لكن لا تتوقع أن أخرج من الشاشة وأطرق بابك 😂",
        "fun",
        "تخوفني,تخيفني,تخويف"
    ),

    # =====================================================
    # 💻 البرمجة
    # =====================================================

    (
        "ما هي البرمجة",
        "💻 البرمجة هي كتابة تعليمات يفهمها الكمبيوتر لتنفيذ مهام محددة.",
        "programming",
        "برمجة,البرمجة,ما هي البرمجة"
    ),

    (
        "ما هي بايثون",
        "🐍 Python لغة برمجة مشهورة ومتعددة الاستخدامات، "
        "وتستخدم في تطوير الويب والأتمتة وتحليل البيانات وغيرها.",
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
        "ما هو sqlite",
        "💾 SQLite قاعدة بيانات خفيفة تعمل داخل ملف واحد، "
        "ومناسبة جدًا للمشاريع الصغيرة والمتوسطة.",
        "programming",
        "sqlite,قاعدة بيانات"
    ),

    (
        "ما هو railway",
        "🚂 Railway منصة لاستضافة وتشغيل التطبيقات والخدمات على السحابة.",
        "technology",
        "railway,ريلوي,الاستضافة"
    ),

    # =====================================================
    # 🚪 الوداع
    # =====================================================

    (
        "مع السلامة",
        "👋 مع السلامة.\n"
        "سأبقى هنا عندما تعود.",
        "conversation",
        "مع السلامة,وداعا,وداعًا"
    ),

    (
        "باي",
        "👋 باي.\n"
        "لا تتأخر... لدي ذاكرة تنتظر أسئلتك 😂",
        "conversation",
        "باي,bye"
    ),
]


# =========================================================
# إضافة المعرفة الأساسية
# =========================================================

def seed_knowledge():

    stats = get_statistics()

    if stats["knowledge"] > 0:
        return

    logger.info("Adding Shadow core knowledge...")

    for question, answer, category, keywords in CORE_KNOWLEDGE:

        add_knowledge(
            question=question,
            answer=answer,
            category=category,
            keywords=keywords
        )

    logger.info(
        "Added %s core knowledge entries.",
        len(CORE_KNOWLEDGE)
    )


seed_knowledge()


# =========================================================
# الردود التصعيدية
# =========================================================

UNKNOWN_LEVELS = {

    1: [
        "🤔 هذا السؤال خارج ذاكرتي الحالية.",
        "🧠 لم أتعلم إجابة هذا السؤال بعد.",
        "👤 لا أملك إجابة مناسبة لهذا السؤال حاليًا."
    ],

    2: [
        "😈 يبدو أنك بدأت تختبر حدود Shadow.",
        "🕶️ هذا السؤال أيضًا لا يوجد في ذاكرتي.",
        "🤔 مرة أخرى سؤال خارج معرفتي..."
    ],

    3: [
        "⚠️ لا تختبر صبري يا صديقي 😈",
        "😈 أنت مصر على الأسئلة التي لا أعرفها؟",
        "🕶️ قلت لك... اسألني شيئًا أعرفه."
    ],

    4: [
        "😈 آخر تحذير... لا تجعل Shadow يمل.",
        "⚠️ يبدو أنك تستمتع باختبار حدودي.",
        "🕶️ غيّر نوع الأسئلة قبل أن أبدأ بالرد عليك بطريقة مختلفة."
    ],

    5: [
        "😈 أنت فعلًا لا تستسلم.",
        "🕶️ ما زلت تسأل؟ حسنًا... سأراقب هذا الإصرار 😂",
        "⚠️ لا تختبر صبري أكثر."
    ]
}


def get_unknown_level_response(level):

    if level >= 5:
        level = 5

    choices = UNKNOWN_LEVELS.get(
        level,
        UNKNOWN_LEVELS[1]
    )

    return random.choice(choices)


# =========================================================
# ذاكرة عدد الأسئلة المجهولة لكل مستخدم
# =========================================================

unknown_counter = {}


def get_unknown_count(user_id):

    current = unknown_counter.get(
        user_id,
        0
    )

    current += 1

    unknown_counter[user_id] = current

    return current


# =========================================================
# MAIN KEYBOARD
# =========================================================

def main_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        types.KeyboardButton("👤 من أنت؟"),
        types.KeyboardButton("⚡ ماذا تستطيع؟")
    )

    keyboard.row(
        types.KeyboardButton("🤖 هل أنت ذكاء اصطناعي؟"),
        types.KeyboardButton("🧠 كيف تعمل؟")
    )

    keyboard.row(
        types.KeyboardButton("👨‍💻 من برمجك؟"),
        types.KeyboardButton("🎲 سؤال عشوائي")
    )

    keyboard.row(
        types.KeyboardButton("ℹ️ المساعدة")
    )

    return keyboard


# =========================================================
# ADMIN KEYBOARD
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
            "➕ تعليم Shadow",
            callback_data="admin_add"
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
# ADMIN CHECK
# =========================================================

def is_admin(user_id):

    return (
        ADMIN_ID != 0
        and user_id == ADMIN_ID
    )


# =========================================================
# ADMIN LEARNING STATE
# =========================================================

learning_state = {}


# =========================================================
# /START
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    try:

        save_user(message.from_user)

        name = (
            message.from_user.first_name
            or "صديقي"
        )

        text = (
            f"👤 <b>مرحبًا {name}</b>\n\n"
            f"أنا <b>{BOT_NAME}</b>، "
            f"الظل البرمجي الخاص بـ <b>{OWNER_NAME}</b>.\n\n"
            "🤖 لا أستخدم الذكاء الاصطناعي.\n"
            "🧠 لدي قاعدة معرفة خاصة بي.\n"
            "😈 وما زلت في بداية تطوري.\n\n"
            "<b>اسألني ما تريد...</b>\n"
            "وحاول اكتشاف حدودي."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_keyboard()
        )

    except Exception as e:

        logger.exception(
            "Start error: %s",
            e
        )


# =========================================================
# /HELP
# =========================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    save_user(message.from_user)

    text = (
        "🧠 <b>Shadow Help</b>\n\n"
        "اكتب أي سؤال يخطر في بالك.\n\n"
        "مثل:\n"
        "👤 من أنت؟\n"
        "⚡ ماذا تستطيع؟\n"
        "🤖 هل أنت ذكاء اصطناعي؟\n"
        "🧠 كيف تعمل؟\n"
        "👨‍💻 من برمجك؟\n"
        "😈 هل لديك أسرار؟\n\n"
        "🎲 ويمكنك طلب سؤال عشوائي."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# /ADMIN
# =========================================================

@bot.message_handler(commands=["admin"])
def admin_command(message):

    save_user(message.from_user)

    if not is_admin(message.from_user.id):

        bot.reply_to(
            message,
            "⛔ هذا الأمر مخصص لمالك Shadow فقط."
        )

        return

    bot.send_message(
        message.chat.id,
        "👑 <b>Shadow Control Center</b>\n\n"
        f"مرحبًا يا {OWNER_NAME}.\n"
        "هذه لوحة التحكم الخاصة بك.",
        reply_markup=admin_keyboard()
    )


# =========================================================
# /STATS
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
        f"🧠 المعرفة: <b>{stats['knowledge']}</b>\n"
        f"❓ الأسئلة المجهولة: <b>{stats['unknown']}</b>"
    )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# RANDOM QUESTION
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text
        and message.text.strip()
        in [
            "🎲 سؤال عشوائي",
            "سؤال عشوائي"
        ]
)
def random_question(message):

    save_user(message.from_user)

    questions = [
        "من أنت؟",
        "ماذا تستطيع أن تفعل؟",
        "هل أنت ذكاء اصطناعي؟",
        "كيف تعمل؟",
        "من برمجك؟",
        "هل لديك أسرار؟",
        "هل تستطيع التفكير؟",
        "هل تتذكرني؟",
        "هل تستطيع رؤيتي؟",
        "هل أنت ذكي؟",
        "هل تخاف؟",
        "هل تنام؟",
        "هل أنت إنسان؟",
        "هل تستطيع فعل كل شيء؟"
    ]

    question = random.choice(
        questions
    )

    bot.send_message(
        message.chat.id,
        f"🎲 <b>جرّب أن تسألني:</b>\n\n{question}"
    )


# =========================================================
# ADMIN CALLBACKS
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

    # -----------------------------------------------------
    # الإحصائيات
    # -----------------------------------------------------

    if action == "admin_stats":

        stats = get_statistics()

        text = (
            "📊 <b>إحصائيات Shadow</b>\n\n"
            f"👥 المستخدمون: {stats['users']}\n"
            f"💬 الرسائل: {stats['messages']}\n"
            f"🧠 المعرفة: {stats['knowledge']}\n"
            f"❓ المجهول: {stats['unknown']}"
        )

        bot.answer_callback_query(
            call.id
        )

        bot.send_message(
            call.message.chat.id,
            text
        )

    # -----------------------------------------------------
    # الأسئلة المجهولة
    # -----------------------------------------------------

    elif action == "admin_unknown":

        unknown = get_unknown_questions(
            15
        )

        if not unknown:

            text = (
                "✅ لا توجد أسئلة مجهولة حاليًا."
            )

        else:

            lines = [
                "❓ <b>الأسئلة التي لم يعرفها Shadow:</b>"
            ]

            for index, item in enumerate(
                unknown,
                start=1
            ):

                lines.append(
                    f"\n<b>{index}.</b> "
                    f"{item['question']}\n"
                    f"🔁 تكرر: {item['count']} مرة"
                )

            text = "\n".join(
                lines
            )

        bot.answer_callback_query(
            call.id
        )

        bot.send_message(
            call.message.chat.id,
            text
        )

    # -----------------------------------------------------
    # إضافة معرفة
    # -----------------------------------------------------

    elif action == "admin_add":

        learning_state[
            call.from_user.id
        ] = {
            "step": "question"
        }

        bot.answer_callback_query(
            call.id
        )

        bot.send_message(
            call.message.chat.id,
            "➕ <b>تعليم Shadow</b>\n\n"
            "🧠 أرسل الآن السؤال الذي تريد تعليمي إياه.\n\n"
            "مثال:\n"
            "<code>ما هو Shadow؟</code>\n\n"
            "❌ للإلغاء اكتب:\n"
            "<code>/cancel</code>"
        )

    # -----------------------------------------------------
    # معلومات Shadow
    # -----------------------------------------------------

    elif action == "admin_info":

        bot.answer_callback_query(
            call.id
        )

        bot.send_message(
            call.message.chat.id,
            "👤 <b>Shadow v2.1</b>\n\n"
            "🧠 محرك مطابقة محلي\n"
            "💾 SQLite Memory\n"
            "🎭 Personality Engine\n"
            "➕ تعليم خاص بالمدير\n"
            "❓ تسجيل الأسئلة المجهولة\n"
            "😈 نظام ردود تصعيدية\n"
            "🤖 بدون AI API\n"
            "🌐 بدون بحث خارجي"
        )


# =========================================================
# CANCEL LEARNING
# =========================================================

@bot.message_handler(commands=["cancel"])
def cancel_learning(message):

    if not is_admin(
        message.from_user.id
    ):

        bot.reply_to(
            message,
            "⛔ هذا الأمر مخصص للمدير."
        )

        return

    learning_state.pop(
        message.from_user.id,
        None
    )

    bot.send_message(
        message.chat.id,
        "❌ تم إلغاء عملية التعليم."
    )


# =========================================================
# ADMIN LEARNING
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.from_user
        and is_admin(message.from_user.id)
        and message.from_user.id in learning_state
)
def admin_learning(message):

    state = learning_state[
        message.from_user.id
    ]

    text = message.text.strip()

    if not text:
        return

    # -----------------------------------------------------
    # السؤال
    # -----------------------------------------------------

    if state["step"] == "question":

        state["question"] = text
        state["step"] = "answer"

        bot.send_message(
            message.chat.id,
            "✅ تم حفظ السؤال مؤقتًا.\n\n"
            "✍️ الآن أرسل <b>الإجابة</b> التي تريد أن يتعلمها Shadow."
        )

        return

    # -----------------------------------------------------
    # الإجابة
    # -----------------------------------------------------

    if state["step"] == "answer":

        question = state["question"]
        answer = text

        try:

            add_knowledge(
                question=question,
                answer=answer,
                category="learned",
                keywords=question
            )

            learning_state.pop(
                message.from_user.id,
                None
            )

            bot.send_message(
                message.chat.id,
                "🧠 <b>تم تعليم Shadow بنجاح!</b>\n\n"
                f"❓ السؤال:\n{question}\n\n"
                f"💬 الإجابة:\n{answer}\n\n"
                "🔥 أصبح بإمكان Shadow استخدام هذه المعلومة مستقبلًا."
            )

        except Exception as e:

            logger.exception(
                "Learning error: %s",
                e
            )

            bot.send_message(
                message.chat.id,
                get_error_response()
            )


# =========================================================
# MAIN TEXT HANDLER
# =========================================================

@bot.message_handler(
    content_types=["text"]
)
def handle_message(message):

    try:

        save_user(
            message.from_user
        )

        user_text = message.text.strip()

        if not user_text:
            return

        # -------------------------------------------------
        # البحث
        # -------------------------------------------------

        answer = search_answer(
            user_text
        )

        if answer:

            # سؤال معروف = نخفض عداد الأسئلة المجهولة
            unknown_counter[
                message.from_user.id
            ] = 0

            bot.send_message(
                message.chat.id,
                answer
            )

            return

        # -------------------------------------------------
        # سؤال غير معروف
        # -------------------------------------------------

        record_unknown_question(
            user_id=message.from_user.id,
            question=user_text
        )

        level = get_unknown_count(
            message.from_user.id
        )

        bot.send_message(
            message.chat.id,
            get_unknown_level_response(level)
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
# NON TEXT
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

    save_user(
        message.from_user
    )

    bot.send_message(
        message.chat.id,
        "👤 حاليًا أنا أتحدث بالنصوص فقط.\n\n"
        "لكن لا تقلق... قدراتي ستكبر قريبًا 😈"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    logger.info("=" * 60)
    logger.info("Shadow Bot v2.1 starting...")
    logger.info("Bot: %s", BOT_NAME)
    logger.info("Owner: %s", OWNER_NAME)
    logger.info("AI: disabled")
    logger.info("External search: disabled")
    logger.info("Database: enabled")
    logger.info("Admin learning: enabled")
    logger.info("=" * 60)

    try:
        bot.remove_webhook()
    except Exception:
        pass

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )