# TALENT TRAIL AI DOCUMENT VALIDATION SYSTEM

# PREREQUISITES

* Python 3.10 or higher
* Node.js
* Gemini API Key

==================================================

# FIRST-TIME SETUP

1. Open a terminal and navigate to the backend folder

cd backend

2. Install backend dependencies

pip install -r requirements.txt

3. Create a .env file inside the backend folder

GEMINI_API_KEY=YOUR_GEMINI_API_KEY

4. Start the backend server

uvicorn app:app --reload

Backend URL:
http://127.0.0.1:8000

==================================================

5. Open a second terminal and navigate to the frontend folder

cd frontend

6. Install frontend dependencies

npm install

7. Start the frontend application

npm run dev

Frontend URL:
http://localhost:5173

==================================================

# RUNNING THE PROJECT LATER

Every time you want to run the project:

Terminal 1:

cd backend

uvicorn app:app --reload

Terminal 2:

cd frontend

npm run dev

Then open:

http://localhost:5173

==================================================
