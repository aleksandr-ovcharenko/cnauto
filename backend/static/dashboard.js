// Fetch and render admin dashboard stats and chart
function fetchAndRender(endpoint, elementId) {
  fetch(endpoint)
    .then(r => r.json())
    .then(data => {
      if (elementId === 'server-stats') {
        document.getElementById('cpu-percent').textContent = data.cpu_percent;
        document.getElementById('mem-used').textContent = formatBytes(data.memory.used);
        document.getElementById('mem-total').textContent = formatBytes(data.memory.total);
        document.getElementById('mem-percent').textContent = data.memory.percent;
        document.getElementById('disk-used').textContent = formatBytes(data.disk.used);
        document.getElementById('disk-total').textContent = formatBytes(data.disk.total);
        document.getElementById('disk-percent').textContent = data.disk.percent;
        document.getElementById('uptime').textContent = Math.floor(data.uptime_seconds / 3600) + 'h ' +
          Math.floor((data.uptime_seconds % 3600) / 60) + 'm';
      } else if (elementId === 'app-stats') {
        document.getElementById('active-users').textContent = data.active_users;
        document.getElementById('visits-today').textContent = data.visits_today;
        document.getElementById('error-count').textContent = data.error_count_24h;
        document.getElementById('queue-length').textContent = data.queue_length;
        const logins = document.getElementById('recent-logins');
        logins.innerHTML = '';
        (data.recent_logins || []).forEach(login => {
          const li = document.createElement('li');
          li.textContent = login;
          logins.appendChild(li);
        });
      } else if (elementId === 'health-stats') {
        function badge(el, status) {
          el.textContent = status;
          el.className = 'badge ' + (status === 'ok' || status === true ? 'badge-success' : 'badge-danger');
        }
        badge(document.getElementById('db-status'), data.db_status);
        badge(document.getElementById('cache-status'), data.cache_status);
        badge(document.getElementById('worker-status'), data.worker_status);
        document.getElementById('recent-deploy').textContent = data.recent_deploy || '-';
        badge(document.getElementById('pending-updates'), data.pending_updates ? 'yes' : 'no');
      } else if (elementId === 'misc-stats') {
        document.getElementById('version').textContent = data.version || '-';
        document.getElementById('commit').textContent = data.commit || '-';
        const ann = document.getElementById('announcements');
        ann.innerHTML = '';
        (data.announcements || []).forEach(msg => {
          const li = document.createElement('li');
          li.textContent = msg;
          ann.appendChild(li);
        });
      } else {
        document.getElementById(elementId).textContent = JSON.stringify(data, null, 2);
      }
    })
    .catch(() => {
      document.getElementById(elementId).textContent = 'Failed to load.';
    });
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  let units = ['KB', 'MB', 'GB', 'TB'];
  let i = -1;
  do {
    bytes = bytes / 1024;
    i++;
  } while (bytes >= 1024 && i < units.length - 1);
  return bytes.toFixed(1) + ' ' + units[i];
}

document.addEventListener('DOMContentLoaded', function () {
  fetchAndRender('/admin/stats/server', 'server-stats');
  fetchAndRender('/admin/stats/app', 'app-stats');
  fetchAndRender('/admin/stats/health', 'health-stats');
  fetchAndRender('/admin/stats/misc', 'misc-stats');

  fetch('/admin/stats/visualizations')
    .then(r => r.json())
    .then(data => {
      if (data.traffic && data.traffic.length) {
        const labels = data.traffic.map(item => item.hour || item.label);
        const visits = data.traffic.map(item => item.visits);
        const ctx = document.getElementById('traffic-chart').getContext('2d');
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'Visits',
              backgroundColor: '#42b983',
              borderColor: '#42b983',
              fill: false,
              data: visits
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        });
        const barCtx = document.getElementById('traffic-bar-chart').getContext('2d');
        new Chart(barCtx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Visits',
              backgroundColor: '#007bff',
              data: visits
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        });
        const pieCtx = document.getElementById('traffic-pie-chart').getContext('2d');
        new Chart(pieCtx, {
          type: 'pie',
          data: {
            labels: labels,
            datasets: [{
              label: 'Visits',
              backgroundColor: [
                '#42b983', '#007bff', '#ffc107', '#dc3545', '#17a2b8', '#6f42c1', '#fd7e14', '#28a745', '#6610f2', '#e83e8c'
              ],
              data: visits
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        });
      } else {
        document.getElementById('traffic-chart').parentElement.textContent = 'No data';
      }
    })
    .catch(() => {
      document.getElementById('traffic-chart').parentElement.textContent = 'Failed to load chart.';
    });
});
