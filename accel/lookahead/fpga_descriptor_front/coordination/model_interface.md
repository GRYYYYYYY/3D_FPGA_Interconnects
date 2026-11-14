# Final model interface: frozen D

Authoritative machine-readable contract: `../service_contract.json`; executable
closure: `results/fpga_descriptor_front_20261114/model_d/binding.json`.
C0/F1/F2/F3 share64lanes/E256/beat512/fork128/ready128. Groups8/16 and oldROW+META
versus fused8/16B DESC are the only four-grid variables. Full batch selectsC0/F2
from actual matched representatives; no predetermined fusion win.

Sources0..15 EDGE;16..31 H/D;32..47 M;48..111 CAN;112..175 scratch;
176..207 INIT/output/cost physical-port sources. Classes EDGE0, H/D/M/MISC1,
CAN2,scratch3. SourceFIFO4 -> actual registeredRR ->4clientsFIFO4/port ->
physicalrequest/tagreg ->FIFO2 ->memory ->FIFO2 ->returnFIFO4 ->clientreg ->
registeredsourceRR. All32ports share32credits each. No second frozen local backend
port is cascaded; globalnetwork replaces it at logical clients.

Front includes real one-entry elastic parent context on reservecommand/ack,POP,
DESC/ROW/META/EDGE request/return,target and perlane candidate. Six elastic FP
stages preserve immutable operands, nextedge E/beat reuse, held blockedselectors.
CandidateFIFO4/lane -> actualRRholding1/bank ->FIFO16/bank ->backendFIFO2.

Directory uses64actual DirectoryBank FSMs plus MinimumCollector/MinimumTree;
actual response is required before PUB event ACK. Released members enter bounded
perbank holding withnextedge eligibility. No direct linkedlist/bitmap lookup.
BackendinputFIFO2 and deferred directory/result ACK contexts retain real K8 locks.

Output uses shared `dfoutput::Service`: group targethold reused,RRhold1/bank,
syncRAM3positions/II1 withsamecell forwarding, actualcompletion recorded. Export
has16totalread/pack reservations, atmost2read/issuebeats, andactual32->2registered
ACKcollector(two holders, sourceReady ongrant). Entry/done registered edges charged.

Shared service headers frozen; RAM-template RTL repairs proven cycle-identical do
not require model rerun. All source-changing model repairs use new output roots;
A/B/C preserved and explicitly superseded. D small160 and native representatives28
passed; fullC0/F2 native160 completed and334 unique samples independently verified.
See model/STATUS.md and model/RESULTS.md for terminal evidence. No full
kernel frequency or full assembled cycle-calibration qualification is claimed.
