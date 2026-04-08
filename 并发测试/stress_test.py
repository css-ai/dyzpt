import argparse
import concurrent.futures
import json
import statistics
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/json;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass
class RequestResult:
    ok: bool
    status_code: int | None
    elapsed_ms: float
    error: str = ""


_lock = threading.Lock()


def parse_header_items(header_items: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in header_items:
        if ":" not in item:
            raise ValueError(f"无效请求头格式: {item}，正确格式应为 Header:Value")
        key, value = item.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"无效请求头名称: {item}")
        headers[key] = value
    return headers


def build_headers(extra_headers: dict[str, str], referer: str) -> dict[str, str]:
    headers = DEFAULT_HEADERS.copy()
    if referer:
        headers["Referer"] = referer
    headers.update(extra_headers)
    return headers


def prompt_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt}（默认 {default}）: ").strip()
    if not raw:
        return default
    return int(raw)


def prompt_text(prompt: str, default: str) -> str:
    raw = input(f"{prompt}（默认 {default}）: ").strip()
    return raw or default


def single_request(url: str, timeout: float, headers: dict[str, str]) -> RequestResult:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            _ = resp.read()
            elapsed_ms = (time.perf_counter() - start) * 1000
            return RequestResult(ok=200 <= resp.status < 400, status_code=resp.status, elapsed_ms=elapsed_ms)
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return RequestResult(ok=False, status_code=e.code, elapsed_ms=elapsed_ms, error=f"HTTPError: {e.code}")
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return RequestResult(ok=False, status_code=None, elapsed_ms=elapsed_ms, error=str(e))


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = int((len(values) - 1) * p)
    return values[index]


def summarize_results(url: str, total: int, concurrency: int, timeout: float, headers: dict[str, str], started_at: str, total_time: float, results: list[RequestResult]) -> dict:
    latencies = [r.elapsed_ms for r in results]
    success = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]

    status_counter: dict[str, int] = {}
    error_counter: dict[str, int] = {}

    for r in results:
        key = str(r.status_code) if r.status_code is not None else "NO_STATUS"
        status_counter[key] = status_counter.get(key, 0) + 1
        if r.error:
            error_counter[r.error] = error_counter.get(r.error, 0) + 1

    return {
        "url": url,
        "started_at": started_at,
        "total_requests": total,
        "concurrency": concurrency,
        "timeout_seconds": timeout,
        "total_time_seconds": round(total_time, 3),
        "requests_per_second": round(len(results) / total_time, 3) if total_time > 0 else 0,
        "success_count": len(success),
        "failed_count": len(failed),
        "success_rate": round(len(success) / total * 100, 2) if total > 0 else 0,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "min_latency_ms": round(min(latencies), 2) if latencies else 0,
        "max_latency_ms": round(max(latencies), 2) if latencies else 0,
        "p50_latency_ms": round(percentile(latencies, 0.50), 2) if latencies else 0,
        "p95_latency_ms": round(percentile(latencies, 0.95), 2) if latencies else 0,
        "p99_latency_ms": round(percentile(latencies, 0.99), 2) if latencies else 0,
        "status_distribution": status_counter,
        "error_distribution": error_counter,
        "request_headers": headers,
    }


def run_stress_test(url: str, total: int, concurrency: int, timeout: float, headers: dict[str, str]) -> dict:
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    test_start = time.perf_counter()
    results: list[RequestResult] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(single_request, url, timeout, headers) for _ in range(total)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            with _lock:
                results.append(result)

    total_time = time.perf_counter() - test_start
    return summarize_results(url, total, concurrency, timeout, headers, started_at, total_time, results)


