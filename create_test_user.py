"""Create user@test in the database."""
from app.core.security import get_password_hash
from app.db.session import SyncSessionLocal
from app.db.models import User

db = SyncSessionLocal()

# Check if already exists
existing = db.query(User).filter(User.email == "user@test").first()
if existing:
    print(f"⚠️  user@test ya existe (rol: {existing.rol})")
else:
    user = User(
        email="user@test",
        hashed_password=get_password_hash("admin123"),
        rol="admin",
        scopes=["admin:read", "user:read", "admin:products", "admin:orders", "admin:users"],
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ Creado: {user.email} / admin123 (rol: {user.rol})")

# List all users
print("\nUsuarios en la BD:")
for u in db.query(User).all():
    print(f"  • {u.email} — {u.rol}")

db.close()
