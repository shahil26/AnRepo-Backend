from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from routes import auth, data, vis, work_manager, admin, chatbot, notifications, papers, trash, recents

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
) 
# app.mount("/uploads", StaticFiles(directory="/root/sih_root/uploads"), name="uploads")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(vis.router, prefix="/vis", tags=["visualization"])
app.include_router(chatbot.router, prefix="/chat", tags=["chat"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(work_manager.router, prefix="/work", tags=["work"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
# app.include_router(report.router, prefix="/report", tags=["report"])
app.include_router(recents.router, prefix="/recents", tags=["recents"])
app.include_router(trash.router, prefix="/trash", tags=["trash"])
app.include_router(papers.router, prefix="/report", tags=["report"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)