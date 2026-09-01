#!/usr/bin/env python3
"""
Load Testing & Benchmark Script for Todo App API
Measures latency, throughput, P95/P99 metrics, and healthcheck performance under concurrent load.
"""

import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed


def measure_request(url, timeout=5.0):
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TodoApp-LoadTest/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return response.status == 200, latency_ms, response.status
    except urllib.error.HTTPError as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return False, latency_ms, e.code
    except Exception:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return False, latency_ms, 500


def run_benchmark(target_url, total_requests=100, concurrency=10):
    print(f"==================================================")
    print(f" Running Load Test Benchmark against: {target_url}")
    print(f" Total Requests: {total_requests} | Concurrency: {concurrency}")
    print(f"==================================================")

    results = []
    success_count = 0
    failure_count = 0

    start_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(measure_request, target_url) for _ in range(total_requests)]
        for future in as_completed(futures):
            is_success, latency, status_code = future.result()
            results.append(latency)
            if is_success:
                success_count += 1
            else:
                failure_count += 1

    total_duration = time.perf_counter() - start_total
    results.sort()

    avg_latency = sum(results) / len(results) if results else 0.0
    min_latency = results[0] if results else 0.0
    max_latency = results[-1] if results else 0.0
    p95_idx = int(len(results) * 0.95)
    p99_idx = int(len(results) * 0.99)
    p95_latency = results[min(p95_idx, len(results) - 1)] if results else 0.0
    p99_latency = results[min(p99_idx, len(results) - 1)] if results else 0.0
    rps = total_requests / total_duration if total_duration > 0 else 0.0

    print(f"\n--- BENCHMARK RESULTS ---")
    print(f" Total Time Elapsed : {total_duration:.2f} s")
    print(f" Successful Requests : {success_count} ({success_count/total_requests*100:.1f}%)")
    print(f" Failed Requests     : {failure_count}")
    print(f" Throughput (RPS)    : {rps:.2f} req/sec")
    print(f"--------------------------------------------------")
    print(f" Min Latency         : {min_latency:.2f} ms")
    print(f" Average Latency     : {avg_latency:.2f} ms")
    print(f" P95 Latency         : {p95_latency:.2f} ms")
    print(f" P99 Latency         : {p99_latency:.2f} ms")
    print(f" Max Latency         : {max_latency:.2f} ms")
    print(f"==================================================")
    
    if avg_latency < 200.0:
        print(f" STATUS: PASSED (Sub-200ms average latency target met!)")
    else:
        print(f" STATUS: WARNING (Average latency exceeded 200ms target)")


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000/health/'
    reqs = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    run_benchmark(url, total_requests=reqs, concurrency=threads)
