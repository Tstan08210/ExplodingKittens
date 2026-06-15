from telegram.ext import *
from telegram import *
from game import *
import time
from games import games
from health import *
from threading import Thread
from dotenv import load_dotenv
import os
from handlers import *
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

try:
    load_dotenv()
except:
    pass
finally:
    TOKEN = os.getenv('TOKEN')


async def start(update, context):
    await update.message.reply_text("😼 Exploding Kittens Bot online.\nCreate a game with /newgame or wait for someone reckless enough to do it.")

async def newgame(update, context):
    chat_id = update.effective_chat.id
    if chat_id in games:
        await update.message.reply_text("🐈 A game is already waiting for players.\nJoin it instead of making another.")
        return
    game = Game(chat_id)
    games[chat_id] = game
    await update.message.reply_text("🎉 A new game of Exploding Kittens has begun!\n🃏 Use /join to enter.\n⏳ The lobby closes in 60 seconds.")
    game.lobby_job = context.job_queue.run_repeating(
        lobby_tick, 
        interval = 5, 
        first = 5,
        chat_id = chat_id
    )


async def lobby_tick(context):
    chat_id = context.job.chat_id
    game = games.get(chat_id)
    if game is None:
        context.job.schedule_removal()
        return
    remaining = int(game.lobby_end - time.time())
    if remaining <= 0:
        game.join_open = False
        context.job.schedule_removal()
        if len(game.players) < 2:
            await context.bot.send_message(
                chat_id,
                "💀 Game cancelled.\nTurns out two cats are the minimum requirement for chaos."
            )
            del games[chat_id]
            return
        game.started = True
        await context.bot.send_message(
            chat_id,
            "🔒 Lobby closed!\n😼 The kittens have been shuffled.\n🎮 Let the chaos begin!"
        )
        await start_game(game, context)
        return
    # Minute reminders
    minute = remaining // 60
    if minute > 0 and minute != game.last_minute:
        game.last_minute = minute
        await context.bot.send_message(
            chat_id,
            f"⏰ {minute} minute{'s' if minute != 1 else ''} left to join!\n👥 Players: {len(game.players)}"
        )

async def extend(update, context):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    if not game.join_open:
        return
    game.lobby_end += 60
    await update.message.reply_text(
        "⏰ Someone demanded more victims.\nLobby extended by 1 minute!"
    )

@admin_only
async def forcestart(update, context):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    if game.started:
        return
    if len(game.players) < 2:
        await context.bot.send_message(
            chat_id,
            "💀 Game cancelled.\nTurns out two cats are the minimum requirement for chaos."
        )
        del games[chat_id]
        game.lobby_job.schedule_removal()
        return

    game.join_open = False
    game.started = True

    if game.lobby_job:
        game.lobby_job.schedule_removal()

    await update.message.reply_text(
        "🚀 Patience has run out.\nThe game begins now!"
    )
    await start_game(game, context)


async def join(update, context):
    chat_id = update.effective_chat.id
    userid = update.effective_user.id
    name = update.effective_user.first_name
    if chat_id not in games:
        await update.message.reply_text("🫠 There's no game running here.\nUse /newgame to start one.")
        return
    try:
        await context.bot.send_message(update.effective_user.id, "You have joined a game")
    except:
        await update.message.reply_text("I don't know you yet, did you start the bot?")
        return
    game = games[chat_id]
    success, error = game.add_player(userid, name)
    if not success:
        await update.message.reply_text(error)
        return
    await update.message.reply_text(f"✅ {name} has joined the impending disaster.")


if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newgame", newgame))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("extend", extend))
    application.add_handler(CommandHandler("forcestart", forcestart))
    application.add_handler(InlineQueryHandler(inline_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Game running")
    Thread(target=run_app).start()
    application.run_polling()