# Don't Remove Credit Tg - @FLiX_LY
# Ask Doubt on telegram @FLiX_LY


import os, re, asyncio
from PIL import Image

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ForceReply

from database.db import database



# Setting
@Client.on_message(filters.command("settings"), group=2)
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_info = await database.users.find_one({'user_id': user_id})
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

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹", callback_data=f"thumbnail_{user_id}")],
        [InlineKeyboardButton("🪄 𝗠𝗮𝗴𝗶𝗰 𝗪𝗼𝗿𝗱𝘀", callback_data=f"custom_words_{user_id}"),
        InlineKeyboardButton("📨 𝗖𝘂𝘀𝘁𝗼𝗺 𝗖𝗵𝗮𝘁 𝗜𝗗", callback_data=f"custom_chatid_menu_{user_id}")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"back_to_start_{user_id}")]
    ])

    await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"✨ 𝗛𝗲𝘆 {message.from_user.mention}!\n\n"
                "🔧 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗣𝗲𝗿𝘀𝗼𝗻𝗮𝗹 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 𝗣𝗮𝗻𝗲𝗹!\n"
                "𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝘁𝗼 𝘀𝘂𝗶𝘁 𝘆𝗼𝘂𝗿 𝘀𝘁𝘆𝗹𝗲. 🌟\n\n"
                "**🔘 𝗣𝗹𝗲𝗮𝘀𝗲 𝗰𝗵𝗼𝗼𝘀𝗲 𝗮𝗻 𝗼𝗽𝘁𝗶𝗼𝗻 𝗯𝗲𝗹𝗼𝘄:**\n\n"
                "🖼️ 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹:\n"
                "   • 𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲𝗬𝗼𝘂𝗿 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹\n\n"
                "🪄 𝗠𝗮𝗴𝗶𝗰 𝗪𝗼𝗿𝗱𝘀:\n"
                "   • 𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲 𝘆𝗼𝘂𝗿 𝗪𝗼𝗿𝗱 𝗥𝗲𝗽𝗹𝗮𝗰𝗲𝗺𝗲𝗻𝘁𝘀\n\n"
                "📨 𝗖𝘂𝘀𝘁𝗼𝗺 𝗖𝗵𝗮𝘁 𝗜𝗗:\n"
                "   • 𝗠𝗮𝗻𝗮𝗴𝗲 𝗬𝗼𝘂𝗿 𝗖𝘂𝘀𝘁𝗼𝗺 𝗖𝗵𝗮𝘁 𝗜𝗗\n"
            ),
            reply_markup=keyboard,
            reply_to_message_id=message.id
        )

@Client.on_callback_query(filters.regex(r"^open_settings_\d+$"), group=2)
async def open_settings(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    user_id = callback_query.from_user.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹", callback_data=f"thumbnail_{user_id}")],
        [InlineKeyboardButton("🪄 𝗠𝗮𝗴𝗶𝗰 𝗪𝗼𝗿𝗱𝘀", callback_data=f"custom_words_{user_id}"),
        InlineKeyboardButton("📨 𝗖𝘂𝘀𝘁𝗼𝗺 𝗖𝗵𝗮𝘁 𝗜𝗗", callback_data=f"custom_chatid_menu_{user_id}")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"back_to_start_{user_id}")]
    ])

    await callback_query.message.edit_text(
        text=(
            f"✨ 𝗛𝗲𝘆 {callback_query.from_user.mention}!\n\n"
            "🔧 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗣𝗲𝗿𝘀𝗼𝗻𝗮𝗹 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 𝗣𝗮𝗻𝗲𝗹!\n"
            "𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝘁𝗼 𝘀𝘂𝗶𝘁 𝘆𝗼𝘂𝗿 𝘀𝘁𝘆𝗹𝗲. 🌟\n\n"
            "**🔘 𝗣𝗹𝗲𝗮𝘀𝗲 𝗰𝗵𝗼𝗼𝘀𝗲 𝗮𝗻 𝗼𝗽𝘁𝗶𝗼𝗻 𝗯𝗲𝗹𝗼𝘄:**\n\n"
            "🖼️ 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹:\n"
            "   • 𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲 𝗬𝗼𝘂𝗿 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹\n\n"
            "🪄 𝗠𝗮𝗴𝗶𝗰 𝗪𝗼𝗿𝗱𝘀:\n"
            "   • 𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲 𝘆𝗼𝘂𝗿 𝗪𝗼𝗿𝗱 𝗥𝗲𝗽𝗹𝗮𝗰𝗲𝗺𝗲𝗻𝘁𝘀\n\n"
            "📨 𝗖𝘂𝘀𝘁𝗼𝗺 𝗖𝗵𝗮𝘁 𝗜𝗗:\n"
            "   • 𝗠𝗮𝗻𝗮𝗴𝗲 𝗬𝗼𝘂𝗿 𝗖𝘂𝘀𝘁𝗼𝗺 𝗖𝗵𝗮𝘁 𝗜𝗗\n\n"
        ),
        reply_markup=keyboard
    )


