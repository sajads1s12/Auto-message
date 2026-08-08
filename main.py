import asyncio
import sys

# حل مشكلة Event Loop في Python 3.14
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import random
import time
import json
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

# ----------------- بيانات الحساب والـ API -----------------
API_ID = 35070041
API_HASH = "11c5b303993bb4a8a7ce5292e0562a97"
BOT_TOKEN = "8876968791:AAHlYglsEXunkokDYuwtIZ6jw9qHYLPL1aA"

DATA_FILE = "data.json"

# دالة لحفظ البيانات بملف خارجي
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        clean_data = {}
        for uid, val in user_data.items():
            clean_data[str(uid)] = {
                "interval": val.get("interval", 3),
                "msgs": val.get("msgs", []),
                "targets": val.get("targets", []),
                "session": val.get("session", None)
            }
        json.dump(clean_data, f, ensure_ascii=False, indent=4)

# دالة لاسترجاع البيانات عند تشغيل البوت
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                res = {}
                for uid, val in loaded.items():
                    res[int(uid)] = val
                    res[int(uid)]["last_sent"] = {}
                return res
        except Exception as e:
            print(f"خطأ بقراءة الملف: {e}")
    return {}

user_data = load_data()
running_tasks = {}

bot = Client("MakerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ----------------- لوحة التحكم بالأزرار -----------------
def main_keyboard(user_id):
    status = "🟢 شغال" if user_id in running_tasks else "🔴 متوقف"
    data = user_data.get(user_id, {})
    
    account_status = "✅ مسجل" if "session" in data and data["session"] else "❌ غير مسجل"
    msgs_count = len(data.get("msgs", []))
    targets_count = len(data.get("targets", []))
    time_val = data.get("interval", 3)

    text = (
        f"🤖 **لوحة تحكم بوت النشر التلقائي (مع الحفظ التلقائي)**\n\n"
        f"• حالة النشر: {status}\n"
        f"• الحساب: {account_status}\n"
        f"• عدد الرسائل: {msgs_count}\n"
        f"• عدد المجموعات: {targets_count}\n"
        f"• الوقت بين النشر: كل {time_val} دقائق\n\n"
        f"💾 *جميع البيانات محفوظة تلقائياً عند إعادة التشغيل.*"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 إضافة / ربط حساب", callback_data="add_account")],
        [InlineKeyboardButton(f"📝 إضافة رسالة ({msgs_count})", callback_data="set_msg"), 
         InlineKeyboardButton(f"🎯 إضافة مجموعة ({targets_count})", callback_data="set_target")],
        [InlineKeyboardButton("🗑️ مسح الرسائل", callback_data="clear_msgs"),
         InlineKeyboardButton("🗑️ مسح المجموعات", callback_data="clear_targets")],
        [InlineKeyboardButton("⏱️ تغيير الوقت", callback_data="set_time")],
        [InlineKeyboardButton("▶️ تشغيل النشر", callback_data="start_post"),
         InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_post")]
    ])
    return text, buttons

# ----------------- معالجة الأوامر والأزرار -----------------
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    text, markup = main_keyboard(message.from_user.id)
    await message.reply(text, reply_markup=markup)

@bot.on_callback_query()
async def handle_buttons(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if user_id not in user_data:
        user_data[user_id] = {"interval": 3, "msgs": [], "targets": [], "last_sent": {}}

    if data == "add_account":
        user_data[user_id]["step"] = "WAITING_PHONE"
        await callback.message.edit_text("أرسل الآن رقم هاتفك مع رمز الدولة\nمثال: `+9647800000000`")

    elif data == "set_msg":
        user_data[user_id]["step"] = "WAITING_MSG"
        await callback.message.edit_text("أرسل الآن نص الرسالة التي تريد إضافتها للقائمة:")

    elif data == "set_target":
        user_data[user_id]["step"] = "WAITING_TARGET"
        await callback.message.edit_text("أرسل معرف المجموعة (مثال: `@w_2_F`) أو رابطها:")

    elif data == "clear_msgs":
        user_data[user_id]["msgs"] = []
        save_data()
        await callback.answer("🗑️ تم مسح جميع الرسائل!")
        text, markup = main_keyboard(user_id)
        await callback.message.edit_text(text, reply_markup=markup)

    elif data == "clear_targets":
        user_data[user_id]["targets"] = []
        user_data[user_id]["last_sent"] = {}
        save_data()
        await callback.answer("🗑️ تم مسح جميع المجموعات!")
        text, markup = main_keyboard(user_id)
        await callback.message.edit_text(text, reply_markup=markup)

    elif data == "set_time":
        time_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 دقيقة", callback_data="time_1"),
             InlineKeyboardButton("3 دقائق", callback_data="time_3"),
             InlineKeyboardButton("5 دقائق", callback_data="time_5")],
            [InlineKeyboardButton("10 دقائق", callback_data="time_10"),
             InlineKeyboardButton("15 دقيقة", callback_data="time_15")],
            [InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]
        ])
        await callback.message.edit_text("اختر المدة الزمنية بين كل نشر:", reply_markup=time_buttons)

    elif data.startswith("time_"):
        minutes = int(data.split("_")[1])
        user_data[user_id]["interval"] = minutes
        save_data()
        await callback.answer(f"تم تحديد الوقت: كل {minutes} دقائق")
        text, markup = main_keyboard(user_id)
        await callback.message.edit_text(text, reply_markup=markup)

    elif data == "main_menu":
        text, markup = main_keyboard(user_id)
        await callback.message.edit_text(text, reply_markup=markup)

    elif data == "start_post":
        info = user_data.get(user_id, {})
        if not info.get("session") or not info.get("msgs") or not info.get("targets"):
            await callback.answer("⚠️ يرجى ربط الحساب، إضافة رسالة، ومجموعة أولاً!", show_alert=True)
            return
        
        if user_id in running_tasks:
            running_tasks[user_id].cancel()
            del running_tasks[user_id]
            await asyncio.sleep(1)

        task = asyncio.create_task(run_auto_posting(
            user_id, 
            info["session"], 
            info["targets"], 
            info["msgs"]
        ))
        running_tasks[user_id] = task
        await callback.answer("🚀 تم بدء النشر التلقائي!")
        text, markup = main_keyboard(user_id)
        await callback.message.edit_text(text, reply_markup=markup)

    elif data == "stop_post":
        if user_id in running_tasks:
            running_tasks[user_id].cancel()
            del running_tasks[user_id]
            await callback.answer("🛑 تم إيقاف النشر التلقائي!")
        else:
            await callback.answer("لا يوجد نشر شغال حالياً.", show_alert=True)
        text, markup = main_keyboard(user_id)
        await callback.message.edit_text(text, reply_markup=markup)

