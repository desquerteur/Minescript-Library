# Discovery audit — 26 October 2026

Public-source searches covered repository names, README mentions, MIT license
filters, forks, inline MIT/SPDX notices, strip-mining terms, and the official
Minescript downloads page. Search evidence returned 210 repositories for the
plain Minescript-name query; 76 candidate repository trees were inspected.

- [Repository search](https://github.com/search?q=minescript&type=repositories)
- [Official script downloads](https://minescript.net/downloads)
- [Recorded repository audit](repositories.json)

The collection retains 12 source packages with a verified root MIT license or
explicit per-file MIT identifiers. Fork duplicates and identical syntax trees
were deduplicated. Helpers, imports-only fragments, test suites, unrelated
projects with the same name, and third-party reference snapshots are excluded
from the program count. Complete teaching programs are labeled as examples.

DaLama007/SillyMineScripts contained strip-mining code but no stated license;
it was not redistributed. HySpinx/MinescriptModules was excluded because its
README identifies copied code with incomplete credits and missing libraries.
Philogex/Minescript-Miner v2.4.6 describes an adaptation covered by informal
permission rather than MIT; its current version also changed integrations.
The old official chatbot client was excluded because it requires an external
API account and uses a legacy endpoint/model; it is not part of this count.
The two maintained tunnel miners were written independently for this library.

Only explicitly MIT-licensed files were copied from sources without a root
license. Unlicensed README files from those sources were not redistributed.
Original copyright headers and full MIT permission text are retained.

This audit is broad rather than exhaustive. Public search results and upstream
branches can change; the imported file sources are pinned in catalog.json.
Basic source checks and warning labels do not establish live compatibility.