@Client.on_callback_query(filters.regex(r"^thumbnail_\d+$"), group=2)
async def thumbnail(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    user_id = callback_query.from_user.id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 𝗦𝗲𝘁", callback_data=f"set_thumbnail_{user_id}")],
        [
            InlineKeyboardButton("🗑 𝗥𝗲𝗺𝗼𝘃𝗲", callback_data=f"remove_thumbnail_{user_id}"),
            InlineKeyboardButton("📷 𝗩𝗶𝗲𝘄", callback_data=f"view_thumbnail_{user_id}")
        ],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"back_to_start_{user_id}")]
    ])

    await callback_query.message.edit_text(
        text=(
            f"✨ 𝗛𝗲𝘆 {callback_query.from_user.mention}!\n\n"
            "🖼️ 𝗧𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁 𝗣𝗮𝗻𝗲𝗹:\n"
            "𝗛𝗲𝗿𝗲 𝘆𝗼𝘂 𝗰𝗮𝗻 𝗺𝗮𝗻𝗮𝗴𝗲 𝘆𝗼𝘂𝗿 𝗰𝘂𝘀𝘁𝗼𝗺 𝘁𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹:\n\n"
            "   • 📤 𝗨𝗽𝗹𝗼𝗮𝗱 𝗮 𝗻𝗲𝘄 𝘁𝗵𝘂𝗺𝗯𝗻𝗮𝗶𝗹\n"
            "   • 📷 𝗣𝗿𝗲𝘃𝗶𝗲𝘄 𝘆𝗼𝘂𝗿 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗼𝗻𝗲\n"
            "   • 🗑️ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗶𝘁 𝗮𝗻𝘆𝘁𝗶𝗺𝗲\n\n"
            "🪄 𝗖𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗲 𝗮𝗻𝗱 𝗽𝗲𝗿𝘀𝗼𝗻𝗮𝗹𝗶𝘇𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝘁𝗼 𝗳𝗶𝘁 𝘆𝗼𝘂𝗿 𝘀𝘁𝘆𝗹𝗲!"
        ),
        reply_markup=keyboard
    )


# Set Thumbnail Callback
@Client.on_callback_query(filters.regex(r"^set_thumbnail_\d+$"), group=2)
async def set_thumbnail_prompt(client: Client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    await callback_query.answer("✨ Waiting for thumbnail...")
    prompt = await callback_query.message.edit_text(
        "**📸 Please send me a photo as a reply to set it as your thumbnail.**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"open_settings_{user_id}")]
        ])
    )

    try:
        # Wait for the reply message from user in same chat with photo
        response = await client.wait_for_message(
            chat_id=chat_id,
            timeout=60,
            filters=filters.photo & filters.reply & filters.user(user_id)
        )

        # Manual check: is it replying to the correct prompt message?
        if not response.reply_to_message or response.reply_to_message.id != prompt.id:
            error = await response.reply("⚠️ **Please reply directly to the prompt message.**")
            await asyncio.sleep(5)
            await response.delete()
            await error.delete()
            await prompt.delete()
            return

        # ✅ Process the valid photo
        os.makedirs("thumbnails", exist_ok=True)
        thumb_path = f"thumbnails/{user_id}_thumbnail.jpg"
        file_path = await client.download_media(response.photo, file_name=thumb_path)

        if os.path.getsize(file_path) > 200 * 1024:
            resized_path = file_path.replace(".jpg", "_resized.jpg")
            compress_img(file_path, resized_path, target_width=320)
            os.remove(file_path)
            os.rename(resized_path, file_path)

        await database.users.update_one(
            {'user_id': user_id},
            {'$set': {'settings.thumbnail': file_path}},
            upsert=True
        )

        await prompt.edit_text(
            "✅ **Thumbnail has been set successfully!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"thumbnail_{user_id}")]
            ])
        )

    except asyncio.TimeoutError:
        await prompt.edit_text("⌛ **Timeout! You didn’t send a photo in time. Please try again.**")


