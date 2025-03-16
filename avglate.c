#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

struct io_latency_event {  // Rename struct to avoid conflict
    u32 pid;
    u32 type;
    u64 latency;
};

BPF_PERF_OUTPUT(events);
BPF_HASH(start_time, u64, u64);
BPF_HASH(target_pid, u32, u32);

TRACEPOINT_PROBE(block, block_rq_issue) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u32 *monitored_pid = target_pid.lookup(&pid);
    if (!monitored_pid) return 0;

    u64 ts = bpf_ktime_get_ns();
    u64 key = args->sector;
    start_time.update(&key, &ts);
    return 0;
}

TRACEPOINT_PROBE(block, block_rq_complete) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u32 *monitored_pid = target_pid.lookup(&pid);
    if (!monitored_pid) return 0;

    u64 key = args->sector;
    u64 *tsp = start_time.lookup(&key);
    if (!tsp) return 0;

    u64 delta = bpf_ktime_get_ns() - *tsp;
    u64 delta_us = delta / 1000;

    struct io_latency_event event = {};  // Use renamed struct
    event.pid = pid;
    event.type = (args->rwbs[0] == 'R') ? 0 : 1;
    event.latency = delta_us;

    events.perf_submit(args, &event, sizeof(event));
    start_time.delete(&key);
    return 0;
}
