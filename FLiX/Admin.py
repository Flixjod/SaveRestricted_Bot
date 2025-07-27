# Don't Remove Credit Tg - @FLiX_LY
# Ask Doubt on telegram @FLiX_LY

import os, re, time, pytz, psutil, aiofiles, logging, asyncio, platform
from datetime import datetime, timedelta

from telegraph import Telegraph
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserIsBlocked, PeerIdInvalid

from config import OWNER_ID, TOKEN_API_URL, TOKEN_API_KEY
from database.db import database
from FLiX.Save import format_duration

logger = logging.getLogger(__name__)

telegraph = Telegraph()
telegraph.create_account(short_name="SaveRest")



@Client.on_message(filters.command("setplan") & filters.private, group=3)
async def set_plan(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        parts = message.text.strip().split()
        if len(parts) != 5:
            return await client.send_message(
                message.chat.id,
                "❗ **Incorrect Usage!**\n\n"
                "Please use the correct format:\n\n"
                "📌 `/setplan plan_name value unit price`\n\n"
                "**Examples:**\n"
                "`/setplan vip 30 days 99`\n"
                "`/setplan elite 1 none 499`  → (Lifetime Plan)",
                reply_to_message_id=message.id
            )

        _, plan_name, raw_value, raw_unit, raw_price = parts

        unit_map = {
            "day": "days", "days": "days",
            "hour": "hours", "hours": "hours",
            "minute": "minutes", "minutes": "minutes",
            "none": "none"
        }
        unit = unit_map.get(raw_unit.lower())
        if not unit:
            raise ValueError("Invalid unit. Use: day(s), hour(s), minute(s), or none.")

        if unit == "none":
            duration = None
        else:
            duration = int(raw_value)
            if duration < 0:
                raise ValueError("Duration cannot be negative.")

        price = float(raw_price) if "." in raw_price else int(raw_price)
        if price < 0:
            raise ValueError("Price cannot be negative.")

        # Check if plan already exists
        existing = await database.plans.find_one({"plan": plan_name})
        if existing:
            existing_duration = existing.get("duration")
            existing_unit = existing.get("unit", "none")
            existing_price = existing.get("price", 0)

            old_duration_display = "♾️ Lifetime" if existing_unit == "none" else f"{existing_duration} {existing_unit}"
            old_price_display = f"₹{existing_price:.2f}".rstrip('0').rstrip('.') if isinstance(existing_price, float) else f"₹{existing_price}"

            keyboard = ReplyKeyboardMarkup([["✅ 𝗬𝗲𝘀", "❌ 𝗡𝗼", "🗑️ 𝗗𝗲𝗹𝗲𝘁𝗲"]], one_time_keyboard=True, resize_keyboard=True)

            prompt = await client.send_message(
                message.chat.id,
                f"⚠️ **Plan Already Exists!**\n\n"
                f"Here are the current details for `{plan_name}`:\n"
                f"• **Duration:** *{old_duration_display}*\n"
                f"• **Price:** `{old_price_display}`\n\n"
                f"Would you like to **update** this plan with the new values?",
                reply_markup=keyboard,
                reply_to_message_id=message.id
            )

            try:
                response: Message = await client.wait_for_message(
                    chat_id=message.chat.id,
                    timeout=75,
                    filters=filters.text & filters.user(message.from_user.id)
                )
            except asyncio.TimeoutError:
                await prompt.delete()
                return await client.send_message(
                    message.chat.id,
                    "⌛ 𝗧𝗶𝗺𝗲𝗼𝘂𝘁! 𝗬𝗼𝘂 𝗱𝗶𝗱𝗻’𝘁 𝗿𝗲𝘀𝗽𝗼𝗻𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )

            user_input = response.text.strip().replace("✅ 𝗬𝗲𝘀", "yes").replace("❌ 𝗡𝗼", "no").replace("🗑️ 𝗗𝗲𝗹𝗲𝘁𝗲", "delete").lower()
            await prompt.delete()
            await response.delete()

            if user_input == "no":
                return await client.send_message(
                    message.chat.id,
                    "**❌ Plan update cancelled.**",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            elif user_input == "delete":
                await database.plans.delete_one({"plan": plan_name})
                return await client.send_message(
                    message.chat.id,
                    f"🗑️ Plan `{plan_name}` has been deleted.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            elif user_input == "yes":
                # Proceed with updating the plan
                await database.plans.update_one(
                    {"plan": plan_name},
                    {"$set": {
                        "plan": plan_name,
                        "duration": duration,
                        "unit": unit,
                        "price": price
                    }},
                    upsert=True
                )

                duration_display = "♾️ Lifetime" if unit == "none" else f"{duration} {unit}"
                price_display = f"₹{price:.2f}".rstrip('0').rstrip('.') if isinstance(price, float) else f"₹{price}"

                return await client.send_message(
                    message.chat.id,
                    f"✅ **Plan Updated Successfully!**\n\n"
                    f"• **Plan:** `{plan_name}`\n"
                    f"• **Duration:** *{duration_display}*\n"
                    f"• **Price:** `{price_display}`",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                # If invalid response
                return await client.send_message(
                    message.chat.id,
                    "❗ Invalid response! Please choose either **Yes**, **No**, or **Delete**.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )

        # If no existing plan, simply create or update the new plan
        await database.plans.update_one(
            {"plan": plan_name},
            {"$set": {
                "plan": plan_name,
                "duration": duration,
                "unit": unit,
                "price": price
            }},
            upsert=True
        )

        duration_display = "♾️ Lifetime" if unit == "none" else f"{duration} {unit}"
        price_display = f"₹{price:.2f}".rstrip('0').rstrip('.') if isinstance(price, float) else f"₹{price}"

        await client.send_message(
            message.chat.id,
            f"✅ **Plan Saved Successfully!**\n\n"
            f"• **Plan:** `{plan_name}`\n"
            f"• **Duration:** *{duration_display}*\n"
            f"• **Price:** `{price_display}`",
            reply_to_message_id=message.id,
            reply_markup=ReplyKeyboardRemove()
        )

    except Exception as e:
        await client.send_message(
            message.chat.id,
            f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n`{e}`",
            reply_to_message_id=message.id,
            reply_markup=ReplyKeyboardRemove()
        )


# Grant Premium Access
@Client.on_message(filters.command("upgrade") & filters.private)
async def upgrade_to_premium(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        parts = message.text.strip().split()
        if len(parts) < 3:
            return await client.send_message(
                message.chat.id,
                "⚡️ 𝗨𝗽𝗴𝗿𝗮𝗱𝗲 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗨𝘀𝗮𝗴𝗲\n\n"
                "➤ `/upgrade user_id plan_name`\n"
                "➤ `/upgrade user_id value [unit (days/hours/minutes/lifetime)]`\n\n"
                "📝 𝗘𝘅𝗮𝗺𝗽𝗹𝗲𝘀:\n"
                "├ `/upgrade 1234567890 vip`\n"
                "└ `/upgrade 1234567890 30 days`\n\n"
                "💡 𝗧𝗶𝗽: Use a preset plan name or set a custom duration with unit.",
                reply_to_message_id=message.id
            )

        user_id = int(parts[1])
        now_utc = datetime.now(pytz.utc)
        ist = pytz.timezone("Asia/Kolkata")
        is_preset = False
        is_lifetime = False
        is_extension = False
        is_reset = False

        # Check if it's a predefined plan or raw duration
        if len(parts) == 3:
            plan_name = parts[2]
            plan = await database.plans.find_one({'plan': plan_name})
            if not plan:
                return await client.send_message(
                    message.chat.id,
                    f"❌ Plan `{plan_name}` not found in database.",
                    reply_to_message_id=message.id
                )
            value = plan['duration']
            unit = plan['unit']
            is_preset  = True
            is_lifetime = (unit == 'none')

        else:
            value = int(parts[2])
            unit_input = parts[3].lower()
            unit_map = {
                "day": "days", "days": "days",
                "hour": "hours", "hours": "hours",
                "minute": "minutes", "minutes": "minutes",
                "lifetime": "none"
            }
            unit = unit_map.get(unit_input)
            is_lifetime = (unit == "none")
            plan_name = "Custom"
            if not unit:
                return await client.send_message(
                    message.chat.id,
                    "**Invalid time unit. Use 'days', 'hours', or 'minutes'.**",
                    reply_to_message_id=message.id
                )

        # Get user info from database
        user = await database.users.find_one({'user_id': user_id})
        if not user:
            return await client.send_message(
                message.chat.id,
                f"❌ User `{user_id}` not found in database.",
                reply_to_message_id=message.id
            )
        user_info = await client.get_users(user_id)

        # Backend Process
        plan_data = user.get('plan', {})
        existing_exp = plan_data.get('expiration_at')
        started_at = plan_data.get('started_at') or now_utc
        existing_preset = plan_data.get('preset') or "Custom"

        # Normalize existing_exp to datetime
        if isinstance(existing_exp, str):
            existing_exp = datetime.fromisoformat(existing_exp)
        if existing_exp and existing_exp.tzinfo is None:
            existing_exp = existing_exp.replace(tzinfo=pytz.utc)

        has_active_plan = existing_exp and existing_exp > now_utc
        has_lifetime_plan = existing_exp is None and plan_data.get("type") == "premium"
        old_plan_display = None

        if has_active_plan:
            expiry_ist = existing_exp.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p` (IST)")
            old_remaining = format_duration(existing_exp - now_utc)
            old_plan_display = (
                f"📆 **Old Plan:** {existing_preset}\n"
                f"⏳ **Old Remaining:** {old_remaining}\n"
                f"🕘 **Expires At:** {expiry_ist}"
            )

        elif has_lifetime_plan:
            old_plan_display = f"📆 **Current Plan:** {existing_preset}, ♾️"

        new_plan_display = (
            f"`{plan_name}`, ♾️" if is_lifetime else
            f"`{plan_name}`, *{value} {unit}*"
        )

        # Handle confirmation
        if has_lifetime_plan:
            confirm = await client.send_message(
                message.chat.id,
                f"⚠️ 𝗧𝗵𝗶𝘀 𝘂𝘀𝗲𝗿 𝗵𝗮𝘀 𝗮 ♾️ 𝗟𝗶𝗳𝗲𝘁𝗶𝗺𝗲 𝗽𝗹𝗮𝗻.\n\n"
                f"👤 **User ID:** `{user_id}`\n"
                f"{old_plan_display}\n\n"
                f"🆕 **New Plan:** {new_plan_display}\n\n"
                f"⚠️ Type or press `𝗥𝗲𝘀𝗲𝘁` to continue, or `𝗖𝗮𝗻𝗰𝗲𝗹` to abort.",
                reply_to_message_id=message.id,
                reply_markup=ReplyKeyboardMarkup([["♻️ 𝗥𝗲𝘀𝗲𝘁", "❌ 𝗖𝗮𝗻𝗰𝗲𝗹"]], one_time_keyboard=True, resize_keyboard=True),
            )
            try:
                response: Message = await client.wait_for_message(
                    chat_id=message.chat.id,
                    timeout=75,
                    filters=filters.text & filters.user(message.from_user.id)
                )
            except asyncio.TimeoutError:
                await client.delete_messages(message.chat.id, [confirm.id])
                return await client.send_message(
                    message.chat.id,
                    "⌛ 𝗧𝗶𝗺𝗲𝗼𝘂𝘁! 𝗬𝗼𝘂 𝗱𝗶𝗱𝗻’𝘁 𝗿𝗲𝘀𝗽𝗼𝗻𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )

            await client.delete_messages(
                message.chat.id,
                [confirm.id, response.id]
            )
            choice = response.text.strip().lower()
            if choice in ["cancel", "𝗖𝗮𝗻𝗰𝗲𝗹", "❌ 𝗖𝗮𝗻𝗰𝗲𝗹"]:
                return await client.send_message(
                    message.chat.id,
                    "✖️ 𝗢𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗰𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            if choice not in ["reset", "𝗥𝗲𝘀𝗲𝘁", "♻️ 𝗥𝗲𝘀𝗲𝘁"]:
                return await client.send_message(
                    message.chat.id,
                    "❌ Invalid input. Only `𝗥𝗲𝘀𝗲𝘁` is allowed.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            is_reset = choice in ["reset", "𝗥𝗲𝘀𝗲𝘁", "♻️ 𝗥𝗲𝘀𝗲𝘁"]

        elif has_active_plan:
            confirm = await client.send_message(
                message.chat.id,
                f"⚠️ 𝗧𝗵𝗶𝘀 𝘂𝘀𝗲𝗿 𝗵𝗮𝘀 𝗮𝗻 𝗮𝗰𝘁𝗶𝘃𝗲 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗽𝗹𝗮𝗻.\n\n"
                f"👤 **User ID:** `{user_id}`\n"
                f"{old_plan_display}\n\n"
                f"🆕 **New Plan:** {new_plan_display}\n\n"
                f"✳️ Type or press `𝗥𝗲𝘀𝗲𝘁` to reset, or `𝗘𝘅𝘁𝗲𝗻𝗱` to add more time.",
                reply_to_message_id=message.id,
                reply_markup=ReplyKeyboardMarkup([["♻️ 𝗥𝗲𝘀𝗲𝘁", "⏩ 𝗘𝘅𝘁𝗲𝗻𝗱"], ["❌ 𝗖𝗮𝗻𝗰𝗲𝗹"]], one_time_keyboard=True, resize_keyboard=True),
            )
            try:
                response: Message = await client.wait_for_message(
                    chat_id=message.chat.id,
                    timeout=75,
                    filters=filters.text & filters.user(message.from_user.id)
                )
            except asyncio.TimeoutError:
                await client.delete_messages(message.chat.id, [confirm.id])
                return await client.send_message(
                    message.chat.id,
                    "⌛ 𝗧𝗶𝗺𝗲𝗼𝘂𝘁! 𝗬𝗼𝘂 𝗱𝗶𝗱𝗻’𝘁 𝗿𝗲𝘀𝗽𝗼𝗻𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )

            await client.delete_messages(
                message.chat.id,
                [confirm.id, response.id]
            )
            choice = response.text.strip().lower()
            if choice in ["cancel", "𝗖𝗮𝗻𝗰𝗲𝗹", "❌ 𝗖𝗮𝗻𝗰𝗲𝗹"]:
                return await client.send_message(
                    message.chat.id,
                    "✖️ 𝗢𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗰𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            if choice not in ["reset", "𝗥𝗲𝘀𝗲𝘁", "♻️ 𝗥𝗲𝘀𝗲𝘁", "extend", "𝗘𝘅𝘁𝗲𝗻𝗱", "⏩ 𝗘𝘅𝘁𝗲𝗻𝗱"]:
                return await client.send_message(
                    message.chat.id,
                    "❌ Invalid input. Use the buttons or type `𝗥𝗲𝘀𝗲𝘁`, `𝗘𝘅𝘁𝗲𝗻𝗱`, or `𝗖𝗮𝗻𝗰𝗲𝗹`.",
                    reply_to_message_id=message.id,
                    reply_markup=ReplyKeyboardRemove()
                )
            is_reset = choice in ["reset", "𝗥𝗲𝘀𝗲𝘁", "♻️ 𝗥𝗲𝘀𝗲𝘁"]
            is_extension = choice in ["extend", "𝗘𝘅𝘁𝗲𝗻𝗱", "⏩ 𝗘𝘅𝘁𝗲𝗻𝗱"]

        # Calculate new expiration
        if is_lifetime:
            expiration_utc = None
            started_at = now_utc
        else:
            delta = timedelta(**{unit: value})
            if is_extension and existing_exp:
                expiration_utc = existing_exp + delta
            else:
                expiration_utc = now_utc + delta
                started_at = now_utc

        # Convert times for display
        started_time_ist = started_at.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if started_at else "N/A"
        expiry_time_ist = "**Never**" if expiration_utc is None else \
            expiration_utc.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
        plan_info = (
            f"`{plan_name}`, ♾️" if is_lifetime else f"`{plan_name}`, *{value} {unit}*"
        )

        # Update database
        await database.users.update_one(
            {'user_id': user_id},
            {'$set': {
                'plan': {
                    'type': 'premium',
                    'preset': plan_name if is_preset else None,
                    'started_at': started_at,
                    'expiration_at': expiration_utc,
                    'upgrade_by': message.from_user.id
                }
            }},
            upsert=True
        )

        # Text to admin & user
        if is_extension:
            admin_text = (
                f"🎉 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗘𝘅𝘁𝗲𝗻𝗱𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n\n"
                f"👤 **User:** [{user_info.first_name}](tg://user?id={user_info.id})\n"
                f"⚡ **User ID:** `{user_id}`\n"
                f"🕒 **Old Remaining:** {old_remaining}\n"
                f"➕ **Extended With:** {plan_info}\n\n"
                f"⏳ **Joined:** {started_time_ist}\n"
                f"⌛ **Expires:** {expiry_time_ist}"
            )
            user_text = (
                "🔔 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗘𝘅𝘁𝗲𝗻𝗱𝗲𝗱!\n\n"
                f"👋 Hi [{user_info.first_name}](tg://user?id={user_info.id}),\n"
                f"**Your premium has been extended. Enjoy!** ✨🎉\n\n"
                f"🕒 **Old Remaining:** {old_remaining}\n"
                f"➕ **Added:** {plan_info}\n"
                f"⌛ **New Expiry:** {expiry_time_ist}"
            )
        elif is_reset:
            admin_text = (
                f"🔁 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗥𝗲𝘀𝗲𝘁/𝗥𝗲𝗽𝗹𝗮𝗰𝗲𝗱 ✅\n\n"
                f"👤 **User:** [{user_info.first_name}](tg://user?id={user_info.id})\n"
                f"⚡ **User ID:** `{user_id}`\n"
                f"🆕 **New Plan:** {plan_info}\n\n"
                f"⏳ **Joining:** {started_time_ist}\n"
                f"⌛ **Expires:** {expiry_time_ist}"
            )
            user_text = (
                "♻️ 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗥𝗲𝘀𝗲𝘁/𝗥𝗲𝗽𝗹𝗮𝗰𝗲𝗱!\n\n"
                f"👋 Hi [{user_info.first_name}](tg://user?id={user_info.id}),\n"
                f"**Your plan has been reset with a new premium duration.**\n\n"
                f"🆕 **New Plan:** {plan_info}\n"
                f"⌛ **Expires:** {expiry_time_ist}"
            )
        else:
            admin_text = (
                f"🎉 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n\n"
                f"👤 **User:** [{user_info.first_name}](tg://user?id={user_info.id})\n"
                f"⚡ **User ID:** `{user_id}`\n"
                f"⏰ **Plan:** {plan_info}\n\n"
                f"⏳ **Joining:** {started_time_ist}\n"
                f"⌛ **Expires:** {expiry_time_ist}"
            )
            user_text = (
                "✨ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺!\n\n"
                f"👋 Hi [{user_info.first_name}](tg://user?id={user_info.id}),\n"
                f"**Thank you for purchasing premium. Enjoy!** ✨🎉\n\n"
                f"⏰ **Plan:** {plan_info}\n"
                f"⌛ **Expires:** {expiry_time_ist}"
            )

        # 1️⃣3️⃣ Send notifications
        await client.send_message(
            message.chat.id,
            admin_text,
            reply_to_message_id=message.id,
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
        await client.send_message(
            user_id,
            user_text,
            disable_web_page_preview=True
        )


    except ValueError:
        await client.send_message(
            message.chat.id,
            "❌ **Invalid input. Use:** `/upgrade user_id plan` or `/upgrade user_id value unit`",
            reply_to_message_id=message.id
        )
    except Exception as e:
        await client.send_message(
            message.chat.id,
            f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n`{e}`",
            reply_to_message_id=message.id
        )


# Premium User List
@Client.on_message(filters.command("count_pre") & filters.private, group=3)
async def check_premium_users(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        # Send temporary "Fetching..." message
        fetching_msg = await client.send_message(
            chat_id=message.chat.id,
            text="⏳ 𝗙𝗲𝘁𝗰𝗵𝗶𝗻𝗴 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 𝗜𝗻𝗳𝗼, 𝗽𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁...",
            reply_to_message_id=message.id
        )

        if len(message.command) > 1:
            arg = message.command[1].strip()
            if not arg.isdigit():
                await fetching_msg.delete()
                await client.send_message(
                    chat_id=message.chat.id,
                    text="⚠️ 𝗘𝗿𝗿𝗼𝗿:\n\nPlease provide a **valid numeric user ID** only.",
                    reply_to_message_id=message.id
                )
                return
            specific_user_id = int(arg)

            user_data = await database.users.find_one({'user_id': specific_user_id})
            if not user_data:
                await fetching_msg.delete()
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ 𝗡𝗼 𝘀𝘂𝗰𝗵 𝘂𝘀𝗲𝗿 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝗱𝗮𝘁𝗮𝗯𝗮𝘀𝗲!\n\nID: `{specific_user_id}`",
                    reply_to_message_id=message.id
                )
                return

            if user_data.get("plan", {}).get("type") != "premium":

                await fetching_msg.delete()
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ 𝗧𝗵𝗲 𝘂𝘀𝗲𝗿 𝗱𝗼𝗲𝘀 𝗻𝗼𝘁 𝗵𝗮𝘃𝗲 𝗮𝗻 𝗮𝗰𝘁𝗶𝘃𝗲 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗽𝗹𝗮𝗻.\n\nID: `{specific_user_id}`",
                    reply_to_message_id=message.id,
                    disable_web_page_preview=True
                )
                return

            premium_users = [user_data]
        else:
            premium_users = await database.users.find({
                'plan.type': 'premium',
                'plan.preset': {
                    '$not': {'$regex': '^token_'}
                }
            }).to_list(length=None)

        if not premium_users:
            await fetching_msg.delete()
            await client.send_message(chat_id=message.chat.id, text="⚠️ 𝗡𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 𝗙𝗼𝘂𝗻𝗱!", reply_to_message_id=message.id)
            return

        ist = pytz.timezone("Asia/Kolkata")
        now_utc = datetime.now(pytz.utc)
        semaphore = asyncio.Semaphore(20)

        async def process_user(user):
            async with semaphore:
                try:
                    user_id = user['user_id']
                    plan = user.get("plan", {})
                    premium_started = plan.get("started_at")
                    premium_expiration = plan.get("expiration_at")
                    existing_preset = plan.get('preset') or "Custom"
                    admin_id = plan.get("upgrade_by")

                    if isinstance(premium_started, str):
                        premium_started = datetime.fromisoformat(premium_started).replace(tzinfo=pytz.utc)
                    elif premium_started and premium_started.tzinfo is None:
                        premium_started = premium_started.replace(tzinfo=pytz.utc)

                    if isinstance(premium_expiration, str):
                        premium_expiration = datetime.fromisoformat(premium_expiration).replace(tzinfo=pytz.utc)
                    elif premium_expiration is not None and premium_expiration.tzinfo is None:
                        premium_expiration = premium_expiration.replace(tzinfo=pytz.utc)

                    started_time_ist = premium_started.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if premium_started else "N/A"
                    expiry_time_ist = "Never" if not premium_expiration else \
                        f"`{premium_expiration.astimezone(ist).strftime('%d %B, %Y - %I:%M:%S %p')}` (IST)"

                    if premium_expiration:
                        remaining_time_str = format_duration(premium_expiration - now_utc)
                    else:
                        remaining_time_str = "♾️ Lifetime"

                    if premium_started and premium_expiration:
                        plan_validity_str = format_duration(premium_expiration - premium_started)
                    else:
                        plan_validity_str = "♾️ Lifetime"
                    try:
                        user_info = await client.get_users(user_id)
                        user_mention = f"[{user_info.first_name}](tg://user?id={user_id})"
                    except Exception:
                        user_mention = f"`{user_id}`"
                    
                    try:
                        admin_info = await client.get_users(admin_id)
                        admin_mention = f"[{admin_info.first_name}](tg://user?id={admin_id})"
                    except Exception:
                        admin_mention = f"`{admin_id}`"

                    return (
                        f"👤 𝗨𝘀𝗲𝗿: {user_mention}\n"
                        f"⚡ 𝗨𝘀𝗲𝗿 𝗜𝗗: `{user_id}`\n"
                        f"📆 𝗣𝗹𝗮𝗻: `{existing_preset}`, *{plan_validity_str}*\n"
                        f"⏳ 𝗦𝘁𝗮𝗿𝘁𝗲𝗱 𝗧𝗶𝗺𝗲: {started_time_ist}\n"
                        f"⌛ 𝗘𝘅𝗽𝗶𝗿𝘆 𝗧𝗶𝗺𝗲: {expiry_time_ist}\n"
                        f"🕒 𝗧𝗶𝗺𝗲 𝗹𝗲𝗳𝘁: {remaining_time_str}\n"
                        f"🤍 𝗨𝗽𝗴𝗿𝗮𝗱𝗲 𝗕𝘆: {admin_mention}\n"
                        "———————————————"
                    )
                except Exception as e:
                    logger.error(f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ {e}")
                    return None

        tasks = [process_user(user) for user in premium_users]
        results = await asyncio.gather(*tasks)
        user_list = [r for r in results if r]

        await fetching_msg.delete()  # Delete the "Fetching..." message

        result_text = f"👑 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁 [𝗧𝗼𝘁𝗮𝗹: {len(user_list)}]\n\n" + "\n".join(user_list)
        if len(result_text) <= 4096:
            await client.send_message(
                chat_id=message.chat.id,
                text=result_text,
                reply_to_message_id=message.id,
                disable_web_page_preview=True
            )
        else:
            try:
                html_text = result_text.replace("\n", "<br>")
                page = telegraph.create_page(
                    title="Premium Users List",
                    html_content=html_text
                )
                link = f"https://telegra.ph/{page['path']}"
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"**📄 Premium User List.\n\nView here: [View]({link})**",
                    reply_to_message_id=message.id,
                    disable_web_page_preview=True
                )
            except Exception:
                file_path = f"Premium_Users_{int(time.time())}.txt"
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(result_text)

                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    caption="**📄 Premium User List**",
                    reply_to_message_id=message.id
                )
                os.remove(file_path)

    except Exception as e:
        try:
            await fetching_msg.delete()
        except:
            pass
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`",
            reply_to_message_id=message.id
        )


#Remove User From Premium
@Client.on_message(filters.command("remove") & filters.private, group=3)
async def remove_premium(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        # Extract user ID from the command
        command = message.text.split()
        if len(command) != 2:
            await client.send_message(message.chat.id, "❗ **Usage:** `/remove user_id`", reply_to_message_id=message.id)
            return

        # Validate user_id as an integer
        user_id = command[1]
        if not user_id.isdigit():
            await client.send_message(message.chat.id, "**Invalid input. User ID must be a valid number.**", reply_to_message_id=message.id)
            return

        user_id = int(user_id)  # Convert user_id to integer after validation

        # Check if the user exists in the database
        user = await database.users.find_one({'user_id': user_id})
        if user is None:
            await client.send_message(message.chat.id, f"**❌ User ID {user_id} not found in the database.**", reply_to_message_id=message.id)
            return
        
        # Check If User Free Don't remove 
        if not user or user.get("plan", {}).get("type") != "premium":
            await client.send_message(message.chat.id, f"**❌ User ID {user_id} doesn't have a active premium plan.**", reply_to_message_id=message.id)
            return
        
        # Fetch user details for mention
        user_info = await client.get_users(user_id)

        # Update user plan to "free" and set premium_expiration to None
        await database.users.update_one(
            {'user_id': user_id},
            {
              '$set': {
                'plan.type': 'free',
                'plan.started_at': None,
                'plan.expiration_at': None,
                'stop_status': True
              },
              '$unset': {
                'plan.preset': None,
                'plan.upgrade_by': None
              }
            }
        )

        # Notify admin
        await client.send_message(
            chat_id=message.chat.id,
            text=f"**Premium removed successfully ✅**\n\n"
                 f"👤 **User:** [{user_info.first_name}](tg://user?id={user_info.id})\n"
                 f"⚡ **User ID:** `{user_id}`\n\n"
                 f"**User is now on the free plan.**",
            reply_to_message_id=message.id,
            disable_web_page_preview=True
        )
        
        # Notify the user
        await client.send_message(
            chat_id=user_id,
            text=f"👋 Hi [{user_info.first_name}](tg://user?id={user_info.id}),\n"
                 f"**Your premium plan has been removed.**\n"
                 f"**You are now on the free plan.**",
            disable_web_page_preview=True
        )

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`", reply_to_message_id=message.id)




# Broadcast
@Client.on_message(filters.command("broadcast") & filters.private, group=3)
async def broadcast_message(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        total_users = await database.users.count_documents({})
        if total_users == 0:
            await client.send_message(
                chat_id=message.chat.id,  
                text="⚠️ 𝗡𝗼 𝗨𝘀𝗲𝗿𝘀 𝗙𝗼𝘂𝗻𝗱!\n\n💡 There are currently **Zero Users** in the database. Try again later!",  
                reply_to_message_id=message.id
            )
            return

        all_users = await database.users.find().to_list(length=None)

        # Determine the broadcast content
        if message.reply_to_message:
            broadcast_from_chat = message.chat.id
            broadcast_message_id = message.reply_to_message.id
            broadcast_text = None
        else:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await client.send_message(
                    chat_id=message.chat.id,  
                    text="ℹ️ 𝗛𝗼𝘄 𝘁𝗼 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁?\n\n🔹 Reply to a message to broadcast it.\n🔹 Or use `/broadcast Your Message Here`.",  
                    reply_to_message_id=message.id
                )
                return
            broadcast_text = parts[1]

        start_time = time.time()
        # Initialize counters
        sent_count = 0
        failed_count = 0
        blocked_count = 0
        deleted_count = 0
        blocked_user_ids = []
        deactivated_user_ids = []
        other_failed_user_ids = []


        # Send initial progress message:
        progress_message = await client.send_message(
            chat_id=message.chat.id,  
            text=(
            f"🚀 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗦𝗧𝗔𝗥𝗧𝗘𝗗!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👥 𝗧𝗢𝗧𝗔𝗟 𝗨𝗦𝗘𝗥𝗦: `{total_users}`\n"
            f"✅ 𝗗𝗘𝗟𝗜𝗩𝗘𝗥𝗘𝗗: `0`\n"
            f"🚫 𝗕𝗟𝗢𝗖𝗞𝗘𝗗: `0`\n"
            f"🗑️ 𝗗𝗘𝗟𝗘𝗧𝗘𝗗: `0`\n"
            f"❌ 𝗙𝗔𝗜𝗟𝗘𝗗: `0`\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⏳ *𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚...*"
            ),
            reply_to_message_id=message.id
        )
        
        # Limit concurrent tasks to avoid flooding (e.g., 20 at a time)
        semaphore = asyncio.Semaphore(20)

        # Define a helper coroutine to send the message for a single user
        async def send_to_user(user):
            nonlocal sent_count, failed_count, blocked_count, deleted_count
            user_id = user["user_id"]
            async with semaphore:
                try:
                    if message.reply_to_message:
                        await client.copy_message(
                            chat_id=user_id,
                            from_chat_id=broadcast_from_chat,
                            message_id=broadcast_message_id
                        )
                    else:
                        await client.send_message(chat_id=user_id, text=broadcast_text)
                    sent_count += 1
                except UserIsBlocked:
                    blocked_count += 1
                    blocked_user_ids.append(user_id)
                except PeerIdInvalid:
                    deleted_count += 1
                    deactivated_user_ids.append(user_id)
                    await database.users.delete_one({"user_id": user_id})
                except Exception:
                    failed_count += 1
                    other_failed_user_ids.append(user_id)
                await asyncio.sleep(0.1)

        # Create and launch tasks concurrently
        tasks = [asyncio.create_task(send_to_user(user)) for user in all_users]

        # Optionally, update progress periodically while tasks are running.
        # For example, update every 2 seconds until all tasks are complete:
        async def update_progress():
            while any(not task.done() for task in tasks):
                await progress_message.edit_text(
                    f"📡 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧𝗜𝗡𝗚...\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"👥 𝗧𝗢𝗧𝗔𝗟 𝗨𝗦𝗘𝗥𝗦: `{total_users}`\n"
                    f"✅ 𝗗𝗘𝗟𝗜𝗩𝗘𝗥𝗘𝗗: `{sent_count}`\n"
                    f"🚫 𝗕𝗟𝗢𝗖𝗞𝗘𝗗: `{blocked_count}`\n"
                    f"🗑️ 𝗗𝗘𝗟𝗘𝗧𝗘𝗗: `{deleted_count}`\n"
                    f"❌ 𝗙𝗔𝗜𝗟𝗘𝗗: `{failed_count}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔄 *𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚...*"
                )
                await asyncio.sleep(2)

        progress_updater = asyncio.create_task(update_progress())

        # Wait for all sending tasks to complete
        await asyncio.gather(*tasks)
        progress_updater.cancel()  # stop the progress updater
        await progress_message.delete()

        # Compute success and failure rates
        success_rate = (sent_count / total_users) * 100 if total_users > 0 else 0
        failure_rate = ((failed_count + blocked_count + deleted_count) / total_users) * 100 if total_users > 0 else 0
        
        end_time = time.time()
        total_seconds = int(end_time - start_time)

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours:
            duration = f"{hours} hour{'s' if hours != 1 else ''} {minutes} min {seconds} sec"
        elif minutes:
            duration = f"{minutes} min {seconds} sec"
        else:
            duration = f"{seconds} sec"

        # Final completion message
        await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"🎯 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘!\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👥 𝗧𝗢𝗧𝗔𝗟 𝗨𝗦𝗘𝗥𝗦: `{total_users}`\n"
                f"✅ 𝗦𝗨𝗖𝗖𝗘𝗦𝗦: `{sent_count}`\n"
                f"🚫 𝗕𝗟𝗢𝗖𝗞𝗘𝗗: `{blocked_count}`\n"
                f"🗑️ 𝗗𝗘𝗟𝗘𝗧𝗘𝗗: `{deleted_count}`\n"
                f"❌ 𝗙𝗔𝗜𝗟𝗨𝗥𝗘: `{failed_count}`\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📈 𝗦𝗨𝗖𝗖𝗘𝗦𝗦 𝗥𝗔𝗧𝗘: `{success_rate:.2f}%`\n"
                f"📉 𝗙𝗔𝗜𝗟𝗨𝗥𝗘 𝗥𝗔𝗧𝗘: `{failure_rate:.2f}%`\n"
                f"⏱ 𝗗𝗨𝗥𝗔𝗧𝗜𝗢𝗡: `{duration}`\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💖 *𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 𝗳𝗼𝗿 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗙𝗲𝗮𝘁𝘂𝗿𝗲!*"
            ),
            reply_to_message_id=message.id
        )

        broadcast_summary = [
            "━━━━━━━━━━━━ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗦𝗨𝗠𝗠𝗔𝗥𝗬 📣 ━━━━━━━━━━━━",
            f"🗓️  Date & Time         : {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y - %I:%M:%S %p')}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"👥  Total Users         : {total_users}",
            f"✅  Successful          : {sent_count}",
            f"🚫  Blocked             : {blocked_count}",
            f"🗑️  Deactivated/Invalid : {deleted_count}",
            f"❌  Other Failures      : {failed_count}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📈  Success Rate        : {success_rate:.2f}%",
            f"📉  Failure Rate        : {failure_rate:.2f}%",
            f"⏱️  Duration            : {duration}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📛 𝗕𝗹𝗼𝗰𝗸𝗲𝗱 𝗨𝘀𝗲𝗿 𝗜𝗗𝘀:",
            (", ".join(str(uid) for uid in blocked_user_ids) if blocked_user_ids else "None"),
            "",
            "🗑️ 𝗗𝗲𝗮𝗰𝘁𝗶𝘃𝗮𝘁𝗲𝗱/𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗨𝘀𝗲𝗿 𝗜𝗗𝘀:",
            (", ".join(str(uid) for uid in deactivated_user_ids) if deactivated_user_ids else "None"),
            "",
            "⚠️ 𝗢𝘁𝗵𝗲𝗿 𝗙𝗮𝗶𝗹𝗲𝗱 𝗨𝘀𝗲𝗿 𝗜𝗗𝘀:",
            (", ".join(str(uid) for uid in other_failed_user_ids) if other_failed_user_ids else "None"),
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "💖 𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 𝗳𝗼𝗿 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗙𝗲𝗮𝘁𝘂𝗿𝗲!",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        file_path = f"Broadcast_Summary_{int(time.time())}.txt"
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(broadcast_summary))

        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption="📄 *Detailed Broadcast Summary*"
        )

        os.remove(file_path)

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`", reply_to_message_id=message.id)




#Ban User
@Client.on_message(filters.command("ban") & filters.private, group=3)
async def ban_user(client: Client, message: Message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        cmd = message.text.split(maxsplit=2)
        if len(cmd) < 2:
            await client.send_message(
                message.chat.id,
                "❗ **Usage:** `/ban user_id [reason]`",
                reply_to_message_id=message.id
            )
            return

        try:
            user_id = int(cmd[1])
        except ValueError:
            await client.send_message(
                message.chat.id,
                "❌ **Invalid User ID!**",
                reply_to_message_id=message.id
            )
            return

        reason = cmd[2] if len(cmd) > 2 else "No reason provided."
        user = await database.users.find_one({"user_id": user_id})

        if not user:
            await client.send_message(
                message.chat.id,
                f"❌ **User ID `{user_id}` not found in the database.**",
                reply_to_message_id=message.id
            )
            return

        if user.get("banned_info", {}).get("status", False):
            banned_by_id = user['banned_info']['banned_by']
            try:
                admin_info = await client.get_users(banned_by_id)
                banned_by_mention = f"[{admin_info.first_name}](tg://user?id={banned_by_id})"
            except Exception:
                banned_by_mention = f"`{banned_by_id}`"

            ban_time = user['banned_info'].get('ban_time')
            if ban_time:
                ban_time_ist = ban_time.astimezone(pytz.timezone('Asia/Kolkata')).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
            else:
                ban_time_ist = "N/A"

            await client.send_message(
                message.chat.id,
                (
                    "⚠️ 𝗪𝗵𝗼𝗮! 𝗧𝗵𝗶𝘀 𝘂𝘀𝗲𝗿 𝗶𝘀 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗯𝗮𝗻𝗻𝗲𝗱!\n\n"
                    f"⚡️ **User ID:** `{user_id}`\n"
                    f"📝 **Reason:** `{user['banned_info']['reason']}`\n"
                    f"📅 **Banned On:** {ban_time_ist}\n"
                    f"👮‍♂️ **Banned By:** {banned_by_mention}"
                ),
                reply_to_message_id=message.id
            )
            return

        ban_time = datetime.now(pytz.utc)
        ban_time_ist = ban_time.astimezone(pytz.timezone('Asia/Kolkata')).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
        banned_by = message.from_user.id

        await database.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "banned_info": {
                    "status": True,
                    "reason": reason,
                    "ban_time": ban_time,
                    "banned_by": banned_by
                }
            }},
            upsert=True
        )

        try:
            user_info = await client.get_users(user_id)
            user_mention = f"[{user_info.first_name}](tg://user?id={user_id})"
        except Exception:
            user_mention = f"`{user_id}`"

        admin_mention = f"[{message.from_user.first_name}](tg://user?id={banned_by})"

        await client.send_message(
            message.chat.id,
            (
                "💥 𝗕𝗮𝗻𝗻𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!\n\n"
                f"👤 **User:** {user_mention}\n"
                f"⚡️ **User ID:** `{user_id}`\n"
                f"📝 **Reason:** `{reason}`\n"
                f"📅 **Ban Time:** {ban_time_ist}\n\n"
                f"*🚷 𝗧𝗵𝗲 𝘂𝘀𝗲𝗿 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗯𝗮𝗻𝗻𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗯𝗼𝘁.*"
            ),
            reply_to_message_id=message.id
        )

        try:
            await client.send_message(
            user_id,
                (
                    "🚫 𝗬𝗼𝘂 𝗛𝗮𝘃𝗲 𝗕𝗲𝗲𝗻 𝗕𝗮𝗻𝗻𝗲𝗱!\n\n"
                    f"📆 **Time**: {ban_time_ist}\n"
                    f"📝 **Reason**: `{reason}`\n\n"
                    "🔒 𝗬𝗼𝘂 𝗰𝗮𝗻 𝗻𝗼 𝗹𝗼𝗻𝗴𝗲𝗿 𝘂𝘀𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁.\n"
                    "⚠️ 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻 𝗶𝗳 𝘁𝗵𝗶𝘀 𝘄𝗮𝘀 𝗮 𝗺𝗶𝘀𝘁𝗮𝗸𝗲."
                )
            )
        except:
            pass

    except Exception as e:
        await client.send_message(
            message.chat.id,
            f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`",
            reply_to_message_id=message.id
        )


#Banned Users List
@Client.on_message(filters.command("count_banned") & filters.private, group=3)
async def count_banned(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        fetching_msg = await client.send_message(
            chat_id=message.chat.id,
            text="⏳ 𝗙𝗲𝘁𝗰𝗵𝗶𝗻𝗴 𝗯𝗮𝗻𝗻𝗲𝗱 𝘂𝘀𝗲𝗿𝘀, 𝗽𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁...",
            reply_to_message_id=message.id
        )

        if len(message.command) > 1:
            arg = message.command[1].strip()
            if not arg.isdigit():
                await fetching_msg.delete()
                return await client.send_message(
                    chat_id=message.chat.id,
                    text="⚠️ 𝗘𝗿𝗿𝗼𝗿:\n\nPlease provide a **valid numeric user ID**.",
                    reply_to_message_id=message.id
                )
            specific_user_id = int(arg)

            user_data = await database.users.find_one({'user_id': specific_user_id})
            if not user_data:
                await fetching_msg.delete()
                return await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ 𝗡𝗼 𝘀𝘂𝗰𝗵 𝘂𝘀𝗲𝗿 𝗳𝗼𝘂𝗻𝗱!\n\nID: `{specific_user_id}`",
                    reply_to_message_id=message.id
                )

            if not user_data.get("banned_info", {}).get("status", False):
                await fetching_msg.delete()
                return await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ 𝗧𝗵𝗶𝘀 𝘂𝘀𝗲𝗿 𝗶𝘀 𝗻𝗼𝘁 𝗯𝗮𝗻𝗻𝗲𝗱.\n\nID: `{specific_user_id}`",
                    reply_to_message_id=message.id
                )

            banned_users = [user_data]
        else:
            banned_users = await database.users.find({"banned_info.status": True}).to_list(length=None)

        if not banned_users:
            await fetching_msg.delete()
            return await client.send_message(
                chat_id=message.chat.id,
                text="✅ 𝗡𝗼 𝗯𝗮𝗻𝗻𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱.",
                reply_to_message_id=message.id
            )

        ist = pytz.timezone("Asia/Kolkata")
        semaphore = asyncio.Semaphore(20)

        async def format_user(user):
            async with semaphore:
                try:
                    user_id = user.get("user_id")
                    info = user.get("banned_info", {})
                    reason = info.get("reason", "No reason provided.")
                    ban_time = info.get("ban_time", None)
                    banned_by = info.get("banned_by", "Unknown")

                    # Format ban time
                    try:
                        ban_dt_ist = ban_time.astimezone(ist)
                        ban_time_ist = ban_dt_ist.strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
                        time_passed = datetime.now(ist) - ban_dt_ist
                        passed_str = f"{time_passed.days}d, {time_passed.seconds//3600}h, {(time_passed.seconds//60)%60}m"
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        ban_time_ist = "`N/A`"
                        passed_str = "N/A"

                    try:
                        user_info = await client.get_users(user_id)
                        user_mention = f"[{user_info.first_name}](tg://user?id={user_id})"
                    except:
                        user_mention = f"`{user_id}`"

                    try:
                        admin_info = await client.get_users(banned_by)
                        admin_mention = f"[{admin_info.first_name}](tg://user?id={banned_by}) (`{banned_by}`)"
                    except:
                        admin_mention = f"`{banned_by}`"

                    return (
                        f"👤 𝗨𝘀𝗲𝗿: {user_mention}\n"
                        f"⚡️ 𝗨𝘀𝗲𝗿 𝗜𝗗: `{user_id}`\n"
                        f"📝 𝗥𝗲𝗮𝘀𝗼𝗻: `{reason}`\n"
                        f"📅 𝗕𝗮𝗻𝗻𝗲𝗱 𝗢𝗻: {ban_time_ist}\n"
                        f"⏳ 𝗧𝗶𝗺𝗲 𝗦𝗶𝗻𝗰𝗲 𝗕𝗮𝗻: `{passed_str}`\n"
                        f"👮‍♂️ 𝗕𝗮𝗻𝗻𝗲𝗱 𝗕𝘆: {admin_mention}\n"
                        "━━━━━━━━━━━━━━━━━━━━━"
                    )
                except Exception as e:
                    logger.error(f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ {e}")
                    return None

        results = await asyncio.gather(*(format_user(u) for u in banned_users))
        filtered = [r for r in results if r]

        await fetching_msg.delete()

        final_text = f"🚫 𝗕𝗮𝗻𝗻𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁 [𝗧𝗼𝘁𝗮𝗹: {len(filtered)}]\n\n" + "\n".join(filtered)

        if len(final_text) <= 4096:
            await client.send_message(
                chat_id=message.chat.id,
                text=final_text,
                reply_to_message_id=message.id,
                disable_web_page_preview=True
            )
        else:
            try:
                html_text = final_text.replace("\n", "<br>")
                page = telegraph.create_page(
                    title="Banned Users List",
                    html_content=html_text
                )
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"📄 𝗕𝗮𝗻𝗻𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁\n\n𝗩𝗶𝗲𝘄 𝗼𝗻 [𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗽𝗵]({page['url']})",
                    reply_to_message_id=message.id,
                    disable_web_page_preview=True
                )
            except:
                file_path = f"Banned_Users_{int(time.time())}.txt"
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(final_text)

                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    caption="📄 𝗕𝗮𝗻𝗻𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁",
                    reply_to_message_id=message.id
                )
                os.remove(file_path)

    except Exception as e:
        try: await fetching_msg.delete()
        except: pass
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`",
            reply_to_message_id=message.id
        )


#Unban User
@Client.on_message(filters.command("unban") & filters.private, group=3)
async def unban_user(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        cmd = message.text.split(maxsplit=1)
        if len(cmd) < 2:
            await client.send_message(
                chat_id=message.chat.id,
                text="❗ 𝗨𝘀𝗮𝗴𝗲:\n\n`/unban user_id`",
                reply_to_message_id=message.id
            )
            return

        user_id = cmd[1].strip()
        if not user_id.isdigit():
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗨𝘀𝗲𝗿 𝗜𝗗!\n\nPlease provide a valid numeric ID.",
                reply_to_message_id=message.id
            )
            return
        user_id = int(user_id)

        user = await database.users.find_one({"user_id": user_id})
        if not user:
            await client.send_message(
                message.chat.id,
                f"❌ 𝗨𝘀𝗲𝗿 𝗜𝗗 `{user_id}` 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝗼𝘂𝗿 𝗱𝗮𝘁𝗮𝗯𝗮𝘀𝗲.",
                reply_to_message_id=message.id
            )
            return

        if not user.get("banned_info", {}).get("status", False):
            await client.send_message(
                message.chat.id,
                f"ℹ️ 𝗨𝘀𝗲𝗿 `{user_id}` 𝗶𝘀 𝗻𝗼𝘁 𝗯𝗮𝗻𝗻𝗲𝗱.",
                reply_to_message_id=message.id
            )
            return


        await database.users.update_one(
            {"user_id": user_id},
            {"$unset": {"banned_info": ""}}
        )

        try:
            user_info = await client.get_users(user_id)
            user_mention = f"[{user_info.first_name}](tg://user?id={user_id})"
        except Exception:
            user_mention = f"`{user_id}`"

        admin_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

        await client.send_message(
            chat_id=message.chat.id,
            text=(
                "✅ 𝗨𝗻𝗯𝗮𝗻𝗻𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!\n\n"
                f"👤 **User:** {user_mention}\n"
                f"⚡️ **User ID:** `{user_id}`\n\n"
                "*🔓 𝗧𝗵𝗲 𝘂𝘀𝗲𝗿 𝗰𝗮𝗻 𝗻𝗼𝘄 𝘂𝘀𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝗮𝗴𝗮𝗶𝗻.*"
            ),
            reply_to_message_id=message.id
        )

        try:
            await client.send_message(
                user_id,
                (
                    "🔓 𝗬𝗼𝘂 𝗛𝗮𝘃𝗲 𝗕𝗲𝗲𝗻 𝗨𝗻𝗯𝗮𝗻𝗻𝗲𝗱!\n\n"
                    "✅ 𝗬𝗼𝘂 𝗰𝗮𝗻 𝗻𝗼𝘄 𝘂𝘀𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝗮𝘀 𝗻𝗼𝗿𝗺𝗮𝗹.\n"
                    "🎉 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗯𝗮𝗰𝗸!"
                )
            )
        except:
            pass

    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`",
            reply_to_message_id=message.id
        )




