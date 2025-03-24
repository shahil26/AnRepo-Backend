from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, status
from pymongo.errors import PyMongoError
from routes.auth import get_current_user
from schemas import TokenData
from database import db, fs
from pydantic import BaseModel, ValidationError
from fastapi.responses import HTMLResponse
from scholarly import scholarly

router = APIRouter()

@router.post("/find_papers")
def publications(prof_name: str, institute: str):
    flag = 0
    search_query = scholarly.search_author(prof_name)
    author = next(search_query)

    # Fetch the publication list
    author_info = scholarly.fill(author)
    # papers = author_info.get('publications')
    basics = scholarly.fill(author, sections=['basics'])
    if institute in basics['affiliation']:
            papers = author_info.get('publications')
            return {'user':'Found', 'papers': papers}
    else:
        return  {'user': 'Not Found', 'papers': "none"}
    
@router.get("/publications")
def papers():
    try:
        # Access the RGIPT_PROFESSORS collection
        collection = db['RGIPT_PROFESSORS']
        documents = collection.find()
        
        # Loop through each professor's record
        for record in documents:
            name = record.get('name')
            institute = record.get('institute')

            if not name or not institute:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Record missing 'name' or 'institute': {record}"
                )

            # Call publications function
            try:
                papers = publications(name, institute)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error fetching publications for {name}: {str(e)}"
                )

            # Access the RGIPT_PUBLICATIONS collection
            collection1 = db['RGIPT_PUBLICATIONS']
            
            # Insert papers into RGIPT_PUBLICATIONS
            for paper in papers.get('papers', []):
                if 'bib' in paper and paper['bib'].get('pub_year') == "2024":
                    new_record = {
                        'professor': name,
                        'papers': paper
                    }
                    try:
                        result = collection1.insert_one(new_record)
                    except PyMongoError as e:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error inserting publication for {name}: {str(e)}"
                        )
        
        return {"message": "DB updated successfully."}

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )