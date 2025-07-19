# Don't Remove Credit Tg - @FLiX_LY
# Ask Doubt on telegram @FLiX_LY


import os, re, time, pytz, logging, asyncio, aiofiles
from datetime import datetime, timezone, timedelta

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.handlers import MessageHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UsernameNotOccupied, RPCError, AuthKeyUnregistered, SessionExpired, UserNotParticipant, ChatAdminRequired

from database.db import database
from FLiX.strings import strings
from config import API_ID, API_HASH, Session_String, DUMP_CHAT_ID, FSUB_ID, FSUB_INV_LINK, LOGS_CHAT_ID, TOKEN_MODE

logger = logging.getLogger(__name__)


def get(obj, key, default=None):
    try:
        return obj[key]
    except:
        return default


def format_duration(td) -> str:
    if isinstance(td, (float, int)):
        total_seconds = int(td)
    else:
        total_seconds = int(td.total_seconds())

    if total_seconds < 1:
        return "Less than 1s"

    d, rem = divmod(total_seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)

    parts = [
        f"{d}d" if d else "",
        f"{h}h" if h else "",
        f"{m}m" if m else "",
        f"{s}s" if s else ""
    ]
    return ", ".join(filter(None, parts))


async def is_member(client: Client,user_id: int) -> bool:
    if not FSUB_ID:
        return True

    try:
        chat_member = await client.get_chat_member(FSUB_ID, user_id)
        return chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]
    except UserNotParticipant:
        return False  # Explicitly not a member
    except ChatAdminRequired:
        logger.warning("Bot lacks admin privileges in the forced subscription channel (FSUB_ID). Unable to verify user membership. Please promote the bot to admin.")
        return False
    except Exception as e:
        logger.error(f"Error checking membership for user {user_id} in {FSUB_ID}: {e}")
        return False


async def log_msg(client, message: str):
    if LOGS_CHAT_ID:
        try:
            await client.send_message(LOGS_CHAT_ID, message)
        except Exception as e:
            logger.error(f"Failed to log to channel: {e}")


