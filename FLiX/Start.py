# Don't Remove Credit Tg - @FLiX_LY
# Ask Doubt on telegram @FLiX_LY


import pytz, random, aiohttp, logging, asyncio, secrets, urllib.parse
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ChatType

from database.db import database
from FLiX.strings import HELP_TXT
from config import Start_IMG, FSUB_ID, FSUB_INV_LINK
from FLiX.Save import Check_Plan, is_member, format_duration

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")


# Start
@Client.on_message(filters.command(["start"]), group=0)
async def send_start(client: Client, message: Message):
    user_id = message.from_user.id
    user_info = await database.users.find_one({'user_id': user_id})
    args = message.text.strip().split(maxsplit=1)

    # 👤 Register user if not exists
    await database.users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "first_name": message.from_user.first_name
            },
            "$setOnInsert": {
                "registered_at": datetime.now(IST),
                "plan": {
                    "type": "free",
                    "preset": None,
                    "started_at": None,
                    "expiration_at": None
                },
                "last_download_time": None,
                "active_batch": False,
                "stop_status": False,
                "settings": {
                    "thumbnail": None,
                    "word_replacements": None
                }
            }
        },
        upsert=True
    )

    # 🔒 Force subscription check
    if not await is_member(client, user_id):
        return await client.send_message(
            chat_id=message.chat.id,
            text=f"👋 ʜɪ {message.from_user.mention}, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ❤️", url=FSUB_INV_LINK)
            ]]),
            reply_to_message_id=message.id
        )

    # ⛔ Ban check
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            if ban_time else "`N/A`"
        )
        return await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n"
                f"😔 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                f"📅 𝗕𝗮𝗻 𝗧𝗶𝗺𝗲: {ban_time_ist}\n"
                f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{banned_info.get('reason', 'No reason provided.')}`\n\n"
                f"⚠️ 𝗜𝗳 𝘆𝗼𝘂 𝗯𝗲𝗹𝗶𝗲𝘃𝗲 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲, 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝘀𝘂𝗽𝗽𝗼𝗿𝘁."
            ),
            reply_to_message_id=message.id,
        )

    if len(args) > 1:
        param = args[1].strip()
        
        if param.lower() == "buy":
            return await buy_plans(client, message)

        if param.lower().startswith("verify_"):
            parts = param.split("_")
            if len(parts) == 2 and parts[1].isdigit():
                expected_user_id = int(parts[1])
                if message.from_user.id != expected_user_id:
                    return  # 🔇 Silently ignore if not same user
            return await generate_token(client, message)

        if param.startswith("token_"):
            config = await database.config.find_one({"key": "Token_Info"}) or {}
            if not config.get("token_mode", False):
                return await client.send_message(
                    message.chat.id,
                    "🚫 **Token-based access is currently disabled.**",
                    reply_to_message_id=message.id
                )

            plan = user_info.get("plan", {}) if user_info else {}
            preset = plan.get("preset", "")

            if plan.get("type") == "premium" and not str(preset).startswith("token_"):
                return await client.send_message(
                    message.chat.id,
                    "💎 **You already have an active Premium plan.**\nYou don't need to activate a token.",
                    reply_to_message_id=message.id
                )


            token = param[6:]
            now = datetime.utcnow()
            token_data = await database.tokens.find_one({"token": token})

            if not token_data:
                return await client.send_message(
                    message.chat.id,
                    "❌ *Invalid or unknown token!*\nUse /token to generate a valid one.",
                    reply_to_message_id=message.id
                )

            if token_data["expires_at"] < now:
                await database.tokens.update_one({"token": token}, {"$set": {"status": "expired"}})
                return await client.send_message(
                    message.chat.id,
                    "🕓 **Token Expired!**\nPlease generate a new one using /token.",
                    reply_to_message_id=message.id
                )

            if token_data["status"] == "used":
                used_by = token_data.get("used_by")
                if used_by == user_id:
                    return await client.send_message(
                        message.chat.id,
                        "🚫 **Token Already Claimed!**\n\n"
                        "You've already used this token yourself.\n"
                        "🎟️ Tokens are **single-use only**, like golden tickets!\n\n"
                        "✨ Need access again? Just grab a fresh one using **/token**.",
                        reply_to_message_id=message.id
                    )
                else:
                    used_user = await client.get_users(used_by)
                    return await client.send_message(
                        message.chat.id,
                        f"🚫 **Token Already Claimed!**\n\n"
                        f"This token was already used by **[{used_user.first_name}](tg://user?id={used_user.id})**.\n"
                        "🎟️ Tokens are **single-use only**, like golden tickets!\n\n"
                        "✨ Need access? Just grab a fresh one using **/token**.",
                        reply_to_message_id=message.id
                    )

            # ✅ Valid Token - Activate Premium
            duration = config.get("duration", 1)
            started_at = now
            expiration_at = now + timedelta(hours=duration)

            await database.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "plan": {
                            "type": "premium",
                            "preset": f"token_{token}",
                            "started_at": started_at,
                            "expiration_at": expiration_at,
                            "upgrade_by": user_id
                        }
                    }
                }
            )

            await database.tokens.update_one(
                {"token": token},
                {
                    "$set": {
                        "status": "used",
                        "used_by": user_id,
                        "used_at": now
                    }
                }
            )

            exp_str = expiration_at.astimezone(IST).strftime('%d %B %Y - %I:%M %p')

            if config.get("auth_group_mode", False) and config.get("group_id"):
                try:
                    await client.send_message(
                        int(config["group_id"]),
                        f"🔑 **Token Verified!**\n"
                        f"👤 [{message.from_user.first_name}](tg://user?id={user_id}) just unlocked **Premium Access** 💎\n"
                        f"🕒 `{duration}`h • ⏳ Expires: `{exp_str} IST`\n"
                        f"🌟 Access granted — let the premium journey begin!"
                    )
                except Exception as e:
                    logger.info(f"[Auth Group Notify Error]: {e}")

            return await client.send_message(
                message.chat.id,
                (
                    "🎉 **Token Successfully Verified!**\n\n"
                    f"💎 You've been granted **Premium Access** for `{duration}` hour(s)! ✨\n"
                    f"⌛️ **Expires On:** `{exp_str} IST`\n\n"
                    "Enjoy all the exclusive features — faster speeds, batch saves, and more! 🚀"
                ),
                reply_to_message_id=message.id
            )


    # 🚀 Loading animation
    steps = [
        "⏳ **Initializing System...**",
        "♻️ **Connecting To Server...**",
        "🔐 **Performing Security Check...**",
        "⚡️ **Granting Access...**",
        "🚀 **All set Welcome Aboard!**"
    ]
    for step in steps:
        msg = await client.send_message(chat_id=message.chat.id, text=step, reply_to_message_id=message.id)
        await asyncio.sleep(2)
        await client.delete_messages(chat_id=message.chat.id, message_ids=msg.id)

    # Welcome photo
    welcome_photo = await client.send_photo(
        chat_id=message.chat.id,
        photo=Start_IMG,
        caption="✨ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐅𝐋𝐈𝐗 𝐁𝐨𝐭! ✨\n🚀 𝐄𝐱𝐩𝐥𝐨𝐫𝐞 𝐭𝐡𝐞 𝐰𝐨𝐫𝐥𝐝 𝐨𝐟 𝐫𝐞𝐬𝐭𝐫𝐢𝐜𝐭𝐞𝐝 𝐜𝐨𝐧𝐭𝐞𝐧𝐭 𝐰𝐢𝐭𝐡 𝐞𝐚𝐬𝐞!",
        reply_to_message_id=message.id
    )
    await asyncio.sleep(3)
    await welcome_photo.delete()

    # Feature menu
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ ꜱᴇᴛᴛɪɴɢꜱ", callback_data=f"open_settings_{user_id}")],
        [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="https://t.me/FLiX_LY")],
        [
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/Flix_botz'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/Flix_botz')
        ]
    ])

    await client.send_message(
        chat_id=message.chat.id,
        text=(
            f"👋 𝗛𝗲𝘆𝗮 **{message.from_user.mention(style='md')}**\n"
            f"🚀𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗕𝗮𝗰𝗸 𝘁𝗼 𝘁𝗵𝗲 𝗣𝗼𝘄𝗲𝗿𝗳𝘂𝗹\n𝗥𝗲𝘀𝘁𝗿𝗶𝗰𝘁𝗲𝗱 𝗖𝗼𝗻𝘁𝗲𝗻𝘁 𝗕𝗼𝘁!\n\n"
            f"╭🔥**𝙁𝙀𝘼𝙏𝙐𝙍𝙀𝘿 𝘾𝙊𝙈𝙈𝘼𝙉𝘿𝙎**🔥╮\n\n"
            f"**✅ /login**\n"
            f"╰ 💠 𝐋𝐨𝐠𝐢𝐧 𝐭𝐨 𝐲𝐨𝐮𝐫 𝐚𝐜𝐜𝐨𝐮𝐧𝐭.\n"
            f"**🚪 /logout**\n"
            f"╰ 💠 𝐋𝐨𝐠𝐨𝐮𝐭 𝐟𝐫𝐨𝐦 𝐲𝐨𝐮𝐫 𝐚𝐜𝐜𝐨𝐮𝐧𝐭.\n"
            f"**📖 /help**\n"
            f"╰ 💠 𝐔𝐬𝐞 𝐨𝐟 𝐒𝐢𝐧𝐠𝐥𝐞 𝐨𝐫 𝐁𝐚𝐭𝐜𝐡 𝐌𝐨𝐝𝐞\n"
            f"**🔍 /tutorial**\n"
            f"╰ 💠 𝐒𝐭𝐞𝐩 𝐁𝐲 𝐒𝐭𝐞𝐩 𝐆𝐮𝐢𝐝𝐞\n"
            f"**🗓️ /myplan**\n"
            f"╰ 💠 𝐂𝐡𝐞𝐜𝐤 𝐲𝐨𝐮𝐫 𝐬𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧.\n"
            f"**🛑 /stop**\n"
            f"╰ 💠 𝐂𝐚𝐧𝐜𝐞𝐥 𝐎𝐧𝐠𝐨𝐢𝐧𝐠 𝐁𝐚𝐭𝐜𝐡.\n\n"
            f"*Your Restricted Content Assistant, ready 24/7!*"
        ),
        reply_markup=buttons,
        reply_to_message_id=message.id
    )


async def shorten_link(deep_url: str, config) -> str:
    error_report_url = "https://t.me/FLiX_LY?text=%F0%9F%94%A5%20**Yo%20Boss!**%0A%0AThe%20**Token%20link**%20didn%E2%80%99t%20make%20it.%0ALooks%20like%20something%E2%80%99s%20broken%20%E2%80%94%20alias%20might%20be%20taken%20or%20the%20API%20is%20acting%20up.%0A%0AWanna%20take%20a%20look%3F%20%F0%9F%9B%A0%EF%B8%8F"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                config.get("api_url", "❌ Not Set"),
                params={
                    "api": config.get("api_key", "❌ Not Set"),
                    "url": deep_url,
                    "format": "json"
                }
            ) as response:
                data = await response.json()
                if response.status == 200 and data.get("status") == "success":
                    return data["shortenedUrl"]
    except:
        pass

    return error_report_url


# Token
async def generate_token(client: Client, message: Message):
    user_id = message.from_user.id
    user = await database.users.find_one({"user_id": user_id})
    config = await database.config.find_one({"key": "Token_Info"}) or {}

    # 🔒 Force subscription check
    if not await is_member(client, user_id):
        return await client.send_message(
            chat_id=message.chat.id,
            text=f"👋 ʜɪ {message.from_user.mention}, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ❤️", url=FSUB_INV_LINK)]]),
            reply_to_message_id=message.id
        )

    # 🚫 Token system disabled
    if not config.get("token_mode", False):
        return await client.send_message(
            message.chat.id,
            "**🚫 Token-based access is currently disabled.**",
            reply_to_message_id=message.id
        )

    # ❌ User not registered
    if not user:
        return await client.send_message(
            message.chat.id,
            "**❌ You're not registered.\nUse /start first to continue.**",
            reply_to_message_id=message.id
        )

    # 🟡 Already premium
    plan = user.get("plan", {})
    if plan.get("type") == "premium":
        preset = plan.get("preset", "")
        exp = plan.get("expiration_at")
        exp_str = exp.astimezone(IST).strftime("%d %B %Y - %I:%M %p IST") if exp else "Unknown"

        # ✅ Token-based premium (don't show token/link again)
        if preset and preset.startswith("token_"):
            return await client.send_message(
                message.chat.id,
                text=(
                    "🌟 **You're on Premium (Token Access)**\n\n"
                    "✅ Your token-based premium plan is **active**.\n"
                    f"🗓️ **Expires:** `{exp_str}`\n\n"
                    "📬 Use /myplan anytime to check your full subscription details.\n"
                    "✨ Enjoy your premium experience!"
                ),
                reply_to_message_id=message.id
            )

        # 🔐 Other premium plans (not from token)
        return await client.send_message(
            message.chat.id,
            "✨ You're already a **Premium User**!\nUse /myplan to view your subscription.",
            reply_to_message_id=message.id
        )

    # 🔄 Generate new token
    while True:
        token = secrets.token_urlsafe(8)
        if not await database.tokens.find_one({"token": token}):
            break

    expires_at = datetime.utcnow() + timedelta(minutes=30)

    await database.tokens.insert_one({
        "token": token,
        "issued_by": user_id,
        "status": "active",
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    })

    bot_username = (await client.get_me()).username
    token_url = f"https://t.me/{bot_username}?start=token_{token}"
    short_url = await shorten_link(token_url, config)
    token_duration = config.get("token_duration", 1)

    # 🎁 Send token to user
    return await client.send_message(
        chat_id=message.chat.id,
        text=(
            "🔐 **Verify Token Generated!**\n\n"
            f"🎁 **Access Duration:** `{token_duration} hour(s)`\n"
            f"⏳ **Token Validity:** `30 minutes`\n"
            f"⚠️ **One-time use only**\n\n"
            "🔥 Click below to unlock your premium access 👇"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 𝗩𝗲𝗿𝗶𝗳𝘆 𝗧𝗼𝗸𝗲𝗻", url=short_url)],
        ]),
        disable_web_page_preview=True,
        reply_to_message_id=message.id
    )


@Client.on_message(filters.command("token"), group=0)
async def token_command(client: Client, message: Message):
    user = message.from_user
    user_id = user.id
    user_name = user.mention
    chat = message.chat
    chat_type = chat.type

    # ⏬ Load config from DB
    config = await database.config.find_one({"key": "Token_Info"}) or {}

    token_mode = config.get("token_mode", False)
    auth_group_mode = config.get("auth_group_mode", False)
    auth_group_id = config.get("group_id")
    invite_link = config.get("invite_link", "https://t.me/")

    # ❌ Token system off
    if not token_mode:
        return await client.send_message(
            chat.id,
            "🚫 **Token system is currently disabled.**",
            reply_to_message_id=message.id
        )

    # 🤖 Bot username for DM link
    bot = await client.get_me()
    bot_username = bot.username

    # 🔐 Auth Group Mode Enabled
    if auth_group_mode:
        # ❌ Used in private
        if chat_type == ChatType.PRIVATE:
            return await client.send_message(
                chat.id,
                "🚫 **Hold on! Token generation is not allowed here.**\n\n"
                "✨ To keep things secure and premium, tokens can only be generated inside our **exclusive Auth Group**.\n\n"
                "👉 Join the group below and use the `/token` command there to get started!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔐 Join Auth Group", url=invite_link)
                ]]),
                reply_to_message_id=message.id
            )

        # ❌ Used in wrong group
        if not auth_group_id or int(chat.id) != int(auth_group_id):
            return await client.send_message(
                chat.id,
                "⚠️ **Unauthorized Group!**\n\n"
                "🚫 Token generation is only allowed in our **official Auth Group**.\n"
                "Please head over there and use the `/token` command to continue.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔐 Join Auth Group", url=invite_link)
                ]]),
                reply_to_message_id=message.id
            )

        # ✅ Inside valid group → Show verify in DM button
        return await client.send_message(
            chat.id,
            f"👋 Hey {user_name}!\n\n"
            f"🎟️ **Ready to unlock Premium?**\n"
            f"✅ Your personal token is now ready to go!\n\n"
            f"🔐 Just verify yourself in **private chat** to activate it.\n"
            f"👇 Tap the button below to continue:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🚀 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲 & 𝗩𝗲𝗿𝗶𝗳𝘆 𝗧𝗼𝗸𝗲𝗻",
                    url=f"https://t.me/{bot_username}?start=verify_{user_id}"
                )
            ]]),
            reply_to_message_id=message.id
        )

    # 🔓 Auth group mode OFF → allow only private chat
    if chat_type != ChatType.PRIVATE:
        return await client.send_message(
            chat.id,
            "⚠️ **This command can only be used in private chat.**",
            reply_to_message_id=message.id
        )

    # ✅ Private + Token Mode ON + Auth Group Mode OFF
    return await generate_token(client, message)


# Help
@Client.on_message(filters.command(["help"]), group=0)
async def send_help(client: Client, message: Message):
    if not await is_member(client, message.from_user.id):
        
        await client.send_message(
            chat_id=message.chat.id,
            text=f"👋 ʜɪ {message.from_user.mention}, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ❤️", url=FSUB_INV_LINK)
            ]]),
            reply_to_message_id=message.id  
        )
        return

    user_info = await database.users.find_one({'user_id': message.from_user.id})
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            if ban_time else "`N/A`"
        )
        await message._client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n"
                f"😔 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                f"📅 𝗕𝗮𝗻 𝗧𝗶𝗺𝗲: {ban_time_ist}\n"
                f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{banned_info.get('reason', 'No reason provided.')}`\n\n"
                f"⚠️ 𝗜𝗳 𝘆𝗼𝘂 𝗯𝗲𝗹𝗶𝗲𝘃𝗲 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲, 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝘀𝘂𝗽𝗽𝗼𝗿𝘁."
            ),
            reply_to_message_id=message.id,
        )
        return

    await client.send_message(chat_id=message.chat.id, text=f"{HELP_TXT}", reply_to_message_id=message.id)


