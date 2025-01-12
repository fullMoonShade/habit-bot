import discord
from discord.ext import commands
from discord.commands import Option, SlashCommandGroup
from habits_db import HabitsDatabase

class HabitsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = HabitsDatabase()

    habits = SlashCommandGroup("habits", "Manage your daily habits")
    todos = SlashCommandGroup("todos", "Manage your todo list")

    @habits.command(name="add", description="Add a new habit to track")
    async def add_habit(
        self,
        ctx: discord.ApplicationContext,
        name: Option(str, "Name of the habit"),
        frequency: Option(str, "Frequency of the habit (daily/weekly/monthly)", choices=["daily", "weekly", "monthly"]),
        description: Option(str, "Description of the habit", required=False, default=None),
        reminder_time: Option(str, "Reminder time (HH:MM format)", required=False, default=None)
    ):
        success = self.db.add_habit(
            str(ctx.author.id),
            name,
            frequency,
            description,
            reminder_time
        )
        if success:
            embed = discord.Embed(
                title="Habit Added",
                description=f"Successfully added habit: {name}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="You already have a habit with this name",
                color=discord.Color.red()
            )
        await ctx.respond(embed=embed, ephemeral=True)

    @habits.command(name="complete", description="Mark a habit as completed for today")
    async def complete_habit(
        self,
        ctx: discord.ApplicationContext,
        habit_id: Option(int, "ID of the habit to complete")
    ):
        success = self.db.complete_habit(habit_id)
        if success:
            streak = self.db.get_habit_streak(habit_id)
            embed = discord.Embed(
                title="Habit Completed",
                description=f"Current streak: {streak} days",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="Habit already completed for today or habit not found",
                color=discord.Color.red()
            )
        await ctx.respond(embed=embed, ephemeral=True)

    @habits.command(name="list", description="List all your habits")
    async def list_habits(self, ctx: discord.ApplicationContext):
        habits = self.db.get_user_habits(str(ctx.author.id))
        if not habits:
            embed = discord.Embed(
                title="No Habits",
                description="You haven't created any habits yet",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="Your Habits",
                color=discord.Color.blue()
            )
            for habit in habits:
                streak = self.db.get_habit_streak(habit['habit_id'])
                description = habit['description'] or 'No description'
                embed.add_field(
                    name=f"#{habit['habit_id']} - {habit['habit_name']}",
                    value=f"Description: {description}\nFrequency: {habit['frequency']}\nCurrent streak: {streak} days",
                    inline=False
                )
        await ctx.respond(embed=embed, ephemeral=True)

    @todos.command(name="add", description="Add a new todo item")
    async def add_todo(
        self,
        ctx: discord.ApplicationContext,
        title: Option(str, "Title of the todo"),
        description: Option(str, "Description of the todo", required=False, default=None),
        due_date: Option(str, "Due date (YYYY-MM-DD format)", required=False, default=None),
        priority: Option(int, "Priority (0-5)", min_value=0, max_value=5, required=False, default=0)
    ):
        todo_id = self.db.add_todo(
            str(ctx.author.id),
            title,
            description,
            due_date,
            priority
        )
        embed = discord.Embed(
            title="Todo Added",
            description=f"Successfully added todo #{todo_id}: {title}",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @todos.command(name="complete", description="Mark a todo as completed")
    async def complete_todo(
        self,
        ctx: discord.ApplicationContext,
        todo_id: Option(int, "ID of the todo to complete")
    ):
        success = self.db.complete_todo(todo_id)
        if success:
            embed = discord.Embed(
                title="Todo Completed",
                description=f"Marked todo #{todo_id} as completed",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="Todo not found or already completed",
                color=discord.Color.red()
            )
        await ctx.respond(embed=embed, ephemeral=True)

    @todos.command(name="list", description="List all your todos")
    async def list_todos(
        self,
        ctx: discord.ApplicationContext,
        include_completed: Option(bool, "Include completed todos", required=False, default=False)
    ):
        todos = self.db.get_user_todos(str(ctx.author.id), include_completed)
        if not todos:
            embed = discord.Embed(
                title="No Todos",
                description="You haven't created any todos yet",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="Your Todos",
                color=discord.Color.blue()
            )
            for todo in todos:
                status = "✅ Completed" if todo['completed'] else "⏳ Pending"
                due_date = f"Due: {todo['due_date']}" if todo['due_date'] else "No due date"
                description = todo['description'] or 'No description'
                embed.add_field(
                    name=f"#{todo['todo_id']} - {todo['title']} (Priority: {todo['priority']})",
                    value=f"Status: {status}\n{due_date}\nDescription: {description}",
                    inline=False
                )
        await ctx.respond(embed=embed, ephemeral=True)

    @habits.command(name="clear", description="Clear all your habits")
    async def clear_habits(self, ctx: discord.ApplicationContext):
        deleted_count = self.db.clear_habits(str(ctx.author.id))
        embed = discord.Embed(
            title="Habits Cleared",
            description=f"Deleted {deleted_count} habits.",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @todos.command(name="clear", description="Clear all your todos")
    async def clear_todos(self, ctx: discord.ApplicationContext):
        deleted_count = self.db.clear_todos(str(ctx.author.id))
        embed = discord.Embed(
            title="Todos Cleared",
            description=f"Deleted {deleted_count} todos.",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(HabitsCog(bot))