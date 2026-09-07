import pymysql
 
# DATABASE CONFIGURATION
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "my password",
    "database": "readhub"
}
 
def get_connection():
    """Returns a new MySQL connection."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("DB ERROR:", e)
        return None
 
if __name__ == "__main__":
    print("Testing database connection...")
    conn = get_connection()
    if conn:
        print("SUCCESS! Connected to readhub database!")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("Tables found:")
        for table in tables:
            print("  -", table[0])
        cursor.close()
        conn.close()
        print("Connection closed.")
    else:
        print("FAILED! Could not connect.")