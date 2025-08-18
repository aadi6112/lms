# database.py - Enhanced Database Layer with Multi-Combination Support
import sqlite3
import hashlib
import json
from datetime import datetime
import time
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

def get_local_timestamp():
    """Get current local timestamp in YYYY-MM-DD HH:MM:SS format"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_local_datetime():
    """Get current local datetime object"""
    return datetime.now()

class Database:
    def __init__(self, db_path: str = "endorsements.db"):
        self.db_path = Path(db_path)
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables with local datetime"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table - Updated to use local time
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Enhanced endorsements table - Updated to use local time
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS endorsements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_number TEXT NOT NULL,
                    endorsement_type TEXT NOT NULL,
                    endorsement_version TEXT,
                    endorsement_validity TEXT,
                    concepto_id TEXT,
                    combination_number INTEGER DEFAULT 1,
                    combination_id TEXT,
                    total_combinations INTEGER DEFAULT 1,
                    file_group_id TEXT,
                    status TEXT DEFAULT 'In Review',
                    spanish_fields TEXT,
                    json_data TEXT,
                    original_filename TEXT,
                    file_path TEXT,
                    uploaded_by TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            
            # Indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_policy_type ON endorsements(policy_number, endorsement_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON endorsements(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_combination ON endorsements(combination_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_group ON endorsements(file_group_id)')
            
            # Create default admin user
            self.create_default_users()
            
            conn.commit()
            print(f"🕒 Database initialized with local time: {get_local_timestamp()}")

    def create_default_users(self):
        """Create default users if they don't exist - Updated with local time"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = get_local_timestamp()
                
                # Check if admin exists
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
                if cursor.fetchone()[0] == 0:
                    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
                    cursor.execute('''
                        INSERT INTO users (username, password_hash, full_name, email, role, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', ("admin", admin_password, "System Administrator", "admin@company.com", "admin", current_time, current_time))
                    print(f"✅ Created admin user at: {current_time}")
                    
                # Check if demo user exists
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'demo'")
                if cursor.fetchone()[0] == 0:
                    demo_password = hashlib.sha256("demo123".encode()).hexdigest()
                    cursor.execute('''
                        INSERT INTO users (username, password_hash, full_name, email, role, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', ("demo", demo_password, "Demo User", "demo@company.com", "user", current_time, current_time))
                    print(f"✅ Created demo user at: {current_time}")
                
                conn.commit()
        except Exception as e:
            print(f"Error creating default users: {e}")

class UserModel:
    def __init__(self, db: Database):
        self.db = db

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, full_name, email, role, created_at
                    FROM users 
                    WHERE username = ? AND password_hash = ?
                ''', (username, password_hash))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'username': row[1],
                        'full_name': row[2],
                        'email': row[3],
                        'role': row[4],
                        'created_at': row[5]
                    }
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def create_user(self, username: str, password: str, full_name: str = None, 
                   email: str = None, role: str = 'user') -> int:
        """Create a new user"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, full_name, email, role))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("Username already exists")
        except Exception as e:
            print(f"Error creating user: {e}")
            raise

class EndorsementModel:
    def __init__(self, db: Database):
        self.db = db

    def create_endorsement(self, endorsement_data: Dict) -> int:
        """Create a new endorsement with local timestamp"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                current_time = get_local_timestamp()
                
                # Handle JSON serialization
                spanish_fields_json = json.dumps(endorsement_data.get('spanish_fields', {}), ensure_ascii=False)
                json_data_json = json.dumps(endorsement_data.get('json_data', {}), ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO endorsements (
                        policy_number, endorsement_type, endorsement_version, 
                        endorsement_validity, concepto_id, combination_number,
                        combination_id, total_combinations, file_group_id, status,
                        spanish_fields, json_data, original_filename, file_path, uploaded_by,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    endorsement_data.get('policy_number'),
                    endorsement_data.get('endorsement_type'),
                    endorsement_data.get('endorsement_version'),
                    endorsement_data.get('endorsement_validity'),
                    endorsement_data.get('concepto_id'),
                    endorsement_data.get('combination_number', 1),
                    endorsement_data.get('combination_id'),
                    endorsement_data.get('total_combinations', 1),
                    endorsement_data.get('file_group_id'),
                    endorsement_data.get('status', 'In Review'),
                    spanish_fields_json,
                    json_data_json,
                    endorsement_data.get('original_filename'),
                    endorsement_data.get('file_path'),
                    endorsement_data.get('uploaded_by'),
                    current_time,  # created_at
                    current_time   # updated_at
                ))
                
                conn.commit()
                endorsement_id = cursor.lastrowid
                print(f"✅ Created endorsement {endorsement_id} at: {current_time}")

                return endorsement_id
            
        except Exception as e:
            print(f"Error creating endorsement: {e}")
            raise

    def get_endorsements(self, status: str = None, endorsement_type: str = None,
                        policy_number: str = None, limit: int = 50, offset: int = 0,
                        sort_by: str = "created_at", sort_order: str = "DESC") -> List[Dict]:
        """Get endorsements with filtering and pagination"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM endorsements WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if endorsement_type:
                    query += " AND endorsement_type = ?"
                    params.append(endorsement_type)
                
                if policy_number:
                    query += " AND policy_number LIKE ?"
                    params.append(f"%{policy_number}%")
                
                # Add sorting
                valid_sort_columns = ['created_at', 'updated_at', 'policy_number', 'endorsement_type', 'status']
                if sort_by in valid_sort_columns:
                    query += f" ORDER BY {sort_by} {sort_order}"
                else:
                    query += " ORDER BY created_at DESC"
                
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching endorsements: {e}")
            return []

    def get_endorsements_grouped(self, status: str = None, endorsement_type: str = None,
                                policy_number: str = None, limit: int = 50, offset: int = 0,
                                sort_by: str = "created_at", sort_order: str = "DESC") -> List[Dict]:
        """Get endorsements grouped by policy_number and endorsement_type"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        policy_number,
                        endorsement_type,
                        MIN(endorsement_version) as endorsement_version,
                        MIN(endorsement_validity) as endorsement_validity,
                        MIN(concepto_id) as concepto_id,
                        COUNT(*) as combination_count,
                        MIN(status) as status,
                        MIN(created_at) as created_at,
                        MAX(updated_at) as updated_at,
                        MIN(uploaded_by) as uploaded_by
                    FROM endorsements 
                    WHERE 1=1
                '''
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if endorsement_type:
                    query += " AND endorsement_type = ?"
                    params.append(endorsement_type)
                
                if policy_number:
                    query += " AND policy_number LIKE ?"
                    params.append(f"%{policy_number}%")
                
                query += " GROUP BY policy_number, endorsement_type"
                
                # Add sorting
                valid_sort_columns = ['created_at', 'updated_at', 'policy_number', 'endorsement_type', 'status']
                if sort_by in valid_sort_columns:
                    query += f" ORDER BY {sort_by} {sort_order}"
                else:
                    query += " ORDER BY created_at DESC"
                
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                columns = ['policy_number', 'endorsement_type', 'endorsement_version', 
                          'endorsement_validity', 'concepto_id', 'combination_count',
                          'status', 'created_at', 'updated_at', 'uploaded_by']
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error fetching grouped endorsements: {e}")
            return []

    def get_endorsement_by_id(self, endorsement_id: int) -> Optional[Dict]:
        """Get endorsement by ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM endorsements WHERE id = ?", (endorsement_id,))
                row = cursor.fetchone()
                return self._row_to_dict(row) if row else None
        except Exception as e:
            print(f"Error fetching endorsement by ID: {e}")
            return None

    def get_endorsement_combinations(self, policy_number: str, endorsement_type: str) -> List[Dict]:
        """Get all combinations for a specific policy and endorsement type"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Handle both string and integer policy numbers
                try:
                    policy_int = int(policy_number)
                    cursor.execute('''
                        SELECT * FROM endorsements 
                        WHERE (policy_number = ? OR CAST(policy_number AS INTEGER) = ?) 
                        AND endorsement_type = ?
                        ORDER BY combination_number
                    ''', (str(policy_int), policy_int, endorsement_type))
                except (ValueError, TypeError):
                    cursor.execute('''
                        SELECT * FROM endorsements 
                        WHERE policy_number = ? AND endorsement_type = ?
                        ORDER BY combination_number
                    ''', (policy_number, endorsement_type))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching endorsement combinations: {e}")
            return []

    def update_endorsement(self, endorsement_id: int, update_data: Dict, updated_by: str = None) -> bool:
        """Update endorsement with local timestamp"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                current_time = get_local_timestamp()
                
                # Build dynamic update query
                set_clauses = []
                params = []
                
                for field, value in update_data.items():
                    if field in ['spanish_fields', 'json_data']:
                        # Handle JSON fields
                        set_clauses.append(f"{field} = ?")
                        params.append(json.dumps(value, ensure_ascii=False) if value else '{}')
                    else:
                        set_clauses.append(f"{field} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return True  # Nothing to update
                
                # Add updated_at timestamp with local time
                set_clauses.append("updated_at = ?")
                params.append(current_time)
                
                query = f"UPDATE endorsements SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(endorsement_id)
                
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"✅ Updated endorsement {endorsement_id} at: {current_time}")
                    return True
                return False
        except Exception as e:
            print(f"Error updating endorsement: {e}")
            return False

    def delete_endorsement(self, endorsement_id: int) -> bool:
        """Delete a single endorsement"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM endorsements WHERE id = ?", (endorsement_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting endorsement: {e}")
            return False

    def delete_endorsement_group(self, policy_number: str, endorsement_type: str) -> bool:
        """Delete all combinations for a specific policy and endorsement type"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Handle both string and integer policy numbers
                try:
                    policy_int = int(policy_number)
                    cursor.execute('''
                        DELETE FROM endorsements 
                        WHERE (policy_number = ? OR CAST(policy_number AS INTEGER) = ?) 
                        AND endorsement_type = ?
                    ''', (str(policy_int), policy_int, endorsement_type))
                except (ValueError, TypeError):
                    cursor.execute('''
                        DELETE FROM endorsements 
                        WHERE policy_number = ? AND endorsement_type = ?
                    ''', (policy_number, endorsement_type))
                
                conn.commit()
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    print(f"✅ Deleted {deleted_count} endorsement combinations for Policy #{policy_number}, Type: {endorsement_type}")
                    return True
                else:
                    print(f"⚠️ No endorsements found to delete for Policy #{policy_number}, Type: {endorsement_type}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting endorsement group: {e}")
            return False

    def get_endorsement_group_info(self, policy_number: str, endorsement_type: str) -> Dict[str, Any]:
        """Get information about an endorsement group (all combinations)"""
        try:
            combinations = self.get_endorsement_combinations(policy_number, endorsement_type)
            
            if not combinations:
                return {}
            
            return {
                'policy_number': policy_number,
                'endorsement_type': endorsement_type,
                'total_combinations': len(combinations),
                'combination_numbers': [combo['combination_number'] for combo in combinations],
                'status_counts': {
                    'approved': len([c for c in combinations if c['status'] == 'Approved']),
                    'rejected': len([c for c in combinations if c['status'] == 'Rejected']),
                    'in_review': len([c for c in combinations if c['status'] == 'In Review'])
                },
                'created_at': combinations[0]['created_at'] if combinations else None,
                'uploaded_by': combinations[0]['uploaded_by'] if combinations else None
            }
            
        except Exception as e:
            print(f"❌ Error getting endorsement group info: {e}")
            return {}

    def search_endorsements(self, search_term: str) -> List[Dict]:
        """Search endorsements by policy number, endorsement type, or concepto_id"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM endorsements 
                    WHERE policy_number LIKE ? 
                       OR endorsement_type LIKE ? 
                       OR concepto_id LIKE ?
                       OR spanish_fields LIKE ?
                    ORDER BY created_at DESC
                    LIMIT 100
                '''
                
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
                rows = cursor.fetchall()
                
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching endorsements: {e}")
            return []

    def get_unique_endorsement_types(self) -> List[str]:
        """Get all unique endorsement types"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT endorsement_type 
                    FROM endorsements 
                    WHERE endorsement_type IS NOT NULL 
                    ORDER BY endorsement_type
                ''')
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"Error fetching endorsement types: {e}")
            return []

    def get_unique_policy_numbers(self) -> List[str]:
        """Get all unique policy numbers"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT policy_number 
                    FROM endorsements 
                    WHERE policy_number IS NOT NULL 
                    ORDER BY policy_number
                ''')
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            print(f"Error fetching policy numbers: {e}")
            return []

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary"""
        if not row:
            return {}
        
        try:
            columns = ['id', 'policy_number', 'endorsement_type', 'endorsement_version',
                      'endorsement_validity', 'concepto_id', 'combination_number', 
                      'combination_id', 'total_combinations', 'file_group_id', 'status',
                      'spanish_fields', 'json_data', 'original_filename', 'file_path',
                      'uploaded_by', 'created_at', 'updated_at']
            
            result = dict(zip(columns, row))
            
            # Parse JSON fields
            if result.get('spanish_fields'):
                try:
                    result['spanish_fields'] = json.loads(result['spanish_fields'])
                except (json.JSONDecodeError, TypeError):
                    result['spanish_fields'] = {}
            else:
                result['spanish_fields'] = {}
            
            if result.get('json_data'):
                try:
                    result['json_data'] = json.loads(result['json_data'])
                except (json.JSONDecodeError, TypeError):
                    result['json_data'] = {}
            else:
                result['json_data'] = {}
            
            return result
        except Exception as e:
            print(f"Error converting row to dict: {e}")
            return {}

# Global database instance
database = Database()
user_model = UserModel(database)
endorsement_model = EndorsementModel(database)

if __name__ == "__main__":
    print("✅ Database initialized successfully!")
    print(f"📁 Database file: {database.db_path}")
    
    # Test authentication
    admin_user = user_model.authenticate("admin", "admin123")
    if admin_user:
        print("🔐 Default admin user authentication: SUCCESS")
        print(f"   User: {admin_user['full_name']} ({admin_user['username']})")
    else:
        print("❌ Default admin user authentication: FAILED")