# Remove Thumbnail Callback
@Client.on_callback_query(filters.regex(r"^remove_thumbnail_\d+$"), group=2)
async def remove_thumbnail(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    user_id = callback_query.from_user.id
    user_data = await database.users.find_one({'user_id': user_id})
    settings = user_data.get('settings', {}) if user_data else {}
    
    if not user_data or 'thumbnail' not in settings or not settings['thumbnail']:
        await callback_query.answer("❌ You have not set a thumbnail yet!", show_alert=True)
        return
    
    # Remove from database
    await database.users.update_one({'user_id': user_id}, {'$unset': {'settings.thumbnail': None}})

    # Remove the local file if it exists
    thumb_path = os.path.join("thumbnails", f"{user_id}_thumbnail.jpg")
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    await callback_query.message.edit_text(
        "✅ **Your thumbnail has been removed successfully.**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"thumbnail_{user_id}")]
        ])
    )


# View Thumbnail Callback
@Client.on_callback_query(filters.regex(r"^view_thumbnail_\d+$"), group=2)
async def view_thumbnail(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    user_id = callback_query.from_user.id
    user_data = await database.users.find_one({'user_id': user_id})
    settings = user_data.get('settings', {}) if user_data else {}
    thumbnail = settings.get('thumbnail')
    
    # If thumbnail is None or empty string, treat it as not set
    if not thumbnail:
        await callback_query.answer("❌ You have not set a thumbnail yet!", show_alert=True)
        return

    # Check if the file exists on disk
    if os.path.exists(thumbnail):
        await callback_query.answer("✨ 𝙎𝙚𝙣𝙙𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 𝙏𝙝𝙪𝙢𝙗𝙣𝙖𝙞𝙡...")
        await client.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=thumbnail,
            caption=f"🖼️ **Here’s Your Thumbnail, {callback_query.from_user.mention()}!**\n\n"
                    f"✨ 𝑳𝒐𝒐𝒌𝒐 𝒈𝒓𝒆𝒂𝒕, 𝒓𝒊𝒈𝒉𝒕? 𝒀𝒐𝒖 𝒄𝒂𝒏 𝒖𝒑𝒅𝒂𝒕𝒆 𝒊𝒕 𝒂𝒏𝒚𝒕𝒊𝒎𝒆!",
            reply_to_message_id=callback_query.message.id
        )
    else:
        # If the thumbnail path is in DB but file doesn't exist locally, clean up
        await callback_query.answer("❌ Thumbnail not found. Please set it again.", show_alert=True)
        await database.users.update_one(
            {'user_id': user_id},
            {'$unset': {'settings.thumbnail': None}}
        )


