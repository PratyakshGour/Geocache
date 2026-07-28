let clusterData = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchCities();
    fetchClusterStatus();
    setInterval(fetchClusterStatus, 3000);

    document.getElementById('btn-set').addEventListener('click', handleSetCache);
    document.getElementById('btn-get').addEventListener('click', handleGetCache);
    document.getElementById('btn-delete').addEventListener('click', handleDeleteCache);
    document.getElementById('btn-clear-all').addEventListener('click', handleClearCluster);
});

function logMessage(msg, type = 'info') {
    const consoleBox = document.getElementById('console-log');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timeStr = new Date().toLocaleTimeString();
    entry.innerHTML = `<span class="log-time">[${timeStr}]</span> ${msg}`;
    consoleBox.insertBefore(entry, consoleBox.firstChild);
}

async function fetchCities() {
    try {
        const res = await fetch('/api/v1/cluster/cities');
        const data = await res.json();
        const select = document.getElementById('select-city');
        select.innerHTML = '';
        data.cities.forEach(city => {
            const opt = document.createElement('option');
            opt.value = city.name;
            opt.textContent = `${city.name} (${city.lat.toFixed(2)}, ${city.lon.toFixed(2)})`;
            select.appendChild(opt);
        });
    } catch (err) {
        logMessage(`Failed to load preset cities: ${err.message}`, 'warn');
    }
}

async function fetchClusterStatus() {
    try {
        const res = await fetch('/api/v1/cluster/status');
        const data = await res.json();
        clusterData = data;
        renderMetrics(data);
        renderRegions(data.regions);
    } catch (err) {
        console.error('Error fetching cluster status:', err);
    }
}

function renderMetrics(data) {
    document.getElementById('metric-total-items').textContent = data.total_cluster_items;
    document.getElementById('metric-hit-ratio').textContent = `${data.cluster_hit_ratio}%`;
    document.getElementById('metric-total-requests').textContent = (data.total_cluster_hits + data.total_cluster_misses);
    document.getElementById('metric-active-nodes').textContent = data.regions.length;
}

function renderRegions(regions) {
    const grid = document.getElementById('regions-grid');
    grid.innerHTML = '';

    regions.forEach(reg => {
        const card = document.createElement('div');
        card.className = 'region-card';
        card.id = `region-card-${reg.region_id}`;
        
        card.innerHTML = `
            <div class="region-header">
                <div>
                    <div class="region-name">${reg.name}</div>
                    <div class="region-loc">📍 ${reg.location}</div>
                </div>
                <span class="region-badge">${reg.region_id}</span>
            </div>
            <div class="region-stats-list">
                <div class="stats-row">
                    <span>Active Items:</span>
                    <span>${reg.total_items} / ${reg.max_capacity}</span>
                </div>
                <div class="stats-row">
                    <span>Hit Ratio:</span>
                    <span>${reg.hit_ratio}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${reg.hit_ratio}%"></div>
                </div>
                <div class="stats-row" style="margin-top: 0.3rem;">
                    <span>Hits / Misses:</span>
                    <span>${reg.hits} / ${reg.misses}</span>
                </div>
                <div class="stats-row">
                    <span>Evictions:</span>
                    <span>${reg.evictions}</span>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function highlightServedRegion(regionId) {
    document.querySelectorAll('.region-card').className = 'region-card';
    const card = document.getElementById(`region-card-${regionId}`);
    if (card) {
        card.classList.add('active-served');
        setTimeout(() => card.classList.remove('active-served'), 2500);
    }
}

async function handleSetCache(e) {
    e.preventDefault();
    const city = document.getElementById('select-city').value;
    const key = document.getElementById('input-key').value.trim();
    const value = document.getElementById('input-val').value.trim();
    const ttl = parseInt(document.getElementById('input-ttl').value) || 3600;

    if (!key || !value) {
        alert('Please enter both Key and Value to store in GeoCache.');
        return;
    }

    try {
        const res = await fetch('/api/v1/cache/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value, ttl, city })
        });
        const data = await res.json();
        
        if (res.ok) {
            highlightServedRegion(data.served_by_region);
            logMessage(`✅ <span class="highlight">SET</span> Key "<b>${key}</b>" routed from <b>${city}</b> to closest node <span class="highlight">${data.region_name}</span> (Dist: ${data.distance_km}km, Latency: ${data.simulated_latency_ms}ms). Replicated across ${data.replicated_to.length} nodes!`, 'success');
            fetchClusterStatus();
        } else {
            logMessage(`❌ Set Error: ${data.detail || 'Unknown error'}`, 'warn');
        }
    } catch (err) {
        logMessage(`❌ Network error: ${err.message}`, 'warn');
    }
}

async function handleGetCache(e) {
    e.preventDefault();
    const city = document.getElementById('select-city').value;
    const key = document.getElementById('input-key').value.trim();

    if (!key) {
        alert('Please enter a Key to fetch.');
        return;
    }

    try {
        const res = await fetch(`/api/v1/cache/get/${encodeURIComponent(key)}?city=${encodeURIComponent(city)}`);
        const data = await res.json();
        
        if (res.ok) {
            highlightServedRegion(data.served_by_region);
            if (data.hit) {
                logMessage(`⚡ <span class="highlight">GET HIT</span> for Key "<b>${key}</b>" = "<b>${JSON.stringify(data.value)}</b>" served by node <span class="highlight">${data.region_name}</span> in <b>${data.simulated_latency_ms}ms</b> (Dist: ${data.distance_km}km, TTL remaining: ${data.ttl_remaining}s).`, 'success');
            } else {
                logMessage(`⚠️ <span class="highlight">GET MISS</span> for Key "<b>${key}</b>" from node ${data.region_name} (Checked WAN fallback: not found in any region).`, 'warn');
            }
            fetchClusterStatus();
        } else {
            logMessage(`❌ Get Error: ${data.detail || 'Unknown error'}`, 'warn');
        }
    } catch (err) {
        logMessage(`❌ Network error: ${err.message}`, 'warn');
    }
}

async function handleDeleteCache(e) {
    e.preventDefault();
    const key = document.getElementById('input-key').value.trim();

    if (!key) {
        alert('Please enter a Key to delete.');
        return;
    }

    try {
        const res = await fetch(`/api/v1/cache/${encodeURIComponent(key)}`, { method: 'DELETE' });
        const data = await res.json();
        
        if (res.ok) {
            logMessage(`🗑️ <span class="highlight">EVICTED</span> Key "<b>${key}</b>" across cluster nodes: [${data.invalidated_regions.join(', ')}].`, 'info');
            fetchClusterStatus();
        } else {
            logMessage(`⚠️ Delete: ${data.detail || 'Key not found'}`, 'warn');
        }
    } catch (err) {
        logMessage(`❌ Network error: ${err.message}`, 'warn');
    }
}

async function handleClearCluster() {
    if (!confirm('Are you sure you want to clear all data across all regional cache servers?')) return;
    try {
        const res = await fetch('/api/v1/cluster/clear', { method: 'POST' });
        if (res.ok) {
            logMessage(`🧹 <span class="highlight">CLUSTER RESET</span>: All regional cache nodes cleared and counters reset.`, 'info');
            fetchClusterStatus();
        }
    } catch (err) {
        logMessage(`❌ Error clearing cluster: ${err.message}`, 'warn');
    }
}
