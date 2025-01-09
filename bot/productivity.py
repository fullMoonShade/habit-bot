import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional

import discord
from discord.ext import commands
from discord import Option, SlashCommandGroup

class HabitsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = HabitsDatabase()

    habits = SlashCommandGroup("habits", "Manage your daily habits")
    todos = SlashCommandGroup("todos", "Manage your todo list")

    @habits.command(name="add")
    async def add_habit(
        self,
        ctx: discord.ApplicationContext,
        name: Option(str, "Name of the habit"),
        frequency: Option(str, "Frequency of the habit (daily/weekly/monthly)", choices=["daily", "weekly", "monthly"]),
        description: Option(str, "Description of the habit", required=False) = None,
        reminder_time: Option(str, "Reminder time (HH:MM format)", required=False) = None
    ):
        """Add a new habit to track"""
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
            
        await ctx.respond(embed=embed)

    @habits.command(name="complete")
    async def complete_habit(
        self,
        ctx: discord.ApplicationContext,
        habit_id: Option(int, "ID of the habit to complete")
    ):
        """Mark a habit as completed for today"""
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
            
        await ctx.respond(embed=embed)

    @habits.command(name="list")
    async def list_habits(self, ctx: discord.ApplicationContext):
        """List all your habits"""
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
                
        await ctx.respond(embed=embed)

    @todos.command(name="add")
    async def add_todo(
        self,
        ctx: discord.ApplicationContext,
        title: Option(str, "Title of the todo"),
        description: Option(str, "Description of the todo", required=False) = None,
        due_date: Option(str, "Due date (YYYY-MM-DD format)", required=False) = None,
        priority: Option(int, "Priority (0-5)", min_value=0, max_value=5, required=False) = 0
    ):
        """Add a new todo item"""
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
        await ctx.respond(embed=embed)

    @todos.command(name="complete")
    async def complete_todo(
        self,
        ctx: discord.ApplicationContext,
        todo_id: Option(int, "ID of the todo to complete")
    ):
        """Mark a todo as completed"""
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
            
        await ctx.respond(embed=embed)

    @todos.command(name="list")
    async def list_todos(
        self,
        ctx: discord.ApplicationContext,
        include_completed: Option(bool, "Include completed todos", required=False) = False
    ):
        """List all your todos"""
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
                
        await ctx.respond(embed=embed)


class HabitsDatabase:
    def __init__(self, db_path: str = ".db/habits.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.setup_database()

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def setup_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    habit_name TEXT NOT NULL,
                    description TEXT,
                    frequency TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reminder_time TEXT,
                    UNIQUE(user_id, habit_name)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS habit_completions (
                    completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    completed_date DATE NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (habit_id) REFERENCES habits (habit_id),
                    UNIQUE(habit_id, completed_date)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    todo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATE,
                    priority INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            conn.commit()

    def add_habit(self, user_id: str, habit_name: str, frequency: str, 
                  description: Optional[str] = None, 
                  reminder_time: Optional[str] = None) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO habits (user_id, habit_name, frequency, description, reminder_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, habit_name, frequency, description, reminder_time))
                return True
        except sqlite3.IntegrityError:
            return False

    def complete_habit(self, habit_id: int, completion_date: Optional[date] = None) -> bool:
        completion_date = completion_date or date.today()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO habit_completions (habit_id, completed_date)
                    VALUES (?, ?)
                """, (habit_id, completion_date))
                return True
        except sqlite3.IntegrityError:
            return False

    def get_user_habits(self, user_id: str) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT habit_id, habit_name, description, frequency, 
                       created_at, reminder_time
                FROM habits
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            columns = ['habit_id', 'habit_name', 'description', 'frequency', 
                      'created_at', 'reminder_time']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_habit_streak(self, habit_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT completed_date
                FROM habit_completions
                WHERE habit_id = ?
                ORDER BY completed_date DESC
            """, (habit_id,))
            
            completions = [row[0] for row in cursor.fetchall()]
            if not completions:
                return 0
                
            streak = 1
            for i in range(len(completions) - 1):
                date1 = datetime.strptime(completions[i], '%Y-%m-%d').date()
                date2 = datetime.strptime(completions[i + 1], '%Y-%m-%d').date()
                if (date1 - date2).days == 1:
                    streak += 1
                else:
                    break
                    
            return streak

    def add_todo(self, user_id: str, title: str, description: Optional[str] = None,
                 due_date: Optional[str] = None, priority: int = 0) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO todos (user_id, title, description, due_date, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, title, description, due_date, priority))
            return cursor.lastrowid

    def complete_todo(self, todo_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE todos
                SET completed = TRUE, completed_at = CURRENT_TIMESTAMP
                WHERE todo_id = ?
            """, (todo_id,))
            return cursor.rowcount > 0

    def get_user_todos(self, user_id: str, include_completed: bool = False) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT todo_id, title, description, due_date, priority,
                       completed, created_at, completed_at
                FROM todos
                WHERE user_id = ?
            """
            if not include_completed:
                query += " AND completed = FALSE"
            query += " ORDER BY priority DESC, due_date ASC"
            
            cursor.execute(query, (user_id,))
            
            columns = ['todo_id', 'title', 'description', 'due_date', 'priority',
                      'completed', 'created_at', 'completed_at']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def setup(bot):
    bot.add_cog(HabitsCog(bot))