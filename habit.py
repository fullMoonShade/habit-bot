# AI generated abstraction of habit tracking functionality  

import discord
from discord.ext import commands, tasks

class HabitTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.habit_message = None  # Store the stickied message
        self.channel_id = None  # Channel where the habit tracker is posted
        self.habits = []  # List of habits to track
        self.update_habits.start()  # Start the update task

    @commands.slash_command(description="Setup a habit tracker in the current channel.")
    async def setup_habit_tracker(self, ctx):
        """
        Sets up a habit tracker by creating a stickied message in the channel.
        """
        # Save the channel ID for updates
        self.channel_id = ctx.channel.id

        # Create the initial stickied message
        embed = discord.Embed(
            title="Habit Tracker",
            description="Track your habits here!\n\nAdd habits using `/add_habit`.\nMark them complete using `/complete_habit`.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Habits", value="No habits added yet.", inline=False)

        self.habit_message = await ctx.channel.send(embed=embed)
        await ctx.respond("Habit tracker set up successfully!", ephemeral=True)

    @commands.slash_command(description="Add a habit to the tracker.")
    async def add_habit(self, ctx, habit: str):
        """
        Adds a habit to the tracker.
        """
        if not self.habit_message:
            await ctx.respond("No habit tracker is set up yet. Use `/setup_habit_tracker` first.", ephemeral=True)
            return

        # Add the habit and update the message
        self.habits.append({"habit": habit, "completed": False})
        await self.update_habit_message()
        await ctx.respond(f"Added habit: **{habit}**", ephemeral=True)

    @commands.slash_command(description="Mark a habit as completed.")
    async def complete_habit(self, ctx, habit: str):
        """
        Marks a habit as completed.
        """
        if not self.habit_message:
            await ctx.respond("No habit tracker is set up yet. Use `/setup_habit_tracker` first.", ephemeral=True)
            return

        # Mark the habit as completed
        for h in self.habits:
            if h["habit"].lower() == habit.lower():
                h["completed"] = True
                await self.update_habit_message()
                await ctx.respond(f"Marked habit **{habit}** as completed!", ephemeral=True)
                return

        await ctx.respond(f"Habit **{habit}** not found.", ephemeral=True)

    async def update_habit_message(self):
        """
        Updates the stickied message with the latest habits and statuses.
        """
        if not self.habit_message:
            return

        # Prepare the updated embed
        embed = discord.Embed(
            title="Habit Tracker",
            description="Track your habits here!",
            color=discord.Color.blue()
        )
        if self.habits:
            habit_list = "\n".join(
                f"- {'~~' if h['completed'] else ''}{h['habit']}{'~~' if h['completed'] else ''}"
                for h in self.habits
            )
        else:
            habit_list = "No habits added yet."

        embed.add_field(name="Current Habits", value=habit_list, inline=False)
        await self.habit_message.edit(embed=embed)

    @tasks.loop(hours=24)
    async def update_habits(self):
        """
        Resets the completion status of all habits daily.
        """
        for habit in self.habits:
            habit["completed"] = False
        if self.habit_message:
            await self.update_habit_message()

    @update_habits.before_loop
    async def before_update_habits(self):
        """
        Wait until the bot is ready before starting the task.
        """
        await self.bot.wait_until_ready()


# Setup function to register the Cog
def setup(bot):
    bot.add_cog(HabitTracker(bot))
