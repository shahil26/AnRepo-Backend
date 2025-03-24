from fastapi import APIRouter, Depends, HTTPException, status, Form
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from routes.auth import get_current_user
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from database import db
from schemas import LoginCreds, ForgetPassword, AddUsers, TokenData, UserDetails, RoleDetails, RecentActions, RaiseNotifications, NotificationRequest
from dotenv import load_dotenv
import os

router = APIRouter()

def add_recents(institute_id, email_id, item_id, type):
    recent_actions_collection = db[institute_id + 'RECENT_ACTIONS']
    operation_id = recent_actions_collection.insert_one({'_id': ObjectId(), 'email_id': email_id, 'item_id': item_id, 'type': type, 'date_added': datetime.now()})
    return {"status": "200", "data": {"id": str(operation_id)}, "message": "Actions added to Recents successfully"}

@router.post("/add")
async def create_recents(item_id: str = Form(...), type: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        add_recents(current_user.institute_id, current_user.email, item_id, type)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/list")
async def view_recents(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        recent_actions_collection = db[current_user.institute_id+'_RECENT_ACTIONS']
        recents = recent_actions_collection.find({'email_id': current_user.email})
        return {"status": "200", "data": {"recents": list(recents)}, "message": f"Recents fetched successfully for {current_user.email}"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/remove")
async def remove_recents(recent_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        recent_actions_collection = db[current_user.institute_id+'_RECENT_ACTIONS']
        recent_actions_collection.delete_one({'_id': ObjectId(recent_id)})
        return {"status": "200", "message": f"Recents removed successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