def print_summary(summary: dict) -> None:
    print("=" * 60)
    print("并发压力测试结果")
    print("=" * 60)
    print(f"目标地址: {summary['url']}")
    print(f"开始时间: {summary['started_at']}")
    print(f"总请求数: {summary['total_requests']}")
    print(f"并发数: {summary['concurrency']}")
    print(f"总耗时: {summary['total_time_seconds']} 秒")
    print(f"QPS: {summary['requests_per_second']}")
    print(f"成功数: {summary['success_count']}")
    print(f"失败数: {summary['failed_count']}")
    print(f"成功率: {summary['success_rate']}%")
    print(f"平均延迟: {summary['avg_latency_ms']} ms")
    print(f"最小延迟: {summary['min_latency_ms']} ms")
    print(f"最大延迟: {summary['max_latency_ms']} ms")
    print(f"P50 延迟: {summary['p50_latency_ms']} ms")
    print(f"P95 延迟: {summary['p95_latency_ms']} ms")
    print(f"P99 延迟: {summary['p99_latency_ms']} ms")
    print("状态码分布:")
    for code, count in summary["status_distribution"].items():
        print(f"  {code}: {count}")
    if summary["error_distribution"]:
        print("错误分布:")
        for err, count in summary["error_distribution"].items():
            print(f"  {err}: {count}")
    print("本次请求头:")
    for key, value in summary["request_headers"].items():
        print(f"  {key}: {value}")
    print("=" * 60)


def print_stage_table(stage_summaries: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("分阶段压测汇总")
    print("=" * 80)
    print(f"{'并发':<8}{'请求数':<10}{'成功率':<10}{'QPS':<12}{'平均延迟(ms)':<18}{'P95(ms)':<12}{'失败数':<8}")
    for item in stage_summaries:
        print(
            f"{item['concurrency']:<8}{item['total_requests']:<10}{str(item['success_rate']) + '%':<10}"
            f"{item['requests_per_second']:<12}{item['avg_latency_ms']:<18}{item['p95_latency_ms']:<12}{item['failed_count']:<8}"
        )
    print("=" * 80)


def run_stages(url: str, stages: list[int], per_stage_total: int, timeout: float, headers: dict[str, str]) -> list[dict]:
    summaries: list[dict] = []
    for concurrency in stages:
        print(f"\n>>> 开始阶段测试：并发 {concurrency}，请求数 {per_stage_total}")
        summary = run_stress_test(url, per_stage_total, concurrency, timeout, headers)
        print_summary(summary)
        summaries.append(summary)
    return summaries


def maybe_prompt_args(args: argparse.Namespace) -> argparse.Namespace:
    if args.total is None:
        args.total = prompt_int("请输入测试次数，例如 200 或 500", 200)
    if args.interactive and not args.stages:
        stage_text = prompt_text("请输入分阶段并发，例如 10,20,50；如果留空则只跑单轮", "")
        args.stages = stage_text
    if args.interactive and not args.stages and args.concurrency is None:
        args.concurrency = prompt_int("请输入单轮并发数", 20)
    if args.concurrency is None:
        args.concurrency = 20
    return args


def main() -> None:
    parser = argparse.ArgumentParser(description="简单 HTTP 并发压力测试脚本（默认模拟浏览器请求）")
    parser.add_argument("--url", required=True, help="要测试的目标 URL")
    parser.add_argument("--total", type=int, default=None, help="单轮总请求数；不传时可手动输入，例如 200 或 500")
    parser.add_argument("--concurrency", type=int, default=None, help="单轮并发数，默认 20")
    parser.add_argument("--timeout", type=float, default=10, help="单请求超时时间（秒），默认 10")
    parser.add_argument("--output", default="", help="可选：结果输出到 json 文件")
    parser.add_argument("--referer", default="http://www.dyzpt.xyz:5666/", help="可选：模拟来源页面 Referer")
    parser.add_argument("--stages", default="", help="可选：分阶段测试并发列表，例如 10,20,50")
    parser.add_argument("--interactive", action="store_true", help="开启交互式输入，可手动输入测试次数和并发阶段")
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="可重复传入自定义请求头，格式为 Header:Value，例如 --header \"Cookie:foo=bar\"",
    )
    args = parser.parse_args()
    args = maybe_prompt_args(args)

    extra_headers = parse_header_items(args.header)
    headers = build_headers(extra_headers, args.referer)

    if args.stages:
        stages = [int(item.strip()) for item in args.stages.split(",") if item.strip()]
        summaries = run_stages(args.url, stages, args.total, args.timeout, headers)
        print_stage_table(summaries)
        result: dict | list[dict] = summaries
    else:
        summary = run_stress_test(args.url, args.total, args.concurrency, args.timeout, headers)
        print_summary(summary)
        result = summary

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已写入: {args.output}")


if __name__ == "__main__":
    main()
