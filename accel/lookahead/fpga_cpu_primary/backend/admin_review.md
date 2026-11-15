# Admin and bank integration review

Scope: read-only review of parent-owned `rtl/cp_admin.sv` and
`rtl/cp_full_top.sv`; isolated behavioral XSim2022.2 tests added only under
`backend/`. Bank DUT sources remain frozen. This is not full-core functional,
resource, timing or calibration qualification.

Reviewed source hashes and validated current-source bindings are recorded in
`results/fpga_cpu_primary_20261115/backend_admin_review_receipt.json`.
Latest tested admin SHA256:
`094328555f532f1d458f7301e1c7bfb8df57d552d1c16c83e728b7b92e9b307d`.

## Review findings

The inspected full top connects canonical sources48..111 and scratch
sources112..175 directly to the shared network; their local write-data offsets
are0..63 and64..127. Admin sources176..207 use write-data128..159. Cookie20,
localID32, generation32, response kind/status and payload slices match the
bank interface. Sample reset initializes the actual banks; wave restart keeps
PV/directory state and waits for expansion initialization before MIN. No
additional high-impact defect was identified in these bank connections.
This limited review is not proof of full-top correctness.

Two admin issues were reported to the parent, who applied the fixes:

- Cost response validation did not check its physical source port. The latest
  source checks `p == cost_line[4:0]`; an actual queued cost response delivered
  through port1 instead of port0 is now rejected in the negative test.
- An otherwise legal lone lane1 output was rejected when its port matched the
  inactive lane0 port. The latest source gates this conflict on `write_v[0]`.
  The standard output service produces strict-prefix lanes, so this was an
  independent adapter-interface issue. The isolated output regression covers
  the standard output service; lone-lane1 behavior was reviewed in code only.

Transport exact-once identity is the shared physical live-tag network's
responsibility. Admin carries full32-bit ID/gen into its ACK collector and
checks generation/status/kind/phase; it does not implement a second per-output
outstanding-ID scoreboard. INIT checks count/range/owner, rather than detecting
an adversarial duplicate legal ID replacing another ID after the trusted
network. Tests verify exact IDs and uniqueness for legitimate traffic through
an independent scoreboard, but do not claim that admin alone detects arbitrary
post-network ID corruption. MODE2 is an optional out-of-contract diagnostic,
not a required PASS test and was not run.

## Executed tests

Each result directory below contains frozen sources, SHA256 bindings, exact
compile/elaborate/simulation commands, complete stage logs and terminal.json.
All terminal results are PASS, with no ERROR/Fatal in the admin stage logs.

| Result directory under results/fpga_cpu_primary_20261115 | Contract |
|---|---|
| admin_isolated_b | Latest admin:65 INIT lines across32sources,7 actual cost values decoded from2beats,137 output cells packed into35beats |
| admin_negative_mode1 | Flip bit31 of one real output ACK generation; sticky error observed |
| admin_negative_mode3 | Replace one real output ACK kind with15; sticky error observed |
| admin_negative_mode4 | Deliver a real cost response through the wrong source port; sticky error observed |
| backend_bank_b | Latest frozen production-bank positive and full-identity negative regression |

Positive admin test:102 requests and102 responses,35 observed per-port OOO
responses,82 cycles with blocked ACK collector outputs. It instantiates the
actual output RAM/service and ACK collector, compares every output sector,
checks missing-cell and partial-final-beat padding, verifies seven non-echo
64-bit cost values, and checks actual ACK ID/gen conservation using read-only
collector output observation. The last cost beat intentionally has only three
valid values. Returns remain stable through backpressure. There is no forced
DUT state or backdoor memory initialization.

Negative tests inject one malformed response at the public admin boundary and
require rejection within a bounded run. They establish error detection, not
successful continuation after corruption. Positive and negative snapshots
bind the same latest admin source. Original admin_isolated_a remains preserved.

Latest bank negative receipt is `backend_bank_b/terminal.json`; it includes
returned canonical generation bit31, returned localID bit31, scratch generation
bit31 and runtime address2^32 rejection. See README.md for the bank's positive
coverage and measured APPEND II8.

Reproduce into fresh paths, without overwriting completed evidence:

```sh
python3 accel/lookahead/fpga_cpu_primary/backend/run_admin_test.py results/fpga_cpu_primary_20261115/admin_new
python3 accel/lookahead/fpga_cpu_primary/backend/run_admin_test.py results/fpga_cpu_primary_20261115/admin_gen_new --mode 1
python3 accel/lookahead/fpga_cpu_primary/backend/run_admin_test.py results/fpga_cpu_primary_20261115/admin_kind_new --mode 3
python3 accel/lookahead/fpga_cpu_primary/backend/run_admin_test.py results/fpga_cpu_primary_20261115/admin_port_new --mode 4
```

All tests owned by this review are terminal; no bank/admin local simulator job
remains active. Parent-owned full-top simulation and EDA runs are separate.
