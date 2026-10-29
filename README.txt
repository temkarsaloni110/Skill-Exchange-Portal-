SKILL EXCHANGE PORTAL — WITH CHATBOX
====================================

FEATURES
- User registration and login
- Add skills to teach or skills to learn
- Search other users' skills
- Send and accept/reject skill exchange requests
- Chatbox: users can open conversations with other registered members
- Messages are stored in SQLite and remain available when the app is restarted on the same computer

REQUIREMENTS
- Python 3.9 or newer recommended
- VS Code (optional)

RUN THE PROJECT
1. Extract this ZIP file.
2. Open the extracted folder "skill_exchange_portal_chat" in VS Code.
3. Open Terminal > New Terminal.
4. Install dependencies:
      python -m pip install flask werkzeug
5. Start the app:
      python app.py
6. Open the local address shown in the terminal, usually:
      http://127.0.0.1:5000
7. Register two separate accounts in two different browsers/incognito windows (or log in as each account in turn).
8. Add skills. Use "Chatbox" in the navigation, or click "Chat" beside a user's skill/request.
9. Send a message. Open the same conversation later to see the saved messages.

DATABASE
- database.db is created automatically when app.py runs.
- It stores users, skills, requests, and messages.
- Keep database.db if you want to keep local demo data. Do not delete it unless you want to reset the data.

IMPORTANT
- This is a local educational/demo project. The chat updates after sending/refreshing; it is not live real-time messaging.
- To let people use it from different devices over the internet, deploy the app to a hosting service and use a production secret key. Do not use Flask's debug mode in a public deployment.
- For a real public project, add stronger security features such as CSRF protection, rate limits, and moderation/reporting tools.
