from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from database import db
from schemas import LoginCreds, ForgetPassword, TokenData, VerifyOTP, ContactUs, EmailBody
from dotenv import load_dotenv
from email_utils import send_otp_email, send_contact_us_email, send_contact_us_email_files
import os, tempfile
import zipfile
import io


load_dotenv()

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta if expires_delta else datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Helper function to verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Helper function to hash password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Get current user from access token, email and institute_id
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        institute_id: str = payload.get("institute_id")
        if email is None or institute_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, institute_id=institute_id)
    except JWTError:
        raise credentials_exception
    return token_data

@router.post("/login")
async def login(cred: LoginCreds):
    otp = cred.otp
    otp=otp.strip()
    #verify otp, if false return else move forward
    if otp:
        collection1, collection2 = db['MASTER_ADMIN_CREDS'], db[cred.institute_id]
        if collection1.find_one({'email_id': cred.email_id.lower()}):
            sys_otp = collection1.find_one({'email_id': cred.email_id.lower()}).get('otp')
            sys_otp_validity = collection1.find_one({'email_id': cred.email_id.lower()}).get('otp_validity')
            if sys_otp != otp or sys_otp_validity < datetime.now():
                return {"status": "400", "data": {}, "message": "Invalid OTP"}
        elif collection2.find_one({'email_id': cred.email_id.lower()}):
            sys_otp = collection2.find_one({'email_id': cred.email_id.lower()}).get('otp')
            sys_otp_validity = collection2.find_one({'email_id': cred.email_id.lower()}).get('otp_validity')
            if sys_otp != otp or sys_otp_validity < datetime.now():
                return {"status": "400", "data": {}, "message": "Invalid OTP"}
                    
    institute_id = cred.institute_id
    email_id = cred.email_id
    password = cred.password
    collection1 = db['MASTER_ADMIN_CREDS']

    if institute_id not in db.list_collection_names():
        return {"status": "400", "data": {}, "message": "Institute not found"}

    # Check admin credentials
    admin_cred = collection1.find_one({'institute_id': institute_id})
    if admin_cred and admin_cred.get('email_id').lower() == email_id.lower():
        if verify_password(password, admin_cred.get('password')):
            access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
            access_token = create_access_token(data={"sub": email_id, "institute_id": institute_id}, expires_delta=access_token_expires)
            return {"status": "200", "data": {"roles": admin_cred.get('roles'), "token": access_token, "name": admin_cred.get('name'), "image": admin_cred.get('image'),"keepunsaved": admin_cred.get('keepunsaved')}, "message": "Login successful"}
        else:
            return {"status": "400", "data": {}, "message": "Invalid password"}

    # Check user credentials in the institute collection
    collection2 = db[institute_id]
    user_cred = collection2.find_one({'email_id': email_id.lower()})
    
    if user_cred is None:
        return {"status": "400", "data": {}, "message": "User not found"}
    
    if user_cred.get('password') == '':
        return {"status": "400", "data": {}, "message": "Password reset required"}
    
    if verify_password(password, user_cred.get('password')):
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(data={"sub": email_id, "institute_id": institute_id}, expires_delta=access_token_expires)
        return {"status": "200", "data": {"roles": user_cred.get('roles'), "token": access_token}, "message": "Login successful"}
    else:
        return {"status": "400", "data": {}, "message": "Invalid password"}

@router.get("/validate_token")
async def validate_token(current_user: TokenData = Depends(get_current_user)):
    try:
        email = current_user.email
        institute_id = current_user.institute_id
        if email is None or institute_id is None:
            return {"status": "400", "data": {}, "message": "Invalid token"}
        
        collection1 = db['MASTER_ADMIN_CREDS']
        admin_cred = collection1.find_one({'institute_id': institute_id, 'email_id': email.lower()})
        if admin_cred:
            return {"status": "200", "data": {"institute_id":institute_id,"email": email, "roles": admin_cred.get('roles'), "name": admin_cred.get('name'), "image": admin_cred.get('image'),"keepunsaved": admin_cred.get('keepunsaved')}, "message": "Token is valid"}

        collection2 = db[institute_id]
        user_cred = collection2.find_one({'email_id': email.lower()})
        if user_cred:
            return {"status": "200", "data": {"institute_id":institute_id,"email": email, "roles": user_cred.get('roles'), "name": user_cred.get('name'), "image": user_cred.get('image'),"keepunsaved": user_cred.get('keepunsaved')}, "message": "Token is valid"}

        return {"status": "400", "data": {}, "message": "Invalid token"}
    except JWTError:
        return {"status": "400", "data": {}, "message": "Invalid token"}


# /send_otp?institute_id=123&email_id=abc
@router.post("/send_otp")
async def send_otp(cred: ForgetPassword):
    otp = send_otp_email(cred.email_id)
    collection1, collection2 = db['MASTER_ADMIN_CREDS'], db[cred.institute_id]
    if collection1.find_one({'email_id': cred.email_id.lower()}):
        collection1.update_one({'email_id': cred.email_id.lower()}, {'$set': {'otp': otp, 'otp_validity': datetime.now() + timedelta(minutes=5)}})
    else:
        collection2.update_one({'email_id': cred.email_id.lower()}, {'$set': {'otp': otp, 'otp_validity': datetime.now() + timedelta(minutes=5)}})
    return {"status": "200", "message": "OTP sent successfully"}

