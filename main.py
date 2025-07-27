# Don't Remove Credit Tg - @FLiX_LY
# Ask Doubt on telegram @FLiX_LY


import os, pytz, asyncio, logging, pyrogram
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from pyrogram import Client, filters
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import database, users_collection
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, LOGS_CHAT_ID


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    datefmt="%d %b %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            "logs.txt",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=10,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
ist = pytz.timezone('Asia/Kolkata')


class Bot(Client):
    def __init__(self):
        super().__init__(
            "FLIX_savelogin",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="FLiX"),
            workers=50,
            sleep_threshold=10
        )

    #Bot Start
    async def start(self):
        await super().start()
        bot_info = await self.get_me()  # Get bot information
        logger.info(f"🚀 @{bot_info.username} Is Started Powered By @FLiX_LY")
        await self.log_msg(
            f"🚀 𝗕𝗼𝘁 𝗢𝗻𝗹𝗶𝗻𝗲!\n\n"
            f"🤖 **Name**: `{bot_info.first_name}`\n"
            f"🔗 **Username**: @{bot_info.username}\n"
            f"🆔 **ID**: `{bot_info.id}`\n\n"
            f"🛠️ **Status**: `✅ Running Smoothly`\n"
            f"👨‍💻 **Developer**: @FLiX_LY\n"
            f"🕓 **Started At:** `{datetime.now(ist).strftime('%d %B %Y - %I:%M:%S %p')}` (IST)"
        )

        # User Cmds
        user_commands = [
            BotCommand("start", "🚀 𝗖𝗵𝗲𝗰𝗸 𝗔𝗹𝗶𝘃𝗲"),
            BotCommand("login", "🔐 𝗟𝗼𝗴𝗶𝗻 𝘁𝗼 𝗬𝗼𝘂𝗿 𝗔𝗰𝗰𝗼𝘂𝗻𝘁"),
            BotCommand("logout", "🚪 𝗟𝗼𝗴𝗼𝘂𝘁 𝗙𝗿𝗼𝗺 𝗔𝗰𝗰𝗼𝘂𝗻𝘁"),
            BotCommand("help", "❓ 𝗛𝗼𝘄 𝘁𝗼 𝗨𝘀𝗲"),
            BotCommand("id", "🆔 𝗖𝗵𝗲𝗰𝗸 𝗬𝗼𝘂𝗿 𝗖𝗵𝗮𝘁 𝗜𝗗"),
            BotCommand("myplan", "📈 𝗖𝗵𝗲𝗰𝗸 𝗬𝗼𝘂𝗿 𝗣𝗹𝗮𝗻"),
            BotCommand("buy", "🛒 𝗩𝗶𝗲𝘄 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗣𝗹𝗮𝗻𝘀"),
            BotCommand("token", "🎁 𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗣𝗿𝗲𝗺𝗶𝘂𝗺"),
            BotCommand("stop", "⏹️ 𝗦𝘁𝗼𝗽 𝗢𝗻𝗴𝗼𝗶𝗻𝗴 𝗕𝗮𝘁𝗰𝗵"),
            BotCommand("tutorial", "📱 𝗦𝘁𝗲𝗽 𝗕𝘆 𝗦𝗲𝘁𝗽 𝗚𝘂𝗶𝗱𝗲"),
            BotCommand("settings", "⚙️ 𝗢𝗽𝗲𝗻 𝗬𝗼𝘂𝗿 𝗣𝗲𝗿𝘀𝗼𝗻𝗮𝗹 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀")
        ]

        admin_commands = [
            BotCommand("stats", "📊 𝗬𝗼𝘂𝗿 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲 𝗜𝗻𝗳𝗼 [ADMIN]"),
            BotCommand("count_all", "📋 𝗚𝗲𝘁 𝗔𝗹𝗹 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁 [ADMIN]"),
            BotCommand("count_token", "🎟️ 𝗖𝗵𝗲𝗰𝗸 𝗧𝗼𝗸𝗲𝗻 𝗨𝘀𝗲𝗿𝘀 [ADMIN]"),
            BotCommand("upgrade", "💎 𝗚𝗿𝗮𝗻𝘁 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗔𝗰𝗰𝗲𝘀𝘀 [ADMIN]"),
            BotCommand("remove", "🗑️ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗨𝘀𝗲𝗿 𝗳𝗿𝗼𝗺 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 [ADMIN]"),
            BotCommand("count_pre", "👑 𝗖𝗵𝗲𝗰𝗸 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 [ADMIN]"),
            BotCommand("ban", "⛔ 𝗕𝗮𝗻 𝗮 𝗨𝘀𝗲𝗿 [ADMIN]"),
            BotCommand("unban", "✅ 𝗨𝗻𝗯𝗮𝗻 𝗮 𝗨𝘀𝗲𝗿 [ADMIN]"),
            BotCommand("count_banned", "📛 𝗖𝗵𝗲𝗰𝗸 𝗕𝗮𝗻𝗻𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 [ADMIN]"),
            BotCommand("broadcast", "📢 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗮 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 [ADMIN]")
        ]

        await self.set_bot_commands(user_commands + admin_commands)

        # Start Expired Premium Users Check
        asyncio.create_task(self.check_expired_premium())

    #Bot Stop
    async def stop(self, *args):
        logger.info("Bot Has Been Stopped. Alvida!")  # Updated stop message
        await self.log_msg(
            f"⚠️ **Bot Has Been Stopped. Alvida!**\n\n"
            f"🕓 **Stopped At:** `{datetime.now(ist).strftime('%d %B %Y - %I:%M:%S %p')}` (IST)\n"
            f"🔧 **Status:** `Offline`\n"
            f"👨‍💻 **Developer**: @FLiX_LY"
        )
        await super().stop()


    #Log Messagw
    async def log_msg(self, message: str):
        if LOGS_CHAT_ID:
            try:
                await self.send_message(LOGS_CHAT_ID, message)
            except Exception as e:
                logger.error(f"Failed to log to channel: {e}")


    #Expired Premium Users Check
    async def check_expired_premium(self):
        view_plan = f"https://t.me/{(await self.get_me()).username}?start=buy"
        logger.info("✅ Premium Expiry Monitor has started successfully.")

        while True:
            try:
                now_utc = datetime.now(timezone.utc)

                # Fetch expired premium users asynchronously
                expired_users = await users_collection.find({
                    'plan.type': 'premium',
                    'plan.expiration_at': {
                        '$ne': None,
                        '$lt': now_utc
                    }
                }).to_list(length=None)

                for user in expired_users:
                    user_id = user['user_id']
                    premium_started = user['plan'].get('started_at')
                    premium_expiration = user['plan'].get('expiration_at')
                    existing_preset = user['plan'].get('preset', 'Unknown')
                    admin_id = user['plan'].get('upgrade_by')

                    started_time_ist = premium_started.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if premium_started else "N/A"
                    expiry_time_ist = "Never" if not premium_expiration else \
                        f"`{premium_expiration.astimezone(ist).strftime('%d %B %Y - %I:%M:%S %p')}` (IST)"

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
                    try:
                        user_info = await self.get_users(user_id)
                        user_mention = f"[{user_info.first_name}](tg://user?id={user_id})"
                    except Exception:
                        user_mention = f"`{user_id}`"

                    try:
                        admin_info = await self.get_users(admin_id)
                        admin_mention = f"[{admin_info.first_name}](tg://user?id={admin_id})"
                    except Exception:
                        admin_mention = f"`{admin_id}`"

                    # Remove From DB
                    await users_collection.update_one(
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

                    try:
                        config = await database.config.find_one({"key": "Token_Info"}) or {}
                        is_token_user = str(existing_preset or "").startswith("token_")

                        expiry_msg = (
                            "💔 **Oops! Your Premium Access Just Ended.**\n"
                            "You've been moved back to the **Free Plan** — fewer features, but you're still awesome! 😎\n\n"
                        )

                        if is_token_user and config.get("token_mode", False):
                            expiry_msg += (
                                "🎁 **But hey!** You can still grab a **Free Premium Pass** using **/token** — it's waiting for you (but not forever!). ⏳\n"
                                "✨ Want the full VIP experience with zero limits? Just **upgrade** and unlock all the good stuff!"
                            )
                        else:
                            expiry_msg += (
                                "✨ **Want the magic back?** Choose a new plan to return to full **Premium power** — more features, more fun, more you! 💖"
                            )

                        await self.send_message(
                            chat_id=user_id,
                            text=expiry_msg,
                            reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton("💳 𝗩𝗶𝗲𝘄 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗣𝗹𝗮𝗻𝘀", url=view_plan)]]
                            )
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to notify user {user_id}: {e}")
                        await self.log_msg(
                            f"⚠️ **Failed to notify user `{user_id}` about premium expiry.**\n\n"
                            f"❌ Error: `{str(e)}`"
                        )

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

            except Exception as e:
                logger.error(f"Error in premium check: {e}")
                await self.log_msg(
                    f"**❌ Error in premium check**: `{str(e)}`"
                )

            await asyncio.sleep(300)  # Sleep for 5 minutes before next check


