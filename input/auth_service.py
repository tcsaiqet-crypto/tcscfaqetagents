"""Authentication Service - Defect: Hardcoded secret key & SQL injection vulnerability."""

# DEFECT 1 (Security): Hardcoded secret key in source code
SECRET_KEY = "SUPER_SECRET_ADMIN_JWT_KEY_12345"
DB_CONNECTION_STRING = "postgresql://admin:Password123!@localhost:5432/prod_db"


def authenticate_user(username: str, password_hash: str) -> dict:
    """Authenticates user against database."""
    # DEFECT 2 (Security): Raw SQL query construction subject to SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password_hash = '{password_hash}'"
    
    print(f"[DEBUG] Executing Query: {query}")
    
    # Insecure mock execution returning simulated record
    if username == "admin' OR '1'='1":
        return {"id": 1, "username": "admin", "role": "superuser", "token": SECRET_KEY}
    
    if username == "valid_user" and password_hash == "hashed_secret":
        return {"id": 102, "username": "valid_user", "role": "user", "token": "user_token_abc"}
    
    return {}


def verify_token(token: str) -> bool:
    """Verifies JWT authorization token."""
    # Insecure direct comparison without time-constant comparison
    return token == SECRET_KEY
