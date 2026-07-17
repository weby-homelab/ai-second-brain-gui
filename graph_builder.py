import os
import re
import yaml

def build_graph_data(brain_dir: str):
    nodes = []
    links = []
    node_ids = set()

    for root, _, files in os.walk(brain_dir):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            if file.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, file), brain_dir)
                node_id = rel_path.replace("\\", "/").lower()
                
                # Default values
                title = os.path.splitext(file)[0]
                group = "Other"
                
                # Determine PARA category
                parts = rel_path.split(os.sep)
                if len(parts) > 1:
                    if parts[0] in ["01_Projects", "02_Areas", "03_Resources", "04_Archive", "06_Daily_Logs"]:
                        group = parts[0]

                abs_path = os.path.join(brain_dir, rel_path)
                related_links = []
                
                # Parse metadata and inline links
                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Extract YAML frontmatter
                        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                        if frontmatter_match:
                            metadata = yaml.safe_load(frontmatter_match.group(1))
                            if metadata:
                                if "title" in metadata:
                                    title = metadata["title"]
                                if "related" in metadata:
                                    raw_related = metadata["related"]
                                    if isinstance(raw_related, list):
                                        related_links.extend(raw_related)
                                    elif isinstance(raw_related, str):
                                        related_links.append(raw_related)

                        # Extract inline [[Wiki-links]]
                        inline_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
                        for link in inline_links:
                            link_id = link.strip().replace("\\", "/").lower()
                            # Ignore media and links with protocols
                            if not any(link_id.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']) and "://" not in link_id:
                                if not link_id.endswith(".md"):
                                    link_id += ".md"
                                related_links.append(link_id)
                except Exception:
                    pass

                nodes.append({
                    "id": node_id,
                    "title": title,
                    "group": group,
                    "path": rel_path
                })
                node_ids.add(node_id)
                
                # Temporarily save raw links for validation
                for target in related_links:
                    links.append({"source": node_id, "target": target})
                    
    # Validate target links (ensure target nodes exist)
    valid_links = []
    for link in links:
        source = link["source"]
        target = link["target"].lower()
        
        # If target has no path prefix, try to resolve it from node filenames
        if "/" not in target:
            target_resolved = None
            for n_id in node_ids:
                if os.path.basename(n_id) == target or os.path.splitext(os.path.basename(n_id))[0] == target:
                    target_resolved = n_id
                    break
            if target_resolved:
                target = target_resolved
        
        # Re-verify and append
        if target in node_ids:
            # Avoid duplicate links
            link_entry = {"source": source, "target": target}
            if link_entry not in valid_links:
                valid_links.append(link_entry)
            
    return {"nodes": nodes, "links": valid_links}


def build_local_subgraph(graph_data: dict, start_node: str, depth: int = 2):
    start_node = start_node.replace("\\", "/").lower()
    visited_nodes = {start_node}
    current_layer = {start_node}
    
    for _ in range(depth):
        next_layer = set()
        for node in current_layer:
            for link in graph_data["links"]:
                src = link["source"]
                tgt = link["target"]
                if src == node and tgt not in visited_nodes:
                    visited_nodes.add(tgt)
                    next_layer.add(tgt)
                elif tgt == node and src not in visited_nodes:
                    visited_nodes.add(src)
                    next_layer.add(src)
        current_layer = next_layer
        if not current_layer:
            break
            
    sub_nodes = [n for n in graph_data["nodes"] if n["id"] in visited_nodes]
    sub_links = [l for l in graph_data["links"] if l["source"] in visited_nodes and l["target"] in visited_nodes]
    
    return {"nodes": sub_nodes, "links": sub_links}
