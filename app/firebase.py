import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    firebase_key_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if firebase_key_json:
        cred = credentials.Certificate(json.loads(firebase_key_json))
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()