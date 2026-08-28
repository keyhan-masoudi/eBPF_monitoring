from bcc import BPF
import ctypes
import time
import subprocess
import psutil  # Get process PID

# Load eBPF program
bpf = BPF(src_file="avglate.c", cflags=["-Wno-macro-redefined"])

def print_event(cpu, data, size):
    event = bpf["events"].event(data)
    print(f"Captured I/O: PID={event.pid}, Type={'Read' if event.type == 0 else 'Write'}, Latency={event.latency} us")

bpf["events"].open_perf_buffer(print_event)

# Start fio process
fio_cmd = [
    "fio",
    "--name=test",
    "--filename=/dev/sdb",
    "--size=1G",
    "--rw=randrw",
    "--bs=4k",
    "--direct=1",
    "--numjobs=1",
    "--time_based",
    "--runtime=20",
    "--rwmixread=50",
    "--group_reporting",
    "--ioengine=libaio"
]

with open("fio_output.txt", "w") as fio_out, open("fio_error.txt", "w") as fio_err:
    fio_process = subprocess.Popen(fio_cmd, stdout=fio_out, stderr=fio_err)

time.sleep(2)

# Get fio's PID
fio_pid = None
for proc in psutil.process_iter(attrs=["pid", "name"]):
    if "fio" in proc.info["name"]:
        fio_pid = proc.info["pid"]
        break

if fio_pid is None:
    print("Failed to get fio PID!")
    fio_process.terminate()
    exit(1)

print(f"Monitoring fio (PID: {fio_pid})...")

# Store fio PID in eBPF map
bpf["target_pid"][ctypes.c_uint(fio_pid)] = ctypes.c_uint(fio_pid)

# Monitor while fio is running
try:
    while fio_process.poll() is None:
        bpf.perf_buffer_poll()
        time.sleep(1)

    print("fio completed.")

except KeyboardInterrupt:
    print("Monitoring interrupted.")
