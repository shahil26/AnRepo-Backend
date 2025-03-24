from fastapi import APIRouter
from database import db

router = APIRouter()

def convert_many_faqs(faqs):
    new_faqs = []
    for faq in faqs:
        new_faqs.append({'question': faq['question'], 'answer': faq['answer']})
    
    return new_faqs

def convert_many_docs(docs):
    new_docs = []
    for doc in docs:
        new_docs.append({'title': doc['title'], 'content': doc['content']})
    
    return new_docs

@router.get("/faq")
async def faq():
    try:
        collection = db['FAQ']
        faqs = collection.find()
        faqs = convert_many_faqs(faqs)

        return {"status": "200", "data": {"faq": faqs}, "message": "FAQ fetched successfully"}
    except Exception as e:
        return {"status": "500", "data": {}, "message": str(e)}

@router.get("/docs")
async def docs():
    try:
        collection = db['DOCS']
        docs = collection.find()
        docs = convert_many_docs(docs)

        return {"status": "200", "data": {"docs": docs}, "message": "Docs fetched successfully"}
    except Exception as e:
        return {"status": "500", "data": {}, "message": str(e)}