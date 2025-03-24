from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginCreds(BaseModel):
    institute_id: str
    email_id: str
    password: str = ''
    otp: str = ''
    otp_validity: str = ''
    department: str = ''
    otp: str
    
class TokenData(BaseModel):
    email: Optional[str] = None
    institute_id: Optional[str] = None
    
class AddUsers(LoginCreds):
    roles: list = ['student']

class VerifyOTP(BaseModel):
    institute_id: str
    email_id: str
    otp: str
    password: str

class EmailSchema(BaseModel):
    email: EmailStr
    subject: str
    body: str

class ForgetPassword(BaseModel):
    institute_id: str
    email_id: str

class FileMetaData(BaseModel):
    institute_id: str
    roles: list = ['student']
    file_name: str
    file_type: str
    description: str

class ContactUs(BaseModel):
    email: str
    phone: str
    institute: str

class EmailBody(BaseModel):
    subject: str
    details: str

class UserDetails(BaseModel):
    institute_id: str
    email_id: str
    roles: list

class RoleDetails(BaseModel):
    institute_id: str
    role: list
    clearance: str

class RecentActions(BaseModel):
    institute_id: str
    email_id: str
    action: str
    timestamp: datetime

class RaiseNotifications(BaseModel):
    institute_id: str
    raised_by_email_id: str
    raised_for_email_id: str
    message: str

class NotificationRequest(BaseModel):
    email: str
    message: str