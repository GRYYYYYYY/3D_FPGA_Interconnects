# Implementation context to qualify

The selected scope is a complete core OOC, with an external memory timing
contract. The main reports must explicitly separate internal routed paths from
assumed upstream clock and external controller/port routes. An OOC report is
not a shell-inclusive deployment result.

Before implementation, inspect the synthesized clock buffer cells. If the core
clock is supplied externally, declare an actual supported clock-source site
using the installed tool's HD.CLK_SRC property, record the selected site and
include it in the implementation constraint binding. Check the resulting
clock paths and route coverage. Do not infer an achieved clock from WNS at a
different period or from a previous local context.

AMD's [UG905 context-constraint documentation](https://docs.amd.com/r/en-US/ug905-vivado-hierarchical-design/Context-Constraints)
explains that HD.CLK_SRC identifies an external buffer site, while ordinary OOC
boundary nets are not routed unless partition-pin locations/ranges are given.
The available page is2023.2; actual property/part/site support must therefore be
verified in installed2022.2 before use. Lack of an external shell/port placement
is an explicit boundary limitation, not proof of a physically implemented HBM
interface. No set_logic boundary constraints or false paths are introduced to
remove functional traffic or feedback.

MCP's2022.2 webserver status wrapper reports recursive-error strings; direct
Tcl proxy queries and original child-process birth identity/run logs are the
status authority. The runner is not restarted on a misleading status query.
