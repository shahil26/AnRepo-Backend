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

load_dotenv()

router = APIRouter()

def convert_many_requests(requests):
    new_requests = []
    for request in requests:
        request['_id'] = str(request['_id'])
        new_requests.append(request)
    return new_requests
    
@router.post("/raise_notification")
async def raise_notification(cred: RaiseNotifications, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        if current_user.institute_id != cred.institute_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        else:
            notifications_collection = db[cred.institute_id+'_NOTIFICATIONS']
            cred = dict(cred)
            cred['_id'] = ObjectId()
            opertation_id = notifications_collection.insert_one(cred)
            return {"status": "200", "data": {"id": str(opertation_id.inserted_id)}, "message": "Notification raised successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/view_notifications")
async def get_notifications(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        if current_user.institute_id:
            notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
            notifications = notifications_collection.find({'to': current_user.email})
            return {"status": "200", "data": {"notifications": convert_many_requests(notifications)}, "message": f"Notifications fetched successfully"}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.delete("/delete_notification")
async def delete_notification(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        if current_user.institute_id:
            notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
            notifications_collection.delete_one({'email_id': current_user.email})
            return {"status": "200", "data": {}, "message": f"Notifications deleted successfully for {current_user.email}"}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/send_single")
async def send_single(request: NotificationRequest, current_user: TokenData = Depends(get_current_user)):
    email, message = request.email, request.message
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        if current_user.institute_id:
            notifications_collection = db['RGIPT_NOTIFICATIONS']
            data = {'_id': ObjectId(), 'from': current_user.email, 'to': email, 'message': message, 'type': 'single'}
            opertation_id = notifications_collection.insert_one(data)
            return {"status": "200", "data": {"id": str(opertation_id.inserted_id)}, "message": "Notification sent successfully"}
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/send_group")
async def send_group(message: str = Form(...), role: Optional[str] = Form(None), department: Optional[str] = Form(None), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection1, collection2 = db[str(current_user.institute_id)], db['MASTER_ADMIN_CREDS']
        if role and not department:
            if collection1.find({'$in': {'role': role}}):
                users = collection1.find({'$in': {'role': role}})
                notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
                for user in users:
                    data = {'_id': ObjectId(), 'from': current_user.email, 'to': user, 'message': message, 'type': 'group'}
                    opertation_id = notifications_collection.insert_one(data)
                return {"status": "200", "message": "Notifications sent successfully"}
            elif collection2.find({'$in': {'role': role}}):
                users = collection2.find({'$in': {'role': role}})
                notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
                for user in users:
                    data = {'_id': ObjectId(), 'from': current_user.email, 'to': user, 'message': message, 'type': 'group'}
                    opertation_id = notifications_collection.insert_one(data)
                return {"status": "200", "message": "Notifications sent successfully"}
            else:
                raise HTTPException(status_code=401, detail="Unauthorized")
        elif department and not role:
            if collection1.find({'$in': {'department': department}}):
                users = collection1.find({'$in': {'department': department}})
                notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
                for user in users:
                    data = {'_id': ObjectId(), 'from': current_user.email, 'to': user, 'message': message, 'type': 'group'}
                    opertation_id = notifications_collection.insert_one(data)
                return {"status": "200", "message": "Notifications sent successfully"}
            elif collection2.find({'$in': {'department': department}}):
                users = collection2.find({'$in': {'department': department}})
                notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
                for user in users:
                    data = {'_id': ObjectId(), 'from': current_user.email, 'to': user, 'message': message, 'type': 'group'}
                    opertation_id = notifications_collection.insert_one(data)
                return {"status": "200", "message": "Notifications sent successfully"}
            else:
                raise HTTPException(status_code=401, detail="Unauthorized")
        elif role and department:
            if collection1.find({'$in': {'role': role}, '$and': {'department': department}}):
                users = collection1.find({'$in': {'role': role}, '$and': {'department': department}})
                notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
                for user in users:
                    data = {'_id': ObjectId(), 'from': current_user.email, 'to': user, 'message': message, 'type': 'group'}
                    opertation_id = notifications_collection.insert_one(data)
                return {"status": "200", "message": "Notifications sent successfully"}
            elif collection2.find({'$in': {'role': role}, '$and': {'department': department}}):
                users = collection2.find({'$in': {'role': role}, '$and': {'department': department}})
                notifications_collection = db[current_user.institute_id+'_NOTIFICATIONS']
                for user in users:
                    data = {'_id': ObjectId(), 'from': current_user.email, 'to': user, 'message': message, 'type': 'group'}
                    opertation_id = notifications_collection.insert_one(data)
                return {"status": "200", "message": "Notifications sent successfully"}
            else:
                raise HTTPException(status_code=401, detail="Unauthorized")
        else:
            raise HTTPException(status_code=404, detail="Bad Request")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")