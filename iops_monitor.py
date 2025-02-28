from bcc import BPF
import ctypes
import time
import subprocess

# Load the eBPF program
bpf = BPF(src_file="iops.c", cflags=["-Wno-macro-redefined"])

print("Waiting for fio to start...")

# Define the fio command
fio_cmd = [
    "fio",
    "--name=test",
    "--filename=/dev/sda",
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

# Run fio as a subprocess
fio_process = subprocess.Popen(fio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("fio started, monitoring I/O...")

# Monitor I/O while fio is running
try:
    while fio_process.poll() is None:  # Check if fio is still running
        time.sleep(1)  # Sleep to reduce CPU usage

    print("fio completed, calculating final IOPS...")

    # Read final IOPS from eBPF maps
    io_type_count = bpf["io_type_count"]
    
    read_ops = io_type_count[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_type_count else 0
    write_ops = io_type_count[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_type_count else 0

    # Print final IOPS
    print(f"\nFinal IOPS: Reads = {read_ops}, Writes = {write_ops}")

except KeyboardInterrupt:
    print("Monitoring interrupted, stopping.")

