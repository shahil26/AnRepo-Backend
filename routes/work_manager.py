from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from database import db
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from routes.auth import get_current_user
from schemas import TokenData
from database import db
from bson import ObjectId
import os
from datetime import datetime

load_dotenv()

router = APIRouter()

def convert_many_tasks(tasks):
    new_tasks = []
    for task in tasks:
        task['_id'] = str(task['_id'])
        task['id'] = str(task['_id'])
        new_tasks.append(task)
    return new_tasks

@router.post("/add")
async def request_task(title: str = Form(...), description: str = Form(...), assignTo: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[current_user.institute_id + '_WORK_MANAGER']
            task = {'_id': ObjectId(), 'title': title, 'description': description, 'assigned_by': current_user.email, 'assigned_to': assignTo.split(','), 'status': False, 'comments': [], 'timestamp': datetime.now(), 'is_deleted': False}
            operation_id = collection.insert_one(task)
            return {'status': 200, 'operation_id': str(operation_id), 'message': 'Request sent successfully'}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail='Unautherized')
    
@router.get("/requests")
async def get_request(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[current_user.institute_id + '_WORK_MANAGER']
            tasks_requested = collection.find({'assigned_by': current_user.email})
            tasks_requested = convert_many_tasks(tasks_requested)
            return {'status': 200, 'message': 'Task added successfully', 'data': tasks_requested}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail='Unautherized')

@router.get("/assigned")
async def get_assigned(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[current_user.institute_id + '_WORK_MANAGER']
            tasks_assigned = collection.find({'assigned_to': {'$in': [current_user.email]}})
            tasks_assigned = convert_many_tasks(tasks_assigned)
            return {'status': 200, 'message': 'Tasks retrieved successfully', 'data': tasks_assigned}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail='Unauthorized')

@router.delete("/delete/{task_id}")
async def delete_task(task_id: str, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[current_user.institute_id + '_WORK_MANAGER']
            task = collection.find_one({'_id': ObjectId(task_id)})
            if task:
                if current_user.email == task['assigned_by']:
                    collection.delete_one({'_id': ObjectId(task_id)})
                    return {'status': 200, 'message': 'Task deleted successfully'}
                else:
                    return {'status': 400, 'message': 'Unauthorized to delete task'}
            else:
                return {'status': 400, 'message': 'Task not found'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
    else:
        return {'status': 400, 'message': 'Unauthorized'}

@router.put("/status_change")
async def change_status(status: bool = Form(...), task_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[current_user.institute_id + '_WORK_MANAGER']
            task = collection.find_one({'_id': ObjectId(task_id)})
            if task:
                if current_user.email == task['assigned_by']:
                    collection.update_one({'_id': ObjectId(task_id)}, {'$set': {'status': status}})
                    return {'status': 200, 'message': 'Task status updated successfully'}
                else:
                    return {'status': 400, 'message': 'Unauthorized to change status'}
            else:
                return {'status': 400, 'message': 'Task not found'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
    else:
        return {'status': 400, 'message': 'Unauthorized'}

@router.put("/add_comment")
async def add_comment(comment: str = Form(...), task_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[current_user.institute_id + '_WORK_MANAGER']
            task = collection.find_one({'_id': ObjectId(task_id)})
            if task:
                if current_user.email == task['assigned_by']:
                    collection.update_one({'_id': ObjectId(task_id)}, {'$push': {'comments': {'comment': comment, 'commented_by': current_user.email, 'timestamp': datetime.now()}}})
                    return {'status': 200, 'message': 'Comment added successfully'}
                else:
                    return {'status': 400, 'message': 'Unauthorized to add comment'}
            else:
                return {'status': 400, 'message': 'Task not found'}
        except Exception as e:
            return {'status': 500, 'message': str(e)}
    else:
        return {'status': 400, 'message': 'Unauthorized'}