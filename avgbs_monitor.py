from bcc import BPF
import time
import subprocess
import ctypes

# Load the eBPF program
bpf = BPF(src_file="avgbs.c", cflags=["-Wno-macro-redefined"])

print("Waiting for fio to start...")

# Define the fio command
fio_cmd = [
    "fio",
    "--name=test",
    "--filename=/dev/sdb",
    "--size=1G",
    "--rw=randrw",
    "--bs=4k,2k",
    "--direct=1",
    "--numjobs=1",
    "--time_based",
    "--runtime=10",
    "--rwmixread=70",
    "--group_reporting",
    "--ioengine=libaio"
]
# Open a file to store fio output
with open("fio_output.txt", "w") as fio_out, open("fio_error.txt", "w") as fio_err:
    # Run fio as a subprocess and redirect output to files
    fio_process = subprocess.Popen(fio_cmd, stdout=fio_out, stderr=fio_err)


print("fio started, monitoring I/O...")

# Monitor I/O while fio is running
try:
    while fio_process.poll() is None:  # Check if fio is still running
        time.sleep(1)  # Sleep to reduce CPU usage

    print("fio completed, calculating average block size...")

    # Read data from eBPF maps
    io_bytes = bpf["io_bytes"]
    io_count = bpf["io_count"]

    read_bytes = io_bytes[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_bytes else 0
    write_bytes = io_bytes[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_bytes else 0

    read_ops = io_count[ctypes.c_uint(0)].value if ctypes.c_uint(0) in io_count else 0
    write_ops = io_count[ctypes.c_uint(1)].value if ctypes.c_uint(1) in io_count else 0

    # Calculate average block size (bytes per operation)
    avg_block_size_read = read_bytes / read_ops if read_ops else 0
    avg_block_size_write = write_bytes / write_ops if write_ops else 0

    # Print final results
    print(f"\nFinal Average Block Size: Reads = {avg_block_size_read:.2f} bytes, Writes = {avg_block_size_write:.2f} bytes")

    # # Save results to file
    # with open("avg_block_size_results.txt", "w") as f:
    #     f.write(f"Average Block Size (Read): {avg_block_size_read:.2f} bytes\n")
    #     f.write(f"Average Block Size (Write): {avg_block_size_write:.2f} bytes\n")

    print(f"Average Block Size results saved to avg_block_size_results.txt")

except KeyboardInterrupt:
    print("Monitoring interrupted, stopping.")
