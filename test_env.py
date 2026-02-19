from dotenv import load_dotenv
import os

load_dotenv()

print(f"ID: {os.environ.get('GOOGLE_CLIENT_ID')[:10]}...")
print(f"Secret: {os.environ.get('GOOGLE_CLIENT_SECRET')[:10]}...")