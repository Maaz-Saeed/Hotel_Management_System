from getpass import getpass
from app.crud import user as crud_user
from app.db.session import Sessionlocal
from app.schemas.user import UserCreate

def main():
    full_name = input("Full Name: ").strip()
    email = input("Admin Email: ").strip()
    password = getpass("Password (must be 8 characters or above): ")

    db = Sessionlocal()
    try:
        if crud_user.get_by_email(db, email):
            print("Email is Already Registered.")
            return
        data = UserCreate(
            full_name=full_name, email=email, password= password, role="admin"
        )
        user = crud_user.create_user(db, data)
        print(f"Admin Account Created: {user.email} (id={user.id})")
    finally:
        db.close()

if __name__ == "__main__":
    main()
    