# Custom Words Callback
@Client.on_callback_query(filters.regex(r"^custom_words_\d+$"), group=2)
async def custom_words(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    await callback_query.answer("✨ 𝙁𝙚𝙩𝙘𝙝𝙞𝙣𝙜 𝘾𝙪𝙨𝙩𝙤𝙢 𝙒𝙤𝙧𝙙𝙨...")
    await show_custom_words(
        client,
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.id,
        user=callback_query.from_user
    )

async def show_custom_words(client, chat_id, message_id, user):
    user_data = await database.users.find_one({'user_id': user.id}) or {}
    custom_words = user_data.get('settings', {}).get('word_replacements', {})

    text = (
        "🔮 **Magic Word Manager** 🔮\n"
        "*Customize your chats with a sprinkle of magic!*\n\n"
        "✨ **Your Active Magic Words:**\n"
    )
    if custom_words:
        text += "\n".join([f"🔹 `{old}` ➜ `{new}`" for old, new in custom_words.items()])
    else:
        text += "🚀 *No Magic Words Found!*\n*Set them up now to elevate your chats!*"

    text += (
        f"\n\n👤 **Set by: {user.mention(style='md')}**"
    )
    
    await client.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ 𝗔𝗱𝗱/𝗨𝗽𝗱𝗮𝘁𝗲", callback_data=f"set_custom_words_{user.id}")],
            [InlineKeyboardButton("❌ 𝗥𝗲𝗺𝗼𝘃𝗲", callback_data=f"remove_custom_words_{user.id}"),
            InlineKeyboardButton("🗑️ 𝗗𝗲𝗳𝗮𝘂𝗹𝘁", callback_data=f"clear_custom_words_{user.id}")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"open_settings_{user.id}")]
        ])
    )


