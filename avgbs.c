#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>

BPF_HASH(io_bytes, u32, u64);   // Track total bytes read/write
BPF_HASH(io_count, u32, u64);   // Track total read/write operations

// Tracepoint for block I/O completion
TRACEPOINT_PROBE(block, block_rq_complete) {
    u32 type = (args->rwbs[0] == 'R') ? 0 : 1;  // 'R' for read, 'W' for write

    u64 bytes = args->nr_sector * 512;  // Convert sectors to bytes
    io_bytes.increment(type, bytes);    // Track total bytes
    io_count.increment(type);           // Track total operations

    return 0;
}