# Id/Info
@Client.on_message(filters.command(["info", "id"]), group=0)
async def user_info(client: Client, message: Message):

    # Check if the user is a member of the required channel/group
    if not await is_member(client, message.from_user.id):
        
        await client.send_message(
            chat_id=message.chat.id,
            text=f"👋 ʜɪ {message.from_user.mention}, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ❤️", url=FSUB_INV_LINK)
            ]]),
            reply_to_message_id=message.id  
        )
        return

    user_info = await database.users.find_one({'user_id': message.from_user.id})
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            if ban_time else "`N/A`"
        )
        await message._client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n"
                f"😔 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                f"📅 𝗕𝗮𝗻 𝗧𝗶𝗺𝗲: {ban_time_ist}\n"
                f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{banned_info.get('reason', 'No reason provided.')}`\n\n"
                f"⚠️ 𝗜𝗳 𝘆𝗼𝘂 𝗯𝗲𝗹𝗶𝗲𝘃𝗲 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲, 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝘀𝘂𝗽𝗽𝗼𝗿𝘁."
            ),
            reply_to_message_id=message.id,
        )
        return

    await message.reply_text(
        f"**ID Lookup ⚡️**\n\n"
        f"✮ 𝗨𝘀𝗲𝗿 𝗜𝗗 ➔ `{message.from_user.id}`\n"
        f"✮ 𝗖𝗵𝗮𝘁 𝗜𝗗 ➔ `{message.chat.id}`\n"
        f"✮ 𝗠𝗲𝗻𝘁𝗶𝗼𝗻 ➔ {message.from_user.mention}\n",
        quote=True
    )


# Tutorial
@Client.on_message(filters.command("tutorial"))
async def send_tutorial(client, message):
    user_info = await database.users.find_one({'user_id': message.from_user.id})
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            if ban_time else "`N/A`"
        )
        await message._client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n"
                f"😔 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                f"📅 𝗕𝗮𝗻 𝗧𝗶𝗺𝗲: {ban_time_ist}\n"
                f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{banned_info.get('reason', 'No reason provided.')}`\n\n"
                f"⚠️ 𝗜𝗳 𝘆𝗼𝘂 𝗯𝗲𝗹𝗶𝗲𝘃𝗲 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲, 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝘀𝘂𝗽𝗽𝗼𝗿𝘁."
            ),
            reply_to_message_id=message.id,
        )
        return

    text = (
        "**👋 Welcome to Your Ultimate Bot Guide!**\n\n"
        "Master the bot in just **5 quick steps** — it's easy, fast, and beginner-friendly!\n\n"
        "**✨ Covered Topics:**\n"
        "• Starting the bot\n"
        "• Sending links\n"
        "• Logging in (if needed)\n"
        "• Downloading files\n"
        "• Getting extra help\n\n"
        "𝗧𝗮𝗽 𝗮𝗻𝘆 𝘀𝘁𝗲𝗽 𝗯𝗲𝗹𝗼𝘄 𝘁𝗼 𝗯𝗲𝗴𝗶𝗻!"
    )

    buttons = [
        [InlineKeyboardButton("📌 𝗦𝘁𝗲𝗽 𝟭: 𝗦𝘁𝗮𝗿𝘁 𝘁𝗵𝗲 𝗕𝗼𝘁", callback_data="tutorial:step1")],
        [InlineKeyboardButton("🔗 𝗦𝘁𝗲𝗽 𝟮: 𝗦𝗲𝗻𝗱 𝗮 𝗟𝗶𝗻𝗸", callback_data="tutorial:step2")],
        [InlineKeyboardButton("🔐 𝗦𝘁𝗲𝗽 𝟯: 𝗟𝗼𝗴𝗶𝗻 (𝗜𝗳 𝗡𝗲𝗲𝗱𝗲𝗱)", callback_data="tutorial:step3")],
        [InlineKeyboardButton("📥 𝗦𝘁𝗲𝗽 𝟰: 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗙𝗶𝗹𝗲𝘀", callback_data="tutorial:step4")],
        [InlineKeyboardButton("💡 𝗦𝘁𝗲𝗽 𝟱: 𝗠𝗼𝗿𝗲 𝗛𝗲𝗹𝗽", callback_data="tutorial:step5")],
        [InlineKeyboardButton("🎥 𝗪𝗮𝘁𝗰𝗵 𝗩𝗶𝗱𝗲𝗼 𝗚𝘂𝗶𝗱𝗲", callback_data="tutorial:video")],
        [
            InlineKeyboardButton("🏠 𝗠𝗮𝗶𝗻 𝗠𝗲𝗻𝘂", callback_data="tutorial:menu"),
            InlineKeyboardButton("❌ 𝗖𝗹𝗼𝘀𝗲", callback_data="tutorial:close")
        ]
    ]

    await client.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(r"^tutorial:(.+)"))
