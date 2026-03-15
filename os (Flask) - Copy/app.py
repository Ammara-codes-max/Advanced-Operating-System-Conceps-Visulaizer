from flask import Flask, render_template, request, jsonify, redirect, session
from functools import wraps

# ================= IMPORTS =================
from concepts.cpu_scheduling.algorithms import Scheduler as CPUScheduler, Process as CPUProcess
from concepts.deadlock.algorithms import *
from concepts.memory_management.algorithms import *
from concepts.synchronization.algorithms import (
    SynchronizationProcess, Semaphore, Mutex,
    ProducerConsumer, DiningPhilosophers, ReadersWriters
)
from concepts.file_systems.algorithms import FileSystem
from concepts.processes_threads.algorithms import (
    Process as PTProcess, Thread, ThreadModel,
    ProcessScheduler, ThreadManager, IPCManager
)
from concepts.io_management.algorithms import *
from concepts.resource_allocation.algorithms import *

# ================= APP =================
app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# ================= GLOBAL OBJECTS =================
GLOBAL_SEMAPHORES = {}
GLOBAL_MUTEXES = {}
GLOBAL_PC = None
GLOBAL_RW = None
GLOBAL_DP = None
GLOBAL_FS = FileSystem(100)
# ================= GLOBAL MEMORY =================
GLOBAL_MEMORY_BLOCKS = [
    MemoryBlock(0, 100, None)  # total memory = 100
]

# ================= GLOBAL STATES =================

GLOBAL_FS = FileSystem(100)

GLOBAL_SEMAPHORES = {}
GLOBAL_MUTEXES = {}

GLOBAL_PC = None
GLOBAL_RW = None
GLOBAL_DP = None
GLOBAL_SEMAPHORES = {}
GLOBAL_MUTEXES = {}
GLOBAL_PC = ProducerConsumer(5)
GLOBAL_RW = ReadersWriters()
GLOBAL_DP = DiningPhilosophers(5)

# ================= MEMORY GLOBAL STATE =================
GLOBAL_VM = None
GLOBAL_SEGMENT = None


# ================= LOGIN REQUIRED =================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ================= AUTH =================
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            session["user"] = "admin"
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")

# ================= MODULE PAGES =================
@app.route('/cpu_scheduling')
@login_required
def cpu_scheduling(): return render_template('cpu_scheduling.html')
@app.route('/cpu_scheduling/run', methods=['POST'])
@login_required
def run_cpu_scheduling():

    data = request.json
    algorithm = data['algorithm']
    time_quantum = int(data.get('time_quantum', 2))

    processes = []
    for p in data['processes']:
        processes.append(
            CPUProcess(
                p['pid'],
                int(p.get('arrival', p.get('arrival_time', 0))),
                int(p.get('burst', p.get('burst_time', 0))),
                int(p.get('priority', 0))
            )
        )

    if algorithm == 'FCFS':
        result = CPUScheduler.fcfs(processes)
    elif algorithm == 'SJF':
        result = CPUScheduler.sjf(processes)
    elif algorithm == 'Round Robin':
        result = CPUScheduler.round_robin(processes, time_quantum)
    elif algorithm == 'Priority':
        result = CPUScheduler.priority_scheduling(processes)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    return jsonify({
        "processes": [
            {
                "pid": p.pid,
                "waiting_time": p.waiting_time,
                "turnaround_time": p.turnaround_time
            } for p in result["processes"]
        ],
        "order": [g[0] for g in result["gantt_chart"]],
        "gantt_chart": result["gantt_chart"]
    })
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/deadlock')
@login_required
def deadlock(): return render_template('deadlock.html')
@app.route('/deadlock/bankers', methods=['POST'])
@login_required
def run_bankers_algorithm():
    data = request.json

    processes_data = data['processes']
    resources_data = data['resources']

    # -------- RESOURCES --------
    resources = []
    for r in resources_data:
        resources.append(
            Resource(r['rid'], int(r['total_instances']))
        )

    # -------- FIX START --------
    processes = []
    num_resources = len(resources)

    for p in processes_data:
        max_res = [int(x) for x in p['max_resources']]
        alloc_res = [int(x) for x in p['allocated_resources']]

        while len(max_res) < num_resources:
            max_res.append(0)

        while len(alloc_res) < num_resources:
            alloc_res.append(0)

        processes.append(
            Process(p['pid'], max_res, alloc_res)
        )
    # -------- FIX END --------

    result = DeadlockAlgorithms.bankers_algorithm(processes, resources)

    # ✅ RETURN FUNCTION KE ANDAR
    return jsonify(result)
