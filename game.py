import time
from player import Player
from card import *
import random
from collections import deque
from telegram.ext import *
from telegram import *
from games import games
import asyncio


class Game:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.players = deque()
        self.started = False
        self.join_open = True
        self.lobby_end = time.time() + 60
        self.last_minute = None
        self.lobby_job = None
        self.deck = []
        self.discard = [] 
        self.pending_action = []
        self.nope_time = None
        self.nope_lock = asyncio.Lock()
        self.state = "GAME"
        self.curr_action = None
    @property
    def no_players(self):
        return len(self.players)
    def add_player(self, user_id, name):
        if not self.join_open:
            return False, "Lobby closed"
        for p in self.players:
            if p.user_id == user_id:
                return False, "Player already in game"
            elif p.name == name:
                return False, "Player with same name already in game"
            elif self.no_players > 5:
                return False, "5 Player limit reached"
        self.players.append(
            Player(user_id, name)
        )
        return True, None
    @property
    def is_nope_time(self):
        return self.nope_time is not None and time.time() < self.nope_time
    
    def start_nope_time(self):
        self.nope_time = time.time() + 10

    def end_nope_time(self):
        self.nope_time = None
    
    @property
    def nope_time_expired(self):
        return self.nope_time is not None and time.time() >= self.nope_time

    @property
    def current_player(self):
        if not self.players:
            return None
        return self.players[0]
    
    def next_turn(self):
        self.players.rotate(-1)

    def reverse_turn(self):
        self.players.reverse()

    def draw_card(self):
        if not self.deck:
            return None
        return self.deck.pop()
    
    def play_card(self, player, index):
        if index < 0 or index >= len(player.hand):
            return None
        card = player.hand[index]
        player.remove_card(card)
        self.discard.append(card)
        return card
    
    def resolve_card(self, player, card):
        if isinstance(card, SkipCard):
            return "skip"
        if isinstance(card, AttackCard):
            return "attack"
        if isinstance(card, ShuffleCard):
            random.shuffle(self.deck)
            return "shuffle"
        if isinstance(card, SeeTheFutureCard):
            return "future"
        if isinstance(card, FavorCard):
            return "favor"
        if isinstance(card, NopeCard):
            return "nope"
        return None
    
    def resolve_draw(self, player):
        card = self.draw_card()
        if card is None:
            return None
        if isinstance(card, ExplodingKitten):
            return card
        player.add_card(card)
        return card
    
    def resolve_explosion(self, player, kitten):
        if player.has_defuse:
            defuse = player.use_defuse()
            self.discard.append(
                defuse
            )
            self.deck.insert(
                random.randint(0, len(self.deck)),
                kitten
            )
            return "defused"
        player.alive = False
        self.players.remove(player)
        self.discard.append(kitten)
        return "dead"
    
    def add_cards(self, card_type, amount):
        for _ in range(amount):
            self.deck.append(
                card_type()
            )

    def get_player(self, user_id):
        for player in self.players:
            if player.user_id == user_id:
                return player
        return None
    
    def get_player_by_name(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def create_deck(self):
        self.deck = []
        self.add_cards(AttackCard, 4)
        self.add_cards(SkipCard, 4)
        self.add_cards(ShuffleCard, 4)
        self.add_cards(SeeTheFutureCard, 5)
        self.add_cards(FavorCard, 4)
        self.add_cards(NopeCard, 5)
        self.add_cards(DefuseCard, 6)
        self.add_cards(ExplodingKitten, 4)

    def remove_cards(self, card_type):
        removed = []
        remaining = []
        for card in self.deck:
            if isinstance(card, card_type):
                removed.append(card)
            else:
                remaining.append(card)
        self.deck = remaining
        return removed
    
    def setup(self):
        self.create_deck()
        kittens = self.remove_cards(
            ExplodingKitten
        )
        defuses = self.remove_cards(
            DefuseCard
        )
        random.shuffle(self.deck)
        for player in self.players:
            player.add_card(
                defuses.pop()
            )
            for _ in range(4):
                player.add_card(
                    self.deck.pop()
                )
        self.deck.extend(defuses)
        needed = len(self.players) - 1
        for _ in range(needed):
            self.deck.append(
                kittens.pop()
            )
        random.shuffle(self.deck)
        self.discard = []
        start_index = random.randrange(len(self.players))
        self.players.rotate(-start_index)


async def start_game(game, context):
    game.setup()
    chat_id = game.chat_id
    keyboard = [
        [InlineKeyboardButton("Play card", switch_inline_query_current_chat=f"play_{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(game.chat_id, "Game has started!!\nFirst player: " + str(game.current_player), reply_markup=reply_markup)

async def inline_handler(update, context):
    query = update.inline_query.query
    if query.startswith("play_"):
        chat_id = int(query.split("_")[1])
        if chat_id not in games:
            return
        game = games[chat_id]
        player = game.get_player(update.inline_query.from_user.id)
        if player is None:
            return
        if player != game.current_player:
            results = []
            for i, card in enumerate(player.hand):
                results.append(
                    InlineQueryResultCachedSticker(
                        id=str(i),
                        sticker_file_id=card.id,
                        input_message_content=InputTextMessageContent("⏳ Not your turn. Keep your paws off the cards.")
                    )
                )
            await update.inline_query.answer(results, cache_time=0)  
        else:
            results = [
                InlineQueryResultCachedSticker(
                    id="draw",
                    sticker_file_id="CAACAgEAAxkBAAMLaikTJNEw8dYvP7W3nmBf-0CRHC0AAkgKAAJRJklF4sEZeaOP6mU7BA",
                    input_message_content=InputTextMessageContent("Draw")
                )
            ]
            for i, card in enumerate(player.hand):
                results.append(
                    InlineQueryResultCachedSticker(
                        id=str(i),
                        sticker_file_id=card.id,
                        input_message_content=InputTextMessageContent(str(card))
                    )
                )
            await update.inline_query.answer(results, cache_time=0)
    elif query.startswith("attack_"):
        chat_id = int(query.split("_")[1])
        if chat_id not in games:
            return
        game = games[chat_id]
        results = []
        player = game.get_player(update.inline_query.from_user.id)
        if player is None:
            return
        if player != game.current_player:
            return
        if game.state != "ATTACK":
            return
        for p in game.players:
            if p != player:
                results.append(
                    InlineQueryResultArticle(
                        id=str(p.user_id),
                        title=str(p),
                        input_message_content=InputTextMessageContent(f"{p.name}")
                    )
                )
        await update.inline_query.answer(results, cache_time=0)
    elif query.startswith("favor_"):
        chat_id = int(query.split("_")[1])
        if chat_id not in games:
            return
        game = games[chat_id]
        results = []
        player = game.get_player(update.inline_query.from_user.id)
        if player is None:
            return
        if player != game.current_player:
            return
        if game.state != "FAVOR":
            return
        for p in game.players:
            if p != player:
                results.append(
                    InlineQueryResultArticle(
                        id=str(p.user_id),
                        title=str(p),
                        input_message_content=InputTextMessageContent(f"{p.name}")
                    )
                )
        await update.inline_query.answer(results, cache_time=0)
    elif query.startswith("nope_"):
        chat_id = int(query.split("_")[1])
        if chat_id not in games:
            return
        game = games[chat_id]
        results = []
        player = game.get_player(update.inline_query.from_user.id)
        if player is None:
            return
        if game.state != "NOPE":
            return
        if not game.is_nope_time:
            return
        if player == game.current_player:
            return
        nope_card = player.get_card(NopeCard)
        nope_count = player.count_nope
        if nope_card is None:
            return
        results.append(
            InlineQueryResultArticle(
                id="nope",
                title=f"Play Nope card (You have {nope_count})",
                input_message_content=InputTextMessageContent("nope")
            )
        )
        await update.inline_query.answer(results, cache_time=0)

def is_inline_result(func):
    async def wrapper(update, context, *args, **kwargs):
        me = await context.bot.get_me()
        if update.message.via_bot and update.message.via_bot.id==me.id:
            await func(update, context, *args, **kwargs)
    return wrapper

async def card_handler(update, context):
    next_turnable = True
    text = update.message.text
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    player = game.get_player(update.message.from_user.id)
    if player is None:
        return
    if player != game.current_player:
        return
    if text == "Draw":
        result = game.resolve_draw(player)
        if result is None:
            return
        if isinstance(result, ExplodingKitten):
            explosion_result = game.resolve_explosion(player, result)
            if explosion_result == "defused":
                await update.message.reply_text("You drew an Exploding Kitten but defused it with a Defuse card! The kitten has been shuffled back into the deck.")
            elif explosion_result == "dead":
                await update.message.reply_text("You drew an Exploding Kitten and couldn't defuse it. You are out of the game!")
                next_turnable = False
                if len(game.players) == 1:
                    time.sleep(1)
                    await update.message.reply_text(f"🏆 {game.players[0]} survives the chaos and wins!")
                    del games[chat_id]
                    return
            else:
                await update.message.reply_text("You drew an Exploding Kitten but something went wrong with the explosion resolution.")
        else:
            await update.message.reply_text(f"You drew a card.")
        
    else:
        if text == "Attack":
            attackcard = player.get_card(AttackCard)
            if attackcard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(attackcard)
            player.remove_card(attackcard)
            keyboard = [
                [InlineKeyboardButton("Choose victim", switch_inline_query_current_chat=f"attack_{chat_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("⚔️ Choose your victim.\nThey'll have an extra turn to regret it.", reply_markup=reply_markup)
            game.state = "ATTACK"
            return
        elif text == "Defuse":
            defusecard = player.get_card(DefuseCard)
            if defusecard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(defusecard)
            player.remove_card(defusecard)
            await update.message.reply_text("🧯 You burned a Defuse card.\nI hope you know what you're doing.")
        elif text == "Skip":
            skipcard = player.get_card(SkipCard)
            if skipcard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(skipcard)
            player.remove_card(skipcard)
            await update.message.reply_text("🏃 You played Skip.\nSomeone else's problem now.")
        elif text == "Shuffle":
            shufflecard = player.get_card(ShuffleCard)
            if shufflecard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(shufflecard)
            player.remove_card(shufflecard)
            random.shuffle(game.deck)
            await update.message.reply_text("🔀 The deck has been thoroughly scrambled.")
        elif text == "See The Future":
            futurecard = player.get_card(SeeTheFutureCard)
            if futurecard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(futurecard)
            player.remove_card(futurecard)
            top_cards = game.deck[-3:]
            if top_cards:
                await update.message.reply_text("I have sent you the top 3 cards of the deck in DM")
                await context.bot.send_message(chat_id=player.user_id, text="You played a See The Future card! The top cards of the deck are:")
                for card in top_cards:
                    await context.bot.send_sticker(chat_id=player.user_id, sticker=card.id)
            else:
                await update.message.reply_text("You played a See The Future card but the deck is empty!")
        elif text == "Favor":
            favorcard = player.get_card(FavorCard)
            if favorcard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(favorcard)
            player.remove_card(favorcard)
            keyboard = [
                [InlineKeyboardButton("Choose player to favor", switch_inline_query_current_chat=f"favor_{chat_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("🎁 Pick a player.\nThey're about to 'voluntarily' donate a random card.", reply_markup=reply_markup)
            game.state = "FAVOR"
            return
        elif text == "Nope":
            nopecard = player.get_card(NopeCard)
            if nopecard is None:
                await update.message.reply_text("🤨 Nice try. You don't have that card.")
                return
            game.discard.append(nopecard)
            player.remove_card(nopecard)
        else:
            return
    time.sleep(1)
    if next_turnable:
        if player.pending_turns > 0:
            player.pending_turns -= 1
        else:
            game.next_turn()
    keyboard = [
        [InlineKeyboardButton("Play card", switch_inline_query_current_chat=f"play_{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Next player: {game.current_player}, it's your turn!", reply_markup=reply_markup)

async def next_turn(context):
    job = context.job
    game = job.data["game"]
    game.end_nope_time()
    action = job.data['action']
    chat_id = job.data['chat_id']
    player = game.current_player
    if game.curr_action == action:
        game.curr_action = None
        if player is None:
            return
        if action == "attack":
            latest_attack = next((d for d in reversed(game.pending_action) if "attack" in d), None)
            if not latest_attack:
                return
            if player == latest_attack['attack'][0]:
                victim = latest_attack['attack'][1]
            else:
                return
            if victim:
                victim.pending_turns += 1
            for i in range(len(game.pending_action) - 1, -1, -1):
                if "attack" in game.pending_action[i]:
                    game.pending_action.pop(i)
                    break
        elif action == "favor":
            latest_favor = next((d for d in reversed(game.pending_action) if "favor" in d), None)
            if not latest_favor:
                return
            if latest_favor['favor'][0] == player:
                target = latest_favor['favor'][1]
            else:
                return
            if target and target.hand:
                given_card = random.choice(target.hand)
                target.remove_card(given_card)
                player.add_card(given_card)
            for i in range(len(game.pending_action) - 1, -1, -1):
                if "favor" in game.pending_action[i]:
                    game.pending_action.pop(i)
                    break
    elif not game.curr_action:
        pass
    if player.pending_turns > 0:
        player.pending_turns -= 1
    else:
        game.next_turn()
    game.state = "GAME"
    keyboard = [
        [InlineKeyboardButton("Play card", switch_inline_query_current_chat=f"play_{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, f"Next player: {game.current_player}, it's your turn!", reply_markup=reply_markup)

async def attack_handler(update, context):
    text = update.message.text
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    if not game:
        return
    player = game.get_player(update.message.from_user.id)
    if player is None:
        return
    if player != game.current_player:
        return
    victim_name = text
    victim = game.get_player_by_name(victim_name)
    if victim is None:
        await update.message.reply_text("Invalid victim.")
        return
    game.pending_action.append({'attack': [player, victim]})
    game.curr_action = 'attack'
    keyboard = [
        [InlineKeyboardButton("Play Nope", switch_inline_query_current_chat=f"nope_{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚔️ Attack declared!\nAnyone with a Nope has 10 seconds to ruin the fun.", reply_markup=reply_markup)
    game.start_nope_time()
    game.state = "NOPE"
    context.job_queue.run_once(
        next_turn,
        when=10,
        data={
            "game": game,
            "chat_id": chat_id,
            "action": 'attack'
        }
    )
    
async def favor_handler(update, context):
    text = update.message.text
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    if not game:
        return
    player = game.get_player(update.message.from_user.id)
    if player is None:
        return
    if player != game.current_player:
        return
    target_name = text
    target = game.get_player_by_name(target_name)
    
    if target is None:
        await update.message.reply_text("Invalid target.")
        return
    if not target.hand:
        await update.message.reply_text(f"{target} has no cards to give.")
        return
    game.pending_action.append({"favor": [player, target]})
    game.curr_action = 'favor'
    keyboard = [
        [InlineKeyboardButton("Play Nope", switch_inline_query_current_chat=f"nope_{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎁 Favor declared!\nAnyone holding a Nope has 10 seconds to interfere.", reply_markup=reply_markup)
    game.start_nope_time()
    game.state = "NOPE"
    context.job_queue.run_once(
        next_turn,
        when=10,
        data={
            "game": game,
            "chat_id": chat_id,
            "action": 'favor'
        }
    )

@is_inline_result
async def message_handler(update, context):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    if not game:
        return
    state = game.state
    if state=='GAME':
        await card_handler(update, context)
    elif state=='ATTACK':
        await attack_handler(update, context)
    elif state=='FAVOR':
        await favor_handler(update, context)
    elif state=='NOPE':
        await nope_handler(update, context)
    else:
        return
    
async def nope_handler(update, context):
    text = update.message.text
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return
    game = games[chat_id]
    
    async with game.nope_lock:
        if not game or not game.is_nope_time or not game.curr_action:
            await update.message.reply_text("🚫 Too late.\nA Nope already landed, or the Nope window has closed.")
            return
        player = game.get_player(update.message.from_user.id)
        if player is None:
            return
        if player == game.current_player:
            await update.message.reply_text("🙃 You tried to Nope your own card.\nI respect the confidence, but no.")
            return
        nope_card = player.get_card(NopeCard)
        if nope_card is None:
            await update.message.reply_text("You don't have a Nope card.")
            return
        player.remove_card(nope_card)
        game.discard.append(nope_card)
        action = game.curr_action
        for i in range(len(game.pending_action) - 1, -1, -1):
            if action in game.pending_action[i]:
                game.pending_action.pop(i)
                break
        game.end_nope_time()
        game.curr_action = None
        await update.message.reply_text(f"🚫 NOPE!\nThe previous action has been cancelled.")