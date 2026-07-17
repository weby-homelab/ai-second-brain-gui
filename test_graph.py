import os
import pytest
from fastapi.testclient import TestClient
from main import app, BRAIN_DIR, SESSIONS
from graph_builder import build_graph_data, build_local_subgraph

client = TestClient(app)

def test_graph_builder_parsing():
    # Test builder on real BRAIN_DIR
    data = build_graph_data(BRAIN_DIR)
    
    assert "nodes" in data
    assert "links" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["links"], list)
    
    if len(data["nodes"]) > 0:
        # Check node structure
        node = data["nodes"][0]
        assert "id" in node
        assert "title" in node
        assert "group" in node
        assert "path" in node
        
    if len(data["links"]) > 0:
        # Check link structure
        link = data["links"][0]
        assert "source" in link
        assert "target" in link


def test_local_subgraph_extraction():
    data = build_graph_data(BRAIN_DIR)
    
    if len(data["nodes"]) > 0:
        # Select first node as start node
        start_node = data["nodes"][0]["id"]
        subgraph = build_local_subgraph(data, start_node, depth=2)
        
        assert "nodes" in subgraph
        assert "links" in subgraph
        # Subgraph must contain at least the start node
        assert any(n["id"] == start_node for n in subgraph["nodes"])


def test_api_graph_unauthorized():
    # Accessing routes without active session must return 401 (via HTTPException) or redirect to login
    # Wait, in get_current_user: it returns None, and the endpoint raises 401.
    # Let's test the endpoint directly.
    response = client.get("/api/graph/global")
    assert response.status_code == 401
    
    response = client.get("/api/graph/local?path=protocols/home.md")
    assert response.status_code == 401


def test_api_graph_authorized():
    # Mock active session
    session_token = "test-session-1234"
    SESSIONS.add(session_token)
    
    # Set session cookie
    client.cookies.set("session_token", session_token)
    
    # 1. Global graph
    response = client.get("/api/graph/global")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
    
    # 2. Local graph
    response = client.get("/api/graph/local?path=protocols/home.md&depth=2")
    assert response.status_code == 200
    local_data = response.json()
    assert "nodes" in local_data
    assert "links" in local_data
    
    # Clean up
    SESSIONS.remove(session_token)


def test_robots_txt():
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "User-agent" in response.text
    assert "Sitemap:" in response.text


def test_sitemap_xml():
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<urlset" in response.text
    assert "<loc>" in response.text


def test_edit_unauthorized():
    response = client.get("/edit?path=protocols/home.md", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]


def test_edit_authorized_get_and_post():
    session_token = "test-session-1234"
    SESSIONS.add(session_token)
    client.cookies.set("session_token", session_token)
    
    from main import index_brain_files
    file_index = index_brain_files()
    if file_index:
        # Get one real test path
        test_path = list(file_index.values())[0]
        
        # Read current content to restore it later
        from main import validate_path
        abs_path = validate_path(test_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            
        try:
            # Test GET /edit
            response = client.get(f"/edit?path={test_path}")
            assert response.status_code == 200
            assert "editor-textarea" in response.text
            
            # Test POST /edit
            new_content = original_content + "\n\n<!-- test edit edit_authorized_post -->"
            response = client.post("/edit", data={"path": test_path, "content": new_content}, follow_redirects=False)
            assert response.status_code == 303
            
            # Verify file was written
            with open(abs_path, "r", encoding="utf-8") as f:
                updated_content = f.read()
            assert "test edit edit_authorized_post" in updated_content
            
        finally:
            # Restore original content
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(original_content)
                
    SESSIONS.remove(session_token)