@router.post("/verify_otp")
async def verify_otp(cred: VerifyOTP):
    collection1, collection2 = db['MASTER_ADMIN_CREDS'], db[cred.institute_id]
    if collection1.find_one({'email_id': cred.email_id.lower()}):
        sys_otp = collection1.find_one({'email_id': cred.email_id.lower()}).get('otp')
        sys_otp_validity = collection1.find_one({'email_id': cred.email_id.lower()}).get('otp_validity')
        if sys_otp != cred.otp or sys_otp_validity < datetime.now():
            return {"status": "400", "data": {}, "message": "Invalid OTP"}
        
        result = collection1.update_one(
            {'email_id': cred.email_id.lower()}, 
            {'$set': {'password': get_password_hash(cred.password)}}
        )

        print(result.modified_count)
        return {"status": "200", "data": {}, "message": "Password reset successfully"}
    else:
        sys_otp = collection2.find_one({'email_id': cred.email_id.lower()}).get('otp')
        sys_otp_validity = collection2.find_one({'email_id': cred.email_id.lower()}).get('otp_validity')
        if sys_otp != cred.otp or sys_otp_validity < datetime.now():
            return {"status": "400", "data": {}, "message": "Invalid OTP"}
        
        collection2.update_one({'email_id': cred.email_id.lower()}, {'$set': {'password': get_password_hash(cred.password)}})
        return {"status": "200", "data": {}, "message": "Password reset successfully"}

@router.put("/update_profile")
async def update_profile(name: Optional[str] = Form(None), password: Optional[str] = Form(None), department: Optional[str] = Form(None), keepunsaved: Optional[bool] = Form(False), image: Optional[UploadFile] = File(None), current_user: TokenData = Depends(get_current_user)):
   
    update_fields = {}
    if name:
        update_fields['name'] = name
    if keepunsaved is not None:  # Ensures it's updated even if False
        update_fields['keepunsaved'] = keepunsaved
    if password:
        update_fields['password'] = get_password_hash(password)
    if department:
        update_fields['department'] = department
    if image:
        # Accept any image type, no content-type validation
        image_data = await image.read()
        
        # Generate a unique file name using institute_id and email
        file_extension = image.filename.split(".")[-1]  # Get the file extension
        file_name = f"{current_user.institute_id}_email#{current_user.email}.{file_extension}"  # Generate the unique file name

        # Define the directory where the images will be saved on the server
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'images')
        os.makedirs(upload_dir, exist_ok=True)  # Create directory if it doesn't exist

        # Full save path on the server
        save_path = os.path.join(upload_dir, file_name)

        try:
            # Write the image to the server's disk
            with open(save_path, "wb") as f:
                f.write(image_data)
            
            # Save the image path in the database or return it as a response
            update_fields['image'] = file_name  # Update with the actual saved image path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    collection1 = db[current_user.institute_id]  # User collection based on institute_id
    collection2 = db['MASTER_ADMIN_CREDS']  # Admin collection

    # Check if the current user is an admin
    admin_cred = collection2.find_one({
        'institute_id': current_user.institute_id, 
        'email_id': current_user.email
    })

    # If admin credentials are found, update the admin profile
    if admin_cred:
        collection2.update_one(
            {'institute_id': current_user.institute_id, 'email_id': current_user.email}, 
            {'$set': update_fields}
        )
        return {"status": "200", "data": {}, "message": "Profile updated successfully"}

    # If not admin, check if the user exists in the user collection
    user_cred = collection1.find_one({'email_id': current_user.email})

    if user_cred is None:
        return {"status": "400", "data": {}, "message": "User not found"}

    collection1.update_one(
        {'email_id': current_user.email}, 
        {'$set': update_fields}
    )

    return {"status": "200", "data": {}, "message": "Profile updated successfully"}


@router.get("/me")
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    print(current_user)

@router.post("/contact_landing")
async def contact_landing(cred: ContactUs):
    send_contact_us_email(cred.email, cred.phone, cred.institute)
    return {"status": "200", "data": {}, "message": "Email sent successfully"}

async def validate_file(file: UploadFile):
    """Validate the uploaded file type and size."""
    if not file.content_type.startswith(("application/", "image/")):
        raise HTTPException(status_code=400, detail="File type not supported")
    
    file_size_mb = len(await file.read()) / (1024 * 1024)
    if file_size_mb > 25:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds the maximum limit of {25} MB"
        )
    await file.seek(0)

def zip_file(filename: str, file_content: bytes):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(filename, file_content)
    zip_buffer.seek(0)
    return zip_buffer.read()


@router.post("/contact_us")
async def contact_us(
    subject: str = Form(...),
    body: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: TokenData = Depends(get_current_user)
):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            if file:
                await validate_file(file)
                file_content = await file.read()

                unsupported_extensions = (".exe", ".js", ".bat")
                if file.filename.endswith(unsupported_extensions):
                    file_content = zip_file(file.filename, file_content)
                    file.filename = f"{file.filename}.zip"
                
                send_contact_us_email_files(
                email_from='21mc3025@rgipt.ac.in',
                subject=subject,
                body=body,
                filename=file.filename or None,
                file_content=file_content
            )

            else:
                file_content = None
                send_contact_us_email_files(email_from='21mc3025@rgipt.ac.in', subject=subject, body=body)

            return {"message": "File sent successfully!"}

        except Exception as e:
            return {"error": str(e)}

    else:
        raise HTTPException(status_code=401, detail="Unauthorized")