@app.route('/deadlock/detect', methods=['POST'])
@login_required
def detect_deadlock():
    data = request.json
    wait_for_graph = data['wait_for_graph']

    result = DeadlockAlgorithms.detect_deadlock_wait_for_graph(wait_for_graph)
    return jsonify(result)
@app.route('/deadlock/request', methods=['POST'])
@login_required
def resource_request():
    data = request.json

    return jsonify({
        "granted": True,
        "message": "Request granted (simulation)"
    })

@app.route('/memory_management')
@login_required
def memory_management(): return render_template('memory_management.html')
@app.route('/memory_management/page_replacement', methods=['POST'])
@login_required
def page_replacement():
    data = request.json
    algo = data['algorithm']
    pages = data['page_sequence']
    frames = data['num_frames']

    if algo == "fifo":
        return jsonify(PageReplacement.fifo(pages, frames))
    elif algo == "lru":
        return jsonify(PageReplacement.lru(pages, frames))
    else:
        return jsonify(PageReplacement.optimal(pages, frames))

@app.route('/memory_management/virtual_memory', methods=['POST'])
@login_required
def virtual_memory():
    data = request.json

    num_frames = int(data.get('num_frames', 4))   # ✅ FIX
    page_size = int(data.get('page_size', 4096))
    virtual_address = int(data.get('virtual_address'))

    vm = VirtualMemorySimulator(num_frames, page_size)
    pa = vm.translate_address(virtual_address)

    return jsonify({
        "physical_address": pa
    })

@app.route('/memory_management/segmentation', methods=['POST'])
@login_required
def segmentation():
    data = request.json   # ✅ REQUIRED LINE (THIS WAS MISSING)

    segment_number = int(data.get('segment_number', 0))
    offset = int(data.get('offset', 0))

    global GLOBAL_SEGMENT
    if GLOBAL_SEGMENT is None:
        # Example segment table (base, limit)
        GLOBAL_SEGMENT = {
            0: (1000, 500),
            1: (2000, 400),
            2: (3000, 300)
        }

    if segment_number not in GLOBAL_SEGMENT:
        return jsonify({"error": "Invalid segment number"}), 400

    base, limit = GLOBAL_SEGMENT[segment_number]

    if offset > limit:
        return jsonify({"error": "Segmentation Fault"}), 400

    physical_address = base + offset

    return jsonify({
        "segment": segment_number,
        "offset": offset,
        "physical_address": physical_address
    })

@app.route('/memory_management/allocate', methods=['POST'])
@login_required
def allocate_memory():
    data = request.json

    algorithm = data['algorithm']
    process_size = int(data['process_size'])
    process_id = data['process_id']

    global GLOBAL_MEMORY_BLOCKS

    if algorithm == 'first_fit':
        addr = MemoryManager.first_fit(GLOBAL_MEMORY_BLOCKS, process_size, process_id)
    elif algorithm == 'best_fit':
        addr = MemoryManager.best_fit(GLOBAL_MEMORY_BLOCKS, process_size, process_id)
    elif algorithm == 'worst_fit':
        addr = MemoryManager.worst_fit(GLOBAL_MEMORY_BLOCKS, process_size, process_id)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    return jsonify({
        "allocated_address": addr,
        "blocks": [
            {
                "start": b.start,
                "size": b.size,
                "process_id": b.process_id,
                "is_free": b.is_free
            }
            for b in GLOBAL_MEMORY_BLOCKS
        ]
    })
@app.route('/memory_management/deallocate', methods=['POST'])
@login_required
def deallocate_memory():
    data = request.json
    process_id = data['process_id']

    global GLOBAL_MEMORY_BLOCKS
    result = MemoryManager.deallocate_memory(GLOBAL_MEMORY_BLOCKS, process_id)

    return jsonify({
        "deallocated": result,
        "blocks": [
            {
                "start": b.start,
                "size": b.size,
                "process_id": b.process_id,
                "is_free": b.is_free
            }
            for b in GLOBAL_MEMORY_BLOCKS
        ]
    })

@app.route('/synchronization')
@login_required
def synchronization(): return render_template('synchronization.html')
@app.route('/synchronization/dining_philosophers', methods=['POST'])
@login_required
def dining_philosophers():
    data = request.json

    global GLOBAL_DP
    if GLOBAL_DP is None:
        GLOBAL_DP = DiningPhilosophers(int(data.get("num_philosophers", 5)))

    pid = int(data.get("philosopher_id", 0))

    if data["operation"] == "pickup":
        result = GLOBAL_DP.pickup_chopsticks(pid)

    elif data["operation"] == "putdown":
        result = GLOBAL_DP.putdown_chopsticks(pid)

    else:
        return jsonify({"error": "Invalid operation"}), 400

    return jsonify(result)
