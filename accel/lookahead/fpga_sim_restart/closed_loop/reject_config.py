"""Exercise invalid runtime configurations against the final, unchanged RTL binary."""
import hashlib
import json
import pathlib
import shutil
import subprocess

root = pathlib.Path(__file__).resolve().parents[4]
c = root / "results/fpga_sim_restart_20261111T231000Z/closed_loop"
binary = c / "verilator_64_final/Vgraph_top"
source = c / "native_d3_w8"
out = c / "runtime_config_rejections"
out.mkdir(exist_ok=True)
original = [int(x) for x in (source / "config.txt").read_text().split()]
cases = {"zero_nodes": (0, 0), "nodes_above_limit": (0, 67108865),
         "zero_jobs": (1, 0), "zero_cells": (2, 0),
         "unaligned_proposal_base": (11, original[11] + 1)}
rows = []
for name, (index, value) in cases.items():
    p = out / name
    p.mkdir(exist_ok=False)
    for f in ["memory.hex", "expected.hex"]:
        shutil.copy2(source / f, p / f)
    cfg = original.copy()
    cfg[index] = value
    (p / "config.txt").write_text(" ".join(map(str, cfg)) + "\n")
    result = subprocess.run([str(binary), str(p), "64", "60"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (p / "simulate.log").write_text(result.stdout)
    assert result.returncode == 1 and "FAIL DUT error state=0" in result.stdout, (name, result.stdout)
    assert not (p / "actual.hex").exists() and not (p / "summary.json").exists()
    rows.append({"case": name, "returncode": result.returncode,
                 "DUT_error_observed": True, "complete_output_published": False})
report = {"status": "PASS", "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
          "scope": "external configuration admission; does not test dynamic member-pool overflow",
          "cases": rows}
(out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
