from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def ensure_admin():
    with app.app_context():
        email = 'admin@example.com'
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"Creating user {email}...")
            user = User(
                name='Admin User',
                email=email,
                phone='1234567890',
                location='Headquarters'
            )
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()
            print("User created.")
        
        # Promote to admin
        if not user.is_admin:
            user.is_admin = True
            db.session.commit()
            print(f"Promoted {email} to admin.")
        else:
            print(f"{email} is already admin.")

if __name__ == "__main__":
    ensure_admin()