async def Check_Plan(client, user_id):
    try:
        now_utc = datetime.now(timezone.utc)
        user_info = await database.users.find_one({'user_id': user_id})

        if not user_info:
            return True  # User not found, assume free

        plan = user_info.get('plan', {})
        if plan.get('type') == 'free':
            return True  # Already free

        premium_started = plan.get('started_at')
        premium_expiration = plan.get('expiration_at')
        existing_preset = plan.get('preset', 'Unknown')
        admin_id = plan.get('upgrade_by')

        # Convert expiration to timezone-aware datetime
        if isinstance(premium_expiration, str):
            premium_expiration = datetime.fromisoformat(premium_expiration).replace(tzinfo=pytz.utc)
        elif premium_expiration and premium_expiration.tzinfo is None:
            premium_expiration = premium_expiration.replace(tzinfo=pytz.utc)

        # If expired
        if premium_expiration and now_utc > premium_expiration:
            started_time_ist = premium_started.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if premium_started else "N/A"
            expiry_time_ist = f"`{premium_expiration.astimezone(ist).strftime('%d %B %Y - %I:%M:%S %p')}` (IST)"

            if premium_started and premium_expiration:
                delta = premium_expiration - premium_started
                d, s = divmod(delta.total_seconds(), 86400)
                h, s = divmod(s, 3600)
                m, _ = divmod(s, 60)
                plan_validity_str = ", ".join(filter(None, [
                    f"{int(d)} d" if d else "",
                    f"{int(h)} h" if h else "",
                    f"{int(m)} m" if m else ""
                ])) or "Less than 1 minute"
            else:
                plan_validity_str = "♾️ Lifetime"

            # Format mentions
            try:
                user_info = await client.get_users(user_id)
                user_mention = f"[{user_info.first_name}](tg://user?id={user_id})"
            except Exception:
                user_mention = f"`{user_id}`"

            try:
                admin_info = await client.get_users(admin_id)
                admin_mention = f"[{admin_info.first_name}](tg://user?id={admin_id})"
            except Exception:
                admin_mention = f"`{admin_id}`" if admin_id else "Unknown"

            # Downgrade the user
            await database.users.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'plan.type': 'free',
                        'plan.preset': None,
                        'plan.started_at': None,
                        'plan.expiration_at': None,
                        'stop_status': True
                    },
                    '$unset': {
                        'plan.upgrade_by': ""
                    }
                }
            )

            # Notify the user
            try:
                is_token_user = str(existing_preset).startswith("token_")
                bot_username = (await client.get_me()).username

                expiry_msg = (
                    "💔 **Oops! Your Premium Access Just Ended.**\n"
                    "You've been moved back to the **Free Plan** — fewer features, but you're still awesome! 😎\n\n"
                )

                if is_token_user and TOKEN_MODE:
                    expiry_msg += (
                        "🎁 **But hey!** You can still grab a **Free Premium Pass** using **/token** — it's waiting for you (but not forever!). ⏳\n"
                        "✨ Want the full VIP experience with zero limits? Just **upgrade** and unlock all the good stuff!"
                    )
                else:
                    expiry_msg += (
                        "✨ **Want the magic back?** Choose a new plan to return to full **Premium power** — more features, more fun, more you! 💖"
                    )

                await client.send_message(
                    chat_id=user_id,
                    text=expiry_msg,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("💳 𝗩𝗶𝗲𝘄 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗣𝗹𝗮𝗻𝘀", url=f"https://t.me/{bot_username}?start=buy")]]
                    )
                )
            except Exception as e:
                logger.error(f"❌ Failed to notify user {user_id}: {e}")
                await client.log_msg(
                    f"⚠️ **Failed to notify user `{user_id}` about premium expiry.**\n\n"
                    f"❌ Error: `{str(e)}`"
                )

            # Log the expiry
            logger.info("Premium expired: User %s downgraded to free plan.", user_id)
            if not is_token_user:
                await self.log_msg(
                    f"🔻 **Premium Plan Expired** 🔻\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"👤 **User:** {user_mention}\n"
                    f"🆔 **User ID:** `{user_id}`\n"
                    f"💎 **Plan:** `{existing_preset}`, *{plan_validity_str}*\n"
                    f"⏳ **Started On:** {started_time_ist}\n"
                    f"⌛️ **Expired On:** {expiry_time_ist}\n"
                    f"👑 **Upgraded By:** {admin_mention}\n"
                    f"📉 **Status:** `Downgraded to Free Plan`\n"
                    f"🕓 **Logged At:** `{datetime.now(ist).strftime('%d %B %Y - %I:%M:%S %p')}` (IST)\n"
                    f"━━━━━━━━━━━━━━━━━"
                    f"🔔 **Note:** Premium features have been revoked.\n"
                )

            return True  # Now a free user

        return False  # Still premium

    except Exception as e:
        logger.error(f"❌ Error in Check_Plan for user {user_id}: {e}")
        await client.log_msg(
            f"**❌ Error in Check_Plan for user `{user_id}`**\n\n"
            f"`{str(e)}`"
        )
        return True


# Store download time after successful download
async def update_last_download_time(user_id: int):
    await database.users.update_one(
        {'user_id': user_id},
        {'$set': {'last_download_time': time.time()}}
    )

async def can_download(user_id: int):
    user = await database.users.find_one({'user_id': user_id})
    if user:
        last_download_time = user.get('last_download_time')
        if last_download_time:
            elapsed_time = time.time() - last_download_time
            remaining_time = 300 - elapsed_time  # 5 minutes cooldown
            if remaining_time > 0:
                return False, remaining_time
        else:
            # If last_download_time is None, the user can download
            return True, 0
    # If user is not found, assume they can download
    return True, 0


