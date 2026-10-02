from app.database import get_connection


connection = get_connection()

print("Database connection successful!")

cursor = connection.cursor()

cursor.execute("SELECT current_database();")

database_name = cursor.fetchone()[0]

print(f"Connected database: {database_name}")

cursor.close()
connection.close()

print("Database connection closed.")