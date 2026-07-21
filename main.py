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
from graph_builder import build_graph_data, build_local_subgraph

# Load environment variables
load_dotenv("/root/geminicli/.env")

BRAIN_DIR = "/root/geminicli/brain"
DEFAULT_PASSWORD = "weby-brain-secure"
PASSWORD = os.getenv("BRAIN_PORTAL_PASSWORD", DEFAULT_PASSWORD)

# Initialize FastAPI
app = FastAPI(title="Second Brain Portal")

# Static files & Templates directory setup
BASE_DIR = pathlib.Path(__file__).parent.resolve()
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# In-memory sessions
SESSIONS = set()

# Translation dictionary
TRANSLATIONS = {
    "uk": {
        "title_login": "Вхід — Second Brain Portal",
        "login_header": "Second Brain",
        "login_subtitle": "Авторизуйтеся для доступу до знань",
        "login_label": "Пароль доступу",
        "login_placeholder": "Введіть пароль...",
        "login_btn": "Увійти",
        "login_error": "Невірний пароль",
        "dashboard": "Дашборд",
        "knowledge_sections": "Розділи знань",
        "logout": "Вийти",
        "search_placeholder": "Пошук нотаток...",
        "system_ok": "Система в нормі",
        "welcome_user": "Привіт, Weby! 👋",
        "welcome_text": "Ласкаво просимо до веб-порталу твого другого мозку. Тут зібрано знання, документацію, мандати та системний статус домашньої лабораторії.",
        "stat_total_notes": "Всього нотаток",
        "stat_active_projects": "Активних проєктів",
        "stat_archive_notes": "В архіві",
        "stat_total_logs": "Daily Logs всього",
        "recent_updates": "🕒 Останні оновлення знань",
        "structure_navigation": "📚 Навігація по структурі",
        "view": "Переглянути",
        "note_not_found": "Нотатку не знайдено",
        "media_not_found": "Медіа-файл не знайдено",
        "note_path": "Шлях до файлу",
        "search_results": "Результати пошуку",
        "search_found": "Знайдено {count} результатів для \"{query}\"",
        "match_filename": "Збіг у назві файлу",
        "no_results": "Нічого не знайдено",
        "no_results_sub": "Спробуйте змінити запит або перевірити правопис",
        "edit": "Редагувати",
        "save": "Зберегти",
        "cancel": "Скасувати",
        "edit_note": "Редагування нотатки",
    },
    "en": {
        "title_login": "Login — Second Brain Portal",
        "login_header": "Second Brain",
        "login_subtitle": "Authenticate to access knowledge",
        "login_label": "Access Password",
        "login_placeholder": "Enter password...",
        "login_btn": "Sign In",
        "login_error": "Incorrect password",
        "dashboard": "Dashboard",
        "knowledge_sections": "Knowledge Base",
        "logout": "Logout",
        "search_placeholder": "Search notes...",
        "system_ok": "System online",
        "welcome_user": "Hello, Weby! 👋",
        "welcome_text": "Welcome to your second brain web portal. Your knowledge, documentation, mandates, and home lab status, consolidated.",
        "stat_total_notes": "Total notes",
        "stat_active_projects": "Active projects",
        "stat_archive_notes": "Archived notes",
        "stat_total_logs": "Total Daily Logs",
        "recent_updates": "🕒 Recent updates",
        "structure_navigation": "📚 Structure Navigator",
        "view": "View",
        "note_not_found": "Note not found",
        "media_not_found": "Media file not found",
        "note_path": "File path",
        "search_results": "Search Results",
        "search_found": "Found {count} results for \"{query}\"",
        "match_filename": "Match in filename",
        "no_results": "No results found",
        "no_results_sub": "Try changing your query or check your spelling",
        "edit": "Edit",
        "save": "Save",
        "cancel": "Cancel",
        "edit_note": "Edit Note",
    }
}

def get_lang(request: Request) -> str:
    return request.cookies.get("lang", "uk")

