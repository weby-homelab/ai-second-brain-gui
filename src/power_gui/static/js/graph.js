/**
 * POWER-GUI Knowledge Graph Interactive Visualization
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
        btn.textContent = '📋 Показати таблицю доступності';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleTableBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTableView);
    }

    const elem = document.getElementById('graphContainer');
    if (!elem || typeof ForceGraph === 'undefined') return;

    fetch('/api/graph/data')
        .then(res => res.json())
        .then(data => {
            const categoryColors = {
                '01_Projects': '#a855f7',
                '02_Areas': '#3b82f6',
                '03_Resources': '#10b981',
                '04_Archive': '#64748b',
                '06_Daily_Logs': '#eab308',
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

            ForceGraph()(elem)
                .graphData(data)
                .nodeId('id')
                .nodeLabel(node => `${node.label} (${node.category})`)
                .nodeColor(node => getNodeColor(node.category))
                .nodeVal(node => Math.max(3, (node.degree || 1) * 2))
                .linkColor(() => 'rgba(255, 255, 255, 0.2)')
                .linkWidth(1)
                .backgroundColor('#0b0f19')
                .onNodeClick(node => {
                    window.location.href = `/notes/read?path=${encodeURIComponent(node.id)}`;
                });
        })
        .catch(err => console.error("Failed to load graph data:", err));
});
