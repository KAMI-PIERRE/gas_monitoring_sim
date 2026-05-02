// Gas sensors
const co2 = document.getElementById("co2");
const o2 = document.getElementById("o2");
const n2o = document.getElementById("n2o");
const bacteria = document.getElementById("bacteria");

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
    fetch("/update", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            co2: parseInt(co2.value),
            o2: parseFloat(o2.value),
            n2o: parseInt(n2o.value),
            bacteria: parseInt(bacteria.value)
        })
    })
    .then(res => res.json())
    .then(data => {
        status.innerText = "STATUS: " + data.level;
        led.className = "led";
        if (data.level === "NORMAL") {
            led.classList.add("green");
            buzzer.innerText = "🔇";
        } else if (data.level === "WARNING") {
            led.classList.add("yellow");
            buzzer.innerText = "🔊 BEEP";
        } else {
            led.classList.add("red");
            buzzer.innerText = "🚨 ALARM";
        }
        notification.innerText = data.message;
    });
}

// ROBOT
let robot = document.getElementById("robot");
let robotPath = [];
let robotStep = 0;
let isMonitoring = false;

function moveRobot(x, y) {
    robot.style.left = x + "px";
    robot.style.top = y + "px";
}

function stopMonitoring() {
    if (window.monitoringInterval) {
        clearInterval(window.monitoringInterval);
    }
    isMonitoring = false;
}

function startRobot() {
    stopMonitoring();
    robotStep = 0;
    let mode = document.getElementById("mode").value;
    if (mode === "before") beforeOperation();
    else if (mode === "during") duringOperation();
    else afterOperation();
}

// Before operation - robot scans the room
function beforeOperation() {
    robotStatus.innerText = "🤖 PRE-OPERATION: Scanning room for contaminants...";
    robot.classList.add("scanning");
    const path = [
        [20, 20], [180, 20], [340, 20], [340, 100], [340, 180],
        [180, 180], [20, 180], [20, 100], [180, 100]
    ];
    animatePath(path, 600, true);
}

// During operation - robot stays static and monitors
function duringOperation() {
    robotStatus.innerText = "🤖 DURING OPERATION: Continuous monitoring active";
    robot.classList.remove("scanning");
    robot.classList.add("monitoring");
    moveRobot(280, 180);
    isMonitoring = true;
    window.monitoringInterval = setInterval(() => { simulateSensors(); }, 2000);
}

// After operation - robot does final inspection
function afterOperation() {
    robotStatus.innerText = "🤖 POST-OPERATION: Final room inspection...";
    robot.classList.add("scanning");
    const path = [
        [180, 100], [20, 20], [180, 20], [340, 20], [340, 100],
        [340, 180], [180, 180], [20, 180], [20, 100], [180, 100]
    ];
    animatePath(path, 800, false);
}

function animatePath(path, speed, shouldMonitor) {
    robotPath = path;
    robotStep = 0;
    function nextStep() {
        if (robotStep >= path.length) {
            if (shouldMonitor) {
                robotStatus.innerText = "✅ Pre-operation scan complete - Room Ready";
            } else {
                robotStatus.innerText = "✅ Post-operation inspection complete";
            }
            robot.classList.remove("scanning");
            return;
        }
        const [x, y] = path[robotStep];
        moveRobot(x, y);
        robot.innerHTML = "📡";
        if (shouldMonitor) { simulateSensors(); }
        robotStep++;
        setTimeout(nextStep, speed);
    }
    nextStep();
}

// Simulate sensors during robot movement
function simulateSensors() {
    fetch("/simulate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ mode: document.getElementById("mode").value })
    })
    .then(res => res.json())
    .then(data => {
        co2.value = data.co2;
        o2.value = data.o2;
        n2o.value = data.n2o;
        bacteria.value = data.bacteria;
        co2_val.innerText = data.co2;
        o2_val.innerText = data.o2;
        n2o_val.innerText = data.n2o;
        bacteria_val.innerText = data.bacteria;
        status.innerText = "STATUS: " + data.level;
        led.className = "led";
        if (data.level === "NORMAL") {
            led.classList.add("green");
            buzzer.innerText = "🔇";
        } else if (data.level === "WARNING") {
            led.classList.add("yellow");
            buzzer.innerText = "🔊 BEEP";
        } else {
            led.classList.add("red");
            buzzer.innerText = "🚨 ALARM";
        }
        notification.innerText = data.message;
    });
}