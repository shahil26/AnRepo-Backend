from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from datetime import datetime
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from routes.auth import get_current_user
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from database import db, fs
from schemas import TokenData
from dotenv import load_dotenv
import os, io, gridfs

router = APIRouter()

def convert_many_images(images):
    new_images = []
    for image in images:
        image['_id'] = str(image['_id'])
        new_images.append(image)
    return new_images

@router.post("/add")
async def add_image(file: UploadFile = File(...), roles_access: str = Form(...), file_name: str = Form(...), file_type: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_IMAGES']
        exsisting_image = collection.find_one({'file_name': file_name})
        if exsisting_image:
            return {'image_id': str(exsisting_image['_id']), 'file_size': exsisting_image['file_size'], 'message': 'Image already exists.'}
        else:
            # try:
            file_id = ObjectId()
            fs.put(file.file, filename=file_name, _id=file_id, content_type=file.content_type)
        #         file_size = fs.get(file_id).length
        #     except gridfs.errors.GridFSError:
        #         raise HTTPException(status_code=500, detail="Error in uploading file")
        # try:
        #     operation_id = collection.insert_one({'_id': file_id, 'institute_id': current_user.institute_id, 'roles': user['roles'], 'file_name': file_name, 'file_type': file_type, 'file_id': str(file_id), 'file_size': file_size, 'uploader': current_user.email, 'roles_access': roles_access.split(','), 'content_type': file.content_type, 'date_uploaded': datetime.now(), 'is_deleted': False})
        # except:
        #     raise HTTPException(status_code=300, detail="Error in uploading file")

        # return {'operation_id': operation_id, 'image_id': str(file_id), 'file_size': file_size, 'message': 'Image uploaded successfully'}
        print(roles_access, file_name, file_type, current_user.email, file)
        return {roles_access, file_name, file_type, current_user.email, file}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/list")
async def list_images(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_IMAGES']
        images = collection.find({'is_deleted': False})
        images = convert_many_images(images)
        return {'status': '200', 'data': images, 'message': 'Images listed successfully'}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/download")
async def download_image(image_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            file = fs.get(ObjectId(image_id))
            headers = {"Content-Disposition": f"attachment; filename={file.filename}"}
            return StreamingResponse(io.BytesIO(file.read()), media_type=file.content_type, headers=headers)
        except gridfs.errors.NoFile:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.put("/delete")
async def delete_image(image_id: str = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        collection = db[current_user.institute_id+'_IMAGES']
        image = collection.find_one({'_id': ObjectId(image_id)})
        if image:
            collection.update_one({'_id': ObjectId(image_id)}, {'$set': {'is_deleted': True}})
            return {'status': '200', 'message': 'Image deleted successfully'}
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")