async def show_progress(client, statusfile, message, filename, post_link, total_size, user, mode="down"):
    start_time = time.time()

    while not os.path.exists(statusfile):
        await asyncio.sleep(2)

    while os.path.exists(statusfile):
        try:
            async with aiofiles.open(statusfile, "r") as f:
                content = (await f.read()).strip().replace('%', '')
            percent = float(content) if content else 0.0
            done = (percent / 100) * total_size

            elapsed = time.time() - start_time
            speed = done / elapsed if elapsed > 0 else 0
            eta = (total_size - done) / speed if speed > 0 else 0

            # Format progress bar
            bar_length = 10
            filled = int(bar_length * percent / 100)
            bar = '★' * filled + '☆' * (bar_length - filled)

            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024:
                        return f"{size:.2f} {unit}"
                    size /= 1024
                return f"{size:.2f} PB"

            # Format ETA
            if eta >= 3600:
                eta_str = f"{int(eta // 3600)}h {int((eta % 3600) // 60)}m {int(eta % 60)}s"
            elif eta >= 60:
                eta_str = f"{int(eta // 60)}m {int(eta % 60)}s"
            else:
                eta_str = f"{int(eta)}s" if eta > 0 else "Calculating..."

            status = {
                "down": "🔥 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗𝗜𝗡𝗚 🔥",
                "up": "🚀 𝗨𝗣𝗟𝗢𝗔𝗗𝗜𝗡𝗚 🚀"
            }.get(mode, "🔄 𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚")

            # Build message
            text = (
                f"╭─── {status}\n"
                f"├🔖 𝗣𝗼𝘀𝘁/𝗠𝘀𝗴: **[View it]({post_link})**\n"
                f"├📁 𝗙𝗶𝗹𝗲: `{filename}`\n"
                f"├[{bar}] `{percent:.2f}%`\n"
                f"├📥 𝗦𝗶𝘇𝗲: `{format_size(done)} / {format_size(total_size)}`\n"
                f"├⚡ 𝗦𝗽𝗲𝗲𝗱: `{format_size(speed)}/s`\n"
                f"├⏳ 𝗘𝗧𝗔: `{eta_str}`\n"
                f"╰👤 𝗨𝘀𝗲𝗿: **{user.mention}** | 𝗜𝗗: `{user.id}`"
            )

            await client.edit_message_text(message.chat.id, message.id, text)
            await asyncio.sleep(3)

        except Exception as e:
            logger.exception(f"Progress tracking error for file: {filename} | User: {user.id}")
            await asyncio.sleep(3)


# progress writer
async def progress(current, total, message, mode):
    try:
        user_id = message.from_user.id

        # 🔴 Stop flag check
        user_data = await database.users.find_one({'user_id': user_id})
        if user_data and user_data.get("stop_status", False):
            raise asyncio.CancelledError("Stopped by user")

        # ✅ Progress writing
        percent = (current / total) * 100 if total else 0
        with open(f"{message.id}{mode}status.txt", "w") as f:
            f.write(f"{percent:.2f}")
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(f"Failed to update progress for message {message.id}: {e}")


