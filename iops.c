#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

BPF_HASH(io_type_count, u32);  // Track I/O type counts (read/write)

// Tracepoint for block I/O completion
TRACEPOINT_PROBE(block, block_rq_complete) {
    u32 type = args->rwbs[0] == 'R' ? 0 : 1; // 'R' for read, 'W' for write
    io_type_count.increment(type); // Count read/write operations
    return 0;
}