from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from routes.auth import get_current_user
from schemas import TokenData
from google import generativeai as genai
from dotenv import load_dotenv
from database import db
from typing import Optional
import os, tempfile, textwrap

load_dotenv()

router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY2"))
model = genai.GenerativeModel("gemini-1.5-flash")

@router.post("/ask")
async def ask(message: str = Form(...), files: Optional[list[UploadFile]] = File(None), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:    
        if files:    
            try:
                uploaded_files = []
                for file in files:
                    with tempfile.NamedTemporaryFile(delete=False) as temp_media:
                        temp_media.write(file.file.read())
                        temp_media.flush()

                        try:
                            upload_file = genai.upload_file(temp_media.name, mime_type=file.content_type)
                            uploaded_files.append(upload_file)
                        except Exception as e:
                            return {'error': str(e)}
                        finally:
                            if os.path.exists(temp_media.name):
                                os.remove(temp_media.name)

                prompt = '''
                You are a helpful assistant. Your task is to help the user by reading the following text documentation and answer the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.
                
                Question: ''' + message + '''
                Answer: 
                
                The text documentation is as follows:
                '''
                try:
                    final_prompt = [prompt] + uploaded_files
                    answer = model.generate_content(final_prompt, generation_config={'response_mime_type': 'text/plain'})
                    return answer.text
                except Exception as e:
                    return {'error': str(e)}
            except Exception as e:
                return {'error': str(e)}
            finally:
                if uploaded_files:
                    for file in uploaded_files:
                        file.delete()
        else:
            prompt = '''
            You are a helpful assistant. Your task is to help the user by reading the following text documentation and answer the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Question: ''' + message + '''
            Answer: 
            
            The text documentation is as follows:
            '''
            try:
                answer = model.generate_content([prompt], generation_config={'response_mime_type': 'text/plain'})
                return answer.text
            except Exception as e:
                return {'error': str(e)}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")