@app.route('/file_systems')
@login_required
def file_systems(): return render_template('file_systems.html')

@app.route('/processes_threads')
@login_required
def processes_threads(): return render_template('processes_threads.html')
@app.route('/processes_threads/simulate_processes', methods=['POST'])
@login_required
def simulate_processes():
    data = request.json

    processes = [
        PTProcess(
            p.get("pid"),
            int(p.get("arrival_time", 0)),
            int(p.get("burst_time", 0))
        )
        for p in data.get("processes", [])
    ]

    result = ProcessScheduler.simulate_process_lifecycle(
        processes,
        data.get("max_time", 100)
    )

    timeline = []

    for entry in result.get("timeline", []):
        record = {}

        # entry can be tuple/list or single value
        if isinstance(entry, (list, tuple)):
            # Examples:
            # ('P1', 'RUNNING')
            # ('P1', 'READY')
            record["pid"] = str(entry[0]) if len(entry) > 0 else "N/A"
            record["state"] = str(entry[-1])
        else:
            record["pid"] = "N/A"
            record["state"] = str(entry)

        timeline.append(record)

    return jsonify({
        "timeline": timeline,
        "message": "Process lifecycle simulation completed successfully"
    })

@app.route('/processes_threads/simulate_threads', methods=['POST'])
@login_required
def simulate_threads():
    data = request.json

    threads = [
        Thread(
            t.get("tid"),
            t.get("pid"),
            ThreadModel.USER_LEVEL
        )
        for t in data.get("threads", [])
    ]

    result = ThreadManager.simulate_thread_execution(threads)

    timeline = []

    for entry in result.get("timeline", []):
        # Entry can be ANY format → handle safely

        record = {}

        if isinstance(entry, (list, tuple)):
            # Example: ('T1', 'P1', 'RUNNING')
            record["tid"] = str(entry[0]) if len(entry) > 0 else "N/A"
            record["pid"] = str(entry[1]) if len(entry) > 1 else "N/A"
            record["state"] = str(entry[-1])
        else:
            record["tid"] = "N/A"
            record["pid"] = "N/A"
            record["state"] = str(entry)

        timeline.append(record)

    return jsonify({
        "timeline": timeline,
        "message": "Thread simulation completed successfully"
    })

@app.route('/processes_threads/ipc', methods=['POST'])
@login_required
def ipc():
    data = request.json
    ipc = IPCManager()

    if data['operation'] == 'send':
        ipc.send_message(
            data['from_pid'],
            data['to_pid'],
            data['message']
        )
        return jsonify({"status": "Message Sent"})

    return jsonify({
        "message": ipc.receive_message(data['to_pid'])
    })

@app.route('/io_management')
@login_required
def io_management(): return render_template('io_management.html')
@app.route('/io_management/schedule', methods=['POST'])
@login_required
def io_schedule():
    data = request.json
    algorithm = data['algorithm'].lower()
    requests_data = data['requests']

    requests = []
    for r in requests_data:
        req_type = IORequestType.READ if r['type'].lower() == 'read' else IORequestType.WRITE

        requests.append(
            IORequest(
                r['id'],
                r['process_id'],
                req_type,
                int(r.get('block_number', 0)),
                int(r['arrival_time'])
            )
        )

    device = DeviceDriver("disk")

    if algorithm == 'fcfs':
        result = IOScheduler.fcfs(requests, device)
    elif algorithm == 'sstf':
        result = IOScheduler.sstf(requests, device)
    elif algorithm == 'scan':
        result = IOScheduler.scan(requests, device)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    result['schedule'] = [
        {
            "request": item["request"].to_dict(),
            "start_time": item["start_time"],
            "completion_time": item["completion_time"]
        }
        for item in result["schedule"]
    ]

    return jsonify(result)

@app.route('/resource_allocation')
@login_required
def resource_allocation(): return render_template('resource_allocation.html')
# ================= RESOURCE ALLOCATION =================


