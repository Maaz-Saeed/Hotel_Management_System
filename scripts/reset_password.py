from getpass import getpass

from app.core.security import hash_password
from app.crud import user as crud_user
from app.db.session import Sessionlocal


def main():
    email = input("User email: ").strip()
    db = Sessionlocal()
    try:
        user = crud_user.get_by_email(db, email)
        if user is None:
            print("Can't find a use with this Email.")
            return

        password = getpass("New password (8 to 72 characters): ")
        confirm = getpass("Conform password: ")
        if password != confirm:
            print("passwords not matched. Try again.")
            return
        if not 8 <= len(password) <= 72:
            print("Password should be between 8 to 72 characters.")
            return

        user.hashed_password = hash_password(password)
        db.commit()
        print(f"Password Changed: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()