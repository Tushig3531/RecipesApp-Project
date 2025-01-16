from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Updated DATABASE_URI with URL-encoded password
DATABASE_URI = 'mysql+pymysql://Egshig:mypassword@flaskdb.cno0osquwwky.us-east-2.rds.amazonaws.com:3306/flaskaws'

def test_connection(uri):
    try:
        engine = create_engine(uri)
        connection = engine.connect()
        connection.execute("SELECT 1")
        connection.close()
        print("Database connection successful!")
    except SQLAlchemyError as e:
        print(f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection(DATABASE_URI)
