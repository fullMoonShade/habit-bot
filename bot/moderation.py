import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Clear messages in the current channel")
    async def clear(self, ctx, amount: int = 10):
        """
        Clears a specified number of messages from the current channel.
        """
        # Check bot permissions
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.respond("I don't have permission to manage messages.", ephemeral=True)
            return

        # Check user permissions
        if not ctx.channel.permissions_for(ctx.author).manage_messages:
            await ctx.respond("You need 'Manage Messages' permission to use this command.", ephemeral=True)
            return

        if amount <= 0:
            await ctx.respond("Please specify a number greater than 0.", ephemeral=True)
            return

        # Avoiding time-out
        await ctx.defer(ephemeral=True)

        # Purge messages here
        try:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.respond(f"Deleted {len(deleted)} messages.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("I do not have the required permissions to delete messages.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.respond(f"An error occurred: {e}", ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
