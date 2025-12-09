import sqlite3
import pandas as pd
from datetime import datetime

class QuizDatabase:
    def __init__(self, db_path="quiz.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        # Increased timeout to 30s to wait for locks instead of failing immediately
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)

    def _init_db(self):
        with self._get_conn() as conn:
            # Enable Write-Ahead Logging (WAL) for better concurrency
            conn.execute("PRAGMA journal_mode=WAL;")
            # Relax synchronization for speed (safe for non-critical crashes)
            conn.execute("PRAGMA synchronous=NORMAL;")
            
            cursor = conn.cursor()
            
            # Room State
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_state (
                    id INTEGER PRIMARY KEY,
                    current_question_id INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT 0,
                    correct_answer TEXT,
                    start_time TEXT,
                    duration_seconds INTEGER DEFAULT 60
                )
            """)
            # Initialize room state if empty
            cursor.execute("SELECT COUNT(*) FROM room_state")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO room_state (id, current_question_id, is_active, duration_seconds) VALUES (1, 1, 0, 60)")
            else:
                # Migration for existing DB (Add columns if missing)
                try:
                    cursor.execute("SELECT start_time FROM room_state")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE room_state ADD COLUMN start_time TEXT")
                    cursor.execute("ALTER TABLE room_state ADD COLUMN duration_seconds INTEGER DEFAULT 60")

            # Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    score INTEGER DEFAULT 0
                )
            """)

            # Responses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    username TEXT,
                    selected_option TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(question_id, username)
                )
            """)
            conn.commit()

    # --- Room State Methods ---
    def get_room_state(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_question_id, is_active, correct_answer, start_time, duration_seconds FROM room_state WHERE id=1")
            row = cursor.fetchone()
            return {
                "current_question_id": row[0],
                "is_active": bool(row[1]),
                "correct_answer": row[2],
                "start_time": row[3],
                "duration_seconds": row[4] if row[4] else 60
            }

    def update_room_state(self, current_question_id=None, is_active=None, correct_answer=None, start_time=None, duration_seconds=None):
        updates = []
        params = []
        if current_question_id is not None:
            updates.append("current_question_id = ?")
            params.append(current_question_id)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(int(is_active))
        if correct_answer is not None:
            updates.append("correct_answer = ?")
            params.append(correct_answer)
        if start_time is not None:
            updates.append("start_time = ?")
            params.append(start_time)
        if duration_seconds is not None:
            updates.append("duration_seconds = ?")
            params.append(duration_seconds)
        
        if updates:
            query = f"UPDATE room_state SET {', '.join(updates)} WHERE id=1"
            with self._get_conn() as conn:
                conn.execute(query, params)
                conn.commit()

    def reset_game(self):
        with self._get_conn() as conn:
            conn.execute("UPDATE room_state SET current_question_id = 1, is_active = 0, correct_answer = NULL")
            conn.execute("DELETE FROM responses")
            conn.execute("DELETE FROM users")
            conn.commit()

    # --- User Methods ---
    def register_user(self, username):
        if not username:
            return False
        try:
            with self._get_conn() as conn:
                conn.execute("INSERT OR IGNORE INTO users (username, score) VALUES (?, 0)", (username,))
                conn.commit()
            return True
        except Exception:
            return False

    def get_user_score(self, username):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_leaderboard(self, limit=10):
        with self._get_conn() as conn:
            df = pd.read_sql_query(f"SELECT username, score FROM users ORDER BY score DESC LIMIT {limit}", conn)
            return df

    # --- Response Methods ---
    def submit_response(self, question_id, username, selected_option):
        # Retry logic for handling high concurrency locks
        import time
        import random
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                with self._get_conn() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO responses (question_id, username, selected_option)
                        VALUES (?, ?, ?)
                    """, (question_id, username, selected_option))
                    conn.commit()
                return True
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    if attempt < max_retries - 1:
                        sleep_time = 0.1 * (2 ** attempt) + random.uniform(0, 0.1)
                        time.sleep(sleep_time)
                        continue
                print(f"Error submitting response (Attempt {attempt}): {e}")
                return False
            except Exception as e:
                print(f"Critical error submitting response: {e}")
                return False
        return False

    def get_response_counts(self, question_id):
        with self._get_conn() as conn:
            df = pd.read_sql_query("""
                SELECT selected_option, COUNT(*) as count 
                FROM responses 
                WHERE question_id = ? 
                GROUP BY selected_option
            """, conn, params=(question_id,))
            
            # Ensure all options are present for the chart
            options = pd.DataFrame({'selected_option': ['A', 'B', 'C', 'D']})
            df = options.merge(df, on='selected_option', how='left').fillna(0)
            return df

    def get_user_response(self, question_id, username):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT selected_option FROM responses WHERE question_id = ? AND username = ?", (question_id, username))
            row = cursor.fetchone()
            return row[0] if row else None

    def calculate_scores(self, question_id, correct_option):
        with self._get_conn() as conn:
            # Find users who answered correctly
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username FROM responses 
                WHERE question_id = ? AND selected_option = ?
            """, (question_id, correct_option))
            correct_users = [row[0] for row in cursor.fetchall()]

            # Update scores
            if correct_users:
                placeholders = ','.join(['?'] * len(correct_users))
                conn.execute(f"UPDATE users SET score = score + 1 WHERE username IN ({placeholders})", correct_users)
                conn.commit()
            
            return len(correct_users)
