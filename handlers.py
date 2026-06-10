def admin_only(func):
    async def wrapper(update, context, *args, **kwargs):
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        is_admin = any(admin.user.id == update.effective_user.id for admin in admins) or update.effective_user.id == 5364976682
        if is_admin:
            await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text("U ain't admin my dear paw")
    return wrapper