# from fastapi import FastAPI, Request, APIRouter
# from fastapi.responses import HTMLResponse
# from pydantic import BaseModel

# router = APIRouter()

# # Route to serve HTML
# @router.get("/serve_html", response_class=HTMLResponse)
# async def serve_html():
#     html_content = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Visualization</title>
#         <meta charset="utf-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1">
#         <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
#     </head>
#     <body>
#         <canvas id="myChart"></canvas>
#         <script>
#             const chardata = JSON.parse(''' + visualization_json + ''');
#             const ctx = document.querySelector("canvas");
#             const myChart = new Chart(ctx, chardata);

#             setTimeout(() => {
#                 const imageDataURL = myChart.toBase64Image();

#                 // Send the imageDataURL to the FastAPI server
#                 fetch('http://64.227.158.253/save_images/upload_image', {
#                     method: 'POST',
#                     headers: {
#                         'Content-Type': 'application/json'
#                     },
#                     body: JSON.stringify({ image: imageDataURL })
#                 })
#                 .then(response => response.json())
#                 .then(data => {
#                     console.log('Server Response:', data);
#                 })
#                 .catch(error => {
#                     console.error('Error:', error);
#                 });
#             }, 5000);
#         </script>
#     </body>
#     </html>
#     """
#     return HTMLResponse(content=html_content)

# # Endpoint to handle the image data
# class ImageData(BaseModel):
#     image: str

# @router.post("/upload_image")
# async def upload_image(data: ImageData):
#     # Process the base64 image data (e.g., save to file, analyze, etc.)
#     image_data = data.image
#     return {"message": "Image received", "image_data": image_data}

from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Define the APIRouter instance
router = APIRouter()

# Route to serve the HTML content
@router.get("/serve_html", response_class=HTMLResponse)
async def serve_html():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visualization</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <canvas id="myChart"></canvas>
        <script>
            const chardata = JSON.parse(''' + visualization_json + ''');
            const ctx = document.querySelector("canvas");
            const myChart = new Chart(ctx, chardata);

            setTimeout(() => {
                const imageDataURL = myChart.toBase64Image();

                // Send the imageDataURL to the FastAPI server
                fetch('http://64.227.158.253/save_images/upload_image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image: imageDataURL })
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Server Response:', data);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Model to accept image data
class ImageData(BaseModel):
    image: str

# Endpoint to handle the uploaded image
@router.post("/upload_image")
async def upload_image(data: ImageData):
    image_data = data.image
    # Optionally, you could save the image, analyze it, etc.
    return {"message": "Image received", "image_data": image_data}

from playwright.sync_api import sync_playwright
import time
import requests

@router.get("/run")
async def run():

    # Using Playwright to run the JavaScript
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch Chromium in headless mode
        page = browser.new_page()

        # Go to the page serving the HTML content with JavaScript
        page.goto("http://64.227.158.253/save_images/serve_html")  # Change to your FastAPI URL

        # Wait for the page to load and JavaScript to execute (5 seconds in your case)
        time.sleep(5)

        # Extract the imageDataURL (from JavaScript) after chart generation
        image_data_url = page.evaluate("return window.imageDataURL;")

        # Send the image data URL to the FastAPI server
        if image_data_url:
            response = requests.post("http://64.227.158.253/save_images/upload_image", json={"image": image_data_url})
            print("Server Response:", response.json())

        browser.close()

