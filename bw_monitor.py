from bcc import BPF
import time
import subprocess
import ctypes

# Load the eBPF program
bpf = BPF(src_file="bw.c", cflags=["-Wno-macro-redefined"])

print("Waiting for fio to start...")

# Define the fio command
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
    "--runtime=10",
    "--rwmixread=70",
    "--group_reporting",
    "--ioengine=libaio"
]

# Open file to store fio output
with open("fio_output.txt", "w") as fio_out, open("fio_error.txt", "w") as fio_err:
    # Run fio as a subprocess and save output
    fio_process = subprocess.Popen(fio_cmd, stdout=fio_out, stderr=fio_err)

print("fio started, monitoring I/O...")

# Get fio's PID and pass it to eBPF
fio_pid = fio_process.pid
bpf["target_pid"] = ctypes.c_uint(fio_pid)

# Initialize BPF maps
io_bytes = bpf["io_bytes"]
io_bytes[ctypes.c_uint(0)] = ctypes.c_ulonglong(0)  # Read counter
io_bytes[ctypes.c_uint(1)] = ctypes.c_ulonglong(0)  # Write counter

# Monitor I/O while fio is running
try:
    while fio_process.poll() is None:  # Check if fio is still running
        time.sleep(1)  # Sleep to reduce CPU usage

    print("fio completed, calculating Read/Write bandwidth ratio...")

    # Read total bytes from eBPF maps
    read_bytes = io_bytes[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_bytes else 0
    write_bytes = io_bytes[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_bytes else 0

    # Debug output
    print(f"Raw Bytes Counted: Reads = {read_bytes} B, Writes = {write_bytes} B")

    read_bw = read_bytes / 10 / (1024 * 1024)  # Convert to MB/s
    write_bw = write_bytes / 10 / (1024 * 1024)  # Convert to MB/s

    # Calculate Read/Write Bandwidth ratio
    rw_bw_ratio = read_bw / write_bw if write_bw else float("inf")  # Avoid division by zero

    # Print final results
    print(f"\nFinal Bandwidth: Reads = {read_bw:.2f} MB/s, Writes = {write_bw:.2f} MB/s")
    print(f"Read/Write Bandwidth Ratio: {rw_bw_ratio:.2f}")

except KeyboardInterrupt:
    print("Monitoring interrupted, stopping.")