#Token User List
@Client.on_message(filters.command("count_token") & filters.private, group=3)
async def count_token_users(client, message):
    try:
        if not await check_owner(client, message):
            return

        fetching_msg = await client.send_message(
            chat_id=message.chat.id,
            text="⏳ 𝗙𝗲𝘁𝗰𝗵𝗶𝗻𝗴 𝗧𝗼𝗸𝗲𝗻 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀...",
            reply_to_message_id=message.id
        )

        token_users = await database.users.find({
            'plan.type': 'premium',
            'plan.preset': {'$regex': '^token_'}
        }).to_list(length=None)

        total_tokens_used = await database.tokens.count_documents({'status': 'used'})
        ist = pytz.timezone("Asia/Kolkata")
        now_utc = datetime.now(pytz.utc)
        semaphore = asyncio.Semaphore(20)

        async def process_user(user):
            async with semaphore:
                try:
                    user_id = user['user_id']
                    plan = user.get("plan", {})
                    preset = plan.get("preset", "Unknown")
                    started = plan.get("started_at")
                    expires = plan.get("expiration_at")

                    if isinstance(started, str):
                        started = datetime.fromisoformat(started).replace(tzinfo=pytz.utc)
                    elif started and started.tzinfo is None:
                        started = started.replace(tzinfo=pytz.utc)

                    if isinstance(expires, str):
                        expires = datetime.fromisoformat(expires).replace(tzinfo=pytz.utc)
                    elif expires and expires.tzinfo is None:
                        expires = expires.replace(tzinfo=pytz.utc)

                    start_ist = started.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if started else "N/A"
                    expire_ist = expires.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)" if expires else "♾️ Lifetime"

                    validity = format_duration(expires - started) if started and expires else "♾️ Lifetime"
                    remaining = format_duration(expires - now_utc) if expires else "♾️ Lifetime"

                    token_count = await database.tokens.count_documents({'used_by': user_id})

                    try:
                        user_info = await client.get_users(user_id)
                        mention = f"[{user_info.first_name}](tg://user?id={user_id})"
                    except:
                        mention = f"`{user_id}`"

                    return (
                        f"👤 𝗨𝘀𝗲𝗿: {mention}\n"
                        f"🆔 𝗨𝘀𝗲𝗿 ID: `{user_id}`\n"
                        f"🎟️ 𝗧𝗼𝗸𝗲𝗻: `{preset}`\n"
                        f"📅 𝗦𝘁𝗮𝗿𝘁𝗲𝗱: {start_ist}\n"
                        f"📆 𝗘𝘅𝗽𝗶𝗿𝗲𝘀: {expire_ist}\n"
                        f"⌛️ 𝗩𝗮𝗹𝗶𝗱𝗶𝘁𝘆: {validity}\n"
                        f"⏳ 𝗧𝗶𝗺𝗲 𝗟𝗲𝗳𝘁: {remaining}\n"
                        f"📦 𝗧𝗼𝗸𝗲𝗻𝘀 𝗨𝘀𝗲𝗱: `{token_count}`\n"
                        "———————————————"
                    )
                except Exception as e:
                    logger.error(f"Error token user: {e}")
                    return None

        results = await asyncio.gather(*(process_user(u) for u in token_users))
        results = [r for r in results if r]

        await fetching_msg.delete()

        full_text = (
            f"✅ 𝗧𝗼𝘁𝗮𝗹 𝗧𝗼𝗸𝗲𝗻𝘀 𝗨𝘀𝗲𝗱 (𝗢𝘃𝗲𝗿𝗮𝗹𝗹): `{total_tokens_used}`\n"
            f"🎟️ 𝗧𝗼𝗸𝗲𝗻 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 [𝗧𝗼𝘁𝗮𝗹: {len(results)}]\n\n"
            + "\n".join(results)
        )

        if len(full_text) <= 4096:
            await client.send_message(
                chat_id=message.chat.id,
                text=full_text,
                reply_to_message_id=message.id,
                disable_web_page_preview=True
            )
        else:
            try:
                html = full_text.replace("\n", "<br>")
                page = telegraph.create_page("Token Premium Users", html)
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"📄 𝗧𝗼𝗸𝗲𝗻 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁: [𝗩𝗶𝗲𝘄](https://telegra.ph/{page['path']})",
                    reply_to_message_id=message.id,
                    disable_web_page_preview=True
                )
            except:
                path = f"Token_Users_{int(time.time())}.txt"
                async with aiofiles.open(path, "w") as f:
                    await f.write(full_text)
                await client.send_document(
                    chat_id=message.chat.id,
                    document=path,
                    caption="📄 𝗧𝗼𝗸𝗲𝗻 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁",
                    reply_to_message_id=message.id
                )
                os.remove(path)

    except Exception as e:
        logger.error(f"❌ Error in /count_token: {e}")
        try:
            await fetching_msg.delete()
        except:
            pass
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱:\n`{e}`",
            reply_to_message_id=message.id
        )



