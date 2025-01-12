import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional

import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional

class HabitsDatabase:
    def __init__(self):
        os.makedirs('.db', exist_ok=True)
        self.conn = sqlite3.connect('.db/habits.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
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
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_completions (
                completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (habit_id)
            )
        ''')
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

    def verify_habit_owner(self, habit_id: int, user_id: str) -> bool:
        """Verify that a habit belongs to a user"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM habits
            WHERE habit_id = ? AND user_id = ?
        ''', (habit_id, user_id))
        return self.cursor.fetchone()[0] > 0

    def verify_todo_owner(self, todo_id: int, user_id: str) -> bool:
        """Verify that a todo belongs to a user"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM todos
            WHERE todo_id = ? AND user_id = ?
        ''', (todo_id, user_id))
        return self.cursor.fetchone()[0] > 0

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

    def clear_habits(self, user_id: str) -> int:
        """
        Clear all habits for a user
        Returns the number of habits deleted
        """
        # First delete all habit completions for the user's habits
        self.cursor.execute('''
            DELETE FROM habit_completions 
            WHERE habit_id IN (
                SELECT habit_id 
                FROM habits 
                WHERE user_id = ?
            )
        ''', (user_id,))
        
        # Then delete the habits themselves
        self.cursor.execute('''
            DELETE FROM habits 
            WHERE user_id = ?
        ''', (user_id,))
        
        deleted_count = self.cursor.rowcount
        self.conn.commit()
        return deleted_count

    def clear_todos(self, user_id: str) -> int:
        """
        Clear all todos for a user
        Returns the number of todos deleted
        """
        self.cursor.execute('''
            DELETE FROM todos 
            WHERE user_id = ?
        ''', (user_id,))
        
        deleted_count = self.cursor.rowcount
        self.conn.commit()
        return deleted_count


    def __del__(self):
        """Close database connection when object is destroyed"""
        self.conn.close()
