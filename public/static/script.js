const co2 = document.getElementById("co2");
const o2 = document.getElementById("o2");
const n2o = document.getElementById("n2o");
const bacteria = document.getElementById("bacteria");
const co2_val = document.getElementById("co2_val");
const o2_val = document.getElementById("o2_val");
const n2o_val = document.getElementById("n2o_val");
const bacteria_val = document.getElementById("bacteria_val");
const statusLabel = document.getElementById("status");
const led = document.getElementById("led");
const buzzer = document.getElementById("buzzer");
const notification = document.getElementById("notification");
const robotStatus = document.getElementById("robotStatus");
const robot = document.getElementById("robot");

let trendChart = null;
let latestChart = null;
let statusChart = null;
let chartHistory = [];

function createInitialHistoryEntry() {
    return {
        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'}),
        co2: Number(co2.value),
        o2: Number(o2.value),
        n2o: Number(n2o.value),
        bacteria: Number(bacteria.value),
        level: 'NORMAL'
    };
}

function updateValues() {
    co2_val.innerText = co2.value;
    o2_val.innerText = o2.value;
    n2o_val.innerText = n2o.value;
    bacteria_val.innerText = bacteria.value;
}

co2.oninput = updateValues;
o2.oninput = updateValues;
n2o.oninput = updateValues;
bacteria.oninput = updateValues;

function sendData() {
    fetch('/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            co2: Number(co2.value),
            o2: Number(o2.value),
            n2o: Number(n2o.value),
            bacteria: Number(bacteria.value)
        })
    })
    .then(res => res.json())
    .then(data => {
        const reading = {
            timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'}),
            co2: Number(co2.value),
            o2: Number(o2.value),
            n2o: Number(n2o.value),
            bacteria: Number(bacteria.value),
            level: data.level || 'NORMAL'
        };

        addHistoryEntry(reading);
        updateDashboard(data);
        fetchHistory();
    })
    .catch(() => {
        notification.innerText = 'Unable to reach the server. Check deployment or network.';
    });
}

function addHistoryEntry(reading) {
    chartHistory.push(reading);
    if (chartHistory.length > 12) {
        chartHistory.shift();
    }
    localStorage.setItem('gasDashboardHistory', JSON.stringify(chartHistory));
}

function loadHistoryFromStorage() {
    const stored = localStorage.getItem('gasDashboardHistory');
    if (stored) {
        try {
            chartHistory = JSON.parse(stored);
        } catch (error) {
            chartHistory = [];
        }
    }
    if (chartHistory.length === 0) {
        addHistoryEntry(createInitialHistoryEntry());
    }
}

function updateChartsFromStorage() {
    const labels = chartHistory.map(entry => entry.timestamp);
    const co2Data = chartHistory.map(entry => entry.co2);
    const o2Data = chartHistory.map(entry => entry.o2);
    const latest = chartHistory[chartHistory.length - 1] || {co2: 0, o2: 0, n2o: 0, bacteria: 0};
    const statusCounts = {
        NORMAL: chartHistory.filter(entry => entry.level === 'NORMAL').length,
        WARNING: chartHistory.filter(entry => entry.level === 'WARNING').length,
        CRITICAL: chartHistory.filter(entry => entry.level === 'CRITICAL').length
    };

    updateCharts({
        labels,
        co2: co2Data,
        o2: o2Data,
        latest,
        statusCounts
    });
}

function fetchHistory() {
    fetch('/history')
        .then(res => res.json())
        .then(data => {
            if (data && data.labels && data.labels.length > 0) {
                updateCharts({
                    labels: data.labels,
                    co2: data.co2,
                    o2: data.o2,
                    latest: data.latest,
                    statusCounts: data.statusCounts
                });
            } else {
                updateChartsFromStorage();
            }
        })
        .catch(() => {
            updateChartsFromStorage();
        });
}

function updateDashboard(data) {
    const level = data.level || data.status || 'NORMAL';
    statusLabel.innerText = 'STATUS: ' + level;
    led.className = 'led';

    if (level === 'NORMAL') {
        led.classList.add('green');
        buzzer.innerText = '🔇';
    } else if (level === 'WARNING') {
        led.classList.add('yellow');
        buzzer.innerText = '🔊 BEEP';
    } else {
        led.classList.add('red');
        buzzer.innerText = '🚨 ALARM';
    }

    notification.innerText = data.message || 'Status updated.';
}

