from datetime import timedelta
from fastapi import Depends, FastAPI, Request, Body, status,HTTPException
from fastapi.encoders import jsonable_encoder
from database import SessionLocal, DBContext, engine
from sqlalchemy.orm import Session
import uvicorn
import crud, schemas, models

import os
from fastapi_login import LoginManager
from dotenv import load_dotenv

from passlib.context import CryptContext
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY_64')
ACCESS_TOKEN_EXPIRE_MINUTES=60 # 60 phut

manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name="auth"


### password ###

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_hashed_password(plain_password):
    return pwd_ctx.hash(plain_password)

def verify_password(plain_password, hashed_password):
    return pwd_ctx.verify(plain_password,hashed_password)

### -------- ###
def get_database():
    with DBContext() as db:    
        yield db


app = FastAPI()

@manager.user_loader()
def get_user(username: str, db: Session = None):
    if db is None:
        with DBContext() as db:
            return crud.get_user_by_username(db=db,username=username)
    return crud.get_user_by_username(db=db,username=username)

def authenticate_user(username: str, password: str, db: Session = Depends(get_database)):
    user:schemas.User = crud.get_user_by_username(db=db,username=username)
    if not user:
        return None
    if not verify_password(plain_password=password,hashed_password=user.hash_pass):
        return None
    return user

class NotAuthenticatedException(Exception):
    pass

def not_authenticated_exception_handler(request, exception):
    return RedirectResponse("/login")

manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(NotAuthenticatedException, not_authenticated_exception_handler)


@app.get("/")
async def root(request: Request):
    return {"request":"ROOT"}



@app.post("/create/user", tags=["user"])
async def create_user( id : int=Body(...), 
username : str = Body(...),  
password : str = Body(...),
role : str = Body(...),
db: Session = Depends(get_database)):
    invalid = False
    hash_password = get_hashed_password(password)
    if crud.get_user(db = db, id = id) or crud.get_user_by_username(db = db, username=username):
        invalid  = True
    if not invalid:
        return crud.create_user(db=db,id=id, role = role,user=
        schemas.UserCreate(username=username, hash_pass=hash_password))
    return status.HTTP_400_BAD_REQUEST

@app.get("/login", tags=["user"])
async def login():
    return {"login":"tecacom-admin"}

@app.post('/login', tags = ['user'])
async def login(request: Request, 
form_data: OAuth2PasswordRequestForm = Depends(), 
db: Session = Depends(get_database)):
    user:schemas.User = authenticate_user(
        username=form_data.username,
        password = form_data.password, db = db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = manager.create_access_token(
        data={"sub": user.username},
        expires=access_token_expires)
    
    resp = JSONResponse(access_token, status_code=status.HTTP_200_OK)
    #RedirectResponse("/tasks", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp,access_token)
    return resp


@app.get('/logout')
async def protected_route(request: Request, user:schemas.User=Depends(manager)):
    resp = JSONResponse({"status": "logout","user":user.username}, status_code=status.HTTP_200_OK)
    manager.delete_cookie(resp)
    return resp

@app.get("/home")
async def home(user: schemas.User = Depends(manager)):
    return user

# Authorization
# def role_user(func):
#     def decorator(user:schemas.User = Depends(manager)):
#         pass

def role_admin(user:schemas.User = Depends(manager)):
    return user if user.role =='admin' else None

def role_normal(user:schemas.User = Depends(manager)):
    return user if (user.role =='admin' or user.role =='normal') else None


@app.get("/admin")
async def admin(request: Request, user: schemas.User = Depends(role_admin)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission for this",
            headers={"WWW-Authorization": "Admin"},
        )
    return {"status":"Login with admin"}
@app.get("/normal")
async def normal(user: schemas.User = Depends(role_admin)):
    pass
if __name__=="__main__":
    uvicorn.run(app)
    # with DBContext() as db:
    #     a = schemas.UserCreate(username="teca2", hash_pass=get_hashed_password("123"))
    #     crud.create_user(db=db,id=3,user=a)
    # with DBContext() as db:
    #     crud.delete_user_by_username(db, username="teca2")
    # db = SessionLocal()
    # a = schemas.UserCreate(username="teca2", hash_pass=get_hashed_password("123"))
    # crud.create_user(db=db,id=3,user=a)