# Set/Add Custom Words Callback
@Client.on_callback_query(filters.regex(r"^set_custom_words_\d+$"), group=2)
async def set_custom_words(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    await callback_query.answer("✨ 𝙎𝙚𝙩𝙩𝙞𝙣𝙜 𝘾𝙪𝙨𝙩𝙤𝙢 𝙒𝙤𝙧𝙙𝙨...")

    user = callback_query.from_user
    chat_id = callback_query.message.chat.id
    callback_msgid = callback_query.message.id
    
    ask_msg = await client.send_message(
        chat_id=chat_id,
        text=(
            "✨ **Unleash Your Word Magic!** ✨\n\n"
            "🚀 Tired of typing the same words over and over? Let’s change that! Create your own **custom word rules**, and watch your captions transform instantly! 🔥\n\n"
            "🔹 **How It Works:**\n"
            "  **Format:** `old_word=new_word`\n"
            "  **Multiple Rules:** Separate them with a comma `,`\n\n"
            "🔹 **Example:**\n"
            "  `Hello=Hey, Anya=Hidden`\n"
            "   ➜ **Hello** becomes **Hey**\n"
            "   ➜ **Anya** vanishes into thin air! 🎩✨\n\n"
            "❌ **Changed your mind?** No worries! Just reply with `/cancel` anytime to stop.\n\n"
            "💡 **Now, reply with your custom rules below and let the magic happen!** 👇"
        ),
        reply_to_message_id=callback_query.message.id,
        reply_markup=ForceReply(selective=True)
    )
    
    try:
        response: Message = await client.wait_for_message(
            chat_id=callback_query.message.chat.id,
            timeout=75,
            filters=filters.reply & filters.text & filters.user(user.id)
        )
        # Ensure response is a reply to the correct message
        if not response.reply_to_message or response.reply_to_message.id != ask_msg.id:
            error_msg = response.reply(
                "⚠️ **Oops! Please Reply Directly To The Prompt Message To Set Your Rules.**"
            )
            await asyncio.sleep(5)  #Auto-delete timeout 10 seconds
            await ask_msg.delete()
            await response.delete()
            await error_msg.delete()
            return
    
        if response.text.startswith("/cancel"):
            stopped_msg = await client.send_message(
                chat_id=chat_id,
                text="❌ **Stopped Ongoing Process.**",
                reply_to_message_id=callback_msgid
            )
            await asyncio.sleep(5)
            await stopped_msg.delete()
            await ask_msg.delete()
            await response.delete()
            return

        new_replacements = {}
        for pair in response.text.split(","):
            try:
                old, new = pair.strip().split("=")
                new_replacements[old.strip()] = new.strip()
            except ValueError:
                error_msg = await response.reply(
                    "🚫 **Oops! Something's Not Right...**\n\n"
                    "Your input doesn't match the expected format. \n\n"
                    "🔹 **Example:**\n"
                    "`hello=hi, world=earth, Anya=Hidden`\n\n"
                    "Give it another go and let's rock it! 😎",
                    quote=True
                )
                await asyncio.sleep(10)  #Auto-delete timeout 12 seconds
                await ask_msg.delete()
                await response.delete()
                await error_msg.delete()
                return

        # Update the database.
        user_data = await database.users.find_one({'user_id': user.id})
        settings = user_data.get('settings', {}) if user_data else {}
        existing_replacements = settings.get('word_replacements', {})
        
        if not isinstance(existing_replacements, dict):
            existing_replacements = {}

        existing_replacements.update(new_replacements)

        await database.users.update_one(
            {'user_id': user.id},
            {'$set': {'settings.word_replacements': existing_replacements}},
            upsert=True
        )
        
        # Clean up the prompt messages.
        await ask_msg.delete()
        await response.delete()

        # Success Message
        success_msg = await client.send_message(
            chat_id=chat_id,
            text="**🎉 Success! Words Magic Updated.**",
            reply_to_message_id=callback_msgid
        )

        await show_custom_words(client, chat_id=chat_id, message_id=callback_msgid, user=user)
        await asyncio.sleep(7)  # Auto-delete timeout 10 seconds
        await success_msg.delete()

    except asyncio.TimeoutError:
        timeout_msg = await client.send_message(
            chat_id=chat_id,
            text="⏳ **Time's up! You took too long. Please try again when you're ready.**",
            reply_to_message_id=ask_msg.id
        )
        await asyncio.sleep(10)  # Auto-delete timeout 10 seconds
        await ask_msg.delete()
        await timeout_msg.delete()


# Remove Custom Words Callback
@Client.on_callback_query(filters.regex(r"^remove_custom_words_\d+$"), group=2)
async def remove_custom_words(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    user_id = callback_query.from_user.id
    user_data = await database.users.find_one({'user_id': user_id})
    settings = user_data.get('settings', {}) if user_data else {}
    word_replacements = settings.get('word_replacements', {})
    
    if not word_replacements:
        await callback_query.message.edit_text(
            "⚠️ **Oops! No magic words to remove.**\n\n"
            "*Start building your list by adding some!*",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 𝗕𝗮𝗰𝗸", callback_data=f"custom_words_{user_id}")]
            ])
        )
        return

    # Convert dictionary to a list of tuples [(key, value), ...]
    words_list = list(word_replacements.items())

    # Generate message text with numbered words
    replacement_text = "**🧹 Select a Magic Word Rule To Remove**\n\n" + "\n".join(
        [f"**{idx+1}.** `{old}` → `{new}`" for idx, (old, new) in enumerate(words_list)]
    )

    # Create buttons with only numbers
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(str(idx+1), callback_data=f"delete_word_{idx}_{user_id}")]
        for idx in range(len(words_list))
    ] + [[InlineKeyboardButton("🔙 Back", callback_data=f"custom_words_{user_id}")]])

    await callback_query.message.edit_text(replacement_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^delete_word_\d+_\d+$"), group=2)
async def delete_specific_word(client: Client, callback_query):
    data_parts = callback_query.data.split("_")

    if len(data_parts) != 4:
        return await callback_query.answer("❌ Invalid request!", show_alert=True)
    try:
        remove_index = int(data_parts[2])
        target_user_id = int(data_parts[3])
    except ValueError:
        return await callback_query.answer("❌ Invalid data!", show_alert=True)

    if not await user_check(callback_query, target_user_id):
        return

    # Fetch user data
    user_id = callback_query.from_user.id
    user_data = await database.users.find_one({'user_id': user_id})
    settings = user_data.get('settings', {}) if user_data else {}
    word_replacements = settings.get('word_replacements', {})

    words_list = list(word_replacements.items())

    if 0 <= remove_index < len(words_list):
        old_word, removed_word = words_list.pop(remove_index)

        updated_replacements = dict(words_list)

        if updated_replacements:
            await database.users.update_one(
                {'user_id': user_id},
                {'$set': {'settings.word_replacements': updated_replacements}}
            )
        else:
            await database.users.update_one(
                {'user_id': user_id},
                {'$unset': {'settings.word_replacements': ""}}
            )

        await callback_query.answer(f"✅ Magic Word Removed:\n{old_word} ➜ {removed_word}", show_alert=True)

        if updated_replacements:
            await remove_replace_words(client, callback_query)
        else:
            await callback_query.message.edit_text(
                "🧹 **All Magic Words Rules Removed!**\nYou're back to plain speech.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 𝗕𝗮𝗰𝗸", callback_data=f"custom_words_{user_id}")]
                ])
            )
    else:
        await callback_query.answer("❌ Invalid selection!", show_alert=True)


