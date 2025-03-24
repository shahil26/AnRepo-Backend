from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv('MONGO_URI')
client = MongoClient(uri,tls=True, tlsAllowInvalidCertificates=True)

db = client.SIH2024
fs = gridfs.GridFS(db)