from sqlalchemy.orm import Session
import models, schemas
import uuid

def get_user(db: Session, id: str):
    return db.query(models.User).filter(models.User.id == id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, id:int, role:str, user: schemas.UserCreate):
    # id = uuid.uuid4()
    # while get_user(db=db,id=str(id)):
    #     id = uuid.uuid4()
    db_user = models.User(id=id,username=user.username,hash_pass=user.hash_pass, role = role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user_by_username(db: Session, username: str):
    db.query(models.User).filter(models.User.username == username).delete()
    db.commit()



