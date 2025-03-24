from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse, JSONResponse
from routes.auth import get_current_user
from routes.recents import add_recents
from schemas import LoginCreds, ForgetPassword, TokenData
from database import db, fs
from utils import convert_many_list_files, convert_visualizations_to_html, convert_one_visualization
from gemini.gemini import pipeline
from bson import ObjectId
import io
import asyncio
import gridfs
from datetime import datetime


router = APIRouter()

@router.post("/create_visualization")
async def create_visualization(title: str = Form(...), description: str = Form(...), custom_query: str = Form(...), roles: str = Form(...), viz_type: str = Form(...), viz_format: str = Form(...), files: list[str] = Form(...), current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        # controls_collection = db[current_user.institute_id+'_ROLES_ACCESS']
        # is_approved = False if 'needs_approval' == True in controls_collection.find_one({'role': user.get('roles')[0]})['controls'] else True   
        Files = []
        for file_id in files:
            try:
                file = fs.get(ObjectId(file_id))
                Files.append((file, file.content_type))
            except gridfs.errors.NoFile:
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        try:
            visualization_json = pipeline({'files': Files, 'custom_query': custom_query, 'viz_type': viz_type, 'previous_viz': None})
            html_template = convert_visualizations_to_html(visualization_json)
            collection = db[str(current_user.institute_id) + '_VISUALISATIONS']
            viz_metadata = {
                '_id': ObjectId(),
                'uploader': current_user.email,
                'roles': user.get('roles'),
                'title': title,
                'description': description,
                'visualization_json': visualization_json,
                'viz_type': viz_type,
                'roles_access': roles,
                'viz_format': viz_format,
                'date_uploaded': datetime.now(),
                'is_deleted': False,
                # 'is_approved': is_approved
            }
            row = collection.insert_one(viz_metadata)
            # call a route to add this to recents
            add_recents(current_user.institute_id, current_user.email, str(row.inserted_id), 'visualization')
            return {'status_code': 200, 'message': 'Visualization created successfully', 'visualization_id': str(row.inserted_id), 'html_template': html_template}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/update_visualization")
async def update_visualization(title: str, description: str, custom_query: str, roles: str, viz_type: str, viz_format: str, files: list[str], viz_id: str, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[str(current_user.institute_id) + '_VISUALISATIONS']
            previous_viz = collection.find_one({'_id': ObjectId(viz_id)})
            if previous_viz:
                new_visualization_json = pipeline({'files': files, 'custom_query': custom_query, 'viz_type': viz_type, 'previous_viz': previous_viz.get('visualization_json')})
                new_html_template = convert_visualizations_to_html(new_visualization_json)
                collection.update_one({'_id': ObjectId(viz_id)}, {'$set': {
                    'title': title,
                    'uploader': current_user.email,
                    'roles': user.get('roles'),
                    'title': title,
                    'description': description,
                    'visualization_json': new_visualization_json,
                    'viz_type': viz_type,
                    'roles_access': roles,
                    'viz_format': viz_format,
                    'date_uploaded': datetime.now(),
                    'is_deleted': False
                }})
                return {'status_code': 200, 'message': 'Visualization updated successfully', 'visualization_id': str(viz_id), 'html_template': new_html_template}
            else:
                raise HTTPException(status_code=404, detail="Visualization not found")  
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/list_visualizations")
async def list_visualizations(current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[str(current_user.institute_id).upper() + '_VISUALISATIONS']
            vizs = collection.find()
            accessible_visualizations = []
            user_roles = user.get('roles', [])
            user_email = current_user.email
            visualizations = []
            for viz in vizs:
                if user_email == viz['uploader'] or 'Admin' in user_roles or any(role in user_roles for role in viz['roles_access'].split(',')):
                    accessible_visualizations.append(viz)
                    uploader = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': viz['uploader']}) or db[str(current_user.institute_id)].find_one({'email_id': viz['uploader']})
                    viz['uploader_roles'] = uploader.get('roles', [])
                    viz['html_template'] = convert_visualizations_to_html(viz.get('visualization_json'))
                    visualizations.append(convert_one_visualization(viz))

            if not accessible_visualizations:
                return {'visualizations': [], 'message': 'No accessible visualizations found'}
            return {'status_code': 200, 'message': 'Visualizations fetched successfully', 'visualizations': visualizations}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.delete("/delete_visualization/{viz_id}")
async def delete_visualization(viz_id: str, current_user: TokenData = Depends(get_current_user)):
    user = db['MASTER_ADMIN_CREDS'].find_one({'institute_id': current_user.institute_id, 'email_id': current_user.email}) or db[str(current_user.institute_id)].find_one({'email_id': current_user.email})
    if user:
        try:
            collection = db[str(current_user.institute_id) + '_VISUALISATIONS']
            viz = collection.find_one({'_id': ObjectId(viz_id)})
            if viz:
                if current_user.email == viz['uploader']:
                #If isdelete is false or not present, set it to true
                    if viz.get('is_deleted', False)==False:
                        collection.update_one({'_id': ObjectId(viz_id)}, {'$set': {'is_deleted': True}})
                        return {'visualization_id': viz_id, 'message': 'Visualization moved to trash'}
                    else:
                        collection.delete_one({'_id': ObjectId(viz_id)})
                        return {'visualization_id': viz_id, 'message': 'Visualization deleted'}
                else:
                    return {'visualization_id': viz_id, 'message': 'Unauthorized to delete visualization'}
            else:
                return {'visualization_id': viz_id, 'message': 'Visualization not found'}
        except Exception as e:
            return {'visualization_id': viz_id, 'message': str(e)}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

# class Chart(BaseModel):
#     html: str   
    
# def format_html(html_string):
#     formatted_html = html.unescape(html_string)
#     pattern = r'JSON\.parse\((.*?)\)'
#     # Extract the JSON object as a string
#     match = re.search(pattern, formatted_html)
#     if match:
#         json_data = match.group(1)  # Extract JSON content inside JSON.parse()
#         # Replace `JSON.parse({...})` with the raw JSON object
#         formatted_html = re.sub(pattern, json_data, formatted_html)
#     return formatted_html

# async def capture_html_screenshot(html_content, output_image_path):
#     async with async_playwright() as p:
#         # Launch the browser in headless mode
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()

#         # Set the HTML content of the page
#         await page.set_content(html_content)

#         # Wait for the canvas element to be available and Chart.js to render the chart
#         await page.wait_for_selector("canvas")

#         # Take a screenshot and save it to the specified path
#         await page.screenshot(path=output_image_path)

#         # Close the browser
#         await browser.close()
        
# @router.get("/html_to_img")
# async def html_img(current_user: TokenData = Depends(get_current_user)):
#     try:
#         visualizations = await list_visualizations(current_user)
#         for charts in visualizations['visualizations']:
#             chart_html = format_html(charts['html_template'])
#             # return {"html":chart_html}
#     #     return {"error":"not in for"}
#     #     html_string = ""    
#     #     # html_string = '''<!DOCTYPE html>\n    <html>\n    <head>\n        <title>Visualization</title>\n        <meta charset=\"utf-8\">\n        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n        <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>\n    </head>\n    <body>\n        <canvas></canvas>\n        <script>\n            const chardata = JSON.parse({\"type\": \"line\", \"data\": {\"labels\": [\"January\", \"February\", \"March\", \"April\", \"May\", \"June\", \"July\"], \"datasets\": [{\"label\": \"Dataset 1\", \"data\": [65, 59, 80, 81, 56, 55, 40], \"backgroundColor\": \"rgba(75, 192, 192, 0.2)\", \"borderColor\": \"rgba(75, 192, 192, 1)\", \"borderWidth\": 1, \"fill\": {\"target\": \"origin\", \"above\": \"rgb(75, 192, 192)\", \"below\": \"rgb(255, 99, 132)\"}, \"tension\": 0.4}, {\"label\": \"Dataset 2\", \"data\": [25, 29, 50, 51, 26, 25, 10], \"backgroundColor\": \"rgba(54, 162, 235, 0.2)\", \"borderColor\": \"rgba(54, 162, 235, 1)\", \"borderWidth\": 1, \"fill\": {\"target\": 0, \"above\": \"rgb(54, 162, 235)\", \"below\": \"rgb(255, 99, 132)\"}, \"tension\": 0.4}]}, \"options\": {\"responsive\": true, \"plugins\": {\"legend\": {\"display\": true, \"position\": \"top\"}, \"title\": {\"display\": true, \"text\": \"Area Chart Example\"}, \"filler\": {\"propagate\": true}}, \"scales\": {\"x\": {\"beginAtZero\": true}, \"y\": {\"beginAtZero\": true}}}}\n);\n            const ctx = document.querySelector(\"canvas\");\n            const myChart = new Chart(ctx, chardata);\n        </script>\n    </body>\n    </html>\n'''
#     #     # html_string = '''<!DOCTYPE html>\n    <html>\n    <head>\n        <title>Visualization</title>\n        <meta charset="utf-8">\n        <meta name="viewport" content="width=device-width, initial-scale=1">\n        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n    </head>\n    <body>\n        <canvas></canvas>\n        <script>\n            const chardata = {\"type\": \"line\", \"data\": {\"labels\": [\"January\", \"February\", \"March\", \"April\", \"May\", \"June\", \"July\"], \"datasets\": [{\"label\": \"Dataset 1\", \"data\": [65, 59, 80, 81, 56, 55, 40], \"backgroundColor\": \"rgba(75, 192, 192, 0.2)\", \"borderColor\": \"rgba(75, 192, 192, 1)\", \"borderWidth\": 1, \"fill\": {\"target\": \"origin\", \"above\": \"rgb(75, 192, 192)\", \"below\": \"rgb(255, 99, 132)\"}, \"tension\": 0.4}, {\"label\": \"Dataset 2\", \"data\": [25, 29, 50, 51, 26, 25, 10], \"backgroundColor\": \"rgba(54, 162, 235, 0.2)\", \"borderColor\": \"rgba(54, 162, 235, 1)\", \"borderWidth\": 1, \"fill\": {\"target\": 0, \"above\": \"rgb(54, 162, 235)\", \"below\": \"rgb(255, 99, 132)\"}, \"tension\": 0.4}]}, \"options\": {\"responsive\": true, \"plugins\": {\"legend\": {\"display\": true, \"position\": \"top\"}, \"title\": {\"display\": true, \"text\": \"Area Chart Example\"}, \"filler\": {\"propagate\": true}}, \"scales\": {\"x\": {\"beginAtZero\": true}, \"y\": {\"beginAtZero\": true}}}}\n            const ctx = document.querySelector(\"canvas\");\n            const myChart = new Chart(ctx, chardata);\n        </script>\n    </body>\n    </html>'''
#             chart_html = format_html(chart_html)
#     #     # return {"html": chart_html}
#             await capture_html_screenshot(chart_html, f'charts_png/{charts['title']}.png')
#             if __name__ == "__html_img__":  
#                 asyncio.run(html_img())
#     #     # Return a success response if no error occurred
#         return JSONResponse(status_code=200, content={"message": "Screenshot captured successfully!"})
#     except Exception as e:
#         # If any error occurs during screenshot capture
#         raise HTTPException(status_code=500, detail=f"Error capturing screenshot: {str(e)}")
    