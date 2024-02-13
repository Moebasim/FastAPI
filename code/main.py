# Basic example of authentication logic using FastAPI with OAuth2 and JWT tokens

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

app = FastAPI()

# Secret key for JWT token encoding/decoding
SECRET_KEY = "your_secret_key"
# Token expiration time
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Sample user data (in real-world, this would come from a database)
fake_users_db = {
    "user@example.com": {
        "email": "user@example.com",
        "hashed_password": "$2b$12$rIuY.3R1QWuN1uq2QxuT8e1yxtI5oTNU5VDDcfNsY/xxT8ujW21U6",  # password: testpassword
        "disabled": False,
    }
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User model
class User(BaseModel):
    email: str
    disabled: bool = None

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Authenticate user
def authenticate_user(email: str, password: str):
    user = fake_users_db.get(email)
    if not user:
        return False
    if not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user

# Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# Get current user from token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = fake_users_db.get(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Token endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected route", "user_email": current_user["email"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# In this code:

# Users are stored in a dictionary (fake_users_db), but in a real-world scenario, you would fetch user data from a database.
# Passwords are hashed using bcrypt.
# JWT tokens are used for authentication and are created upon successful login.
# The /token endpoint authenticates users using OAuth2PasswordRequestForm.
# The /protected endpoint is protected and can only be accessed with a valid JWT token.