def get_context(request: Request, **kwargs) -> dict:
    lang = get_lang(request)
    t = TRANSLATIONS.get(lang, TRANSLATIONS["uk"])
    context = {"request": request, "lang": lang, "t": t}
    context.update(kwargs)
    return context

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

@app.get("/robots.txt")
def get_robots(request: Request):
    base_url = str(request.base_url).rstrip("/")
    robots_path = os.path.join(BASE_DIR, "robots.txt")
    if os.path.exists(robots_path):
        with open(robots_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("Sitemap: /sitemap.xml", f"Sitemap: {base_url}/sitemap.xml")
    else:
        content = f"User-agent: *\nDisallow: /note\nDisallow: /search\nDisallow: /media\nDisallow: /api/\nDisallow: /logout\nAllow: /\nAllow: /login\nSitemap: {base_url}/sitemap.xml"
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml")
def get_sitemap(request: Request):
    base_url = str(request.base_url).rstrip("/")
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/login</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>"""
    return Response(content=xml_content, media_type="application/xml")

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request, error: str = None):
    if get_current_user(request):
        return RedirectResponse(url="/", status_code=303)
    
    lang = get_lang(request)
    t = TRANSLATIONS[lang]
    translated_error = None
    if error:
        if "пароль" in error.lower() or "password" in error.lower():
            translated_error = t["login_error"]
        else:
            translated_error = error
            
    return templates.TemplateResponse(request, "login.html", get_context(request, error=translated_error))

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

@app.get("/set-lang")
def set_lang(request: Request, lang: str):
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=303)
    if lang in ["uk", "en"]:
        response.set_cookie(key="lang", value=lang, max_age=31536000, httponly=True, samesite="strict")
    return response

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    # Build statistics
    total_notes = 0
    note_categories = {"01_Projects": 0, "02_Areas": 0, "03_Resources": 0, "04_Archive": 0, "06_Daily_Logs": 0, "Other": 0}
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
    
    return templates.TemplateResponse(request, "dashboard.html", get_context(
        request,
        total_notes=total_notes,
        categories=note_categories,
        recent_notes=recent_notes
    ))

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
    
    return templates.TemplateResponse(request, "note.html", get_context(
        request,
        note_name=note_name,
        html_content=html_content,
        note_path=safe_rel_path,
        relative_dir=relative_dir
    ))

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
    
    lang = get_lang(request)
    t = TRANSLATIONS[lang]
    found_text = t["search_found"].format(count=len(results), query=q)
    
    return templates.TemplateResponse(request, "search.html", get_context(
        request,
        query=q,
        results=results,
        found_text=found_text
    ))

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

@app.get("/api/graph/global")
def api_global_graph(request: Request):
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return build_graph_data(BRAIN_DIR)

@app.get("/api/graph/local")
def api_local_graph(request: Request, path: str, depth: int = 2):
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    graph_data = build_graph_data(BRAIN_DIR)
    return build_local_subgraph(graph_data, path, depth)

@app.get("/edit", response_class=HTMLResponse)
def get_edit(request: Request, path: str):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    path_key = path.replace("\\", "/").lower()
    file_index = index_brain_files()
    if path_key not in file_index:
        raise HTTPException(status_code=404, detail="Note not found")
        
    safe_rel_path = file_index[path_key]
    abs_path = validate_path(safe_rel_path)
        
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    note_name = os.path.splitext(os.path.basename(abs_path))[0]
    
    return templates.TemplateResponse(request, "edit.html", get_context(
        request,
        note_name=note_name,
        note_path=safe_rel_path,
        content=content
    ))

@app.post("/edit")
def post_edit(request: Request, path: str = Form(...), content: str = Form(...)):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=303)
        
    path_key = path.replace("\\", "/").lower()
    file_index = index_brain_files()
    if path_key not in file_index:
        raise HTTPException(status_code=404, detail="Note not found")
        
    safe_rel_path = file_index[path_key]
    abs_path = validate_path(safe_rel_path)
    
    # Normalize line endings to avoid git diff noise
    normalized_content = content.replace("\r\n", "\n")
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(normalized_content)
        
    return RedirectResponse(url=f"/note?path={safe_rel_path}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=True)
