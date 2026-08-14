/**
 * POWER-GUI Knowledge Graph Interactive Visualization with Filtering & Uniform Node Sizing
 */

function toggleTableView() {
    const tbl = document.getElementById('accessibleTableContainer');
    const btn = document.getElementById('toggleTableBtn');
    if (!tbl || !btn) return;
    if (tbl.style.display === 'none') {
        tbl.style.display = 'block';
        btn.textContent = '🙈 Приховати таблицю';
    } else {
        tbl.style.display = 'none';
        btn.textContent = '📋 Показати таблицю';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleTableBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTableView);
    }

    const elem = document.getElementById('graphContainer');
    if (!elem || typeof ForceGraph === 'undefined') return;

    const searchInput = document.getElementById('graphSearchInput');
    const categorySelect = document.getElementById('graphCategorySelect');
    const degreeSelect = document.getElementById('graphDegreeSelect');
    const resetBtn = document.getElementById('graphResetBtn');
    const zoomFitBtn = document.getElementById('graphZoomFitBtn');
    const nodesCountEl = document.getElementById('nodesCount');
    const edgesCountEl = document.getElementById('edgesCount');
    const tableRows = document.querySelectorAll('.graph-table-row');

    let graphInstance = null;
    let rawGraphData = { nodes: [], links: [] };

    const categoryColors = {
        '00_Inbox': '#06b6d4',
        '01_Projects': '#a855f7',
        '02_Areas': '#3b82f6',
        '03_Resources': '#10b981',
        '04_Archive': '#64748b',
        '06_Daily_Logs': '#eab308',
        'PROTOCOLS': '#f43f5e',
        'Projects': '#a855f7',
        'Areas': '#3b82f6',
        'Resources': '#10b981',
        'Archive': '#64748b',
        'Inbox': '#06b6d4',
        'root': '#38bdf8'
    };

    const getNodeColor = (cat) => {
        if (!cat) return '#38bdf8';
        if (categoryColors[cat]) return categoryColors[cat];
        let hash = 0;
        for (let i = 0; i < cat.length; i++) {
            hash = cat.charCodeAt(i) + ((hash << 5) - hash);
        }
        const hue = Math.abs(hash % 360);
        return `hsl(${hue}, 75%, 60%)`;
    };

    const updateFilter = () => {
        if (!rawGraphData.nodes.length) return;

        const q = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const selectedCat = categorySelect ? categorySelect.value : '';
        const minDegree = degreeSelect ? (parseInt(degreeSelect.value, 10) || 0) : 0;

        const filteredNodes = rawGraphData.nodes.filter(node => {
            const matchesQuery = !q ||
                (node.label && node.label.toLowerCase().includes(q)) ||
                (node.id && node.id.toLowerCase().includes(q));
            const matchesCat = !selectedCat || node.category === selectedCat;
            const matchesDegree = (node.degree || 0) >= minDegree;
            return matchesQuery && matchesCat && matchesDegree;
        });

        const activeNodeIds = new Set(filteredNodes.map(n => n.id));

        const filteredLinks = rawGraphData.links.filter(link => {
            const sId = typeof link.source === 'object' ? link.source.id : link.source;
            const tId = typeof link.target === 'object' ? link.target.id : link.target;
            return activeNodeIds.has(sId) && activeNodeIds.has(tId);
        });

        if (graphInstance) {
            graphInstance.graphData({
                nodes: filteredNodes,
                links: filteredLinks
            });
        }

        if (nodesCountEl) nodesCountEl.textContent = filteredNodes.length;
        if (edgesCountEl) edgesCountEl.textContent = filteredLinks.length;

        // Filter accessibility table rows
        tableRows.forEach(row => {
            const rowId = row.getAttribute('data-id');
            if (activeNodeIds.has(rowId)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    };

    fetch('/api/graph/data')
        .then(res => res.json())
        .then(data => {
            rawGraphData = {
                nodes: data.nodes || [],
                links: data.links || []
            };

            // Populate Category Select dynamically
            if (categorySelect) {
                const categories = Array.from(new Set(rawGraphData.nodes.map(n => n.category).filter(Boolean))).sort();
                categorySelect.innerHTML = '<option value="">Усі категорії (All)</option>';
                categories.forEach(cat => {
                    const opt = document.createElement('option');
                    opt.value = cat;
                    opt.textContent = `${cat} (${rawGraphData.nodes.filter(n => n.category === cat).length})`;
                    categorySelect.appendChild(opt);
                });
            }

            // Instantiate 2D ForceGraph with UNIFORM NODE SIZES (all dots equal size)
            graphInstance = ForceGraph()(elem)
                .graphData({
                    nodes: [...rawGraphData.nodes],
                    links: [...rawGraphData.links]
                })
                .nodeId('id')
                .nodeLabel(node => `${node.label} (${node.category})\nЗв'язків: ${node.degree || 0}`)
                .nodeColor(node => getNodeColor(node.category))
                .nodeVal(4) // Uniform node size: every dot is exactly size 4
                .nodeRelSize(4) // Fixed relative scale
                .linkColor(() => 'rgba(255, 255, 255, 0.25)')
                .linkWidth(1)
                .backgroundColor('#0b0f19')
                .onNodeClick(node => {
                    window.location.href = `/notes/read?path=${encodeURIComponent(node.id)}`;
                });

            if (nodesCountEl) nodesCountEl.textContent = rawGraphData.nodes.length;
            if (edgesCountEl) edgesCountEl.textContent = rawGraphData.links.length;

            // Attach event listeners
            if (searchInput) searchInput.addEventListener('input', updateFilter);
            if (categorySelect) categorySelect.addEventListener('change', updateFilter);
            if (degreeSelect) degreeSelect.addEventListener('change', updateFilter);

            if (resetBtn) {
                resetBtn.addEventListener('click', () => {
                    if (searchInput) searchInput.value = '';
                    if (categorySelect) categorySelect.value = '';
                    if (degreeSelect) degreeSelect.value = '0';
                    updateFilter();
                    if (graphInstance) graphInstance.zoomToFit(400, 20);
                });
            }

            if (zoomFitBtn) {
                zoomFitBtn.addEventListener('click', () => {
                    if (graphInstance) graphInstance.zoomToFit(400, 20);
                });
            }
        })
        .catch(err => console.error("Failed to load graph data:", err));
});
