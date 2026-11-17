#!/usr/bin/env python3
"""Build/check this independent manuscript; never execute solver or EDA jobs."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW = ROOT / "results/fpga_cpu_primary_20261115"
MUTABLE = [
    "tables/implementation.tex", "sections/performance_qualification.tex",
    "sections/abstract_hardware.tex", "sections/conclusion_hardware.tex",
]
DEADLINE = "2026-11-18T01:00:00+00:00"

def digest(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def run(args, cwd=HERE):
    r = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    if r.returncode:
        raise RuntimeError(f"{args[0]} failed ({r.returncode}):\n{r.stdout}")
    return r.stdout

def evidence_check():
    bindings = {}
    for name in ["research_scope_freeze.json", "evidence/additional_frozen_inputs.json",
                 "evidence/physical_snapshot_20261117_a.json"]:
        for p, h in read(HERE / name)["bound_files"].items():
            assert p not in bindings or bindings[p] == h, p
            bindings[p] = h
    for p, h in bindings.items():
        assert digest(ROOT / p) == h, f"Changed frozen input: {p}"
    for name in ["macros", "lstm", "legacy", "qor"]:
        assert digest(HERE / f"tables/{name}.tex") == digest(
            ROOT / f"paper/dac2027_integrated/tables/{name}.tex")
    stats = read(HERE / "evidence/native_computed_statistics.json")
    nstats = 0
    for key, val in stats.items():
        if isinstance(val, dict) and "values" in val and "sample_sd" in val:
            assert abs(statistics.mean(val["values"]) - val["mean"]) < 1e-10, key
            assert abs(statistics.stdev(val["values"]) - val["sample_sd"]) < 1e-10, key
            nstats += 1
    cpu = read(RAW / "software_a/delivery.json")
    for val in cpu["configurations"]:
        means = [statistics.mean(x) for x in val["retained_seconds_by_process"]]
        assert all(abs(a-b) < 1e-12 for a,b in zip(means, val["process_means"]))
        assert abs(statistics.mean(means)-val["mean_of_process_means_seconds"]) < 1e-12
        assert abs(statistics.stdev(means)-val["sample_sd_of_process_means_seconds"]) < 1e-12
        assert val["all_output_exact"]
    for case, val in cpu["selected_CPU"].items():
        assert val["threads"] == 64
        assert val["mean_of_process_means_seconds"] == min(
            c["mean_of_process_means_seconds"] for c in cpu["configurations"]
            if c["case"] == case)
    model = read(RAW / "full_g_200_two_scenario_summary_a/summary.json")
    expected = {"base": [102557024, 104154414],
                "conservative_diagnostic": [135128351, 137198248]}
    nout = 0
    model_text = (HERE / "sections/conditional_model.tex").read_text()
    for model_run in model["runs"]:
        service = model_run["memory_contract"]
        assert service["frequency_mhz"] == 200
        for case, cycles in zip(["bnn_export", "lstm_s2"], expected[service["scenario"]]):
            c = model_run["cases"][case]
            assert c["total_cycles"] == sum(c["sample_cycles"]) == cycles
            assert sum(c["core_phase_cycles"].values()) == cycles
            assert c["samples"] == 40 and c["complete_batch"]
            assert c["full_output_sha256"] == c["input"]["golden_sha256"]
            assert abs(c["fpga_assumed_frequency_seconds"]-cycles/200e6) < 1e-12
            assert f"{cycles:,}" in model_text and f"{cycles/200e6:.6f}" in model_text
            nout += c["samples"]
    assert nout == 160
    for case, baselines in model["software_baselines"].items():
        gpu = baselines["GPU"]
        means = [statistics.mean(p["raw_seconds"]) for p in gpu["processes"]]
        assert abs(statistics.mean(means) - gpu["mean_s"]) < 1e-12
        assert f"{gpu['mean_s']:.6f}" in model_text
    physical = read(HERE / "evidence/physical_snapshot_20261117_a.json")
    assert physical["place_return_code"] == 0
    util = (ROOT / next(p for p in physical["bound_files"] if p.endswith("utilization.rpt"))).read_text()
    for label, val in [("CLB LUTs",1212828), ("Register as Flip Flop",749091),
                       ("LUT as Distributed RAM",286232), ("LUT as Shift Register",896),
                       ("Block RAM Tile",1148), ("URAM",640), ("DSPs",0)]:
        match = re.search(r"\|\s*" + re.escape(label) + r"\s*\|\s*(\d+)\s*\|", util)
        assert match and int(match.group(1)) == val, label
    cal = read(RAW / "model_calibration_h_return_wordmux_a/calibration_reuse_contract.json")
    assert cal["verified_native_samples"] == 52
    assert cal["verified_ordered_phase_intervals"] == 3772
    assert cal["verified_waves"] == 402
    assert cal["verified_logical_requests"] == cal["verified_logical_returns"] == 72917
    assert cal["all_full_outputs_19_phases_retirement_counts_and_cycle_identity_request_return_events_exact"]
    assert cal["top_and_other30_DUT_sources_unchanged_from_f"]
    assert cal["dispatcher_sequential_text_identical"]
    for p, h in cal["new_rtl_source_sha256"].items():
        assert digest(ROOT / p) == h
    return {"frozen_input_bindings": len(bindings), "native_statistics_recomputed": nstats,
            "CPU_configurations_recomputed": len(cpu["configurations"]),
            "full_model_outputs_from_bound_receipts": nout,
            "RTL_calibration_complete_cases": 52, "new_solver_or_EDA_runs": 0}

def source_files():
    return sorted([HERE / "main.tex", HERE / "references.bib"] +
                  list((HERE / "sections").glob("*.tex")) +
                  list((HERE / "tables").glob("*.tex")))

def verify_freeze():
    p = HERE / "manuscript_freeze.json"
    if not p.exists():
        return "not_yet_frozen"
    freeze = read(p)
    assert freeze["mutable_manuscript_files"] == MUTABLE
    addendum_path = HERE / "submission_compliance_addendum.json"
    expected = dict(freeze["fixed_source_sha256"])
    if addendum_path.exists():
        addendum = read(addendum_path)
        assert expected["main.tex"] == addendum["original_main_sha256"]
        expected["main.tex"] = addendum["replacement_main_sha256"]
        expected.update(addendum["added_fixed_source_sha256"])
        layout = read(HERE / "submission_compliance_layout.json")
        assert digest(addendum_path) == layout["preceding_addendum_sha256"]
        assert expected[layout["file"]] == layout["previous_sha256"]
        expected[layout["file"]] = layout["final_sha256"]
    for name, h in expected.items():
        assert digest(HERE / name) == h, f"Scientific freeze changed: {name}"
    return "fixed_scientific_sources_unchanged"

def qualification_check():
    q = read(HERE / "physical_qualification.json")
    assert q["board_measured"] is False
    if q["new_FPGA_success_claim"]:
        for key in ["route_complete", "setup_qualified", "hold_qualified",
                    "clock_context_qualified", "constraints_qualified",
                    "source_service_frequency_join_valid", "full_batch_outputs_verified"]:
            assert q[key], key
        assert q["qualified_frequency_MHz"] > 0
        when = dt.datetime.fromisoformat(q["success_claim_evidence_UTC"])
        assert when <= dt.datetime.fromisoformat(DEADLINE)
        # A later author pass must not introduce a new success result after the deadline.
        assert q["claim_frozen_before_deadline"]
    else:
        assert q["qualified_frequency_MHz"] is None
        assert q["FPGA_seconds"] is None and q["CPU_over_FPGA"] is None
    return q["new_FPGA_success_claim"]

def inspect_pdf(directory):
    info = run(["pdfinfo", "main.pdf"], directory)
    fonts = run(["pdffonts", "main.pdf"], directory)
    text = run(["pdftotext", "-layout", "main.pdf", "-"], directory)
    pages = text.split("\f")
    if not pages[-1].strip():
        pages.pop()
    assert len(pages) == 7, f"Need six content + one reference page, got {len(pages)}"
    assert "R EFERENCES" in pages[6][:150] or "REFERENCES" in pages[6][:150]
    assert "C ONCLUSION" in pages[5] or "CONCLUSION" in pages[5]
    assert not re.search(r"^Author:\s*\S", info, re.M)
    assert "612 x 792 pts (letter)" in info
    assert "Anonymous Authors" in text
    assert "C ONTENT G ENERATED BY AI" in text or "CONTENT GENERATED BY AI" in text
    for value in ["/inspire/", "guoruiyuan", "GRYYYYYYY", "TODO", "TBD", "??"]:
        assert value not in text, value
    rows = [line.split() for line in fonts.splitlines()[2:] if line.strip()]
    assert rows and all(row[-5] == "yes" for row in rows), "All fonts must be embedded"
    assert "Type 3" not in fonts
    log = (directory / "main.log").read_text(errors="replace")
    for pattern in [r"Overfull \\[hv]box", r"LaTeX Warning:.*undefined",
                    r"Citation .*undefined", r"Reference .*undefined"]:
        assert not re.search(pattern, log), pattern
    return info, fonts, text, log

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tectonic", default=os.environ.get("TECTONIC", "tectonic"))
    ap.add_argument("--freeze", action="store_true",
                    help="Create the one-time fixed-manuscript receipt after review; refuses overwrite")
    args = ap.parse_args()
    (HERE / "review/checks.json").write_text(json.dumps({"status":"RUNNING","UTC":dt.datetime.now(dt.timezone.utc).isoformat()})+"\n")
    evidence = evidence_check()
    frozen = verify_freeze()
    qualification_check()
    compiler = shutil.which(args.tectonic)
    if compiler is None:
        raise SystemExit("Set --tectonic to Tectonic 0.17.0; no solver or EDA will run.")
    version = run([compiler, "--version"]).strip()
    output = run([compiler, "--keep-logs", "--keep-intermediates", "main.tex"])
    (HERE / "build.log").write_text(output)
    info, fonts, text, log = inspect_pdf(HERE)
    (HERE / "main.txt").write_text(text)
    (HERE / "review").mkdir(exist_ok=True)
    (HERE / "review/pdfinfo.txt").write_text(info)
    (HERE / "review/fonts.txt").write_text(fonts)
    members = source_files()
    with zipfile.ZipFile(HERE / "submission_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            name = p.relative_to(HERE).as_posix()
            content = p.read_bytes()
            assert all(x not in content for x in [b"/inspire/", b"guoruiyuan", b"GRYYYYYYY"])
            zi = zipfile.ZipInfo(name, date_time=(2026,11,17,0,0,0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, content)
        z.writestr("BUILD.txt", "Anonymous LaTeX source. Compile with Tectonic 0.17.0:\n"
                   "tectonic main.tex\nRequires its standard TeX bundle (IEEEtran, TikZ, "
                   "algorithm/algpseudocode, BibTeX). No external data or experiment runs.\n")
    with tempfile.TemporaryDirectory(prefix="anonymous-paper-") as d:
        clean = Path(d)
        with zipfile.ZipFile(HERE / "submission_source.zip") as z:
            z.extractall(clean)
        cleanlog = run([compiler, "--keep-logs", "--keep-intermediates", "main.tex"], clean)
        _, _, rebuilt, _ = inspect_pdf(clean)
        assert rebuilt == text, "Clean archive build must preserve all rendered text"
        (HERE / "review/clean_build.log").write_text(cleanlog)
    run(["pdftoppm", "-scale-to", "1500", "-png", "main.pdf", "review/page"])
    if args.freeze:
        assert not (HERE / "manuscript_freeze.json").exists(), "Never overwrite the freeze"
        record = {
            "UTC": dt.datetime.now(dt.timezone.utc).isoformat(),
            "fixed_source_sha256": {p.relative_to(HERE).as_posix():digest(p)
                for p in members if p.relative_to(HERE).as_posix() not in MUTABLE},
            "mutable_manuscript_files": MUTABLE,
            "mutable_scope": "Only implementation table, performance qualification, related abstract/conclusion sentences after h terminal; native claims remain fixed.",
            "new_FPGA_success_claim_deadline_UTC": DEADLINE,
            "new_FPGA_success_claim_deadline_Beijing": "2026-11-18T09:00:00+08:00",
            "automatic_new_architecture_on_h_failure": False,
            "initial_PDF_sha256": digest(HERE/"main.pdf"),
            "initial_source_zip_sha256": digest(HERE/"submission_source.zip"),
            "scientific_scope_receipt_sha256": digest(HERE/"research_scope_freeze.json"),
        }
        with (HERE / "manuscript_freeze.json").open("x") as f:
            json.dump(record, f, indent=2); f.write("\n")
        frozen = verify_freeze()
    result = {"status":"PASS", "UTC":dt.datetime.now(dt.timezone.utc).isoformat(),
              "compiler":version, "evidence":evidence, "freeze":frozen,
              "content_pages":6, "reference_pages":1,
              "clean_source_zip_rebuild_text_equal":True, "all_fonts_embedded":True,
              "anonymous_metadata_and_text":True, "overfull_boxes":0,
              "undefined_references":0, "external_submission_performed":False,
              "PDF_sha256":digest(HERE/"main.pdf"),
              "source_zip_sha256":digest(HERE/"submission_source.zip"),
              "retained_warnings":"Underfull boxes and upstream algorithm.sty comment UTF-8 warning; inspect build.log. No local source UTF-8 replacement or overflow."}
    (HERE / "review/checks.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