#Get message id from bot
@Client.on_message(filters.command("bot"), group=4)
async def run_userbot(client, message):
    user_id = message.from_user.id
    user_data = await database.sessions.find_one({'user_id': user_id})

    if not user_data or not user_data.get("logged_in") or not user_data.get("session"):
        await client.send_message(
            chat_id=message.chat.id,
            text="❌ 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗹𝗼𝗴𝗴𝗲𝗱 𝗶𝗻. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘂𝘀𝗲 /login 𝗳𝗶𝗿𝘀𝘁.",
            reply_to_message_id=message.id
        )
        return

    usage_msg = await client.send_message(
        chat_id=message.chat.id,
        text=(
            "✅ 𝗦𝗲𝘀𝘀𝗶𝗼𝗻 𝗔𝗰𝘁𝗶𝗼𝗻𝗲𝗱 — 𝟱 𝗠𝗶𝗻𝘀 𝗢𝗻𝗹𝗶𝗻𝗲 ✨\n\n"
            "🔹 𝗚𝗲𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗜𝗗:\n"
            "• 𝗥𝗲𝗽𝗹𝘆 𝘁𝗼 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘄𝗶𝘁𝗵 `..` 𝗶𝗻 𝘁𝗵𝗲 𝗕𝗼𝘁 𝗖𝗵𝗮𝘁\n"
            "  → 𝗬𝗼𝘂’𝗹𝗹 𝗿𝗲𝗰𝗲𝗶𝘃𝗲 𝗶𝘁’𝘀 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗜𝗗\n"
            "✨ 𝗘𝗻𝗷𝗼𝘆 𝗧𝗵𝗲 𝗕𝗼𝘁! ✨"
        ),
        reply_to_message_id=message.id
    )

    try:
        acc = Client(
            name=f"ubot_{user_id}",
            session_string=user_data['session'],
            api_id=API_ID,
            api_hash=API_HASH,
            device_model="𝗙𝗟𝗶𝗫 𝗕𝗼𝘁 🚀",
            app_version="ꜱʀʙ 2.0",
            system_version="𝗙𝗟𝗶𝗫 𝗖𝗹𝗼𝘂𝗱 ⚡️",
            lang_code="en"
        )

        async with acc as ubot:
            me = await ubot.get_me()
            logged_msg = await client.send_message(
                chat_id=message.chat.id,
                text=f"👤 𝗟𝗼𝗴𝗴𝗲𝗱 𝗶𝗻 𝗮𝘀 [{me.first_name}](https://t.me/{me.username or me.id})",
                reply_to_message_id=usage_msg.id,
                disable_web_page_preview=True
            )

            # Function to handle ".." messages
            async def on_dot(client, msg):
                if msg.text == ".." and msg.from_user.id == me.id:
                    if msg.reply_to_message:
                        await client.send_message(
                            chat_id=msg.chat.id,
                            text=f"🆔 **Message ID:** `{msg.reply_to_message.id}`",
                            reply_to_message_id=msg.reply_to_message.id
                        )
                        await client.delete_messages(msg.chat.id, msg.id)

            handler = MessageHandler(on_dot, filters.text)
            ubot.add_handler(handler)

            await asyncio.sleep(300)  # Keep the userbot alive for 5 mins
            ubot.remove_handler(handler)

            await client.send_message(
                chat_id=message.chat.id,
                text="❌ 𝗨𝘀𝗲𝗿𝗯𝗼𝘁 𝘀𝗲𝘀𝘀𝗶𝗼𝗻 𝗲𝗻𝗱𝗲𝗱.",
                reply_to_message_id=usage_msg.id
            )
            await client.delete_messages(message.chat.id, [logged_msg.id])

    except (AuthKeyUnregistered, SessionExpired):
        await database.sessions.update_one({'user_id': user_id}, {'$set': {'logged_in': False, 'session': None}})
        await client.send_message(message.chat.id, f"❌ **Session expired. Please /login again.**", reply_to_message_id=message.id)
    except FloodWait as fw:
        await asyncio.sleep(fw.value)
    except Exception as e:
        await client.send_message(message.chat.id, f"⚠️ **Error:**\n`{e}`", reply_to_message_id=message.id)



# Stop Ongoing Batch
@Client.on_message(filters.command(["stop"]), group=4)
async def stop_handler(client: Client, message: Message):
    
    # Retrieve the user's document from the database
    user_info = await database.users.find_one({'user_id': message.from_user.id})
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
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

    # If no active batch is running, inform the user.
    if not user_info or not user_info.get('active_batch', False):
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ There Is No Active Ongoing Batch.**",
            reply_to_message_id=message.id
        )
        return

    # Set the stop flag in the user's document
    await database.users.update_one(
        {'user_id': message.from_user.id},
        {'$set': {'active_batch': False, 'stop_status': True}}
    )
    await client.send_message(
        chat_id=message.chat.id,
        text="**⏹️ Force Stopping the Ongoing Process.**",
        reply_to_message_id=message.id
    )


