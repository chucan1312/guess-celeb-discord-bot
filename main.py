import discord
import logging
from dotenv import load_dotenv
import os
import random

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()

bot = discord.Bot(intents=intents)
# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='discord.log',
    filemode='w',
    encoding='utf-8'
)

@bot.event
async def on_ready():
    print(f"Successfully connected to {len(bot.guilds)} servers")

active_games={} # key = server id, value = {"category": str, "current_answer": str, "full_pic": jpg, "scores": dictionary}

def pick_random_celebrity(category):
    if (category == "Random"):
        outerFolder = "celebs"
        folder = "celebs/" + random.choice(os.listdir(outerFolder))
    else: folder = f"celebs/{category}"
    celeb = os.path.join(folder, random.choice(os.listdir(folder)))

    path_feature = os.path.join(celeb, "feature.jpg")
    path_full = os.path.join(celeb, "full.jpg")
    answer = os.path.basename(celeb)

    return path_feature, path_full, answer

class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # No timeout

    async def start_game(self, interaction, category):
        path_feature, path_full, answer = pick_random_celebrity(category)
        # Save game state
        active_games[interaction.channel.id] = {"category": category, "current_answer": answer, "full_pic": path_full, "scores": {}}
        await interaction.response.send_message(
            f"Category chosen: {category}. Guess who this is:",
            file=discord.File(path_feature)
        )

    @discord.ui.button(label="Singer", style=discord.ButtonStyle.primary)
    async def singer_button(self, button, interaction):
        await self.start_game(interaction, "Singer")

    @discord.ui.button(label="Actor", style=discord.ButtonStyle.primary)
    async def actor_button(self, button, interaction):
        await self.start_game(interaction, "Actor")

    @discord.ui.button(label="Random", style=discord.ButtonStyle.primary)
    async def random_button(self, button, interaction):
        await self.start_game(interaction, "Random")

@bot.slash_command(name="play", description="Start game")
async def play(ctx):
    await ctx.respond("Guess the celebrity by one of their features!")
    await ctx.send("Choose a category:", view = CategoryView())

@bot.slash_command(name="guess", description="Make a guess")
async def guess(ctx, guess: str):
    player_id = ctx.author.id
    channel_id = ctx.channel.id
    if player_id not in active_games[channel_id]["scores"]:
        active_games[channel_id]["scores"][player_id] = 0

    correct_answer = active_games[channel_id]["current_answer"].lower()
    if (guess.lower() == correct_answer):
        active_games[channel_id]["scores"][player_id] += 1
        await ctx.respond(f"Correct! It is {active_games[channel_id]["current_answer"]}", file=discord.File(active_games[channel_id]["full_pic"]))
        category = active_games[channel_id]["category"]
        path_feature, path_full, answer = pick_random_celebrity(category)
        active_games[channel_id]["current_answer"] = answer
        active_games[channel_id]["full_pic"] = path_full
        await ctx.send(f"Next one! Guess who this is:", file=discord.File(path_feature))
    else: 
        await ctx.respond("Wrong! Try again.")

@bot.slash_command(name="skip", description="Skip this celebrity")
async def skip(ctx):
    channel_id = ctx.channel.id
    await ctx.respond(f"The answer was: {active_games[channel_id]["current_answer"]}", file=discord.File(active_games[channel_id]["full_pic"]))
    category = active_games[channel_id]["category"]
    path_feature, path_full, answer = pick_random_celebrity(category)
    active_games[channel_id]["current_answer"] = answer
    active_games[channel_id]["full_pic"] = path_full
    await ctx.send(f"Next one! Guess who this is:", file=discord.File(path_feature))
    
@bot.slash_command(name="quit", description="Quit game")
async def quit_game(ctx):
    channel_id = ctx.channel.id

    if channel_id not in active_games:
        await ctx.respond("No active game session in this channel.")
        return
    
    scores = active_games[channel_id]["scores"]
    if scores:
        leaderboard = "\n".join(
            [f"<@{player_id}>: {score}" for player_id, score in scores.items()]
        )
        await ctx.send(f"Final Scores:\n{leaderboard}")

    await ctx.send("Thanks for playing!")
    del active_games[channel_id]

bot.run(token)