#All User List
@Client.on_message(filters.command("count_all") & filters.private, group=3)
async def check_all_users(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        fetching_msg = await client.send_message(
            chat_id=message.chat.id,
            text="⏳ 𝗙𝗲𝘁𝗰𝗵𝗶𝗻𝗴 𝗔𝗹𝗹 𝗨𝘀𝗲𝗿𝘀 𝗜𝗻𝗳𝗼, 𝗽𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁...",
            reply_to_message_id=message.id
        )

        if len(message.command) > 1:
            arg = message.command[1].strip()
            if not arg.isdigit():
                await fetching_msg.delete()
                await client.send_message(
                    chat_id=message.chat.id,
                    text="⚠️ 𝗘𝗿𝗿𝗼𝗿:\n\nPlease provide a **valid numeric user ID** only.",
                    reply_to_message_id=message.id
                )
                return
            specific_user_id = int(arg)

            user_data = await database.users.find_one({'user_id': specific_user_id})
            if not user_data:
                await fetching_msg.delete()
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ 𝗡𝗼 𝘀𝘂𝗰𝗵 𝘂𝘀𝗲𝗿 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝗱𝗮𝘁𝗮𝗯𝗮𝘀𝗲!\n\nID: `{specific_user_id}`",
                    reply_to_message_id=message.id
                )
                return

            all_users = [user_data]
        else:
            all_users = await database.users.find({}).to_list(length=None)

        if not all_users:
            await fetching_msg.delete()
            await client.send_message(chat_id=message.chat.id, text="⚠️ 𝗡𝗼 𝗨𝘀𝗲𝗿𝘀 𝗙𝗼𝘂𝗻𝗱!", reply_to_message_id=message.id)
            return

        ist = pytz.timezone("Asia/Kolkata")
        semaphore = asyncio.Semaphore(20)

        async def format_user(user):
            async with semaphore:
                try:
                    user_id = user.get("user_id")
                    registered_at = user.get("registered_at")
                    plan_info = user.get("plan", {})
                    plan_type = plan_info.get("type", "free")
                    preset = str(plan_info.get("preset", ""))
                    if plan_type == "premium" and preset.startswith("token_"):
                        type = "Token"
                    elif plan_type == "premium":
                        type = "Premium"
                    else:
                        type = "Free"

                    saved_files = user.get("saved_files", 0)
                    banned = user.get("banned_info", {}).get("status", False)

                    user_status = "⛔️ 𝗕𝗮𝗻𝗻𝗲𝗱" if banned else "✅ 𝗔𝗰𝘁𝗶𝘃𝗲"

                    # Format registration date
                    if registered_at:
                        if isinstance(registered_at, str):
                            registered_at = datetime.fromisoformat(registered_at)
                        if registered_at.tzinfo is None:
                            registered_at = pytz.utc.localize(registered_at)
                        registered_at = registered_at.astimezone(ist).strftime("`%d %B %Y - %I:%M:%S %p`") + " (IST)"
                    else:
                        registered_at = "N/A"

                    # Get user mention
                    try:
                        user_info = await client.get_users(user_id)
                        mention = f"[{user_info.first_name}](tg://user?id={user_id})"
                    except Exception:
                        mention = f"`{user_id}`"

                    return (
                        f"👤 𝗨𝘀𝗲𝗿: {mention}\n"
                        f"⚡ 𝗨𝘀𝗲𝗿 𝗜𝗗: `{user_id}`\n"
                        f"🕓 𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱: {registered_at}\n"
                        f"💖 𝗧𝘆𝗽𝗲: `{type}`\n"
                        f"📥 𝗦𝗮𝘃𝗲𝗱 𝗙𝗶𝗹𝗲𝘀: `{saved_files}`\n"
                        f"💠 𝗦𝘁𝗮𝘁𝘂𝘀: {user_status}\n"
                        "———————————————"
                    )
                except Exception as e:
                    logger.error(f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ {e}")
                    return None

        tasks = [format_user(user) for user in all_users]
        results = await asyncio.gather(*tasks)
        user_infos = [r for r in results if r]

        await fetching_msg.delete()

        result_text = f"📋 𝗔𝗹𝗹 𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁 [𝗧𝗼𝘁𝗮𝗹: {len(user_infos)}]\n\n" + "\n".join(user_infos)

        if len(result_text) <= 4096:
            await client.send_message(
                chat_id=message.chat.id,
                text=result_text,
                reply_to_message_id=message.id,
                disable_web_page_preview=True
            )
        else:
            try:
                html_text = result_text.replace("`", "").replace("\n", "<br>")
                page = telegraph.create_page(
                    title="All Users List",
                    html_content=html_text
                )
                link = f"https://telegra.ph/{page['path']}"
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"📄 𝗔𝗹𝗹 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁\n\n𝗩𝗶𝗲𝘄 𝗵𝗲𝗿𝗲: [𝗟𝗶𝗻𝗸]({link})",
                    reply_to_message_id=message.id,
                    disable_web_page_preview=True
                )
            except Exception:
                file_path = f"All_Users_{int(time.time())}.txt"
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(result_text)

                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    caption="📄 𝗔𝗹𝗹 𝗨𝘀𝗲𝗿𝘀 𝗟𝗶𝘀𝘁",
                    reply_to_message_id=message.id
                )
                os.remove(file_path)

    except Exception as e:
        try:
            await fetching_msg.delete()
        except:
            pass
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`",
            reply_to_message_id=message.id
        )



#logs
@Client.on_message(filters.command("logs") & filters.private, group=3)
async def send_logs(client, message: Message):
    try:
        if not await check_owner(client, message):
            return

        log_file = "logs.txt"
        if not os.path.isfile(log_file):
            await message.reply_text("🚫 **Oops! Log file not found!\nPlease check the server..**", quote=True)
            return

        async with aiofiles.open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            logs = await f.read()

        if not logs.strip():
            await message.reply_text("📭 **Log file is empty. Nothing to show.**", quote=True)
            return

        ist = pytz.timezone("Asia/Kolkata")
        timestamp = datetime.now(ist).strftime("%d %b %Y - %I:%M:%S %p")

        try:
            html_text = re.sub(r'[\ud800-\udfff]', '', logs).replace("\n", "<br>")[:38000]
            page = telegraph.create_page(
                title="📘 Bot Logs",
                html_content=html_text[:38000]  # Telegram Telegraph limit is ~40KB
            )

            log_url = f"https://telegra.ph/{page['path']}"
            await message.reply_text(
                text=(
                    "✨ **Your bot logs have been uploaded!**\n\n"
                    "🔍 Click the button below to view them.\n\n"
                    f"🕒 **Time:** `{timestamp}` (IST)\n"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📄 𝗩𝗶𝗲𝘄 𝗟𝗼𝗴𝘀", url=log_url)]]
                ),
                disable_web_page_preview=True,
                quote=True
            )
        except Exception as upload_err:
            logger.error(f"Telegraph error: {upload_err}")
            await client.send_document(
                chat_id=message.chat.id,
                document=log_file,
                caption=(
                    "🧾 **Bot Logs (Full File)**\n"
                    f"🕒 **Fetched at:** `{timestamp}` (IST)"
                ),
                reply_to_message_id=message.id
            )

    except Exception as e:
        await message.reply_text(
            f"⚠️ **Error while fetching logs:**\n\n`{str(e)}`",
            quote=True
        )


# All User Stats
@Client.on_message(filters.command("stats"), group=4)
async def user_stats(client, message):
    try:
        # Owner Check: only allow authorized users
        if not await check_owner(client, message):
            return

        all_users = await database.users.find().to_list(length=None)
        total_users = len(all_users)

        banned_users = sum(1 for user in all_users if user.get('banned') is True)

        premium_users = 0
        token_users = 0

        for user in all_users:
            plan = user.get('plan', {})
            if plan.get('type') == 'premium':
                preset = str(plan.get('preset', ''))
                if preset.startswith('token_'):
                    token_users += 1
                else:
                    premium_users += 1

        free_users = total_users - premium_users - token_users
        total_downloads = sum(user.get('saved_files', 0) for user in all_users)

        msg = await client.send_message(
            chat_id=message.chat.id,
            text="**⏳ Fetching Info...**",
            reply_to_message_id=message.id
        )

        await msg.edit_text(
            "**✨ USER STATISTICS**\n\n"
            f"👥 **Total Users:** `{total_users}`\n"
            f"💎 **Premium Users:** `{premium_users}`\n"
            f"🔑 **Token Users:** `{token_users}`\n"
            f"🆓 **Free Users:** `{free_users}`\n"
            f"⛔ **Banned Users:** `{banned_users}`\n"
            f"📥 **Total Saved:** `{total_downloads}`"
        )

    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ 𝗘𝗿𝗿𝗼𝗿 𝗢𝗰𝗰𝘂𝗿𝗿𝗲𝗱!\n\n❌ `{e}`",
            reply_to_message_id=message.id
        )



# Token Info
@Client.on_message(filters.command("token_auth") & filters.private)
async def token_auth_command(client, message):
    if not await check_owner(client, message):
        return

    config_key = {"key": "Token_Info"}
    config = await database.config.find_one(config_key)

    # Set default config if missing
    if not config:
        config = {
            "key": "Token_Info",
            "token_mode": True,
            "api_url": TOKEN_API_URL,
            "api_key": TOKEN_API_KEY,
            "duration": 1,
            "auth_group_mode": False,
            "group_id": "❌ Not Set",
            "invite_link": "❌ Not Set"
        }
        await database.config.insert_one(config)

    await show_token_panel(client, message)


async def show_token_panel(client, message_or_callback):
    config = await database.config.find_one({"key": "Token_Info"}) or {}
    token_mode = config.get("token_mode", False)
    api_url = config.get("api_url", "❌ Not Set")
    api_key = config.get("api_key", "❌ Not Set")
    duration = config.get("duration", 1)
    auth_mode = config.get("auth_group_mode", False)
    group_id = config.get("group_id", "❌ Not Set")
    invite_link = config.get("invite_link", "❌ Not Set")

    try:
        group_name = (await client.get_chat(group_id)).title if isinstance(group_id, int) else "❓ Unknown"
    except:
        group_name = "❓ Unknown"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔘 Mode: {'✅ ON' if token_mode else '🚫 OFF'}", callback_data="TA_toggle_mode")],
        [
            InlineKeyboardButton("🌐 Set API URL", callback_data="TA_set_api_url"),
            InlineKeyboardButton("🔑 Set API Key", callback_data="TA_set_api_key"),
        ],
        [InlineKeyboardButton("⏱ Set Duration", callback_data="TA_set_duration")],
        [InlineKeyboardButton(f"🛡 Auth Group: {'✅ ON' if auth_mode else '🚫 OFF'}", callback_data="TA_toggle_auth")],
        [
            InlineKeyboardButton("🆔 Set Group ID", callback_data="TA_set_group_id"),
            InlineKeyboardButton("🔗 Set Invite Link", callback_data="TA_set_invite_link"),
        ]
    ])

    text = (
        f"🛠️ **Token Auth Configuration Panel**\n\n"
        f"🔘 **Token Mode:** {'✅ ON' if token_mode else '🚫 OFF'}\n"
        f"🌐 **API URL:** `{api_url}`\n"
        f"🔑 **API Key:** `{api_key}`\n"
        f"⏱ **Duration:** `{duration}` hour(s)\n\n"
        f"🛡 **Auth Group Mode:** {'✅ ON' if auth_mode else '🚫 OFF'}\n"
        f"📛 **Group Name:** `{group_name}`\n"
        f"🆔 **Group ID:** `{group_id}`\n"
        f"🔗 **Invite Link:** {invite_link}"
    )

    # Send or edit based on source
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        msg_id = message_or_callback.reply_to_message.message_id if message_or_callback.reply_to_message else message_or_callback.id
        await client.send_message(
            message_or_callback.chat.id,
            text,
            reply_markup=keyboard,
            reply_to_message_id=msg_id,
            disable_web_page_preview=True
        )

@Client.on_callback_query(filters.regex(r"^TA_(.+)"), group=3)
async def token_auth_callback(client, callback):
    user_id = callback.from_user.id
    action = callback.data.split("_", 1)[1]
    config_key = {"key": "Token_Info"}
    config = await database.config.find_one(config_key) or {}

    if not await check_owner(client, callback):
        return

    async def ask_input(prompt: str):
        ask = await client.send_message(user_id, prompt)
        r = await client.listen(user_id)
        await ask.delete(), await r.delete()
        return r.text.strip()

    if action == "toggle_mode":
        await database.config.update_one(config_key, {"$set": {"token_mode": not config.get("token_mode", False)}}, upsert=True)
        await callback.answer("🔄 Token Mode toggled!", show_alert=True)

    elif action == "toggle_auth":
        await database.config.update_one(config_key, {"$set": {"auth_group_mode": not config.get("auth_group_mode", False)}}, upsert=True)
        await callback.answer("🛡 Auth Group Mode Toggled!", show_alert=True)

    elif action == "set_api_url":
        text = await ask_input("🌐 **Send new API URL:**\n\nSend `unset` to clear.")
        value = text if text != "unset" else "❌ Not Set"
        await database.config.update_one(config_key, {"$set": {"api_url": value}}, upsert=True)
        await callback.answer("✅ API URL Updated!", show_alert=True)

    elif action == "set_api_key":
        text = await ask_input("🔑 **Send new API Key:**\n\nSend `unset` to clear.")
        value = text if text != "unset" else "❌ Not Set"
        await database.config.update_one(config_key, {"$set": {"api_key": value}}, upsert=True)
        await callback.answer("✅ API Key Updated!", show_alert=True)

    elif action == "set_duration":
        text = await ask_input("⏱ **Send Duration in hours (1-168):**")
        if text.isdigit() and 1 <= int(text) <= 168:
            await database.config.update_one(config_key, {"$set": {"duration": int(text)}}, upsert=True)
            await callback.answer("✅ Duration Updated!", show_alert=True)
        else:
            await callback.answer("❌ Invalid duration!", show_alert=True)

    elif action == "set_group_id":
        text = await ask_input("🆔 **Send Group ID (starts with -100):**\n\nSend `unset` to clear.")
        if text == "unset":
            await database.config.update_one(config_key, {"$set": {"group_id": "❌ Not Set"}}, upsert=True)
            await callback.answer("✅ Group ID cleared.", show_alert=True)
        elif text.startswith("-100") and text.lstrip("-").isdigit():
            await database.config.update_one(config_key, {"$set": {"group_id": int(text)}}, upsert=True)
            await callback.answer("✅ Group ID Updated!", show_alert=True)
        else:
            await callback.answer("❌ Invalid Group ID!", show_alert=True)

    elif action == "set_invite_link":
        text = await ask_input("🔗 **Send Invite Link:**\n\nSend `unset` to clear.")
        value = text if text != "unset" else "❌ Not Set"
        await database.config.update_one(config_key, {"$set": {"invite_link": value}}, upsert=True)
        await callback.answer("✅ Invite Link Updated!", show_alert=True)

    await show_token_panel(client, callback)



async def check_owner(client: Client, event) -> bool:
    user_id = event.from_user.id

    if user_id not in OWNER_ID:
        if isinstance(event, Message):
            await client.send_message(
                chat_id=event.chat.id,
                text="🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n🔒 This command is **restricted** to bot admins.",
                reply_to_message_id=event.id
            )
        elif isinstance(event, CallbackQuery):
            await event.answer(
                "🚫 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!\n\n🔒 This action is restricted to bot admins.",
                show_alert=True
            )
        return False
    return True