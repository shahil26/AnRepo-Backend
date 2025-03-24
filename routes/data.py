from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from routes.auth import get_current_user
from routes.recents import add_recents
from schemas import LoginCreds, ForgetPassword, TokenData
from database import db, fs
from utils import convert_one_list_file
from typing import List
from bson import ObjectId
import io
import gridfs

router = APIRouter()

# upload_file?institute_id=123&file_name=abc&file_type=xyz&description=desc&file=abx.pdf&roles=[role1,role2]
@router.post("/upload_file")
async def upload_file(title: str = Form(...), file_type: str = Form(...), description: str = Form(...), access_roles: str = Form(...), file: UploadFile = File(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            # controls_collection = db[current_user.institute_id+'_ROLES_ACCESS']
            # is_approved = False if 'needs_approval' == True in controls_collection.find_one({'role': user.get('roles')[0]})['controls'] else True
            file_dict = {
                'uploader': user.get('email_id'),
                'roles_access': access_roles,
                'file_name': title,
                'file_type': file_type,
                'description': description,
                'content_type': file.content_type,
                'date_uploaded': datetime.now(),
                'is_deleted': False,
                # 'is_approved': is_approved
            }
            collection = db[current_user.institute_id + '_FILES']

            existing_file = collection.find_one({'file_name': file_dict['file_name']})
            if existing_file:
                return {'file_id': str(existing_file['_id']), 'file_size': existing_file['file_size'], 'message': 'File already exists.'}
            
            file_id = ObjectId()
            fs.put(file.file, filename=title, _id=file_id, content_type=file.content_type)

            file_size = fs.get(file_id).length

            file_dict['_id'] = file_id
            file_dict['file_id'] = str(file_id)
            file_dict['file_size'] = file_size

            collection.insert_one(file_dict)
            add_recents(current_user.institute_id, current_user.email_id, file_id, 'data')
            
            return {'file_id': str(file_id), 'file_size': file_size, 'message': 'File uploaded successfully'}
        
        except Exception as e:
            return {'file_id': None, 'message': str(e)}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
# /list_files?institute_id=123
@router.get("/list_files")
async def list_files(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:    
        try:
            collection = db[str(current_user.institute_id).upper() + '_FILES']
            files = collection.find()
            accessible_files = []
            user_roles = user.get('roles', [])
            user_email = current_user.email
            files_meta_data = []
            for file in files:
                if user_email == file['uploader'] or 'Admin' in user_roles or any(role in user_roles for role in file['roles_access'].split(',')):
                    accessible_files.append(file)
                    file_data = convert_one_list_file(file)
                    uploader = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': file['uploader']}) or db[str(current_user.institute_id)].find_one({'email_id': file['uploader']})
                    file_data['uploader_roles'] = uploader.get('roles', [])
                    files_meta_data.append(file_data)
                    
            if not accessible_files:
                return {'files_meta_data': [], 'message': 'No accessible files found'}
            return {'files_meta_data': files_meta_data, 'message': 'Files listed successfully'}
        except Exception as e:
            return {'files_meta_data': [], 'message': str(e)}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

# /download_file?&file_id=abc
@router.get("/download_file/{file_id}")
async def download_file(file_id: str, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:    
        try:
            file = fs.get(ObjectId(file_id))
            headers = {"Content-Disposition": f"attachment; filename={file.filename}"}
            return StreamingResponse(io.BytesIO(file.read()), media_type=file.content_type, headers=headers)
        except gridfs.errors.NoFile:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
# /delete_file?file_id=abc
@router.delete("/delete_file/{file_id}")
async def delete_file(file_id: str, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:    
        try:
            collection = db[current_user.institute_id + '_FILES']
            file = collection.find_one({'_id': ObjectId(file_id)})
            if file:
                if current_user.email == file['uploader']:
                    #If isdelete is False or not present, set it to True
                    if file.get('is_deleted', False) == False:
                        collection.update_one({'_id': ObjectId(file_id)}, {'$set': {'is_deleted': True}})
                        return {'file_id': file_id, 'message': 'File moved to trash'}
                    else:
                        # If isdelete is True, delete the file
                        collection.delete_one({'_id': ObjectId(file_id)})
                        return {'file_id': file_id, 'message': 'File deleted'}
                else:
                    return {'file_id': file_id, 'message': 'Unauthorized to delete file'}
            else:
                return {'file_id': file_id, 'message': 'File not found'}
        except Exception as e:
            return {'file_id': file_id, 'message': str(e)}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

# /peek_file?file_id=abc[&max_size=1024]
@router.get("/peek_file/{file_id}")
async def peek_file(file_id: str, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    
    if user:
        try:
            file = fs.get(ObjectId(file_id))
            headers = {
                "Content-Disposition": f"inline; filename={file.filename}"
            }
            return StreamingResponse(io.BytesIO(file.read()), media_type=file.content_type, headers=headers)
        except gridfs.errors.NoFile:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")