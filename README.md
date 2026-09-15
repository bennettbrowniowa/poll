# Classroom Poll — hosted version

A simple five-button classroom polling app.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python server.py
```
Teacher: `http://localhost:8000/?teacher`
Students: `http://<computer-ip>:8000/`

## Deploy
This is a Flask app and can be deployed to a Python web host such as Render, Railway, Fly.io, or a similar service.

### Important persistence note
The included SQLite database persists on a normal persistent filesystem. Some free web hosts use ephemeral filesystems, in which case move the database to a persistent disk or replace SQLite with the host's PostgreSQL database.

## Behavior
- Students see only five buttons: 1–5.
- One tap immediately records one vote.
- A tablet can submit unlimited votes, one for each student who uses it.
- A student cannot revise a vote because there is no revision mechanism.
- Teacher view updates about every 0.7 seconds.
- "New question" creates a new poll while retaining all previous poll data.