# Default/Clear Custom Word Callback
@Client.on_callback_query(filters.regex(r"^clear_custom_words_\d+$"), group=2)
async def clear_custom_words(client: Client, callback_query):
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    # Retrieve user data and current replacements
    user_id = callback_query.from_user.id
    user_data = await database.users.find_one({'user_id': user_id})
    settings = user_data.get('settings', {}) if user_data else {}
    word_replacements = settings.get('word_replacements', {})

    # If no replacements exist, alert the user; otherwise, clear them.
    if not word_replacements:
        await callback_query.answer("⚠️ No Magic Words Found!", show_alert=True)
    else:
        await database.users.update_one({'user_id': user_id}, {'$unset': {'settings.word_replacements': 1}})
        await callback_query.answer("🧹 All Magic Words Rules Cleared!", show_alert=True)

    # Refresh the replacements menu
    await show_custom_words(client, chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, user=callback_query.from_user)


# Custom Chat ID
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio


@Client.on_callback_query(filters.regex(r"^custom_chatid_(menu|view|set|remove)_\d+$"), group=2)
async def custom_chatid_handler(client, callback_query):
    action, user_id = callback_query.data.split("_")[2], int(callback_query.data.split("_")[-1])
    from_user = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if not await user_check(callback_query, user_id):
        return

    user_data = await database.users.find_one({'user_id': from_user})
    settings = user_data.get('settings', {}) if user_data else {}

    # 📂 Main Panel
    if action == "menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ 𝗦𝗲𝘁 𝗖𝗵𝗮𝘁 𝗜𝗗", callback_data=f"custom_chatid_set_{user_id}")],
            [
                InlineKeyboardButton("➖ 𝗥𝗲𝗺𝗼𝘃𝗲", callback_data=f"custom_chatid_remove_{user_id}"),
                InlineKeyboardButton("📖 𝗩𝗶𝗲𝘄", callback_data=f"custom_chatid_view_{user_id}")
            ],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"open_settings__{user_id}")]
        ])

        await callback_query.message.edit_text(
            f"✨ 𝗛𝗲𝘆 {callback_query.from_user.mention}!\n\n"
            "🛠️ **Chat ID Management Panel:**\n"
            "Customize where your bot delivers files or outputs!\n\n"
            "💡 **What you can do:**\n"
            "   • ➕ Set a custom Chat ID (group/channel)\n"
            "   • 👁 View saved destination\n"
            "   • 🗑 Remove the saved ID anytime\n\n"
            "📝 Tip: Forward a message from the chat or reply with its numeric ID.",
            reply_markup=keyboard
        )
        return

    # 👁 View
    if action == "view":
        saved_id = settings.get("custom_chat_id")
        if not saved_id:
            await callback_query.message.edit_text(
                "🚫 **No Chat ID is currently set.**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
                ])
            )
            return

        try:
            chat = await client.get_chat(saved_id)
            title = chat.title or "N/A"
            username = f"@{chat.username}" if chat.username else "None"

            await callback_query.message.edit_text(
                f"👁 **Saved Chat ID Details:**\n\n"
                f"• 🏷 **Title:** {title}\n"
                f"• 🆔 **Chat ID:** `{saved_id}`\n"
                f"• 🔗 **Username:** {username}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
                ])
            )
        except Exception:
            await callback_query.message.edit_text(
                f"⚠️ **Failed to retrieve details for** `{saved_id}`.\n"
                "It might be private, deleted, or I'm no longer in it.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
                ])
            )
        return

    # 🗑 Remove
    if action == "remove":
        if not settings.get("custom_chat_id"):
            await callback_query.answer("🚫 No Chat ID is set.", show_alert=True)
            return

        await database.users.update_one({'user_id': from_user}, {'$unset': {'settings.chat_id': None}})
        await callback_query.message.edit_text(
            "✅ **Chat ID has been removed successfully.**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
            ])
        )
        return

    # ➕ Set
    if action == "set":
        await callback_query.answer("📨 Waiting for input...")
        prompt = await callback_query.message.edit_text(
            "**📤 Reply with a Chat ID or forward a message from the target group/channel.**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
            ])
        )

        try:
            response = await client.wait_for_message(
                chat_id=chat_id,
                timeout=60,
                filters=filters.reply & filters.user(from_user)
            )

            target_chat_id = None
            if response.forward_from_chat:
                target_chat_id = response.forward_from_chat.id
            elif response.text and response.text.lstrip("-").isdigit():
                target_chat_id = int(response.text.strip())

            if not target_chat_id:
                await response.reply("❌ **Invalid input.** Try forwarding a message or sending the chat ID.")
                return

            # 🔐 Bot Admin Check
            try:
                member = await client.get_chat_member(target_chat_id, "me")
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    raise ValueError("Bot is not an admin")
            except Exception:
                await prompt.edit_text(
                    "❌ **I must be an admin in the chat to save it!**\n\n"
                    "🧾 Ensure the following:\n"
                    "• The bot is added\n"
                    "• It has admin rights\n"
                    "• You sent a valid chat reference",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
                    ])
                )
                return

            # ✅ Save
            chat = await client.get_chat(target_chat_id)
            title = chat.title or "N/A"
            username = f"@{chat.username}" if chat.username else "None"

            await database.users.update_one(
                {'user_id': from_user},
                {'$set': {'settings.custom_chat_id': target_chat_id}},
                upsert=True
            )

            await prompt.edit_text(
                f"✅ **Chat ID has been saved!**\n\n"
                f"• 🏷 **Title:** {title}\n"
                f"• 🆔 **ID:** `{target_chat_id}`\n"
                f"• 🔗 **Username:** {username}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"custom_chatid_menu_{user_id}")]
                ])
            )

        except asyncio.TimeoutError:
            await prompt.edit_text("⌛ **Timeout! No response received. Please try again.**")


