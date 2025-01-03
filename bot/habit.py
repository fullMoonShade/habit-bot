import discord
from discord.ext import commands, tasks
import sqlite3
import os

class ToDoList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = self._setup_database()  # Set up the database
        self.todo_messages = {}  # Store stickied messages per user
        self.reset_tasks.start()  # Start the reset task

    def _setup_database(self):
        """
        Sets up the database by creating the `.db` directory and the `tasks` table.
        """
        db_dir = ".db"
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "todo_list.db")

        # Connect to SQLite and create the `tasks` table if it doesn't exist
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

        return db_path

    def _db_execute(self, query, params=(), fetch=False):
        """
        Helper function to execute queries against the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()

    @commands.slash_command(description="Set up a to-do list in this channel.")
    async def setup_todo_list(self, ctx):
        """
        Sets up a to-do list by creating a stickied message in the current channel.
        """
        embed = discord.Embed(
            title="To-Do List",
            description="Track your tasks here!\n\nAdd tasks using `/add_task`.\nMark them complete using `/complete_task`.",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Tasks", value="No tasks added yet.", inline=False)

        message = await ctx.channel.send(embed=embed)
        self.todo_messages[ctx.author.id] = message
        await ctx.respond("To-do list set up successfully!", ephemeral=True)

    @commands.slash_command(description="Add a task to the to-do list.")
    async def add_task(self, ctx, task: str):
        """
        Adds a task to the to-do list for the user.
        """
        user_id = ctx.author.id
        self._db_execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task))
        await self.update_todo_message(user_id)
        await ctx.respond(f"Added task: **{task}**", ephemeral=True)

    @commands.slash_command(description="Mark a task as completed by ID.")
    async def complete_task(self, ctx, task_id: int):
        """
        Marks a task as completed by its ID.
        """
        user_id = ctx.author.id

        # Check if the task exists
        task = self._db_execute(
            "SELECT id FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
            fetch=True
        )
        if not task:
            await ctx.respond(f"No task found with ID **{task_id}** for your user.", ephemeral=True)
            return

        # Update the task's completion status
        self._db_execute(
            "UPDATE tasks SET completed = TRUE WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await self.update_todo_message(user_id)
        await ctx.respond(f"Marked task ID **{task_id}** as completed!", ephemeral=True)

    @commands.slash_command(description="Clear all your tasks.")
    async def clear_tasks(self, ctx):
        """
        Clears all tasks for the user.
        """
        user_id = ctx.author.id
        self._db_execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        await self.update_todo_message(user_id)
        await ctx.respond("All your tasks have been cleared.", ephemeral=True)

    async def update_todo_message(self, user_id: int):
        """
        Updates the stickied message with the latest tasks and statuses for the user.
        """
        message = self.todo_messages.get(user_id)
        if not message:
            return

        # Retrieve tasks for the user
        tasks = self._db_execute(
            "SELECT id, task, completed FROM tasks WHERE user_id = ? ORDER BY created_at",
            (user_id,),
            fetch=True
        )

        # Prepare the updated embed
        embed = discord.Embed(
            title="To-Do List",
            description="Track your tasks here!",
            color=discord.Color.green()
        )
        if tasks:
            task_list = "\n".join(
                f"{'[x]' if completed else '[ ]'} **{task_id}** - {task}"
                for task_id, task, completed in tasks
            )
        else:
            task_list = "No tasks added yet."

        embed.add_field(name="Current Tasks", value=task_list, inline=False)
        await message.edit(embed=embed)

    @tasks.loop(hours=24)
    async def reset_tasks(self):
        """
        Resets the completion status of all tasks daily.
        """
        self._db_execute("UPDATE tasks SET completed = FALSE")

    @reset_tasks.before_loop
    async def before_reset_tasks(self):
        """
        Wait until the bot is ready before starting the task.
        """
        await self.bot.wait_until_ready()

# Setup function to register the Cog
def setup(bot):
    bot.add_cog(ToDoList(bot))
