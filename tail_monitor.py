from bcc import BPF
import time
import subprocess

# Configurable percentile for tail latency
TAIL_LATENCY_PERCENTILE = 95  # Set your desired percentile (e.g., 99)

# Load the eBPF program
bpf = BPF(src_file="tail.c", cflags=["-Wno-macro-redefined"])

print(f"Waiting for fio to start... (Monitoring {TAIL_LATENCY_PERCENTILE}th percentile tail latency)")

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

# Open files to store fio output
with open("fio_output.txt", "w") as fio_out, open("fio_error.txt", "w") as fio_err:
    fio_process = subprocess.Popen(fio_cmd, stdout=fio_out, stderr=fio_err)

print("fio started, monitoring I/O...")

try:
    while fio_process.poll() is None:
        time.sleep(1)  # Sleep to reduce CPU usage
    
    print("fio completed, calculating final metrics...")
    
    latency_hist_read = bpf["latency_hist_read"]
    latency_hist_write = bpf["latency_hist_write"]
    
    # Compute tail latency for the given percentile
    def compute_tail_latency(hist, percentile):
        values = []
        for bucket, count in hist.items():
            latency = 2 ** bucket.value  # Reverse log scale
            values.extend([latency] * count.value)
        if values:
            values.sort()
            index = int(len(values) * (percentile / 100.0)) - 1
            return values[max(index, 0)]
        return 0
    
    tail_latency_read = compute_tail_latency(latency_hist_read, TAIL_LATENCY_PERCENTILE)
    tail_latency_write = compute_tail_latency(latency_hist_write, TAIL_LATENCY_PERCENTILE)
    
    print(f"\nTail Latency (Read {TAIL_LATENCY_PERCENTILE}%): {tail_latency_read:.2f} us")
    print(f"Tail Latency (Write {TAIL_LATENCY_PERCENTILE}%): {tail_latency_write:.2f} us")
    

except KeyboardInterrupt:
    print("Monitoring interrupted, stopping.")
