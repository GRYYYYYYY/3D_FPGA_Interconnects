# Output service initial exact implementation contract

No extra per-group input register: consume existing front target_context[group].
Reuse services/df_rr_router.sv (groups8/16 ->8banks, one holding register/bank,
pre-edge cyclic RR, replacement only on OLD downstream handshake). Payload is
cell15+immutable pair64. Bank=cell&7, row=cell>>3. No new physical memory ports.

Each bank contains one synchronous65-bit {seen,pair} BRAM, depth4096. Reset/sample
clear performs4096actual writes, {seen0,pair=MISSING}; no input accepted until done.
Sample state cannot clear while prior output export/ACKs are active.

Bank pipeline has three finite positions: s0 capture+RAM read, s1 compare/result,
s2 completion event. The entire bank advances iff s2empty or completion_ready.
Accepted bank input at C reads RAM and captures{addr,pair}; C+1 computes whole-pair
minimum; C+2 writesRAM and asserts completion; earliestcompletionhandshakeC+3.
II1 including consecutive samecell. Comparison forwards newest s1 result first,
then last actual RAM write (covers read/write collision at distance2), else sync
read data. seen first/improved computed from that same forwarded old state.
Both forward records preserve stall behavior. Backpressure freezes all bank pipe
positions, no overwritten result or free bypass. Semantic recorded count consumes
actual completion events, not group handshake. Allfour controls share this.

C++output/output_model.hpp: dfoutput::Update{cell,pair}; Service(groups,addr_bits=12),
.tick(vector<optional<Update>>,array<bool,8>event_ready) -> Tick{accepted[group],
completion[8] optional{cell,pair,first,improved}} reporting pre-edge handshakes;
.init_done(), .idle(), .get(cell), .seen(cell). Call one tick per actual initcycle;
constructor initial state is uninitialized. A busy service must drain beforeexport.

Export starts only after input group holds/router/bank pipeline drain. Eight sync
bank reads/cycle form atmosttwo consecutive32Bbeats. Total finite packing reservations
16 includes pending sync-read/pack beats, not16+freepipeline. Launch readC -> pack
FIFOwriteC+1 -> earliest logicalmemoryrequestC+2. Capacity decision uses pre-edge
16-count including pending beats; no same-edge freed-slot reuse. FIFO issues strict
prefix atmost2/cycle, blockssecond iffirstrejected, matching existingmodel export.
If onlyone reservation free readfourbanks; consecutive two beats maystraddle rows
but neveruseonebanktwice. Lastpartialbeat pads missing. Tags use unique outputbeat
index/sample generation through shared memorynetwork source176+(line&31), classcontrol.
FIFOslots releaseonacceptedlogicalrequest; outstandingACKs tracked untilallreal
responses consumed. No complete done beforeeverybeat ACK; physicaltag/OOOvalidation
belongscommonmemorynetwork, not duplicated here. Export counters areperjobandreset
onlyafterdrain. No200MHz/fullkernel claim from simulation or RAMinference.

## Final export/ACK correction after cross-review (frozen D contract)

The two write offers are a strict-prefix pair, not two independent AXI channels:
secondvalid is gated by firstready, so it never overtakes a rejected first. The
common source FIFO/network sees atmost2 accepted logicalwrites/cycle at sources
176+(physical_line&31); no physicalbandwidth is added.

`df_output_context` includes actual `df_ack_collector` between32existing MISC
return holding registers and exporter. Two global cyclicRR winners feed exactly
two real output holding registers; no added source FIFO. Cursor advances onlyon
real selected input transfer, afterthelast accepted winner. A blocked holder
keepsallmetadata; the other mayadvance. Oldholder consumption maypermit replacement;
newly accepted source ACKatR cannot reach exporterbeforeR+1. Returnedmetadata is
opaque WIDTH(default64; sample32+beat32 tested), parameterizable tocommonIDwidth,
never silentlytruncated. Physicaltag/generation validation isupstream commonnetwork.
The generic C++ `AckCollector<Packet>` retains thecomplete packet and exposes
`out[2]`, `input_ready(inputs32,ready2)`, `tick`, `idle`. Integration must consume
OLDout beforetick and clear a networksourcehold only onactualinput_ready. One
sample export completes only whenallACKs andcollector/network stateareempty.

If exportstart isacceptededgeS, that edge onlyregisters thecommand; firstbankread
isS+1, firstFIFOwriteS+2, earliestlogicalmemorywriteofferS+3 (actualacceptance stillrequiresready). Last exporter ACKacceptedA
incrementscounterafterA; registered export_done isassertedafteredgeA+1 andvisible
atpreedgeA+2. A modelusinghalf-open completed-clockcounter returns export_end=A+2.
Thus entry1+exit1 clocks areadditional topreviousC; ACKcollector addsitsactual
registered edge (normalcases typically+1, jitter mayalsoincur finitearbitration).

Actual XSim2022.2 `output_c` is thecombined outputRAM/export/ACKcollector closedloop:
1413cycles,1024updates/retirements,twoepochs,62writes/ACKs,packingpeak16,
4coincidentlogicalACKsources retained behindmax2collector. output_model.hpp and
ack_model.hpp arebothusedunchanged incycle-exact replay. Separate output_ack_a
covers32simultaneoussources,twooutputbackpressure,384packets/304cycles.
This islocalfunctional/calibration evidence,not completecommonnetwork/fullkernel
calibration, completekernel timing, or boardmeasurement.

## Final RAM inference closure

The final bank RTL muxes init/normal write address, data and enable before one
syntactic memory write. `output_d` repeats the combined TB and both frozen C++
replays; output/collector traces are byte-identical to `output_c`. The model
headers and every latency/handshake above are unchanged.

`output_ram_b` actually synthesizes G16/AW12, eight4096x65 banks:56 RAMB36E2
and8 RAMB18E2 (60 BRAM tiles),16971 LUT,7477 FF,zero LUTRAM/URAM/DSP/latches
for the complete local output context including router/exporter/ACK collector.
All64 RAM primitive optional output registers are disabled. `output_ram_a`
remains a negative inference record (0 BRAM,77824 LUTRAM) for the old template.
The exporter packing FIFO remains registers and is included in these totals.
No clock-frequency qualification follows from this synthesis-only result.
