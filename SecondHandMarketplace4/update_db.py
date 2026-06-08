from app import app, db
from sqlalchemy import text

def update_db():
    with app.app_context():
        # Check if we're using SQLite
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            print("Detected SQLite database. Applying migrations...")
            
            with db.engine.connect() as conn:
                try:
                    # Add is_admin to user
                    conn.execute(text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                    print("Added is_admin to user table.")
                except Exception as e:
                    print(f"Column is_admin might already exist: {e}")

                try:
                    # Add image_hash to product
                    conn.execute(text("ALTER TABLE product ADD COLUMN image_hash VARCHAR(64)"))
                    print("Added image_hash to product table.")
                except Exception as e:
                    print(f"Column image_hash might already exist: {e}")
                
            # Create new tables (FraudAlert)
            db.create_all()
            print("Ensured all tables exist (including FraudAlert).")
            
        else:
            # For MySQL or others, usually better to use Alembic, but for this scope check constraints
            print("Not using SQLite. Attempting db.create_all() for new tables...")
            db.create_all()
            print("Done. NOTE: If columns are missing in existing tables, please manually migrate.")

if __name__ == "__main__":
    update_db()