# Save Fetch And Forward to You
@Client.on_message(filters.text & ~filters.regex(r"^/") & (filters.private | filters.group), group=4)
async def save(client: Client, message: Message):
    if not await is_member(client, message.from_user.id):
        
        await client.send_message(
            chat_id=message.chat.id,
            text=f"👋 ʜɪ {message.from_user.mention}, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("ᴊᴏɪɴ ❤️", url=FSUB_INV_LINK)
            ]]),
            reply_to_message_id=message.id  
        )
        return

    user_info = await database.users.find_one({'user_id': message.from_user.id})
    if user_info and "banned_info" in user_info:
        banned_info = user_info.get("banned_info", {})
        ban_time = banned_info.get("ban_time")
        ban_time_ist = (
            ban_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
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

    if "t.me/joinchat/" in message.text or "t.me/+" in message.text:
        try:
            if not Session_String:
                await client.send_message(message.chat.id, f"❌ **String Session is not Set Yet.**", reply_to_message_id=message.id)
                return
            acc = Client("shared_session", session_string=Session_String, api_hash=API_HASH, api_id=API_ID)
            await acc.connect()

            # Extract chat link
            chat_link = message.text.split()[-1]

            # Try joining the chat
            try:
                await acc.join_chat(chat_link)
                await client.send_message(
                    chat_id=message.chat.id,
                    text="✅ **Successfully joined the chat!**",
                    reply_to_message_id=message.id,
                )
            except UserAlreadyParticipant:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="✅ **I am already a member of this chat!**",
                    reply_to_message_id=message.id,
                )
            except Exception as e:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ **Failed to join the chat:** {e}",
                    reply_to_message_id=message.id,
                )

            await acc.disconnect()
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ **Unexpected error:** {e}",
                reply_to_message_id=message.id,
            )
        return

    if "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single","").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID
        #if batch
        total_msg = toID - fromID + 1
        last_msg = fromID - 2

        is_free_user = await Check_Plan(client, message.from_user.id)

        if is_free_user and fromID != toID:
            bot_info = await client.get_me()

            msg = (
                "🚫 **Free Plan Restriction**\n\n"
                "You can only save **1 file at a time** on the free plan.\n\n"
                "✨ Upgrade to **Premium** to unlock:\n"
                "• Batch downloads\n"
                "• Faster speeds\n"
                "• Priority support & more!\n"
            )
            if TOKEN_MODE:
                msg += "\n🎁 Get **Free Premium Access** with /token – limited time only!"


            await client.send_message(
                chat_id=message.chat.id,
                text=msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ", url=f"https://t.me/{bot_info.username}?start=buy")
                ]]),
                reply_to_message_id=message.id
            )
            return

        if user_info.get('active_batch', False):
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Active Batch Detected!**\n\nPlease wait until it finishes or stop it using /stop.",
                reply_to_message_id=message.id
            )
            return

        if is_free_user:
            can_download_now, remaining_time = await can_download(message.from_user.id)
            if not can_download_now:
                bot_info = await client.get_me()
                remaining_minutes, remaining_seconds = divmod(remaining_time, 60)

                msg = (
                    "🕐 **Hold on! Cooldown Active**\n\n"
                    "As a free user, you need to wait **5 minutes** between downloads.\n\n"
                    f"⏳ *Time Left:* `{int(remaining_minutes)} min {int(remaining_seconds)} sec`\n\n"
                    "⚡ Want instant access with *no waiting*?\n"
                    "Upgrade to Premium and enjoy unlimited freedom!"
                )
                if TOKEN_MODE:
                    msg += "\n\n🎁 Use `/token` for **Free Premium Access** – limited time only!"

                await client.send_message(
                    chat_id=message.chat.id,
                    text=msg,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ", url=f"https://t.me/{bot_info.username}?start=buy")
                    ]]),
                    reply_to_message_id=message.id
                )
                return

        await database.users.update_one(
            {'user_id': message.from_user.id},
            {'$set': {'active_batch': True, 'stop_status': False}}
        )

        if is_free_user:
            await update_last_download_time(message.from_user.id)

        if total_msg > 1:
            progress_msg = await client.send_message(
                chat_id=message.chat.id,
                text=f"🔄 **Batch Mode Started**\nfrom `{fromID}` to `{toID}`...",
                reply_to_message_id=message.id
            )
        
        for msgid in range(fromID, toID + 1):
            last_msg = msgid

            # ✅ Check stop_status inside the loop
            was_cancelled = None
            user_data = await database.users.find_one({'user_id': message.from_user.id})
            if user_data and user_data.get("stop_status", False):
                await database.users.update_one(
                    {'user_id': message.from_user.id},
                    {'$set': {'stop_status': False, 'active_batch': False}}
                )
                was_cancelled = True
                if progress_msg:
                    await progress_msg.delete()
                break

            if total_msg > 1:
                await progress_msg.edit_text(
                    f"🔄 **Batch Mode Started**\nfrom `{fromID} to `{toID}`\n\n"
                    f"**Now Processing: {msgid}**"
                )
            
            # Private
            if "https://t.me/c/" in message.text:
                try:
                    acc = Client("shared_session", session_string=Session_String, api_hash=API_HASH, api_id=API_ID)
                    await acc.connect()
                    chatid = int("-100" + datas[4])
                    try:
                        await acc.get_chat(chat_id)
                    except Exception as e:
                        await client.send_message(
                            message.chat.id,
                            f"🚫 **Access Denied or Chat Not Found.**\n`{e}`",
                            reply_to_message_id=message.id
                        )
                        break
                    was_cancelled = await handle_private(client, acc, message, chatid, msgid)
                except (AuthKeyUnregistered, SessionExpired) as e:
                    await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'active_batch': False}})
                    await client.send_message(message.chat.id, f"❌ **Your session is invalid or expired.\nPlease Tell Owner To Update Session.**", reply_to_message_id=message.id)
                    break
                except Exception as e:
                    await client.send_message(message.chat.id, f"⚠️**Error:** {e}", reply_to_message_id=message.id)
                    await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'last_download_time': None}})


            # public
            else:
                username = datas[3]

                try:
                    msg = await client.get_messages(username, msgid)
                except UsernameNotOccupied: 
                    await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'active_batch': False}})
                    await client.send_message(message.chat.id, "**Username/Channel Not Found**", reply_to_message_id=message.id)
                    break
                    
                try:
                    user_data = await database.users.find_one({'user_id': message.from_user.id})
                    settings = user_data.get('settings', {}) if user_data else {}
                    custom_thumb = settings.get('thumbnail')
                    word_replacements = settings.get('word_replacements', {}) or {}

                    #Thumbnail
                    if custom_thumb and os.path.exists(custom_thumb):
                        raise ValueError("Custom thumbnail Exists, Need To Use Handle_Private.")  # Force exception

                    #Custom Words
                    caption = msg.caption or ""
                    for old, new in word_replacements.items():
                        if new.lower() == "hidden":
                            caption = re.sub(rf'\s*{re.escape(old)}\s*', ' ', caption, flags=re.IGNORECASE).strip()
                        else:
                            caption = re.sub(re.escape(old), new, caption, flags=re.IGNORECASE)

                    await client.copy_message(
                        message.chat.id,
                        msg.chat.id,
                        msg.id,
                        caption=caption,  
                        reply_to_message_id=message.id
                    )
                    dm_tag = await client.copy_message(
                        DUMP_CHAT_ID,
                        msg.chat.id,
                        msg.id,
                        caption=caption,  
                        reply_to_message_id=message.id
                    )
                    await client.send_message(DUMP_CHAT_ID, f"┖ ᴜsᴇʀ: [{message.from_user.first_name}](tg://user?id={message.from_user.id}) | ɪᴅ: <code>{message.from_user.id}</code>", reply_to_message_id=dm_tag.id)
                    await database.users.update_one({'user_id': message.from_user.id}, {"$inc": {"saved_files": 1}}, upsert=True)

                except:
                    try:    
                        acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
                        await acc.connect()
                        try:
                            await acc.get_chat(chat_id)
                        except Exception as e:
                            await client.send_message(
                                message.chat.id,
                                f"🚫 **Access Denied or Chat Not Found.**\n`{e}`",
                                reply_to_message_id=message.id
                            )
                            break
                        was_cancelled = await handle_private(client, acc, message, username, msgid)
                    except (AuthKeyUnregistered, SessionExpired) as e:
                        await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'active_batch': False}})
                        await client.send_message(message.chat.id, f"❌ **Your session is invalid or expired.\nPlease Tell Owner To Update Session.**", reply_to_message_id=message.id)
                        break
                    except Exception as e:
                        await client.send_message(message.chat.id, f"⚠️**Error:** {e}", reply_to_message_id=message.id)
                        await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'last_download_time': None}})

            # wait time
            await asyncio.sleep(2.5)

        if is_free_user:
            await update_last_download_time(message.from_user.id)

        await database.users.update_one(
            {'user_id': message.from_user.id},
            {'$set': {'active_batch': False}}
        )
        if was_cancelled:
            await client.send_message(
                chat_id=message.chat.id,
                text="**⏹️ Stopped Ongoing Process.**",
                reply_to_message_id=message.id
            )
        elif total_msg > 1:
            await progress_msg.delete()
            await client.send_message(
                chat_id=message.chat.id,
                text=f"✅ **Batch Mode Completed**\nfrom `{fromID}` to `{last_msg}`",
                reply_to_message_id=message.id
            )

