#!/usr/bin/env python3
"""Recompute planning bounds from the fixed R2 review data. No experiments are run.

All frequencies and memory-service rates here are conditional planning inputs.
This script does not qualify an FPGA clock or report board-measured performance.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def calculate(metrics, wave_bounds, frequency_mhz):
    if frequency_mhz <= 0:
        raise ValueError("frequency_mhz must be positive")
    frequency_hz = frequency_mhz * 1e6
    targets = {x["case"]: x for x in metrics["prepared_gpu_targets_and_bounds"]}
    waves = {x["case"]: x for x in wave_bounds["cases"]}
    rows = []
    for observed in metrics["p32_F1_latency60_gap2"]:
        name = observed["case"]
        t = targets[name]
        w = waves[name]
        service = observed["service_metrics"]["totals"]
        arrays = observed["array_32B_transactions"]
        byte_arrays = {k: v * 32 for k, v in arrays.items()}
        total_bytes = sum(byte_arrays.values())
        if total_bytes != observed["internal_traffic_bytes"]:
            raise ValueError(f"Array traffic mismatch: {name}")
        if arrays["proposal_read"] != service["owner_misses"] + observed["commit"]["total"]:
            raise ValueError(f"Proposal-read identity mismatch: {name}")
        if sum(service[k] for k in ("owner_hits", "owner_misses", "owner_merges")) != t["edges"]:
            raise ValueError(f"Owner partition mismatch: {name}")
        gpu_s = t["gpu_seconds"]
        budgets = []
        for ports, gap in [(32, 1), (32, 2), (8, 1)]:
            budget_bytes = gpu_s * ports * 32 * frequency_hz / gap
            budgets.append({
                "ports": ports,
                "gap_cycles": gap,
                "nominal_bytes_budget": budget_bytes,
                "minimum_fraction_cut_from_observed_P32_l60_g2_traffic": max(0, 1-budget_bytes/total_bytes),
                "includes_latency_imbalance_dependencies_and_control": False,
            })
        mark = service["state_accepted"] - (w["summary"]["active"] + service["stale"]) - 2 * observed["commit"]["total"] - 40
        command_offload = mark + observed["commit"]["total"]
        proposal_state = sum(byte_arrays[k] for k in ("proposal_read", "proposal_write", "state_read", "state_write"))
        rows.append({
            "case": name,
            "gpu_target_seconds": gpu_s,
            "gpu_variant": t["gpu_variant"],
            "candidate_count": t["edges"],
            "planning_gpu_cycle_budget": gpu_s * frequency_hz,
            "edge_only_min_cycles_32II1": math.ceil(t["edges"] / 32),
            "edge_only_required_frequency_MHz_32II1": t["edges"] / (32*gpu_s*1e6),
            "minimum_ideal_lanes_for_edge_only_strict_win": math.floor(t["edges"] / (gpu_s*frequency_hz)) + 1,
            "observed_P32_l60_g2_cycles": observed["cycles"],
            "observed_internal_bytes": total_bytes,
            "proposal_state_traffic_fraction": proposal_state/total_bytes,
            "expansion_owner_miss_read_bytes": service["owner_misses"]*32,
            "owner_hit_fraction": service["owner_hits"]/t["edges"],
            "owner_merge_fraction": service["owner_merges"]/t["edges"],
            "owner_miss_fraction": service["owner_misses"]/t["edges"],
            "state_hit_fraction": service["state_hits"]/service["state_accepted"],
            "derived_MARK_plus_CLEAR_logical_commands": command_offload,
            "derived_MARK_plus_CLEAR_command_fraction": command_offload/service["state_accepted"],
            "complete_node_to_changed_line_commit_read_saving_upper_bytes": 32*(observed["commit"]["total"]-w["total_changed_lines"]),
            "traffic_budgets": budgets,
            "touched4_peak_count_bounds_not_measured_exact": [w["peak_touched_line_lb"],w["peak_touched_line_ub"]],
            "all_resident_capacity_32owners_x4096_ruled_out_by_aggregate_lower_bound": 32*4096 < w["peak_touched_line_lb"],
        })
    port_rows = []
    for x in metrics["p8_F1_completed"]:
        transactions = [c["reads"]+c["writes"] for c in x["channels"]]
        port_rows.append({
            "case": x["case"], "config": x["config"],
            "model_resident_cycles": x["resident_cycles"],
            "total_internal_bytes": sum(transactions)*32,
            "per_port_request_counts": transactions,
            "busiest_port_service_only_min_cycles": max((n-1)*x["service_gap_cycles"]+1 if n else 0 for n in transactions),
            "clock_qualified": False,
        })
    return {
        "review_commit": metrics["commit"],
        "scope": "Derived necessary planning bounds; no new RTL, OOC, board, software or cycle-model experiments.",
        "planning_frequency_mhz": frequency_mhz,
        "qualified_frequency_mhz": None,
        "board_measured": False,
        "cautions": [
            "A necessary bound passing does not establish achievable performance.",
            "Traffic budgets hold gap_cycles fixed; varying frequency here changes the assumed service rate. A fixed-nanosecond memory contract must be converted separately.",
            "P32_l60_g2 traffic is a measured model outcome for that model, not a proof that a changed architecture or different memory contract has identical traffic.",
            "MARK/CLEAR command savings are not proportional off-chip byte savings.",
            "The exact number of all touched lines is unknown; interval endpoints are not measurements of that count.",
            "New algorithmic transformations may improve software too; refresh targets when a software-applicable transformation changes work.",
        ],
        "cases": rows,
        "p8_F1_per_port_bounds": port_rows,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metrics", type=Path, default=ROOT/"sparse_r2_review_metrics.json")
    ap.add_argument("--wave-bounds", type=Path, default=ROOT/"sparse_r2_wave_accumulator_bounds.json")
    ap.add_argument("--frequency-mhz", type=float, default=200.0)
    ap.add_argument("--output", type=Path)
    args=ap.parse_args()
    result=calculate(read_json(args.metrics),read_json(args.wave_bounds),args.frequency_mhz)
    payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(payload,encoding="utf-8")
        print(args.output.resolve())
    else:
        print(payload,end="")


if __name__ == "__main__":
    main()
