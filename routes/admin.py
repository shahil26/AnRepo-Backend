from fastapi import APIRouter, Depends, HTTPException, status, Form
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from routes.auth import get_current_user, get_password_hash
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from database import db
from schemas import LoginCreds, ForgetPassword, AddUsers, TokenData
from dotenv import load_dotenv
import os, json

load_dotenv()

router = APIRouter()

def convert_many_requests(requests):
    new_requests = []
    for request in requests:
        request['_id'] = str(request['_id'])
        new_requests.append(request)
    return new_requests

@router.post("/request_access")
async def request_access(text: str = Form(...), role: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_ADMIN_REQUESTS']
        request_body = {'_id': ObjectId(), 'email_id': current_user.email, 'text': text, 'role': role.split(',')}
        operation_id = collection.insert_one(request_body)
        return {"status": "200", "data": {"id": str(operation_id.inserted_id)}, "message": "Request sent successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.get("/list_requests")
async def list_requests(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_ADMIN_REQUESTS']
        requests = collection.find()
        requests = convert_many_requests(requests)
        return {"status": "200", "data": requests, "message": "Requests retrieved successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/approve_access")
async def approve_access(request_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_ADMIN_REQUESTS']
        request = collection.find_one({'_id': ObjectId(request_id)})
        if request:
            roles, user = request['role'], request['email_id']
            institute_collection = db[current_user.institute_id]
            user_in_institute = institute_collection.find_one({'email_id': user})
            if user_in_institute:
                user_in_institute['roles'] += roles
                institute_collection.update_one({'email_id': user}, {'$set': {'roles': user_in_institute['roles']}})
                collection.delete_one({'_id': ObjectId(request_id)})
                return {"status": "200", "data": {"id": str(request_id)}, "message": "Request approved successfully"}
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=404, detail="Request not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/disapprove_access")
async def disapprove_access(request_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_ADMIN_REQUESTS']
        request = collection.find_one({'_id': ObjectId(request_id)})
        if request:
            collection.delete_one({'_id': ObjectId(request_id)})
            return {"status": "200", "data": {"id": str(request_id)}, "message": "Request disapproved"}
        else:
            raise HTTPException(status_code=404, detail="Request not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/add_individual")
async def add_individual(email_id: str = Form(...), role: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id]
        user = collection.find_one({'email_id': email_id})
        if user:
            user['roles'] += role.split(',')
            collection.update_one({'email_id': email_id}, {'$set': {'roles': user['roles']}})
            return {"status": "200", "data": {"email_id": email_id}, "message": "User roles modified successfully"}
        else:
            operation_id = collection.insert_one({'_id': ObjectId(), 'institute_id': current_user.institute_id, 'email_id': email_id, 'password': get_password_hash(email_id), 'roles': role.split(','), 'otp': '', 'otp_validity': '', 'department': ''})
            return {"status": "200", "data": {"id": str(operation_id.inserted_id)}, "message": "User added and role alloted successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/add_domain")
async def add_domain(domain: str = Form(...), role: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id]
        users = collection.find({'email_id': {'$regex': domain}})
        for user in users:
            user['roles'] += role.split(',')
            collection.update_one({'email_id': user['email_id']}, {'$set': {'roles': user['roles']}})
        return {"status": "200", "data": {"domain": domain}, "message": "Roles alloted to domain successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/remove_individual")
async def remove_individual(email_id: str = Form(...), role: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id]
        user = collection.find_one({'email_id': email_id})
        if user:
            user['roles'] = list(set(user['roles']) - set(role.split(',')))
            collection.update_one({'email_id': email_id}, {'$set': {'roles': user['roles']}})
            return {"status": "200", "data": {"email_id": email_id}, "message": "User roles modified successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/remove_domain")
async def remove_domain(domain: str = Form(...), role: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id]
        users = collection.find({'email_id': {'$regex': domain}})
        for user in users:
            user['roles'] = list(set(user['roles']) - set(role.split(',')))
            collection.update_one({'email_id': user['email_id']}, {'$set': {'roles': user['roles']}})
        return {"status": "200", "data": {"domain": domain}, "message": "Roles removed from domain successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/set_controls")
async def set_controls(control_changes: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_ROLES_ACCESS']
        controls = collection.find()
        if controls:
            collection.delete_many({})
        
        # control_changes = [dict(owners) for owners in control_changes.split(',')]
        # for owners in control_changes:
        #     key = owners.keys()
        #     value = owners.values()
        #     inner_key = value[0].keys()
        #     inner_value = value[0].values()
        #     operation_id = collection.insert_one({'_id': ObjectId(), 'role': key[0], 'controls': [inner_key[i] for i in range(len(inner_value)) if inner_value[i] == True]})
        #     return {"status": "200", "data": {"id": str(operation_id.inserted_id)}, "message": "Controls set successfully"}
        operation_id = collection.insert_one({'_id': ObjectId(), 'controls': json.dumps(control_changes)})
        return {"status": "200", "data": {"id": str(operation_id.inserted_id)}, "message": "Controls set successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/list_controls")
async def list_controls(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_ROLES_ACCESS']
        controls = collection.find()
        controls = convert_many_requests(controls)
        return {"status": "200", "data": controls, "message": "Controls retrieved successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/list_publications")
async def list_publications(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_PUBLICATIONS']
        publications = collection.find()
        publications = convert_many_requests(publications)
        return {"status": "200", "data": publications, "message": "Publications retrieved successfully"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.put("/approve_publication")
async def approve_publication(publication_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_PUBLICATIONS']
        publication = collection.find_one({'_id': ObjectId(publication_id)})
        if publication:
            collection.update_one({'_id': ObjectId(publication_id)}, {'$set': {'is_approved': True}})
            return {"status": "200", "data": {"id": str(publication_id)}, "message": "Publication approved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Publication not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.put("/disapprove_publication")
async def disapprove_publication(publication_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_PUBLICATIONS']
        publication = collection.find_one({'_id': ObjectId(publication_id)})
        if publication:
            collection.update_one({'_id': ObjectId(publication_id)}, {'$set': {'is_approved': False}})
            return {"status": "200", "data": {"id": str(publication_id)}, "message": "Publication disapproved"}
        else:
            raise HTTPException(status_code=404, detail="Publication not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.put("/approve")
async def approve(item_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection1, collection2 = db[current_user.institute_id+'_FILES'], db[current_user.institute_id+'_VISUALISATIONS']
        in_files, in_visualizations = collection1.find_one({'_id': ObjectId(item_id)}), collection2.find_one({'_id': ObjectId(item_id)})
        if in_files:
            collection1.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_approved': True}})
            return {"status": "200", "message": "Item approved successfully"}
        elif in_visualizations:
            collection2.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_approved': True}})
            return {"status": "200", "message": "Item approved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/disapprove")
async def disapprove(item_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email})
    if user:
        collection1, collection2 = db[current_user.institute_id+'_FILES'], db[current_user.institute_id+'_VISUALISATIONS']
        in_files, in_visualizations = collection1.find_one({'_id': ObjectId(item_id)}), collection2.find_one({'_id': ObjectId(item_id)})
        if in_files:
            collection1.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_approved': False}})
            return {"status": "200", "message": "Item disapproved successfully"}
        elif in_visualizations:
            collection2.update_one({'_id': ObjectId(item_id)}, {'$set': {'is_approved': False}})
            return {"status": "200", "message": "Item disapproved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")