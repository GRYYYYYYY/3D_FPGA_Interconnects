# Vivado 2022.2 post-route host-library abort

Observed signature: `mremap_chunk(): invalid pointer`, SIGABRT6, after
`Router Completed Successfully`, before Tcl could write the post-route DCP.
`hs_err_pid3071178.log` locates `realloc` in system `libudev.so.1`, called from
`libXil_lmgr11.so`, `XilReg::Utils::GetHostInfo*`, `HAPRWebtalkHelper` and
`HAPRDesign::prepAndTransmitWebtalkData`. Cgroup OOM/oom_kill counters are zero.
This is a tool/host failure; the last router timing estimates are not signoff.

The available Vivado MCP has no `vivado_doc_search` tool. Public primary-source
research used the exact stack, WebTalk callback and libudev queries. No exact
AMD Answer Record or fixed-in-version claim was found. The
[AMD UG973 WebTalk transmission documentation](https://docs.amd.com/r/2021.1-English/ug973-vivado-release-notes-install-license/Transmission-of-Data)
confirms that route completion invokes WebTalk. A
[first-hand 2022.1 report on the licensing vendor's community](https://community.revenera.com/s/question/0D5PL00000NwuKu0AJ/issues-when-running-xilinx-tools-or-other-vendor-tools-in-docker-environment)
contains the same libudev/FlexNet/host-information abort and a process-scoped
`LD_PRELOAD` of the existing system libudev as a reported workaround.
The linked AMD community page returned only its loading/CSS shell, so no unseen
AMD answer is asserted. This is a matching reported mechanism, not a confirmed
2022.2 fixed release.

Local 2022.2 `config_webtalk -info` reports both user and installation preferences
already disabled. No matching user-definable WebTalk/license parameter exists
in local `report_param`; preferences were not changed. Disabling transmission
is therefore not evidence that the host-information constructor is avoided.

Recovery C starts the same installed Vivado 2022.2 through its own MCP session
with only `LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1` added to that process.
The resolved library hash is in `workaround.json`. The process environment and
maps confirm that this existing system library is loaded. No vendor binary,
system library, license, global installation/user preference, RTL, clock or
I/O constraint is patched. Allocator/load-order incompatibility is an inference
from the matching stack and reported workaround, not a proven vendor diagnosis.

C reopens the exact frozen synthesized DCP and writes checkpoints after opt,
place, physical optimization and route. It separately writes setup/hold/pulse,
unconstrained-path, resource, methodology, DRC and route reports. Verification
of the workaround succeeded for this same-design run: route_design returned,
the post-route DCP and all requested reports were written, and Tcl returned0. Timing qualification is evaluated separately;
a surviving tool process does not mean that 200 MHz passed.
