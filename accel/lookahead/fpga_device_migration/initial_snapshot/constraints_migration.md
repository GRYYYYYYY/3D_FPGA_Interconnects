# Frozen OOC constraint migration
Original h clock.xdc copied byte for byte: core_clock 5.000 ns, uncertainty 0.100 ns, all non-clock inputs/outputs min/max 0.100/0.800 ns. No timing exceptions added.
Implementation-only HD.CLK_SRC changes from U280 BUFGCE_X0Y144 to BUFGCE_X0Y192, selected as the median dictionary-sorted unused BUFGCE in the loaded xcu250-figd2104-2L-e database. Recheck availability after synthesis. This is an external OOC clock assumption, not an instantiated clock buffer or board qualification.
No old LOC/BEL/Pblock/partition-pin constraints or DCP imported. No PACKAGE_PIN added. Full RTL and all defaults unchanged. Retain original boundary assumptions and unproven aliases; no post-synthesis formal equivalence claim.