function refreshDashboard() {
    fetchHistory();
}

function initCharts() {
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    const latestCtx = document.getElementById('latestChart').getContext('2d');
    const statusCtx = document.getElementById('statusChart').getContext('2d');

    trendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CO2 (ppm)',
                    data: [],
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.2)',
                    tension: 0.3,
                    yAxisID: 'y1'
                },
                {
                    label: 'O2 (%)',
                    data: [],
                    borderColor: '#7cff00',
                    backgroundColor: 'rgba(124, 255, 0, 0.2)',
                    tension: 0.3,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.08)' } },
                y1: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'CO2 (ppm)' },
                    grid: { color: 'rgba(255,255,255,0.08)' }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'O2 (%)' },
                    grid: { drawOnChartArea: false, color: 'rgba(255,255,255,0.08)' }
                }
            }
        }
    });

    latestChart = new Chart(latestCtx, {
        type: 'bar',
        data: {
            labels: ['CO2', 'O2', 'N2O', 'Bacteria'],
            datasets: [{
                label: 'Latest Reading',
                data: [0, 0, 0, 0],
                backgroundColor: ['#00d4ff', '#7cff00', '#ffea00', '#ff4d4d']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.08)' } }
            }
        }
    });

    statusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['NORMAL', 'WARNING', 'CRITICAL'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#00ff88', '#ffcc00', '#ff4d4d']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function updateCharts(data) {
    if (!trendChart || !latestChart || !statusChart) return;

    const labels = data.labels && data.labels.length ? data.labels : ['No data'];
    const co2Data = data.co2 && data.co2.length ? data.co2 : [0];
    const o2Data = data.o2 && data.o2.length ? data.o2 : [0];

    trendChart.data.labels = labels;
    trendChart.data.datasets[0].data = co2Data;
    trendChart.data.datasets[1].data = o2Data;
    trendChart.update();

    latestChart.data.datasets[0].data = [
        data.latest?.co2 || 0,
        data.latest?.o2 || 0,
        data.latest?.n2o || 0,
        data.latest?.bacteria || 0
    ];
    latestChart.update();

    statusChart.data.datasets[0].data = [
        data.statusCounts?.NORMAL || 0,
        data.statusCounts?.WARNING || 0,
        data.statusCounts?.CRITICAL || 0
    ];
    statusChart.update();
}

function moveRobot(x, y) {
    robot.style.left = x + 'px';
    robot.style.top = y + 'px';
}

function stopMonitoring() {
    if (window.monitoringInterval) {
        clearInterval(window.monitoringInterval);
    }
}

function startRobot() {
    stopMonitoring();
    const mode = document.getElementById('mode').value;

    if (mode === 'before') beforeOperation();
    else if (mode === 'during') duringOperation();
    else afterOperation();
}

function beforeOperation() {
    robotStatus.innerText = 'Scanning before operation...';
    robot.classList.add('scanning');
    animate([[0,0],[300,0],[300,150],[0,150],[150,75]], 500, true);
}

function duringOperation() {
    robotStatus.innerText = 'Static monitoring...';
    robot.classList.add('monitoring');
    moveRobot(150,75);
    window.monitoringInterval = setInterval(() => { sendData(); }, 2000);
}

function afterOperation() {
    robotStatus.innerText = 'Final inspection...';
    robot.classList.remove('monitoring', 'scanning');
    animate([[150,75],[300,50],[200,150],[50,120],[0,0]], 1200, true);
}

function animate(path, speed, monitor = false) {
    let i = 0;
    function step() {
        if (i < path.length) {
            moveRobot(path[i][0], path[i][1]);
            if (monitor) sendData();
            i++;
            setTimeout(step, speed);
        } else {
            robot.classList.remove('monitoring', 'scanning');
        }
    }
    step();
}

window.addEventListener('DOMContentLoaded', () => {
    updateValues();
    loadHistoryFromStorage();
    initCharts();
    updateChartsFromStorage();
    fetchHistory();
});