# ----------------- استقبال النصوص والخطوات -----------------
@bot.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    if user_id not in user_data:
        user_data[user_id] = {"interval": 3, "msgs": [], "targets": [], "last_sent": {}}

    step = user_data[user_id].get("step")

    if step == "WAITING_PHONE":
        try:
            temp_client = Client(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH)
            await temp_client.connect()
            code_hash = await temp_client.send_code(text)
            
            user_data[user_id]["temp_client"] = temp_client
            user_data[user_id]["phone"] = text
            user_data[user_id]["code_hash"] = code_hash.phone_code_hash
            user_data[user_id]["step"] = "WAITING_CODE"
            
            await message.reply("تم إرسال كود التحقق من تليجرام.\n\n⚠️ **تنبيه:** أرسل الكود بوضع مسافات بين الأرقام (مثال: `1 2 3 4 5`).")
        except Exception as e:
            await message.reply(f"حدث خطأ: {e}\nتأكد من الرقم وحاول مجدداً.")

    elif step == "WAITING_CODE":
        temp_client = user_data[user_id]["temp_client"]
        clean_code = text.replace(" ", "").replace("-", "").strip()
        try:
            await temp_client.sign_in(user_data[user_id]["phone"], user_data[user_id]["code_hash"], clean_code)
            session_string = await temp_client.export_session_string()
            await temp_client.disconnect()

            user_data[user_id]["session"] = session_string
            user_data[user_id]["step"] = None
            save_data()
            
            txt, markup = main_keyboard(user_id)
            await message.reply("✅ تم تسجيل دخول الحساب بنجاح وتأكيده بالمحفظة!", reply_markup=markup)
        except Exception as e:
            await message.reply(f"حدث خطأ في التسجيل: {e}\nأعد المحاولة وأرسل الكود بمسافات بين الأرقام.")

    elif step == "WAITING_MSG":
        if "msgs" not in user_data[user_id]:
            user_data[user_id]["msgs"] = []
        user_data[user_id]["msgs"].append(text)
        user_data[user_id]["step"] = None
        save_data()
        
        txt, markup = main_keyboard(user_id)
        await message.reply(f"✅ تم إضافة الرسالة وبحفظها! (المجموع: {len(user_data[user_id]['msgs'])})", reply_markup=markup)

    elif step == "WAITING_TARGET":
        if "targets" not in user_data[user_id]:
            user_data[user_id]["targets"] = []
        user_data[user_id]["targets"].append(text)
        user_data[user_id]["step"] = None
        save_data()
        
        txt, markup = main_keyboard(user_id)
        await message.reply(f"✅ تم إضافة المجموعة وبحفظها! (المجموع: {len(user_data[user_id]['targets'])})", reply_markup=markup)

# ----------------- دالة محرك النشر التلقائي الذكي -----------------
async def run_auto_posting(user_id, session_string, targets_list, msgs_list):
    user_app = Client(f"poster_{user_id}", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
    try:
        await user_app.start()
        
        while True:
            current_interval = user_data.get(user_id, {}).get("interval", 3) * 60
            if "last_sent" not in user_data[user_id]:
                user_data[user_id]["last_sent"] = {}

            for target in targets_list:
                chat_identifier = target.strip()
                if "t.me/" in chat_identifier and not "t.me/+" in chat_identifier:
                    chat_identifier = "@" + chat_identifier.split("t.me/")[1].replace("/", "")

                now = time.time()
                last_time = user_data[user_id]["last_sent"].get(chat_identifier, 0)
                
                if now - last_time >= current_interval:
                    selected_msg = random.choice(msgs_list)
                    
                    try:
                        await user_app.send_message(chat_id=chat_identifier, text=selected_msg)
                        user_data[user_id]["last_sent"][chat_identifier] = time.time()
                        print(f"[{time.strftime('%H:%M:%S')}] تم الإرسال إلى: {chat_identifier}")
                    except Exception as send_err:
                        print(f"فشل الإرسال إلى {chat_identifier}: {send_err}")
                    
                    await asyncio.sleep(5)

            await asyncio.sleep(10)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"خطأ في عملية النشر للمستخدم {user_id}: {e}")
    finally:
        await user_app.stop()

# تشغيل البوت
bot.run()