# handle private
async def handle_private(client: Client, acc, message: Message, chatid, msgid: int):
    try:
        msg: Message = await acc.get_messages(chatid, msgid)
        if not msg or msg.empty:
            return
        if msg.chat.username:
            post_link = f"https://t.me/{msg.chat.username}/{msg.id}"
        else:
            chat_id = str(msg.chat.id).removeprefix("-100")
            post_link = f"https://t.me/c/{chat_id}/{msg.id}"

    except RPCError as e:
        await client.send_message(message.chat.id, f"Error fetching message: {e}", reply_to_message_id=message.id)
        await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'last_download_time': None}})
        return

    msg_type = get_message_type(msg)
    chat = message.chat.id
    dosta = None
    upsta = None
    file = None
    thumb_path = None

    if msg_type == "Unknown":
        await client.send_message(
            chat,
            f"𝗘𝗿𝗿𝗼𝗿: 𝗨𝗻𝘀𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗼𝗿 𝗨𝗻𝗿𝗲𝗰𝗼𝗴𝗻𝗶𝘇𝗲𝗱 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗧𝘆𝗽𝗲\n"
            f"➥ 𝗦𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗧𝘆𝗽𝗲𝘀: `Text, Document, Video, Audio, Voice, Photo, Sticker`",
            reply_to_message_id=message.id
        )
        return

    if msg_type == "Text":
        try:
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id)
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
            await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'last_download_time': None}})
        return

    # Settings
    user_data = await database.users.find_one({'user_id': message.from_user.id})
    settings = user_data.get('settings', {}) if user_data else {}
    custom_thumb = settings.get('thumbnail', None)
    word_replacements = settings.get('word_replacements', {}) or {}

    filename, file_size = get_file_info(msg, message)
    for old_word, new_word in word_replacements.items():
        if new_word.lower() == "hidden":
            filename = re.sub(rf'\s*{re.escape(old_word)}\s*', ' ', filename, flags=re.IGNORECASE).strip()
        else:
            filename = re.sub(re.escape(old_word), new_word, filename, flags=re.IGNORECASE)

    # Download Media
    smsg = await client.send_message(chat, "ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ꜰɪʟᴇꜱ 😈", reply_to_message_id=message.id)
    dosta = asyncio.create_task(
        show_progress(client, f"{message.id}downstatus.txt", smsg, filename, post_link, file_size, message.from_user, mode="down")
    )

    try:
        # Downloading
        try:
            file = await acc.download_media(msg, file_name=filename, progress=progress, progress_args=[message, "down"])
            if not file:
                raise ValueError("Downloaded file is missing or invalid.")
            dosta.cancel()

        except asyncio.CancelledError:
            was_cancelled = True
            if os.path.exists(f"{message.id}downstatus.txt"):
                os.remove(f"{message.id}downstatus.txt")
            if file and os.path.exists(file):
                os.remove(file)
            return was_cancelled

        except Exception as e:
            logging.error(f"Error downloading file for user {message.from_user.id}: {str(e)}")
            await smsg.delete()
            await client.send_message(chat, f"𝗘𝗿𝗿𝗼𝗿: 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗱 𝗳𝗶𝗹𝗲 𝗶𝘀 𝗺𝗶𝘀𝘀𝗶𝗻𝗴 𝗼𝗿 𝗶𝗻𝘃𝗮𝗹𝗶𝗱. {str(e)}", reply_to_message_id=message.id)
            await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'last_download_time': None}})
            dosta.cancel()
            if os.path.exists(f"{message.id}downstatus.txt"):
                os.remove(f"{message.id}downstatus.txt")
            if file and os.path.exists(file):
                os.remove(file)
            return

        # Caption replacement
        caption = msg.caption or ""
        original_caption = msg.caption
        for old, new in word_replacements.items():
            if new.lower() == "hidden":
                caption = re.sub(rf'\s*{re.escape(old)}\s*', ' ', caption, flags=re.IGNORECASE).strip()
            else:
                caption = re.sub(re.escape(old), new, caption, flags=re.IGNORECASE)
        caption_entities = msg.caption_entities if caption == original_caption else None

        # Thumbnail logic
        if custom_thumb and os.path.exists(custom_thumb):
            thumb_path = custom_thumb
        else:
            media = None
            if msg_type == "Video":
                media = msg.video
            elif msg_type == "Audio":
                media = msg.audio
            elif msg_type == "Document":
                media = msg.document

            if media:
                thumb = getattr(media, "thumb", None)
                thumbs = getattr(media, "thumbs", None)
                selected_thumb = thumb or (thumbs[0] if thumbs else None)

                if selected_thumb:
                    try:
                        ph_path = await acc.download_media(selected_thumb)
                        if isinstance(ph_path, (str, bytes, os.PathLike)) and os.path.exists(ph_path):
                            thumb_path = ph_path
                        else:
                            logger.warning(f"⚠️ Invalid thumbnail path: {ph_path}")
                    except Exception as e:
                        logger.error(f"❌ Exception while downloading thumbnail: {e}")

        # Uploading File
        await smsg.edit("ꜱᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ꜰɪʟᴇꜱ 😈")
        upsta = asyncio.create_task(
            show_progress(client, f"{message.id}upstatus.txt", smsg, filename, post_link, file_size, message.from_user, mode="up")
        )

        kwargs = {
            "caption": caption,
            "caption_entities": caption_entities,
            "reply_to_message_id": message.id,
            "progress": progress,
            "progress_args": [message, "up"]
        }
        if thumb_path and os.path.exists(thumb_path):
            kwargs["thumb"] = thumb_path

        if msg_type == "Document":
            dm = await client.send_document(chat, file, **kwargs)

        elif msg_type == "Video":
            dm = await client.send_video(
                chat, file,
                duration=msg.video.duration,
                width=msg.video.width,
                height=msg.video.height,
                **kwargs
            )

        elif msg_type == "Sticker":
            await client.send_sticker(chat, msg.sticker.file_id, reply_to_message_id=message.id)

        elif msg_type == "Voice":
            await client.send_voice(chat, file, **kwargs)

        elif msg_type == "Audio":
            await client.send_audio(chat, file, **kwargs)

        elif msg_type == "Photo":
            await client.send_photo(chat, file, **kwargs)

        if msg_type in ["Document", "Video"]:
            dm_tag = await dm.copy(DUMP_CHAT_ID)
            await client.send_message(DUMP_CHAT_ID, f"┖ ᴜsᴇʀ: [{message.from_user.first_name}](tg://user?id={message.from_user.id}) | ɪᴅ: `{message.from_user.id}`", reply_to_message_id=dm_tag.id)

        await database.users.update_one({'user_id': message.from_user.id}, {"$inc": {"saved_files": 1}}, upsert=True)


    except asyncio.CancelledError:
        was_cancelled = True
        if os.path.exists(f"{message.id}upstatus.txt"):
            os.remove(f"{message.id}upstatus.txt")
        if file and os.path.exists(file):
            os.remove(file)
        return was_cancelled

    except Exception as e:
        await client.send_message(chat, f"𝗘𝗿𝗿𝗼𝗿: {e}", reply_to_message_id=message.id)
        await database.users.update_one({'user_id': message.from_user.id}, {'$set': {'last_download_time': None}})

    finally:
        for task in [dosta, upsta]:
            if task and not task.done():
                task.cancel()
        for f in [f"{message.id}downstatus.txt", f"{message.id}upstatus.txt"]:
            if os.path.exists(f):
                os.remove(f)
        if file and os.path.exists(file):
            os.remove(file)
        if thumb_path and thumb_path != custom_thumb and os.path.exists(thumb_path):
            os.remove(thumb_path)
        await smsg.delete()


def get_message_type(msg: Message) -> str:
    for media_type in ["document", "video", "sticker", "voice", "audio", "photo", "text"]:
        if getattr(msg, media_type, None):
            return media_type.capitalize()
    return "Unknown"


def get_file_info(msg: Message, sender_msg: Message):
    user = sender_msg.from_user
    username = user.username if user and user.username else "unknown"
    message_id = msg.id

    media_info = [
        ("document", msg.document, ".doc"),
        ("video", msg.video, ".mp4"),
        ("audio", msg.audio, ".mp3"),
        ("voice", msg.voice, ".ogg"),
        ("photo", msg.photo, ".jpg"),
        ("sticker", msg.sticker, ".webp"),
    ]

    for media_type, media_obj, default_ext in media_info:
        if media_obj:
            filename = getattr(media_obj, "file_name", None)
            file_size = getattr(media_obj, "file_size", 0) or 0
            if not filename:
                filename = f"{username}_{message_id}_{media_type}{default_ext}"
            return filename, file_size

    return f"{username}_{message_id}_file", 0

