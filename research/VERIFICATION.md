# Verification — 26 October 2026

| Check | Result |
| --- | --- |
| Catalog size | 101 programs: 53 command entries and 48 teaching/demo entries |
| Support modules | 41, excluded from the program count |
| Maintained commands | 22 |
| Provenance | 12 pinned community/tutorial source packages; MIT notices preserved |
| Syntax | All 142 catalog files parse; 101 program syntax trees are distinct |
| Python undefined names | No F821 findings in catalog Python programs after documented fixes |
| Regression tests | 114 passed |
| Maintained-code statement coverage | 91%; community, examples, tests, and tools excluded |
| Ruff | Maintained code and tools passed |
| Pyright | Maintained command/helper code passed against the installed Minescript 5.0 API |
| Bandit | Maintained code and tools passed; vendor code excluded from this gate |
| Recognizable secret scan | No matching long API tokens, GitHub tokens, AWS access IDs, or Discord webhook secrets found |
| Catalog integrity | Unique IDs, file hashes, source license markers, package notices, and README coverage checked |
| Local preview | HTTP 200 on 127.0.0.1:8765; 101 program rows, 142 with support; search tested |
| File-serving boundary | Requests for .git/config return HTTP 404 |

The mining tests exercise fluid hazards, unsupported floors, falling ceilings,
container protection, entity interference, blocked movement, route endpoints,
cardinal directions, full inventory, missing tools, and key release. Tests use
a fake game bridge and do not dig or move in a real world.

Four vendor fixes retain original snapshots and hashes: a missing `echo`
import, a missing farmer help function, and two hardcoded job-1 termination
calls replaced by current-script exit.

Community scripts retain manual-setup/live-test-pending status. Some require
older Java mappings, Minescript Plus, third-party Python modules, operator
commands, or SkyBlock-specific mechanics. Syntax checks and source flags are
not a complete vendor security audit or a guarantee of Minecraft 26.3 support.
Live Minecraft trials remain outstanding for all new functionality.
