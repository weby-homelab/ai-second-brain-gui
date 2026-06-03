import os
import re
import uuid
import pathlib
import datetime
from fastapi import FastAPI, Request, Response, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import markdown

# Load environment variables
load_dotenv("/root/geminicli/.env")

BRAIN_DIR = "/root/geminicli/brain"
DEFAULT_PASSWORD = "weby-brain-secure"
PASSWORD = os.getenv("BRAIN_PORTAL_PASSWORD", DEFAULT_PASSWORD)

# Initialize FastAPI
app = FastAPI(title="Second Brain Portal")

# Static files & Templates directory setup
os.makedirs("/root/geminicli/projects/second-brain-portal/static", exist_ok=True)
os.makedirs("/root/geminicli/projects/second-brain-portal/templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="/root/geminicli/projects/second-brain-portal/static"), name="static")
templates = Jinja2Templates(directory="/root/geminicli/projects/second-brain-portal/templates")

# In-memory sessions
SESSIONS = set()

# File indexing for wiki-links
def index_brain_files():
    file_index = {}
    for root, dirs, files in os.walk(BRAIN_DIR):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            if file.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, file), BRAIN_DIR)
                name_without_ext = os.path.splitext(file)[0].lower()
                file_index[name_without_ext] = rel_path
                file_index[rel_path.lower()] = rel_path
    return file_index

# File indexing for media files (to break taint flow for CodeQL)
def index_media_files():
    media_index = {}
    valid_exts = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}
    for root, dirs, files in os.walk(BRAIN_DIR):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_exts:
                rel_path = os.path.relpath(os.path.join(root, file), BRAIN_DIR)
                name_lower = file.lower()
                media_index[name_lower] = rel_path
                media_index[rel_path.lower()] = rel_path
    return media_index

