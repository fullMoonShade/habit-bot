import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot kick someone with a higher or equal role.", ephemeral=True)
            return
        
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked by {ctx.author.mention}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to kick that member.", ephemeral=True)

    @discord.slash_command(description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot ban someone with a higher or equal role.", ephemeral=True)
            return
        
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned by {ctx.author.mention}",
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to ban that member.", ephemeral=True)

    @discord.slash_command(description="Unban a member using their ID.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member_id: int):
        try:
            member_to_unban = discord.Object(id=member_id)
            await ctx.guild.unban(member_to_unban)
            await ctx.respond(f"User with ID {member_id} has been unbanned.")
        except discord.NotFound:
            await ctx.respond("This user is not banned.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to unban members.", ephemeral=True)

    @discord.slash_command(description="Purge a specified number of messages.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        if amount < 1 or amount > 100:
            await ctx.respond("Please specify a number between 1 and 100.", ephemeral=True)
            return

        try:
            deleted = await ctx.channel.purge(limit=amount)
            msg = await ctx.respond(f"Deleted {len(deleted)} messages.", delete_after=3)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to delete messages.", ephemeral=True)

    @discord.slash_command(description="Timeout a member for a specified duration in minutes.")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot timeout someone with a higher or equal role.", ephemeral=True)
            return
        
        try:
            until = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"{member.mention} has been timed out for {duration} minutes",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to timeout that member.", ephemeral=True)

    @discord.slash_command(description="Remove timeout from a member.")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.respond(f"Timeout removed from {member.mention}.")
        except discord.Forbidden:
            await ctx.respond("I don't have permission to remove timeouts.", ephemeral=True)

# Error handling for missing permissions and other errors
    @kick.error
    @ban.error
    @unban.error
    @purge.error
    @timeout.error
    @untimeout.error
    async def moderation_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.respond("Member not found.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.respond("Invalid argument provided.", ephemeral=True)
        else:
            logger.error(f"An unexpected error occurred: {error}")
            await ctx.respond("An unexpected error occurred.", ephemeral=True)

def setup(bot):
    bot.add_cog(Moderation(bot))
