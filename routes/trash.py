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
from schemas import TokenData
from dotenv import load_dotenv
import os

router = APIRouter()

def convert_many_requests(requests, type):
    new_requests = []
    for request in requests:
        request['_id'] = str(request['_id'])
        request['type'] = type
        new_requests.append(request)
    return new_requests

@router.get("/dump")
async def dump(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection1, collection2, collection3, collection4 = db[current_user.institute_id+'_FILES'], db[current_user.institute_id+'_VISUALISATIONS'], db[current_user.institute_id+'_WORK_MANAGER'], db[current_user.institute_id+'_IMAGES']
        files, visualisations, tasks, images = collection1.find({'is_deleted': True}) or [], collection2.find({'is_deleted': True}) or [], collection3.find({'is_deleted': True}) or [], collection4.find({'is_deleted': True}) or []
        files, visualisations, tasks, images = convert_many_requests(files, 'data'), convert_many_requests(visualisations, 'visualization'), convert_many_requests(tasks, 'work'), convert_many_requests(images, 'image')
        return {"status": "200", "data": {"files": files, "visualisations": visualisations, "tasks": tasks, "images": images}, "message": "Dump shown successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.put("/restore")
async def restore(item_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection1, collection2, collection3, collection4 = db[current_user.institute_id+'_FILES'], db[current_user.institute_id+'_VISUALISATIONS'], db[current_user.institute_id+'_WORK_MANAGER'], db[current_user.institute_id+'_IMAGES']
        in_files, in_visualizations, in_work_manager, in_images = collection1.find_one({'_id': ObjectId(item_id)}), collection2.find_one({'_id': ObjectId(item_id)}), collection3.find_one({'_id': ObjectId(item_id)}), collection4.find_one({'_id': ObjectId(item_id)})
        if in_files:
            collection1.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_deleted': False}})
            return {"status": "200", "message": "Item restored successfully"}
        elif in_visualizations:
            collection2.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_deleted': False}})
            return {"status": "200", "message": "Item restored successfully"}
        elif in_work_manager:
            collection3.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_deleted': False}})
            return {"status": "200", "message": "Item restored successfully"}
        elif in_images:
            collection4.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_deleted': False}})
            return {"status": "200", "message": "Item restored successfully"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.put("/delete")
async def delete(item_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection1, collection2, collection3, collection4 = db[current_user.institute_id+'_FILES'], db[current_user.institute_id+'_VISUALISATIONS'], db[current_user.institute_id+'_WORK_MANAGER'], db[current_user.institute_id+'_IMAGES']
        in_files, in_visualizations, in_work_manager, in_images = collection1.find_one({'_id': ObjectId(item_id)}), collection2.find_one({'_id': ObjectId(item_id)}), collection3.find_one({'_id': ObjectId(item_id)}), collection4.find_one({'_id': ObjectId(item_id)})
        if in_files:
            collection1.delete_one({'_id': ObjectId(item_id)})
            return {"status": "200", "message": "Item deleted successfully"}
        elif in_visualizations:
            collection2.delete_one({'_id': ObjectId(item_id)})
            return {"status": "200", "message": "Item deleted successfully"}
        elif in_work_manager:
            collection3.delete_one({'_id': ObjectId(item_id)})
            return {"status": "200", "message": "Item deleted successfully"}
        elif in_images:
            collection4.delete_one({'_id': ObjectId(item_id)})
            return {"status": "200", "message": "Item deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")