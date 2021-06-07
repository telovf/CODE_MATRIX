import os
import json
import time
import asyncio

from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)


API_TEXT = """❄️ مرحـبـاً {},

في البوت الرسـمي لسـورس 𝙕𝞝𝘿𝙏𝙃𝙊𝙉 ↬

 لاستخراج كود تيرمكس .

قم الان بإرسال كود API_ID الخـاص بك
"""
HASH_TEXT = "☃️ قم الان بإرسال كود API_HASH.\nاو اضغط /cancel للالغاء. ↬"
PHONE_NUMBER_TEXT = (
    "❄️__ الان قم بإرسال رقم هاتف حساب تيليجرام الخاص بك للمتابعه"
    " ادخل مفتاح دولتك.__\n**مثال:** `+13124522345`\n\n"
    "اضغط /للالغاء Cancel."
)



@Client.on_message(filters.private & filters.command("start"))
async def generate_str(c, m):
    get_api_id = await c.ask(
        chat_id=m.chat.id,
        text=API_TEXT.format(m.from_user.mention(style='md')),
        filters=filters.text
    )
    api_id = get_api_id.text
    if await is_cancel(m, api_id):
        return

    await get_api_id.delete()
    await get_api_id.request.delete()
    try:
        check_api = int(api_id)
    except Exception:
        await m.reply("**--🛑 API ID خطأ 🛑--**\nاضغط /start للعوده من جديد.")
        return

    get_api_hash = await c.ask(
        chat_id=m.chat.id, 
        text=HASH_TEXT,
        filters=filters.text
    )
    api_hash = get_api_hash.text
    if await is_cancel(m, api_hash):
        return

    await get_api_hash.delete()
    await get_api_hash.request.delete()

    if not len(api_hash) >= 30:
        await m.reply("--**🛑 API HASH خطأ 🛑**--\nاضغط /start للعوده من جديد.")
        return

    try:
        client = Client(":memory:", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await c.send_message(m.chat.id ,f"**🛑 ERROR: 🛑** `{str(e)}`\nPress /start to create again.")
        return

    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    while True:
        get_phone_number = await c.ask(
            chat_id=m.chat.id,
            text=PHONE_NUMBER_TEXT
        )
        phone_number = get_phone_number.text
        if await is_cancel(m, phone_number):
            return
        await get_phone_number.delete()
        await get_phone_number.request.delete()

        confirm = await c.ask(
            chat_id=m.chat.id,
            text=f'🤔 اذا كان رقمك `{phone_number}` صحيح? (y/n): \n\nارسل: `y` (للتاكيد)\nاو ارسل: `n` (للالغاء)'
        )
        if await is_cancel(m, confirm.text):
            return
        if "y" in confirm.text.lower():
            await confirm.delete()
            await confirm.request.delete()
            break
    try:
        code = await client.send_code(phone_number)
        await asyncio.sleep(1)
    except FloodWait as e:
        await m.reply(f"__Sorry to say you that you have floodwait of {e.x} Seconds 😞__")
        return
    except ApiIdInvalid:
        await m.reply("🕵‍♂ The API ID or API HASH is Invalid.\n\nPress /start to create again.")
        return
    except PhoneNumberInvalid:
        await m.reply("☎ رقمك غير صحيح عذراً.`\n\nPress /start to create again.")
        return

    try:
        sent_type = {"app": "Telegram App 💌",
            "sms": "SMS 💬",
            "call": "Phone call 📱",
            "flash_call": "phone flash call 📲"
        }[code.type]
        otp = await c.ask(
            chat_id=m.chat.id,
            text=(f"لقد قمنا بارسال كود دخول البوت لحسابك `{phone_number}` للتحقق {sent_type}\n\n"
                  "قم بادخال الكود بالشكل الاتي `1 2 3 4 5` __(خلي مسافه بين كل رقم والآخر)__\n\n"
                  "اذا لم يصلك كود التحقق ارسل /start .\n"
                  "اضغط /cancel للالغاء."), timeout=300)
    except TimeoutError:
        await m.reply("**⏰ TimeOut Error:** You reached Time limit of 5 min.\nPress /start to create again.")
        return
    if await is_cancel(m, otp.text):
        return
    otp_code = otp.text
    await otp.delete()
    await otp.request.delete()
    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await m.reply("**📵 كود خاطئ**\n\nPress /start to create again.")
        return 
    except PhoneCodeExpired:
        await m.reply("**⌚ كود منتهي الصلاحيه **\n\nPress /start to create again.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await c.ask(
                chat_id=m.chat.id, 
                text="`🔐 هذا الحساب يحتوي على تحقق بخطوتين.\nقم بارسال كلمة المرور.`\nاضغط /cancel للالغاء.",
                timeout=300
            )
        except TimeoutError:
            await m.reply("**⏰ لقد انتهى الوقت:** You reached Time limit of 5 min.\nPress /start to create again.")
            return
        if await is_cancel(m, two_step_code.text):
            return
        new_code = two_step_code.text
        await two_step_code.delete()
        await two_step_code.request.delete()
        try:
            await client.check_password(new_code)
        except Exception as e:
            await m.reply(f"**⚠️ ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await c.send_message(m.chat.id ,f"**⚠️ ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"**كود تيرمكس الخاص بك 👇**\n\n`{session_string}`\n\nشكرا لك لاستخدام {(await c.get_me()).mention(style='md')}")
        text = "✅ تم إنشاء جلسة تيرمكس الخاصة بك بنجاح وإرسال الكود الى حافظة حسابك.\nتحقق من رسائلك المحفوظة أو انقر ع الزر أدناه."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="String Session ↗️", url=f"tg://openmessage?user_id={m.chat.id}")]]
        )
        await c.send_message(m.chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await c.send_message(m.chat.id ,f"**⚠️ ERROR:** `{str(e)}`")
        return
    

@Client.on_message(filters.private & filters.command("help"))
async def help(c, m):
    await help_cb(c, m, cb=False)


@Client.on_callback_query(filters.regex('^help$'))
async def help_cb(c, m, cb=True):
    help_text = """**Hey You need Help??👨‍✈️**


>>>> Press the start button

>>>> Send Your API_ID when bot ask.

>>>> Then send your API_HASH when bot ask.

>>>> Send your mobile number.

>>>> Send the OTP reciveved to your numer in the format `1 2 3 4 5` (Give space b/w each digit)

>>>> (If you have two step verification send to bot if bot ask.)


**NOTE:**

If you made any mistake anywhere press /cancel and then press /start
"""

    buttons = [[
        InlineKeyboardButton('📕 About', callback_data='about'),
        InlineKeyboardButton('❌ Close', callback_data='close')
    ]]
    if cb:
        await m.answer()
        await m.message.edit(text=help_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    else:
        await m.reply_text(text=help_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True, quote=True)


@Client.on_message(filters.private & filters.command("about"))
async def about(c, m):
    await about_cb(c, m, cb=False)


@Client.on_callback_query(filters.regex('^about$'))
async def about_cb(c, m, cb=True):
    me = await c.get_me()
    about_text = f"""**معلوماتي:**

__🤖 بوت تيرمكس:__ {me.mention(style='md')}
    
__📝 لغة البوت:__ [Python3](https://www.python.org/)

__👨‍💻 المطور:__ [𝐀𝐧𝐨𝐧𝐲𝐦𝐨𝐮𝐬](https://t.me/ZlZZl77)

__📢 قناة السورس:__ [𝙕𝞝𝘿𝙏𝙃𝙊𝙉 ↬](https://t.me/Zedthon)

__👥 كروب السورس:__ [ترحيب™ 𝙕𝞝𝘿𝙏𝙃𝙊𝙉 ↬](https://t.me/Zedthon_1)

__🚀 شروحات السورس:__ [شروحات 𝙕𝞝𝘿𝙏𝙃𝙊𝙉 ↬](https://t.me/ZED_Thon)
"""

    buttons = [[
        InlineKeyboardButton('💡 Help', callback_data='help'),
        InlineKeyboardButton('❌ Close', callback_data='close')
    ]]
    if cb:
        await m.answer()
        await m.message.edit(about_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    else:
        await m.reply_text(about_text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True, quote=True)


@Client.on_callback_query(filters.regex('^close$'))
async def close(c, m):
    await m.message.delete()
    await m.message.reply_to_message.delete()


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("⛔ Process Cancelled.")
        return True
    return False


