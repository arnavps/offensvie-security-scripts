# NOTES

## Architecture Decisions

*   **Concurrency:** Opted for `asyncio` over threading/multiprocessing. Network I/O is the bottleneck in brute-forcing, and `asyncio` handles thousands of concurrent connections with minimal memory overhead compared to threads.
*   **HTTP Client:** Chosen `httpx` for modern HTTP/1.1 and HTTP/2 support, out-of-the-box async connection pooling, and a familiar API comparable to `requests`.
*   **File Handling:** Large wordlists (e.g., SecLists) can be gigabytes in size. To prevent OOM errors, the file is read iteratively in a producer-consumer model where a dedicated async task yields lines into a bounded `asyncio.Queue`.
*   **False Positive Reduction:** Implemented baseline signature comparison for "Soft 404s". A random non-existent path is requested initially to compute a baseline length/signature. Subsequent 200 OK responses matching this signature are discarded.

## Future Improvements

*   Implement recursive directory scanning.
*   Add proxy support and rotating User-Agents for evasion.
*   Integrate ML-based classification of response body to detect generic error pages returning 200 OK.