async def tutorial_router(client, callback_query):
    action = callback_query.data.split(":")[1]

    steps = {
        "step1": {
            "text": "📌 **𝗦𝘁𝗲𝗽 𝟭 𝗼𝗳 𝟱: Start the Bot**\n\n"
                    "• Send **/start** in this chat.\n"
                    "• The bot will greet you and unlock all features.\n\n"
                    "➡ Tap **Next** to continue.",
            "next": "step2"
        },
        "step2": {
            "text": "🔗 **𝗦𝘁𝗲𝗽 𝟮 𝗼𝗳 𝟱: Send the Link**\n\n"
                    "• Copy the **message link** from any Telegram channel or bot.\n"
                    "• Paste it here and send it to the bot.\n\n"
                    "➡ Tap **Next** to continue.",
            "next": "step3", "back": "step1"
        },
        "step3": {
            "text": "🔐 **𝗦𝘁𝗲𝗽 𝟯 𝗼𝗳 𝟱: Login (If Needed)**\n\n"
                    "• Use **/login** if login is required.\n"
                    "• Follow instructions to verify your session.\n\n"
                    "➡ Tap **Next** to continue.",
            "next": "step4", "back": "step2"
        },
        "step4": {
            "text": "📥 **𝗦𝘁𝗲𝗽 𝟰: 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗙𝗶𝗹𝗲𝘀**\n\n"
                    "1. Once a valid link is sent, the bot will begin downloading instantly.\n"
                    "2. **Premium access may be required** for:\n"
                    "   • Batch downloads\n"
                    "   • Download Files without time limits\n\n"
                    "💡 **Tip:** Use **/buy** to explore premium plans and unlock full access.\n\n"
                    "➡ Tap **Next** to continue.",
            "next": "step5", "back": "step3"
        },
        "step5": {
            "text": "💡 **𝗦𝘁𝗲𝗽 𝟱 𝗼𝗳 𝟱: More Help**\n\n"
                    "• Use **/help** for full command list.\n"
                    "• Contact support for extra assistance.\n\n"
                    "🎉 You're all set!\n"
                    "🎥 Tap below to watch the full video guide.",
            "next": "video", "back": "step4"
        }
    }

    if action in steps:
        data = steps[action]
        buttons = []

        if "next" in data:
            buttons.append([InlineKeyboardButton("➡ 𝗡𝗲𝘅𝘁", callback_data=f"tutorial:{data['next']}")])
        if "back" in data:
            buttons.append([InlineKeyboardButton("⬅ 𝗕𝗮𝗰𝗸", callback_data=f"tutorial:{data['back']}")])

        buttons.append([InlineKeyboardButton("🔁 𝗥𝗲𝘀𝘁𝗮𝗿𝘁 𝗧𝘂𝘁𝗼𝗿𝗶𝗮𝗹", callback_data="tutorial:step1")])
        buttons.append([
            InlineKeyboardButton("🏠 𝗠𝗮𝗶𝗻 𝗠𝗲𝗻𝘂", callback_data="tutorial:menu"),
            InlineKeyboardButton("❌ 𝗖𝗹𝗼𝘀𝗲", callback_data="tutorial:close")
        ])

        await callback_query.message.edit_text(
            text=data["text"],
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

    elif action == "video":
        await callback_query.message.delete()
        await client.send_video(
            chat_id=callback_query.message.chat.id,
            video="https://t.me/MSB_tutorial/4",
            caption="🎬 **Complete Video Guide**\n\n"
                    "This walkthrough covers all steps with real examples.\n"
                    "Perfect if you’re a visual learner!"
        )
        await callback_query.message.reply_text(
            "**⬅ Choose an option below:**",
            reply_markup=InlineKeyboardMarkup([
                 [InlineKeyboardButton("⬅ 𝗕𝗮𝗰𝗸 𝘁𝗼 𝗦𝘁𝗲𝗽 𝟱", callback_data="tutorial:step5")],
                 [
                     InlineKeyboardButton("🔁 𝗥𝗲𝘀𝘁𝗮𝗿𝘁", callback_data="tutorial:step1"),
                     InlineKeyboardButton("❌ 𝗖𝗹𝗼𝘀𝗲", callback_data="tutorial:close")
                 ]
            ])
        )

    elif action == "menu":
        try:
            await callback_query.message.delete()
        except:
            pass
        await send_tutorial(client, callback_query.message)

    elif action == "close":
        await callback_query.message.delete()
        await callback_query.answer("✅ Closed the tutorial. Type /tutorial anytime!")


# Buy
@Client.on_message(filters.command("buy"), group=0)
async def buy_plans(client, message):
    user_info = await database.users.find_one({'user_id': message.from_user.id})
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            if ban_time else "`N/A`"
        )
        await message._client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n"
                f"😔 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                f"📅 𝗕𝗮𝗻 𝗧𝗶𝗺𝗲: {ban_time_ist}\n"
                f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{banned_info.get('reason', 'No reason provided.')}`\n\n"
                f"⚠️ 𝗜𝗳 𝘆𝗼𝘂 𝗯𝗲𝗹𝗶𝗲𝘃𝗲 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲, 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝘀𝘂𝗽𝗽𝗼𝗿𝘁."
            ),
            reply_to_message_id=message.id,
        )
        return

    plans = await database.plans.find().to_list(length=None)

    if not plans:
        return await client.send_message(
            message.chat.id,
            "❌ **No premium plans available right now. Stay tuned!**",
            reply_to_message_id=message.id
        )

    plan_emojis = ["🔥", "💎", "✨", "⚡️", "💥", "🚀", "🌟"]

    text = "╭━〔 ✨ 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗣𝗟𝗔𝗡𝗦 ✨ 〕━╮\n\n"
    text += "💎 *Unlock a whole new world of features!*\n\n"

    for plan in plans:
        name = plan.get('plan', 'Unnamed Plan')
        duration = plan.get('duration', 0)
        unit = plan.get('unit', 'days')
        price = plan.get('price', 0)

        emoji = random.choice(plan_emojis)

        dur_str = "♾️ Lifetime Access" if unit == 'none' else f"{duration} {unit.capitalize()}"
        
        price_str = f"₹{int(price)}" if price == int(price) else f"₹{price}"

        text += (
            f"➤ {emoji} **{name} Plan**\n"
            f"⏳ *Validity:* `{dur_str}`\n"
            f"💵 *Price:* `{price_str}`\n"
            "──────────────────\n"
        )

    text += (
        "🎁 **Unlock premium benefits like:**\n"
        "➟ Faster access 🚀\n"
        "➟ Exclusive features 🔥\n"
        "➟ Priority support & more! 🌟\n\n"
        "💝 *Choose your plan and DM the owner to upgrade instantly!*"
    )

    await client.send_message(
        message.chat.id,
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿", url="https://t.me/FLiX_LY?text=%F0%9F%94%A5%20**Yo%20Boss!**%0A%0AI%E2%80%99m%20ready%20to%20unlock%20the%20**%F0%9F%92%8E%20PREMIUM**%20power.%0A%0AHit%20me%20up%20with%20the%20plans%20%E2%80%94%20I%20want%20the%20good%20stuff.%20%F0%9F%98%8E")]
        ]),
        reply_to_message_id=message.id,
        disable_web_page_preview=True
    )


# My Plan
@Client.on_message(filters.command(["myplan"]), group=0)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    user_info = await database.users.find_one({'user_id': user_id})
    
    # Check if the user is a member of the required channel/group
    if not await is_member(client, message.from_user.id):
        
        await client.send_message(
            chat_id=message.chat.id,
            text=f"👋 ʜɪ {message.from_user.mention}, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ❤️", url=FSUB_INV_LINK)
            ]]),
            reply_to_message_id=message.id  
        )
        return

    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            if ban_time else "`N/A`"
        )
        await message._client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n"
                f"😔 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                f"📅 𝗕𝗮𝗻 𝗧𝗶𝗺𝗲: {ban_time_ist}\n"
                f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{banned_info.get('reason', 'No reason provided.')}`\n\n"
                f"⚠️ 𝗜𝗳 𝘆𝗼𝘂 𝗯𝗲𝗹𝗶𝗲𝘃𝗲 𝘁𝗵𝗶𝘀 𝗶𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲, 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝘀𝘂𝗽𝗽𝗼𝗿𝘁."
            ),
            reply_to_message_id=message.id,
        )
        return

    # Check and possibly update the user's plan
    await Check_Plan(client, user_id)

    if not user_info:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Oops! You are not registered. Use /start to get going.**",
            reply_to_message_id=message.id
        )
        return

    plan_data = user_info.get('plan')
    if not plan_data:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Oops! Plan data missing. Please contact our support team.**",
            reply_to_message_id=message.id
        )
        return

    plan_type = plan_data.get('type', 'free')

    if plan_type == 'free':
        text = (
            "💫 **Your Current Plan**: `Free` 💫\n\n"
            "🚀 *Want to unlock exclusive features and elevate your experience?* 🔥\n\n"
            "💎 **Upgrade to Premium** and get access to:\n"
            "  - *Unlimited features* 💥\n"
            "  - *Priority support* 🏅\n"
            "  - *Special bonuses and more* 🎁\n\n"
            "🔑 Ready to level up? Here's your chance! 🌟\n\n"
            "💬 Use the button below to view premium plans!"
        )
        await client.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("💳 𝗩𝗶𝗲𝘄 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗣𝗹𝗮𝗻𝘀", url=f"https://t.me/{(await client.get_me()).username}?start=buy")]]
            )
        )
        return

    premium_started = plan_data.get("started_at")
    premium_expiration = plan_data.get("expiration_at")
    plan_name = plan_data.get("preset") or "Custom"
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    if not premium_expiration:
        # Lifetime plan
        if isinstance(premium_started, str):
            premium_started = datetime.fromisoformat(premium_started).replace(tzinfo=pytz.utc)
        elif premium_started and premium_started.tzinfo is None:
            premium_started = premium_started.replace(tzinfo=pytz.utc)

        started_time_ist = premium_started.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if premium_started else "N/A"

        await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🎉 **Premium Plan Access!** 🎊\n\n"
                f"💎 **Plan:** `{plan_name}`\n"
                f"🕒 **Started At:** {started_time_ist}\n"
                f"♾️ **Validity:** Lifetime\n\n"
                f"💝 ***You have permanent access to all premium features. Enjoy! 💎***"
            ),
            reply_to_message_id=message.id
        )
        return

    # Handle timezone parsing
    if isinstance(premium_started, str):
        premium_started = datetime.fromisoformat(premium_started).replace(tzinfo=pytz.utc)
    elif premium_started.tzinfo is None:
        premium_started = premium_started.replace(tzinfo=pytz.utc)
    
    started_time_ist = premium_started.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if premium_started else "N/A"

    if premium_expiration:
        # Normalize to UTC
        if isinstance(premium_expiration, str):
            premium_expiration = datetime.fromisoformat(premium_expiration).replace(tzinfo=pytz.utc)
        elif premium_expiration.tzinfo is None:
            premium_expiration = premium_expiration.replace(tzinfo=pytz.utc)

        expiry_time_ist = premium_expiration.astimezone(IST).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"

        # Remaining time
        remaining_seconds = int((premium_expiration - now_utc).total_seconds())
        remaining_time_str = format_duration(remaining_seconds)

        # Plan validity
        validity_seconds = int((premium_expiration - premium_started).total_seconds())
        plan_validity_str = format_duration(validity_seconds)

    else:
        expiry_time_ist = "Never"
        remaining_time_str = "♾️ Lifetime"
        plan_validity_str = "♾️ Lifetime"

    await client.send_message(
        chat_id=message.chat.id,
        text=(
            f"🎉 𝗪𝗼𝗼𝗵𝗼𝗼! 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗣𝗹𝗮𝗻 𝗔𝗰𝘁𝗶𝘃𝗲𝗱 ✨\n\n"
            f"💎 **Plan:** `{plan_name}`, *{plan_validity_str}*\n"
            f"⏳ **Activated On:** {started_time_ist}\n"
            f"⌛ **Expiry On:** {expiry_time_ist}\n"
            f"🕒 **Time Left:** {remaining_time_str}\n\n"
            "🔓 **𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀 𝗨𝗻𝗹𝗼𝗰𝗸𝗲𝗱:**\n"
            "• 𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝘀 ⚡\n"
            "• 𝗕𝗮𝘁𝗰𝗵 𝗦𝗮𝘃𝗲 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 📦\n"
            "• 𝗙𝗮𝘀𝘁 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 🚀\n"
            "• 𝗣𝗿𝗶𝗼𝗿𝗶𝘁𝘆 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 🛠️\n\n"
            "🎉 𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 𝗳𝗼𝗿 𝘂𝗽𝗴𝗿𝗮𝗱𝗶𝗻𝗴! 𝗲𝗻𝗷𝗼𝘆 𝘁𝗵𝗲 𝗿𝗶𝗱𝗲."
        ),
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 𝗨𝗽𝗴𝗿𝗮𝗱𝗲 𝗢𝗿 𝗘𝘅𝘁𝗲𝗻𝗱", url=f"https://t.me/{(await client.get_me()).username}?start=buy")
        ]])
    )


