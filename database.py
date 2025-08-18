# database.py - Database Setup & Models
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DATABASE = "policy_management.db"

class Database:
    """Database manager class for Policy Management System"""
    
    def __init__(self, db_path: str = DATABASE):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables and default data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create endorsements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS endorsements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_number TEXT NOT NULL,
                    endorsement_type TEXT NOT NULL,
                    endorsement_version TEXT,
                    endorsement_validity TEXT,
                    concepto_id TEXT,
                    status TEXT DEFAULT 'In Review' CHECK(status IN ('Approved', 'Rejected', 'In Review')),
                    json_data TEXT NOT NULL,
                    original_filename TEXT,
                    file_path TEXT,
                    uploaded_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    FOREIGN KEY (uploaded_by) REFERENCES users (username),
                    FOREIGN KEY (updated_by) REFERENCES users (username)
                )
            ''')
            
            # Create indexes for better search performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_policy_number ON endorsements(policy_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_endorsement_type ON endorsements(endorsement_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON endorsements(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON endorsements(created_at)')
            
            # Create default admin user (password: admin123)
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password_hash, full_name, email) 
                VALUES (?, ?, ?, ?)
            ''', ("admin", admin_hash, "System Administrator", "admin@company.com"))
            
            conn.commit()
            print("✅ Database initialized successfully!")

class UserModel:
    """User data model and operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if valid"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, full_name, email, is_active 
                FROM users 
                WHERE username = ? AND password_hash = ? AND is_active = 1
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            if user:
                return dict(user)
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, full_name, email, is_active, created_at
                FROM users 
                WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            if user:
                return dict(user)
            return None
    
    def create_user(self, username: str, password: str, full_name: str = None, email: str = None) -> bool:
        """Create a new user"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, full_name, email)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, full_name, email))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Username already exists

class EndorsementModel:
    """Endorsement data model and operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_endorsement(self, data: Dict[str, Any]) -> int:
        """Create a new endorsement and return its ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO endorsements 
                (policy_number, endorsement_type, endorsement_version, endorsement_validity, 
                 concepto_id, status, json_data, original_filename, file_path, uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('policy_number'),
                data.get('endorsement_type'),
                data.get('endorsement_version'),
                data.get('endorsement_validity'),
                data.get('concepto_id'),
                data.get('status', 'In Review'),
                json.dumps(data.get('json_data', {})),
                data.get('original_filename'),
                data.get('file_path'),
                data.get('uploaded_by')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_endorsement_by_id(self, endorsement_id: int) -> Optional[Dict]:
        """Get endorsement by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM endorsements WHERE id = ?', (endorsement_id,))
            row = cursor.fetchone()
            
            if row:
                endorsement = dict(row)
                # Parse JSON data
                endorsement['json_data'] = json.loads(endorsement['json_data'])
                return endorsement
            return None
    
    def get_endorsements(self, 
                        status: Optional[str] = None,
                        endorsement_type: Optional[str] = None,
                        policy_number: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0,
                        sort_by: str = 'created_at',
                        sort_order: str = 'DESC') -> List[Dict]:
        """Get endorsements with optional filters"""
        
        query = 'SELECT * FROM endorsements WHERE 1=1'
        params = []
        
        # Add filters
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if endorsement_type:
            query += ' AND endorsement_type = ?'
            params.append(endorsement_type)
        
        if policy_number:
            query += ' AND policy_number LIKE ?'
            params.append(f'%{policy_number}%')
        
        # Add sorting
        valid_sort_columns = ['created_at', 'policy_number', 'endorsement_type', 'status', 'updated_at']
        if sort_by not in valid_sort_columns:
            sort_by = 'created_at'
        
        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'DESC'
        
        query += f' ORDER BY {sort_by} {sort_order}'
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            endorsements = []
            for row in rows:
                endorsement = dict(row)
                # Parse JSON data
                endorsement['json_data'] = json.loads(endorsement['json_data'])
                endorsements.append(endorsement)
            
            return endorsements
    
    def update_endorsement(self, endorsement_id: int, data: Dict[str, Any], updated_by: str) -> bool:
        """Update an endorsement"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE endorsements 
                    SET policy_number = ?, endorsement_type = ?, endorsement_version = ?, 
                        endorsement_validity = ?, concepto_id = ?, status = ?, json_data = ?,
                        updated_at = CURRENT_TIMESTAMP, updated_by = ?
                    WHERE id = ?
                ''', (
                    data.get('policy_number'),
                    data.get('endorsement_type'),
                    data.get('endorsement_version'),
                    data.get('endorsement_validity'),
                    data.get('concepto_id'),
                    data.get('status'),
                    json.dumps(data.get('json_data', {})),
                    updated_by,
                    endorsement_id
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating endorsement: {e}")
            return False
    
    def delete_endorsement(self, endorsement_id: int) -> bool:
        """Delete an endorsement"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM endorsements WHERE id = ?', (endorsement_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting endorsement: {e}")
            return False
    
    def get_unique_endorsement_types(self) -> List[str]:
        """Get all unique endorsement types for search dropdown"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT endorsement_type FROM endorsements ORDER BY endorsement_type')
            return [row[0] for row in cursor.fetchall()]
    
    def get_unique_policy_numbers(self) -> List[str]:
        """Get all unique policy numbers for search dropdown"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT policy_number FROM endorsements ORDER BY policy_number')
            return [row[0] for row in cursor.fetchall()]
    
    def search_endorsements(self, search_term: str) -> List[Dict]:
        """Search endorsements by policy number or endorsement type"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM endorsements 
                WHERE policy_number LIKE ? OR endorsement_type LIKE ?
                ORDER BY created_at DESC
                LIMIT 50
            ''', (f'%{search_term}%', f'%{search_term}%'))
            
            rows = cursor.fetchall()
            endorsements = []
            for row in rows:
                endorsement = dict(row)
                endorsement['json_data'] = json.loads(endorsement['json_data'])
                endorsements.append(endorsement)
            
            return endorsements

# Initialize database instance
database = Database()
db = database  # For compatibility
user_model = UserModel(database)
endorsement_model = EndorsementModel(database)

if __name__ == "__main__":
    # Test the database setup
    print("🚀 Testing database setup...")
    
    # Test user creation
    print("📝 Creating test user...")
    user_created = user_model.create_user("testuser", "password123", "Test User", "test@company.com")
    print(f"✅ User created: {user_created}")
    
    # Test authentication
    print("🔐 Testing authentication...")
    user = user_model.authenticate("admin", "admin123")
    print(f"✅ Admin login: {user is not None}")
    
    print("✨ Database setup complete!")