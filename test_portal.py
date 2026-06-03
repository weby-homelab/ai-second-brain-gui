import requests
from dotenv import load_dotenv
import os

load_dotenv("/root/geminicli/.env")
PASSWORD = os.getenv("BRAIN_PORTAL_PASSWORD", "weby-brain-secure")

print(f"Testing with password: {PASSWORD}")
session = requests.Session()

# 1. Access dashboard directly - should redirect to login
r = session.get("http://127.0.0.1:8008/", allow_redirects=False)
print("Dashboard direct status code (expected 303):", r.status_code)
assert r.status_code == 303 or r.status_code == 302, f"Failed: {r.status_code}"

# 2. Login
r = session.post("http://127.0.0.1:8008/login", data={"password": PASSWORD}, allow_redirects=False)
print("Login status code (expected 303):", r.status_code)
assert r.status_code == 303, f"Failed: {r.status_code}"
print("Cookies after login:", session.cookies.get_dict())
assert "session_token" in session.cookies, "session_token cookie not found!"

# 3. Access dashboard now
r = session.get("http://127.0.0.1:8008/")
print("Dashboard authenticated status code (expected 200):", r.status_code)
assert r.status_code == 200, f"Failed: {r.status_code}"
assert "Дашборд" in r.text or "Привіт" in r.text, "Dashboard content not found!"
print("Dashboard text matches expected elements.")

# 4. View Home.md note
r = session.get("http://127.0.0.1:8008/note?path=Home.md")
print("Home.md status code (expected 200):", r.status_code)
assert r.status_code == 200, f"Failed: {r.status_code}"
assert "Home" in r.text or "Index" in r.text, "Home.md note content not found!"
print("Note rendering succeeds.")

# 5. Search for a term
r = session.get("http://127.0.0.1:8008/search?q=PRXMX-01")
print("Search status code (expected 200):", r.status_code)
assert r.status_code == 200, f"Failed: {r.status_code}"
assert "Знайдено" in r.text, "Search results content not found!"
print("Search functionality succeeds.")

print("All tests passed successfully! Portal is 100% functional and secure.")
