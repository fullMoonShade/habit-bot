import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# api key 
load_dotenv()
API_KEY = os.getenv("api_key")

# Intents
intents = discord.Intents.default()
intents.messages = True  # Bot can read messages 

bot = commands.Bot(intents=intents)


# Bot is ready
@bot.event
async def on_ready():
    print(f"Bot is online! Logged in as {bot.user}")

# Test command
@bot.slash_command(description="Test command")
async def test(ctx):
    await ctx.respond("Bot is working as intended.")

"""
Loading all cogs
"""

# Moderation cog
try:
    bot.load_extension("moderation")
    print("Moderation Cog loaded successfully.")
except Exception as e:
    print(f"Failed to load Moderation Cog: {e}")

# Habit cog
try:
    bot.load_extension("habit")
    print("To-do Cog loaded successfully.")
except Exception as e:
    print(f"Failed to load To-do Cog: {e}")
  
# Run
if __name__ == "__main__":
    if API_KEY:
        bot.run(API_KEY)
    else:
        print("Please make sure api key is available in .env format.")