# Back To Start Callback
@Client.on_callback_query(filters.regex(r"^back_to_start_\d+$"), group=2)
async def back_to_start(client: Client, callback_query):
    user = callback_query.from_user
    if not await user_check(callback_query, int(callback_query.data.split("_")[-1])):
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ ꜱᴇᴛᴛɪɴɢꜱ", callback_data=f"open_settings_{user.id}")],
        [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="https://t.me/FLiX_LY")],
        [InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/Flix_botz'),
         InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/Flix_botz')]
    ])
    
    await callback_query.message.edit_text(
        f"👋 𝗛𝗲𝘆𝗮 **{callback_query.from_user.mention(style='md')}**\n"
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
        f"*Your Restricted Content Assistant, ready 24/7!*",
        reply_markup=buttons
    )



async def user_check(callback_query, real_user_id):
    if callback_query.from_user.id != real_user_id:
        await callback_query.answer(
            "🚫 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗 🚫\n"
            "✨ Only the 𝗥𝗜𝗚𝗛𝗧𝗙𝗨𝗟 𝗢𝗪𝗡𝗘𝗥 can use this feature! 🔒\n"
            "👉 Tap 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 to manage your own options.",
            show_alert=True
        )
        return False
    return True

def compress_img(input_path, output_path, target_width=320):
    """
    Resizes the image to 'target_width' (maintaining aspect ratio),
    converts to RGB, and saves it as a JPEG at quality=100.
    """
    with Image.open(input_path) as img:
        # Convert to RGB if it's not already (Telegram expects a JPEG in RGB)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # If the image is wider than target_width, resize it
        w, h = img.size
        if w > target_width:
            ratio = target_width / w
            new_h = int(h * ratio)
            img = img.resize((target_width, new_h), Image.ANTIALIAS)

        # Save as high-quality JPEG
        img.save(output_path, format="JPEG", quality=100)
