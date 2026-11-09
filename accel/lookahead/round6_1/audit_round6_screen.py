#!/usr/bin/env python3
"""Recompute the frozen R6 screen; never predict achieved FPGA performance.

Only reads git objects from BASE. It does not run a solver, build, GPU job,
HLS/RTL process, or change the repository. The caller selects the JSON output.
"""
import argparse
import hashlib
import json
import math
import pathlib
import subprocess

BASE = "480ba6d5cc2b9d73696a44315777c0e658d8a7b4"
ROOT = "results/lookahead_accel_round6_20261109T150000Z/evidence_snapshot"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()
    source_hashes = {}

    def frozen_json(name):
        path = ROOT + "/" + name
        raw = git(args.repo, "show", BASE + ":" + path)
        source_hashes[path] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    profile = frozen_json("profile_summary.json")
    report = frozen_json("report_final.json")
    p = next(x for x in profile if x["case"] == "bnn_export" and x["shift"] == 20)
    m = next(x for x in report["hardware"] if x["case"] == "bnn_export" and x["shift"] == 20)
    e, raw, directory = p["eligible_edges"], p["raw_edges"], p["directory_insert_lookups"]
    gpu, cpu = m["gpu_s"], m["cpu_s"]
    reference_hz = 200_000_000
    target = 0.8 * gpu
    traffic = p["conditional_screen"]["accounted_traffic_bytes"]
    parts = {
        "edge_8B": 8 * raw,
        "node_16B": 16 * e,
        "counted_label_reads_and_writes": 8 * (p["cpu_algorithmic_label_reads"] + p["updates"]),
        "reset": p["reset_bytes"],
        "output": 8 * p["J"] * p["C"],
    }
    assert sum(parts.values()) == traffic
    assert math.isclose(e / (16 * reference_hz), m["ideal_edge_only_s"], rel_tol=1e-12)
    assert m["ideal_edge_only_s"] > gpu
    barrier = 64 * p["wave_count"] / reference_hz
    reconstructed = max(
        p["bank16_service_sum_of_maxima"] / reference_hz,
        directory / reference_hz,
        traffic / 100e9,
    ) + barrier
    assert math.isclose(reconstructed, m["optimistic_conditional_s"], rel_tol=1e-12)
    compact = traffic - 4 * raw - 14 * e
    assert compact > 0
    candidates = []
    for hz in (125_000_000, 200_000_000):
        for lanes in (16, 32, 64):
            ideal = e / (lanes * hz)
            candidates.append({
                "lanes": lanes, "assumed_hz": hz, "implemented_hz": None,
                "ideal_edge_only_s": ideal,
                "required_effective_edge_utilization_to_match_GPU_before_other_costs": ideal / gpu,
                "required_effective_edge_utilization_for_20pct_time_reserve_before_other_costs": ideal / target,
                "original_single_directory_service_s": directory / hz,
                "original_counted_traffic_at_assumed_100GBps_s": traffic / 100e9,
                "compact_counterfactual_counted_traffic_at_assumed_100GBps_s": compact / 100e9,
                "warning": "Each term is separate; no full hardware makespan or speedup is implied.",
            })
    result = {
        "kind": "frozen_R6_arithmetic_audit_not_a_hardware_prediction",
        "base_commit": BASE,
        "checkout_head": git(args.repo, "rev-parse", "HEAD").decode().strip(),
        "sources_sha256": source_hashes,
        "measured_software_scope": "same-worker warm full native-export batch E1, ALT shift20; not native E2",
        "measured_cpu_s": cpu, "measured_cuda_s": gpu,
        "cuda_speedup_over_best_measured_ALT_cpu": cpu / gpu,
        "old_optimized_CPU_same_worker_in_R6": False,
        "native_shift20_qualified_in_R6": False,
        "native_CUDA_backend_qualified_in_R6": False,
        "work": {k: p[k] for k in ["N", "E", "J", "C", "raw_edges", "eligible_edges", "wave_count", "max_qid_waves", "directory_insert_lookups", "same_dst_duplicate_candidates", "active_bucket_peak", "pending_member_peak"]},
        "duplicate_fraction_across_entire_waves_not_finite_cache_hit_rate": p["same_dst_duplicate_candidates"] / e,
        "original_model": {
            "assumed_hz": reference_hz,
            "edge_only_16lane_s": e / (16 * reference_hz),
            "single_directory_service_s": directory / reference_hz,
            "counted_traffic_parts_bytes": parts,
            "counted_traffic_bytes": traffic,
            "counted_traffic_at_assumed_100GBps_s": traffic / 100e9,
            "bank16_service_s": p["bank16_service_sum_of_maxima"] / reference_hz,
            "serial_64cycle_per_wave_barrier_assumption_s": barrier,
            "reconstructed_conditional_total_s": reconstructed,
            "barrier_note": "R6 accounting assumption only; cross-qid overlap is not established.",
        },
        "necessary_rates_before_nonoverlap_costs": {
            "match_GPU_eligible_edges_per_s": e / gpu,
            "20pct_time_reserve_target_s": target,
            "20pct_time_reserve_eligible_edges_per_s": e / target,
            "match_GPU_original_directory_ops_per_200MHz_cycle": directory / (gpu * reference_hz),
            "20pct_reserve_original_directory_ops_per_200MHz_cycle": directory / (target * reference_hz),
            "match_GPU_original_counted_traffic_GBps": traffic / gpu / 1e9,
            "20pct_reserve_original_counted_traffic_GBps": traffic / target / 1e9,
            "20pct_reserve_max_bytes_at_assumed_100GBps": target * 100e9,
        },
        "compact_counterfactual": {
            "change": "8B edge -> 4B dst and 16B node -> 2B metadata, inside the OLD counting formula only",
            "counted_bytes": compact,
            "counted_seconds_at_assumed_100GBps": compact / 100e9,
            "packing_admission_verified_by_this_script": False,
            "physical_traffic_measured": False,
            "includes_new_directory_design": False,
            "includes_burst_amplification_and_all_proposal_RMW": False,
            "prediction_or_measured_speedup": False,
        },
        "edge_lane_sensitivity": candidates,
        "hardware_status": {"new_implemented_frequency_hz": None, "board_measured": False, "fpga_superiority_verified": False},
        "interpretation": [
            "The screened candidate fails three separate service budgets.",
            "Changing lane count alone leaves directory and counted-traffic constraints.",
            "A count-derived byte model is not an immutable physical lower bound.",
            "Packing, bucket metadata batching and finite proposal combining need functional and transaction evidence.",
            "Apply common representation optimizations to CPU/CUDA and re-freeze the comparison target.",
            "The 20 percent time reserve is an engineering screen, not a confidence interval or FPGA proof.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.out), "audit_passed": True, "cuda_s": gpu,
        "edge_only_s": e / (16 * reference_hz), "directory_s": directory / reference_hz,
        "counted_memory_s": traffic / 100e9, "new_hardware_performance_claim": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
