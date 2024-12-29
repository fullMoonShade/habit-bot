import discord
from discord.ext import commands, tasks

class ToDoList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.todo_message = None  # Store the stickied message
        self.channel_id = None  # Channel where the to-do list is posted
        self.todos = []  # List storing the to-do items
        self.reset_tasks.start()  # Start the reset task

    @commands.slash_command(description="Set up a to-do list in this channel.")
    async def setup_todo_list(self, ctx):
        """
        Sets up a to-do list by creating a stickied message in the current channel.
        """
        # Save the channel ID for updates
        self.channel_id = ctx.channel.id

        # Create the initial stickied message
        embed = discord.Embed(
            title="To-Do List",
            description="Track your tasks here!\n\nAdd tasks using `/add_task`.\nMark them complete using `/complete_task`.",
            color=discord.Color.green()
        )
        embed.add_field(name="Current Tasks", value="No tasks added yet.", inline=False)

        self.todo_message = await ctx.channel.send(embed=embed)
        await ctx.respond("To-do list set up successfully!", ephemeral=True)

    @commands.slash_command(description="Add a task to the to-do list.")
    async def add_task(self, ctx, task: str):
        """
        Adds a task to the to-do list.
        """
        if not self.todo_message:
            await ctx.respond("No to-do list is set up yet. Use `/setup_todo_list` first.", ephemeral=True)
            return

        # Add the task and update the message
        self.todos.append({"task": task, "completed": False})
        await self.update_todo_message()
        await ctx.respond(f"Added task: **{task}**", ephemeral=True)

    @commands.slash_command(description="Mark a task as completed.")
    async def complete_task(self, ctx, task: str):
        """
        Marks a task as completed on the to-do list.
        """
        if not self.todo_message:
            await ctx.respond("No to-do list is set up yet. Use `/setup_todo_list` first.", ephemeral=True)
            return

        # Mark the task as completed
        for t in self.todos:
            if t["task"].lower() == task.lower():
                t["completed"] = True
                await self.update_todo_message()
                await ctx.respond(f"Marked task **{task}** as completed!", ephemeral=True)
                return

        await ctx.respond(f"Task **{task}** not found.", ephemeral=True)

    async def update_todo_message(self):
        """
        Updates the stickied message with the latest tasks and statuses.
        """
        if not self.todo_message:
            return

        # Prepare the updated embed
        embed = discord.Embed(
            title="To-Do List",
            description="Track your tasks here!",
            color=discord.Color.green()
        )
        if self.todos:
            task_list = "\n".join(
                f"- {'~~' if t['completed'] else ''}{t['task']}{'~~' if t['completed'] else ''}"
                for t in self.todos
            )
        else:
            task_list = "No tasks added yet."

        embed.add_field(name="Current Tasks", value=task_list, inline=False)
        await self.todo_message.edit(embed=embed)

    @tasks.loop(hours=24)
    async def reset_tasks(self):
        """
        Resets the completion status of all tasks daily.
        """
        for task in self.todos:
            task["completed"] = False
        if self.todo_message:
            await self.update_todo_message()

    @reset_tasks.before_loop
    async def before_reset_tasks(self):
        """
        Wait until the bot is ready before starting the task.
        """
        await self.bot.wait_until_ready()


# Setup function to register the Cog
def setup(bot):
    bot.add_cog(ToDoList(bot))
