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
            
        await ctx.respond(embed=embed, ephemeral=True)

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
            
        await ctx.respond(embed=embed, ephemeral=True)

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
                
        await ctx.respond(embed=embed, ephemeral=True)

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
        await ctx.respond(embed=embed, ephemeral=True)

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
            
        await ctx.respond(embed=embed, ephemeral=True)

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
                
        await ctx.respond(embed=embed, ephemeral=True)


class HabitsDatabase:
    def __init__(self):
        # Create db directory if it doesn't exist
        os.makedirs('.db', exist_ok=True)
        
        # Connect to SQLite database
        self.conn = sqlite3.connect('.db/habits.db')
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create the necessary database tables if they don't exist"""
        # Habits table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                habit_name TEXT NOT NULL,
                frequency TEXT NOT NULL,
                description TEXT,
                reminder_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, habit_name)
            )
        ''')
        
        # Habit completions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_completions (
                completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (habit_id)
            )
        ''')
        
        # Todos table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                todo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATE,
                priority INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_habit(self, user_id: str, name: str, frequency: str, 
                  description: Optional[str] = None, 
                  reminder_time: Optional[str] = None) -> bool:
        """Add a new habit for a user"""
        try:
            self.cursor.execute('''
                INSERT INTO habits (user_id, habit_name, frequency, description, reminder_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, frequency, description, reminder_time))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def complete_habit(self, habit_id: int) -> bool:
        """Mark a habit as completed for today"""
        # Check if habit exists and hasn't been completed today
        today = date.today()
        self.cursor.execute('''
            SELECT COUNT(*) FROM habit_completions
            WHERE habit_id = ? AND DATE(completed_at) = ?
        ''', (habit_id, today))
        
        if self.cursor.fetchone()[0] > 0:
            return False
            
        self.cursor.execute('''
            INSERT INTO habit_completions (habit_id)
            VALUES (?)
        ''', (habit_id,))
        self.conn.commit()
        return True
    
    def get_habit_streak(self, habit_id: int) -> int:
        """Calculate current streak for a habit"""
        self.cursor.execute('''
            SELECT frequency FROM habits WHERE habit_id = ?
        ''', (habit_id,))
        frequency = self.cursor.fetchone()
        
        if not frequency:
            return 0
            
        frequency = frequency[0]
        today = date.today()
        
        # Get all completion dates for this habit
        self.cursor.execute('''
            SELECT DATE(completed_at) as completion_date
            FROM habit_completions
            WHERE habit_id = ?
            ORDER BY completed_at DESC
        ''', (habit_id,))
        
        completions = [row[0] for row in self.cursor.fetchall()]
        if not completions:
            return 0
            
        streak = 0
        current_date = today
        
        # Count consecutive days/weeks/months of completion
        for completion in completions:
            completion_date = datetime.strptime(completion, '%Y-%m-%d').date()
            
            if frequency == 'daily':
                if (current_date - completion_date).days <= 1:
                    streak += 1
                    current_date = completion_date
                else:
                    break
            elif frequency == 'weekly':
                if (current_date - completion_date).days <= 7:
                    streak += 1
                    current_date = completion_date
                else:
                    break
            elif frequency == 'monthly':
                if (current_date.year == completion_date.year and 
                    current_date.month - completion_date.month <= 1):
                    streak += 1
                    current_date = completion_date
                else:
                    break
                    
        return streak
    
    def get_user_habits(self, user_id: str) -> List[Dict]:
        """Get all habits for a user"""
        self.cursor.execute('''
            SELECT habit_id, habit_name, frequency, description, reminder_time
            FROM habits
            WHERE user_id = ?
        ''', (user_id,))
        
        habits = []
        for row in self.cursor.fetchall():
            habits.append({
                'habit_id': row[0],
                'habit_name': row[1],
                'frequency': row[2],
                'description': row[3],
                'reminder_time': row[4]
            })
        return habits
    
    def add_todo(self, user_id: str, title: str, 
                 description: Optional[str] = None,
                 due_date: Optional[str] = None,
                 priority: int = 0) -> int:
        """Add a new todo item for a user"""
        self.cursor.execute('''
            INSERT INTO todos (user_id, title, description, due_date, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, due_date, priority))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def complete_todo(self, todo_id: int) -> bool:
        """Mark a todo as completed"""
        self.cursor.execute('''
            UPDATE todos
            SET completed = TRUE, completed_at = CURRENT_TIMESTAMP
            WHERE todo_id = ? AND completed = FALSE
        ''', (todo_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_user_todos(self, user_id: str, include_completed: bool = False) -> List[Dict]:
        """Get todos for a user"""
        query = '''
            SELECT todo_id, title, description, due_date, priority, completed
            FROM todos
            WHERE user_id = ?
        '''
        
        if not include_completed:
            query += ' AND completed = FALSE'
            
        self.cursor.execute(query, (user_id,))
        
        todos = []
        for row in self.cursor.fetchall():
            todos.append({
                'todo_id': row[0],
                'title': row[1],
                'description': row[2],
                'due_date': row[3],
                'priority': row[4],
                'completed': row[5]
            })
        return todos
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        self.conn.close()

def setup(bot):
    bot.add_cog(HabitsCog(bot))