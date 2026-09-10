"""Bootstrap an initial admin interactively without demo seeding or command-line passwords."""
import getpass
from app.database import SessionLocal,init_db
from app.models import User
from app.auth import hash_password


def main():
    email=input('Admin email: ').strip().lower()
    password=getpass.getpass('Password (at least 14 characters): ')
    if '@' not in email or len(password)<14: raise SystemExit('Valid email and 14+ character password required')
    if password != getpass.getpass('Confirm password: '): raise SystemExit('Passwords differ')
    init_db()
    with SessionLocal.begin() as db:
        if db.query(User).count(): raise SystemExit('Users already exist; use authenticated user administration')
        db.add(User(email=email,name='Administrator',role='admin',password_hash=hash_password(password),is_active=True))
    print('Initial administrator created.')

if __name__=='__main__': main()
