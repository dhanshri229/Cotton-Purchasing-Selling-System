import sqlite3

def get_db_connection():
    conn = sqlite3.connect('cotton.db')
    conn.row_factory = sqlite3.Row  
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT,
            village TEXT
        )
    ''')

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT NOT NULL,
            driver_name TEXT,
            driver_mobile TEXT
        )
    ''')

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            vehicle_id INTEGER,
            date TEXT,
            weight REAL,         
            rate REAL,           
            total_amount REAL,   
            paid_amount REAL DEFAULT 0,
            FOREIGN KEY (farmer_id) REFERENCES farmers (id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
    ''')

   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            date TEXT,
            amount REAL,
            payment_mode TEXT,   -- Cash, Bank, UPI
            FOREIGN KEY (farmer_id) REFERENCES farmers (id)
        )
    ''')

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_name TEXT NOT NULL,
            date TEXT,
            weight REAL,         
            rate REAL,          
            total_amount REAL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database")

if __name__ == '__main__':
    init_db()