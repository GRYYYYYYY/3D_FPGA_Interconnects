#!/usr/bin/env python3
"""Recompute work-based NECESSARY bounds; not an FPGA performance simulator.

The counterfactual rows are conditional on explicit unimplemented service caps.
They omit memory, initialization, conflict, and drain costs and cannot prove a
speedup. This script reads the frozen R1 evidence; it never runs VPR or hardware.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

BASE_SHA = "5651a34abb97939bee6402c5af585753ab07f64b"
CASES = {
    "bnn_export": {
        "gpu_resident_mean_s": 0.30468024222222223,
        "old_bound_cycles": 78748700,
        "candidates": 1286937147,
        "nodes": 4102608,
        "cells": 25088,
    },
    "lstm_s2": {
        "gpu_resident_mean_s": 0.30605324977777776,
        "old_bound_cycles": 80129990,
        "candidates": 1309512712,
        "nodes": 4166724,
        "cells": 25538,
    },
}


def ceil_div(n, d):
    return (n + d - 1) // d


def review_case(root, name, expected):
    source = root / "results/fpga_sparse_stream_20261112/evidence_snapshot" / name / "waves.csv.gz"
    with gzip.open(source, "rt", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"sample", "bucket", "active", "candidates", "changed", "changed_lines", "closed"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Missing wave columns: {source}")

    specs = [
        ("r1_published", 64, 2, 3, False, False),
        ("owner_ii1_only_original_scope", 64, 1, 3, False, False),
        ("owner_ii1_closure_ii3_parent8_commit16", 64, 1, 3, True, True),
        ("owner_ii1_closure_ii1_parent8_commit16", 64, 1, 1, True, True),
        ("pop_reduce_owner32_ii1_parent8_commit16", 32, 1, 0, True, True),
        ("pop_reduce_owner64_ii1_parent8_commit16", 64, 1, 0, True, True),
    ]
    variants = {}
    for label, owners, owner_ii, closure_ii, parent_cap, commit_cap in specs:
        expansion = closure = commit = 0
        for index, row in enumerate(rows):
            bucket_ends = index + 1 == len(rows) or (
                row["sample"], row["bucket"]
            ) != (rows[index + 1]["sample"], rows[index + 1]["bucket"])
            e = ceil_div(owner_ii * int(row["candidates"]), owners)
            if parent_cap:
                e = max(e, ceil_div(int(row["active"]), 8))
            expansion += e
            if bucket_ends and closure_ii:
                closure += ceil_div(closure_ii * int(row["closed"]), 8)
            if commit_cap:
                commit += ceil_div(int(row["changed"]), 16)
        total = expansion + closure + commit
        variants[label] = {
            "evidence_type": "conditional_optimistic_necessary_bound_not_prediction",
            "owner_count": owners,
            "assumed_owner_ii": owner_ii,
            "parent_cap_per_cycle": 8 if parent_cap else None,
            "commit_cap_nodes_per_cycle": 16 if commit_cap else None,
            "closure_engines": 8 if closure_ii else 0,
            "assumed_closure_ii": closure_ii if closure_ii else None,
            "pop_reducer_assumption": "overlapped_and_not_limiting; unimplemented" if closure_ii == 0 else None,
            "expansion_cycles": expansion,
            "closure_cycles": closure,
            "commit_cycles": commit,
            "total_cycles": total,
            "seconds_at_hypothetical_200MHz": total / 200e6,
            "seconds_at_hypothetical_125MHz": total / 125e6,
            "achieved_clock_mhz": None,
            "board_measured": False,
        }
    sums = {k: sum(int(r[k]) for r in rows) for k in ("candidates", "active", "touched", "changed", "changed_lines")}
    sums["closed_bucket_final_only"] = sum(
        int(r["closed"]) for i, r in enumerate(rows)
        if i + 1 == len(rows) or (r["sample"], r["bucket"]) != (rows[i + 1]["sample"], rows[i + 1]["bucket"])
    )
    if sums["candidates"] != expected["candidates"]:
        raise ValueError(f"Candidate count differs from frozen review: {name}")
    if variants["r1_published"]["total_cycles"] != expected["old_bound_cycles"]:
        raise ValueError(f"Old bound differs from frozen review: {name}")
    gpu = expected["gpu_resident_mean_s"]
    return {
        "case": name,
        "source": str(source.relative_to(root)),
        "compressed_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "waves": len(rows),
        "jobs": len({r["sample"] for r in rows}),
        "gpu_resident_mean_s": gpu,
        "sums": sums,
        "one_qid_cell_pair_bytes": expected["cells"] * 8,
        "one_qid_seen_bytes_ceil": ceil_div(expected["cells"], 8),
        "batch40_output_bytes": expected["cells"] * 8 * 40,
        "label64_plus_pending32_bytes": expected["nodes"] * 12,
        "edge_only_required_mean_candidates_per_cycle_at_200MHz": sums["candidates"] / (gpu * 200e6),
        "edge_only_16_ii1_seconds_at_200MHz": sums["candidates"] / (16 * 200e6),
        "variants": variants,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    report = {
        "source_sha": BASE_SHA,
        "scope": "Arithmetic audit of frozen per-wave work; not runtime, RTL, or architectural simulation",
        "exclusions": [
            "initialization and sample switching",
            "proposal and node-state memory service",
            "logical-to-physical channel sharing",
            "bank and same-address conflicts",
            "directory/member/free-list implementation costs",
            "target metadata lookup and cell reducer stalls",
            "pipeline and FIFO fill/drain, write ACKs",
            "achievable clock and resources",
        ],
        "cases": [review_case(root, name, data) for name, data in CASES.items()],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for case in report["cases"]:
        print(case["case"], "waves=", case["waves"], "old_cycles=", case["variants"]["r1_published"]["total_cycles"], "verified")
    print("All new rows are conditional necessary bounds, NOT FPGA predictions.")


if __name__ == "__main__":
    main()