@app.route('/resource_allocation/allocate', methods=['POST'])
@login_required
def resource_allocate():
    data = request.json

    policy = data.get("policy")
    processes_data = data.get("processes", [])
    resources_data = data.get("resources", [])

    # ---------------- RESOURCES ----------------
    resources = []
    for r in resources_data:
        resources.append(
            Resource(
                r["rid"],
                int(r["total_instances"])
            )
        )

    # ---------------- PROCESSES ----------------
    processes = []
    for p in processes_data:
        processes.append(
            Process(
                p["pid"],
                p["max_resources"],
                p["allocated_resources"],
                int(p.get("priority", 0)),
                int(p.get("arrival_time", 0))  # ✅ IMPORTANT FIX
            )
        )

    # ---------------- RUN POLICY ----------------
    try:
        if policy == "bankers":
            result = ResourceAllocationAlgorithms.bankers_algorithm(
                processes, resources
            )

        elif policy == "fcfs":
            result = ResourceAllocationAlgorithms.fcfs_allocation(
                processes, resources, []
            )

        elif policy == "priority":
            result = ResourceAllocationAlgorithms.priority_allocation(
                processes, resources, []
            )

        elif policy == "round_robin":
            result = ResourceAllocationAlgorithms.round_robin_allocation(
                processes, resources, [], time_quantum=1
            )

        elif policy == "fair_share":
            result = ResourceAllocationAlgorithms.fair_share_allocation(
                processes, resources
            )

        else:
            return jsonify({"error": "Invalid policy"}), 400

        return jsonify({
            "status": "success",
            "result": result
        })

    except Exception as e:
        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500

# ================= FILE SYSTEM APIs =================
def safe_file_list(fs):
    files = []
    def walk(dir, path=""):
        for f in dir.files:
            files.append(path + f.name)
        for d in dir.subdirectories:
            walk(d, path + d.name + "/")
    walk(fs.root)
    return files

@app.route('/file_systems/create_file', methods=['POST'])
@login_required
def create_file():
    data = request.json
    GLOBAL_FS.allocation_method = data.get("allocation_method", "contiguous")
    success = GLOBAL_FS.create_file("/", data["name"], int(data["size"]))
    return jsonify({
        "success": success,
        "files": safe_file_list(GLOBAL_FS),
        "disk_usage": GLOBAL_FS.get_disk_usage()
    })

@app.route('/file_systems/delete_file', methods=['POST'])
@login_required
def delete_file():
    success = GLOBAL_FS.delete_file("/", request.json["name"])
    return jsonify({
        "success": success,
        "files": safe_file_list(GLOBAL_FS),
        "disk_usage": GLOBAL_FS.get_disk_usage()
    })

# ================= SYNCHRONIZATION =================
@app.route('/synchronization/semaphore', methods=['POST'])
def semaphore_op():
    d = request.json
    name = d["semaphore_name"]
    if name not in GLOBAL_SEMAPHORES:
        GLOBAL_SEMAPHORES[name] = Semaphore(int(d.get("initial_value", 1)), name)

    sem = GLOBAL_SEMAPHORES[name]
    proc = SynchronizationProcess(d.get("process_id"), d.get("process_id"))

    if d["operation"] == "wait":
        return jsonify({"success": sem.wait(proc), "value": sem.value})
    else:
        u = sem.signal()
        return jsonify({"value": sem.value, "unblocked": u.pid if u else None})

@app.route('/synchronization/mutex', methods=['POST'])
def mutex_op():
    d = request.json
    name = d["mutex_name"]
    if name not in GLOBAL_MUTEXES:
        GLOBAL_MUTEXES[name] = Mutex(name)

    mutex = GLOBAL_MUTEXES[name]
    proc = SynchronizationProcess(d.get("process_id"), d.get("process_id"))

    if d["operation"] == "lock":
        return jsonify({"success": mutex.lock(proc)})
    else:
        u = mutex.unlock()
        return jsonify({"unblocked": u.pid if u else None})

@app.route('/synchronization/producer_consumer', methods=['POST'])
def pc_op():
    global GLOBAL_PC
    d = request.json
    if GLOBAL_PC is None:
        GLOBAL_PC = ProducerConsumer(int(d.get("buffer_size", 5)))

    proc = SynchronizationProcess(d["process_id"], d["process_id"])
    if d["operation"] == "produce":
        return jsonify(GLOBAL_PC.produce(proc, d["item"]))
    else:
        return jsonify(GLOBAL_PC.consume(proc))

@app.route('/synchronization/readers_writers', methods=['POST'])
def rw_op():
    global GLOBAL_RW
    if GLOBAL_RW is None:
        GLOBAL_RW = ReadersWriters()

    d = request.json
    proc = SynchronizationProcess(d["process_id"], d["process_id"])

    if d["operation"] == "start_read":
        return jsonify(GLOBAL_RW.start_read(proc))
    elif d["operation"] == "end_read":
        return jsonify(GLOBAL_RW.end_read(proc))
    elif d["operation"] == "start_write":
        return jsonify(GLOBAL_RW.start_write(proc))
    else:
        return jsonify(GLOBAL_RW.end_write(proc))

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
