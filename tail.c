#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

BPF_HASH(io_type_count, u32);  // Count read/write operations
BPF_HASH(io_bytes, u32);       // Track total bytes read/write
BPF_HISTOGRAM(latency_hist_read);  // Latency histogram for reads
BPF_HISTOGRAM(latency_hist_write); // Latency histogram for writes
BPF_HASH(start_time, u64, u64);  // Store issue timestamps

// Trace block request issue
TRACEPOINT_PROBE(block, block_rq_issue) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 ts = bpf_ktime_get_ns();
    start_time.update(&pid_tgid, &ts);
    return 0;
}

// Trace block request completion
TRACEPOINT_PROBE(block, block_rq_complete) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u64 *tsp = start_time.lookup(&pid_tgid);

    if (tsp) {
        u64 delta = bpf_ktime_get_ns() - *tsp;
        u32 type = (args->rwbs[0] == 'R') ? 0 : 1;  // 'R' for read, else write

        // Update latency histogram
        if (type == 0)
            latency_hist_read.increment(bpf_log2l(delta / 1000)); // Convert to us
        else
            latency_hist_write.increment(bpf_log2l(delta / 1000));

        start_time.delete(&pid_tgid);
    }

    // Count operations
    u32 type = (args->rwbs[0] == 'R') ? 0 : 1; // Detect read/write correctly
    io_type_count.increment(type);

    // Track bytes read/written
    u64 bytes = args->nr_sector * 512;  // Convert sectors to bytes
    io_bytes.increment(type, bytes);
    
    return 0;
}
