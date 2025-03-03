# from bcc import BPF
# import ctypes
# import time
# import subprocess

# # Load the eBPF program
# bpf = BPF(src_file="iops.c", cflags=["-Wno-macro-redefined"])

# print("Waiting for fio to start...")

# # Define the fio command
# fio_cmd = [
#     "fio",
#     "--name=test",
#     "--filename=/dev/sdb",
#     "--size=1G",
#     "--rw=randrw",
#     "--bs=4k",
#     "--direct=1",
#     "--numjobs=1",
#     "--time_based",
#     "--runtime=10",
#     "--rwmixread=60",
#     "--group_reporting",
#     "--ioengine=libaio"
# ]

# # Open a file to store fio output
# with open("fio_iops.txt", "w") as fio_out, open("fio_error.txt", "w") as fio_err:
#     # Run fio as a subprocess and redirect output to files
#     fio_process = subprocess.Popen(fio_cmd, stdout=fio_out, stderr=fio_err)
# # Run fio as a subprocess
# fio_process = subprocess.Popen(fio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# print("fio started, monitoring I/O...")

# # Monitor I/O while fio is running
# try:
#     while fio_process.poll() is None:  # Check if fio is still running
#         time.sleep(1)  # Sleep to reduce CPU usage

#     print("fio completed, calculating final IOPS...")

#     # Read final IOPS from eBPF maps
#     io_type_count = bpf["io_type_count"]
    
#     read_ops = io_type_count[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_type_count else 0
#     write_ops = io_type_count[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_type_count else 0

#     runtime = 10  # Your fio runtime in seconds

# # Normalize eBPF counts to get IOPS comparable to fio
#     read_iops = read_ops / runtime
#     write_iops = write_ops / runtime

#     print(f"\nFinal IOPS: Reads = {read_iops:.2f}, Writes = {write_iops:.2f}")


#     # Print final IOPS
#     # print(f"\nFinal IOPS: Reads = {read_ops}, Writes = {write_ops}")

# except KeyboardInterrupt:
#     print("Monitoring interrupted, stopping.")

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
    "--filename=/dev/sdb",
    "--size=1G",
    "--rw=randrw",
    "--bs=4k",
    "--direct=1",
    "--numjobs=1",
    "--time_based",
    "--runtime=10",
    "--rwmixread=60",
    "--group_reporting",
    "--ioengine=libaio"
]

# Open files to store fio output
with open("fio_iops.txt", "w") as fio_out, open("fio_error.txt", "w") as fio_err:
    fio_process = subprocess.Popen(fio_cmd, stdout=fio_out, stderr=fio_err)

print("fio started, monitoring I/O...")

# Initialize IOPS tracking maps in BPF
io_type_count = bpf["io_type_count"]
io_type_count[ctypes.c_uint(0)] = ctypes.c_ulonglong(0)  # Read counter
io_type_count[ctypes.c_uint(1)] = ctypes.c_ulonglong(0)  # Write counter

# Monitor IOPS while fio is running
try:
    while fio_process.poll() is None:  # Check if fio is still running
        time.sleep(1)  # Sleep to reduce CPU usage

    print("fio completed, calculating final IOPS...")

    # Read total operation counts from eBPF maps

    read_ops = io_type_count[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_type_count else 0
    write_ops = io_type_count[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_type_count else 0

    runtime = 10  # Your fio runtime in seconds

# Normalize eBPF counts to get IOPS
    read_iops = read_ops / runtime
    write_iops = write_ops / runtime

    print(f"\nFinal IOPS: Reads = {read_iops:.2f}, Writes = {write_iops:.2f}")


    # Save results to a file
    with open("iops_results.txt", "w") as f:
        f.write(f"Read IOPS: {read_iops:.2f}\n")
        f.write(f"Write IOPS: {write_iops:.2f}\n")

except KeyboardInterrupt:
    print("Monitoring interrupted, stopping.")
