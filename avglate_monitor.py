from bcc import BPF
import time
import subprocess
import ctypes  # <-- Add this import

# Load the eBPF program
bpf = BPF(src_file="avglate.c", cflags=["-Wno-macro-redefined"])

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
    "--rate=2048k",
    "--rwmixread=70",
    "--group_reporting",
    "--ioengine=libaio"
]

# Run fio as a subprocess
fio_process = subprocess.Popen(fio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("fio started, monitoring I/O...")

# Monitor while fio is running
try:
    while fio_process.poll() is None:
        time.sleep(1)

    print("fio completed, calculating final metrics...")

    # Read final IOPS
    io_type_count = bpf["io_count"]
    total_latency = bpf["total_latency"]

    read_ops = io_type_count[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_type_count else 0
    write_ops = io_type_count[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_type_count else 0

    read_latency = total_latency[ctypes.c_uint(0)].value if ctypes.c_uint(0) in total_latency else 0
    write_latency = total_latency[ctypes.c_uint(1)].value if ctypes.c_uint(1) in total_latency else 0

    avg_read_latency = (read_latency / read_ops) / 1000 if read_ops > 0 else 0  # Convert to us
    avg_write_latency = (write_latency / write_ops) / 1000 if write_ops > 0 else 0

    # Print results
    print(f"\nFinal IOPS: Reads = {read_ops}, Writes = {write_ops}")
    print(f"Average Latency: Reads = {avg_read_latency:.2f} us, Writes = {avg_write_latency:.2f} us")

    # Save to file
    with open("iops_latency_results.txt", "w") as f:
        f.write(f"Final IOPS: Reads = {read_ops}, Writes = {write_ops}\n")
        f.write(f"Average Latency: Reads = {avg_read_latency:.2f} us, Writes = {avg_write_latency:.2f} us\n")

except KeyboardInterrupt:
    print("Monitoring interrupted, stopping.")
