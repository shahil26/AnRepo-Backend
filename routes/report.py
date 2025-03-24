# from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
# from routes.auth import get_current_user
# from schemas import TokenData
# from database import db, fs
# from pydantic import BaseModel, ValidationError
# from fastapi.responses import HTMLResponse
# # from gemini.config import model
# from google import generativeai as genai

# API_KEY = "AIzaSyBV1kFZP1bN0FLe51LKC5OwU44gNz8AnUA"
# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel('gemini-1.5-flash')

# def report_pipeline(custom_query, institute, report_type):
#     # prompt = "Create a detailed report based on the chart data provided below. For each chart, provide a brief explanation, discuss trends, and summarize key insights. In each section, leave a placeholder `<chart_title>` where the chart will be inserted. The rest of the content should only include textual explanations—do **not** include the actual chart data or any chart information, only the placeholder `<chart_title>`. Provide an introductory paragraph explaining the overall context of the report. Mention that the following charts will help in analyzing various aspects such as performance, trends, and key observations. Each chart corresponds to a specific dataset, and you will summarize important insights from each one. Summarize the main insights derived from all the charts. Discuss any overarching trends, patterns, or conclusions that can be drawn from the data. Based on the charts presented, provide any recommendations, insights, or potential next steps for further analysis or decision-making. "
#     prompt = f'''Create a detailed report based on the charts and data provided below. The report should be a single continuous text, without any dictionaries or separate attributes. Each chart should be represented by the placeholder `|chart_title|` with the title of the chart where it should be inserted. 
#     {custom_query}
# **Key Instructions**:
# -Use only the information provided through the charts.
# -GIVE THE REPORT IN A SINGLE STRING.
# - Only include the chart real title in |chart_title| not anything else.
# - **** Instead of next line tags (\n) give <br> tags only......
# - DO NOT GIVE ANY STARTING LIKE "This report is..." , "Continuing from the older pages..." JUST START THE REPORT WITH EXPLAING ALL THE THINGS.
# - **The report should be atleast 2 pages long.
# - Each chart should be represented only by the placeholder `|chart_title|` where chart_title should be the title of that chart which should be inserted, followed by a continuation of the text. The placeholder should be on its own line where the chart will be inserted.
# - The report should be in a single, cohesive block of text that includes the introduction, chart descriptions, trends, insights, and conclusion all integrated together.
# - Do **not** include the chart data or JSON information. Just insert the placeholder for where the chart will go.
# '''
#     db_name = f"{institute}_VISUALISATIONS"
#     collection = db[db_name]
#     documents = collection.find()
#     if not documents:
#         return ""
#     i = 0
#     for record in documents:
#         chart_type = record.get("viz_format")
#         if chart_type == report_type:
#             prompt += ' <br>'
#             i += 1
#             prompt += str(record.get("title")) + str(record.get("description")) + "<br>"
#             prompt += str(record.get("visualization_json"))
#     response = model.generate_content(
#         prompt,
#         generation_config={'response_mime_type': 'application/json'}
#     )
#     return response.text
# # def chart_info(institute):
# #     charts = []
    
# #     for name in chart_names:
# #         filter_query = {"title": name}
# #         chart = collection.find_one(filter_query)
# #         # charts.append(filter_query)
# #         if chart:
# #             chart_info = {"title": chart.get("title"),
# #                         "description": chart.get("description"),
# #                         "visualization_json": chart.get("visualization_json"),
# #                         "viz_type": chart.get("viz_type")}
# #             charts.append(str(chart_info))
# #     return charts

# # class ChartModel(BaseModel): 
# #     names: list
# #     custom_query: str

# router = APIRouter()
# # current_user: TokenData = Depends(get_current_user)
# @router.post("/create")
# def create(custom_query: str):
#     institute = "RGIPT"
#     # charts = chart_info(chart_names, institute)
#     report_type = ['Informative', 'Financial', 'Facilities', 'Achievements']
#     final_report = ""
#     for r_type in report_type:
#         report = report_pipeline(custom_query, institute, r_type)
#         final_report += str(report)
#     return {'report': final_report}
