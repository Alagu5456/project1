from app import app, db
from models import User

def set_admin(email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"User {email} is now an admin.")
            return True
        else:
            print(f"User {email} not found.")
            return False

def list_users():
    with app.app_context():
        users = User.query.all()
        for u in users:
            print(f"ID: {u.id}, Email: {u.email}, Admin: {u.is_admin}")

if __name__ == "__main__":
    list_users()
    # Uncomment to promote a user or run interactively
    # set_admin('admin@example.com') 
