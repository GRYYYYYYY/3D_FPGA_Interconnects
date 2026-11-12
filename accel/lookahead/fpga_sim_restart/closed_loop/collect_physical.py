"""Collect actual SLR occupancy; a nominal shell allowance is not a fit proof."""
import hashlib
import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[4]
c = root / "results/fpga_sim_restart_20261111T231000Z/closed_loop"
ooc = c / "ooc_64_fixed"
report = ooc / "slr_utilization.rpt"
rows = {}
links = []
total_sll = None
for line in report.read_text().splitlines():
    f = [x.strip() for x in line.split("|")][1:-1]
    if len(f) == 7 and all(x.isdigit() for x in f[1:4]):
        rows[f[0]] = {"used": list(map(int, f[1:4])),
                      "percent": list(map(float, f[4:7]))}
    if len(f) == 5 and "<->" in f[0]:
        links.append({"boundary": f[0], "used": int(f[1]),
                      "available": int(f[3]), "percent": float(f[4])})
    if f and f[0] == "Total SLLs Used":
        total_sll = int(f[1])
assert len(links) == 2 and total_sll == sum(x["used"] for x in links)
required = ["CLB", "CLBL", "CLBM", "CLB LUTs", "LUT as Logic", "LUT as Memory",
            "CLB Registers", "Block RAM Tile", "URAM", "DSPs"]
assert all(k in rows for k in required)
slrs = [{"slr": i, **{k: {"used": rows[k]["used"][i],
                           "percent": rows[k]["percent"][i]} for k in required}}
        for i in range(3)]
totals = {k: sum(rows[k]["used"]) for k in required}
assert totals["CLB LUTs"] == totals["LUT as Logic"] + totals["LUT as Memory"]
receipt = json.load(open(ooc / "execution_receipt.json"))
assert receipt["returncode"] == 0 and receipt["route_complete"]
binding = json.load(open(ooc / "inspection_binding.json"))
audit = {
    "part": "xcu280-fsvh2892-2L-e", "scope": "final routed standalone module",
    "aggregate_used": totals, "slrs": slrs, "sll_boundaries": links,
    "total_sll_used": total_sll, "nominal_shell_reserve_fraction": 0.20,
    "reserve_provenance": "assumed allowance, not verified shell quota",
    "uniform_20pct_free_CLB_sites_each_SLR": all(x["CLB"]["percent"] <= 80 for x in slrs),
    "uniform_20pct_free_CLBM_sites_each_SLR": all(x["CLBM"]["percent"] <= 80 for x in slrs),
    "actual_shell_fit_verified": False,
    "reserve_interpretation": "Occupied CLB sites and used LUT counts differ. SLR0/1 lack 20% entirely free CLB/CLBM sites; these observations do not establish actual shell fit or impossibility of sharing partially occupied sites.",
    "route_complete": True, "routable_nets": receipt["routable_nets"],
    "routing_errors": receipt["routing_errors"],
    "unconstrained_internal_endpoints": receipt["check_timing_counts"]["unconstrained_internal_endpoints"],
    "drc_rules": receipt["drc_rules"],
    "checkpoint_sha256": binding["input_checkpoint_sha256"],
    "source_reports_sha256": {str(p.relative_to(c)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [report, ooc / "clock_source_audit.txt", ooc / "routed_utilization.rpt"]},
}
(c / "physical_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps({"aggregate_used": totals, "SLR_CLB_percent": rows["CLB"]["percent"],
                  "SLR_CLBM_percent": rows["CLBM"]["percent"], "SLL_used": total_sll}, indent=2))