# Path validation for LFI protection
def validate_path(rel_path: str) -> str:
    # Sanitization check to satisfy CodeQL path analysis patterns
    if ".." in rel_path or "\\" in rel_path:
        raise HTTPException(status_code=400, detail="Invalid path")
    # Build absolute path
    abs_path = os.path.abspath(os.path.join(BRAIN_DIR, rel_path))
    # Verify absolute path starts with BRAIN_DIR
    common_path = os.path.commonpath([BRAIN_DIR, abs_path])
    if common_path != os.path.abspath(BRAIN_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    return abs_path

# Authentication helper
def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token in SESSIONS:
        return "admin"
    return None

# Markdown custom Callout renderer
def render_callout(c_type, title, content):
    icons = {
        'NOTE': '💡',
        'TIP': '✨',
        'IMPORTANT': '🔥',
        'WARNING': '⚠️',
        'CAUTION': '🚨'
    }
    icon = icons.get(c_type, '📝')
    content_html = "\n".join(content)
    # Render nested markdown
    html_body = markdown.markdown(content_html, extensions=['tables', 'fenced_code'])
    return f'<div class="callout callout-{c_type.lower()}"><div class="callout-header"><span class="callout-icon">{icon}</span><span class="callout-title">{title}</span></div><div class="callout-body">{html_body}</div></div>'

# Callout preprocessor
def convert_callouts(text):
    lines = text.split('\n')
    processed_lines = []
    in_callout = False
    callout_type = ""
    callout_title = ""
    callout_content = []
    
    for line in lines:
        match = re.match(r'^>\s*\[!([a-zA-Z]+)\]\s*(.*)$', line)
        if match:
            if in_callout:
                processed_lines.append(render_callout(callout_type, callout_title, callout_content))
                callout_content = []
            in_callout = True
            callout_type = match.group(1).upper()
            callout_title = match.group(2).strip() or callout_type.capitalize()
        elif in_callout and line.startswith('>'):
            content_line = line[1:]
            if content_line.startswith(' '):
                content_line = content_line[1:]
            callout_content.append(content_line)
        else:
            if in_callout:
                processed_lines.append(render_callout(callout_type, callout_title, callout_content))
                in_callout = False
                callout_content = []
            processed_lines.append(line)
            
    if in_callout:
        processed_lines.append(render_callout(callout_type, callout_title, callout_content))
        
    return '\n'.join(processed_lines)

# Wiki-links preprocessor
def convert_wikilinks(text, file_index):
    pattern = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    
    def replace_link(match):
        target = match.group(1).strip()
        label = match.group(2).strip() if match.group(2) else target
        target_lower = target.lower()
        
        # Check if it's an image link
        if any(target_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
            # Render media link, which resolves to local media asset endpoint
            return f'<a href="/media?path={target}" target="_blank" class="media-link">🖼️ {label}</a>'
            
        resolved_path = None
        if target_lower in file_index:
            resolved_path = file_index[target_lower]
        else:
            target_md = target_lower + ".md"
            if target_md in file_index:
                resolved_path = file_index[target_md]
                
        if resolved_path:
            return f'<a href="/note?path={resolved_path}" class="wiki-link">{label}</a>'
        else:
            return f'<span class="broken-wiki-link" title="File not found">{label}</span>'
            
    return pattern.sub(replace_link, text)

# Render note markdown to HTML
def render_markdown(text, file_index):
    # Preprocess callouts first
    text = convert_callouts(text)
    # Preprocess wiki-links
    text = convert_wikilinks(text, file_index)
    # Convert to HTML
    html = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    return html

# ----------------- ROUTES -----------------

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request, error: str = None):
    if get_current_user(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": error})

@app.post("/login")
def post_login(request: Request, password: str = Form(...)):
    if password == PASSWORD:
        session_token = str(uuid.uuid4())
        SESSIONS.add(session_token)
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_token", value=session_token, httponly=True, samesite="strict")
        return response
    return RedirectResponse(url="/login?error=Невірний пароль", status_code=303)

@app.get("/logout")
def get_logout(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token in SESSIONS:
        SESSIONS.remove(session_token)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    # Build statistics
    total_notes = 0
    note_categories = {"01_Projects": 0, "02_Areas": 0, "03_Resources": 0, "06_Daily_Logs": 0, "Other": 0}
    recent_notes = []
    
    for root, dirs, files in os.walk(BRAIN_DIR):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            if file.endswith(".md"):
                total_notes += 1
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BRAIN_DIR)
                
                # Determine category
                parts = rel_path.split(os.sep)
                if len(parts) > 1 and parts[0] in note_categories:
                    note_categories[parts[0]] += 1
                else:
                    note_categories["Other"] += 1
                    
                # Modification time
                mtime = os.path.getmtime(full_path)
                mtime_dt = datetime.datetime.fromtimestamp(mtime)
                recent_notes.append({
                    "name": os.path.splitext(file)[0],
                    "path": rel_path,
                    "mtime": mtime_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "mtime_raw": mtime
                })
                
    recent_notes = sorted(recent_notes, key=lambda x: x["mtime_raw"], reverse=True)[:7]
    
    return templates.TemplateResponse(request, "dashboard.html", {
        "total_notes": total_notes,
        "categories": note_categories,
        "recent_notes": recent_notes
    })

@app.get("/note", response_class=HTMLResponse)
def get_note(request: Request, path: str):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    # Standardize input query key
    path_key = path.replace("\\", "/").lower()
    
    file_index = index_brain_files()
    if path_key not in file_index:
        raise HTTPException(status_code=404, detail="Note not found")
        
    # Break CodeQL path expression taint by using trusted relative path from the index
    safe_rel_path = file_index[path_key]
    abs_path = validate_path(safe_rel_path)
        
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    html_content = render_markdown(content, file_index)
    note_name = os.path.splitext(os.path.basename(abs_path))[0]
    relative_dir = os.path.dirname(safe_rel_path)
    
    return templates.TemplateResponse(request, "note.html", {
        "note_name": note_name,
        "html_content": html_content,
        "note_path": safe_rel_path,
        "relative_dir": relative_dir
    })

@app.get("/search", response_class=HTMLResponse)
def search_notes(request: Request, q: str):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    q_lower = q.lower()
    results = []
    
    for root, dirs, files in os.walk(BRAIN_DIR):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BRAIN_DIR)
                name = os.path.splitext(file)[0]
                
                # Search filename and content
                filename_match = q_lower in name.lower()
                content_snippet = ""
                content_match = False
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if q_lower in line.lower():
                                content_match = True
                                # Build a clean snippet
                                if not content_snippet:
                                    content_snippet = f"Line {line_num}: ... {line.strip()[:100]} ..."
                except Exception:
                    pass
                    
                if filename_match or content_match:
                    score = 10 if filename_match and name.lower() == q_lower else (5 if filename_match else 2)
                    results.append({
                        "name": name,
                        "path": rel_path,
                        "snippet": content_snippet if content_match else "Match in filename",
                        "score": score
                    })
                    
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    
    return templates.TemplateResponse(request, "search.html", {
        "query": q,
        "results": results
    })

@app.get("/media")
def get_media(request: Request, path: str):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    # Standardize input query key
    path_key = path.replace("\\", "/").lower()
    if "/" not in path_key:
        path_key = os.path.basename(path_key)
        
    media_index = index_media_files()
    if path_key not in media_index:
        raise HTTPException(status_code=404, detail="Media file not found")
        
    # Break CodeQL path expression taint by using trusted relative path from the index
    safe_rel_path = media_index[path_key]
    abs_path = validate_path(safe_rel_path)
    
    return FileResponse(abs_path)

if __name__ == "__main__":
    import uvicorn
    # Bind strictly to localhost (127.0.0.1) for security.
    # Access can be tunnelled securely via Tailscale or Cloudflare.
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=True)
