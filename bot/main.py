import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    logger.error("No Discord token found in environment variables!")
    raise ValueError("DISCORD_TOKEN environment variable is required")

def create_bot():
    """Creates and configures the bot instance"""
    intents = discord.Intents.all()
    bot = discord.Bot(intents=intents)
    
    @bot.event
    async def on_ready():
        """Event triggered when the bot successfully connects to Discord."""
        logger.info(f'{bot.user} has connected to Discord!')
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your commands"
            )
        )

    @bot.slash_command(description="Check if the bot is responsive")
    async def ping(ctx):
        """Simple command to check bot latency."""
        await ctx.respond(f'Pong! 🏓 Latency: {round(bot.latency * 1000)}ms')

    @bot.slash_command(description="Get information about the server")
    async def serverinfo(ctx):
        """Displays information about the current server."""
        server = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 Information about {server.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Server Owner", value=server.owner, inline=True)
        embed.add_field(name="Member Count", value=server.member_count, inline=True)
        embed.add_field(name="Channel Count", value=len(server.channels), inline=True)
        embed.add_field(name="Role Count", value=len(server.roles), inline=True)
        embed.add_field(name="Server Created", value=server.created_at.strftime("%Y-%m-%d"), inline=True)
        
        if server.icon:
            embed.set_thumbnail(url=server.icon.url)
        
        await ctx.respond(embed=embed)

    # Load extensions
    try:
        bot.load_extension('moderation')
        logger.info("Successfully loaded moderation extension")
    except Exception as e:
        logger.error(f"Failed to load moderation extension: {e}") 

    return bot

if __name__ == "__main__":
    bot = create_bot()
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Failed to login to Discord. Please check your token.")
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")