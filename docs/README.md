# Documentation

Place your submission documents here:

- `report.docx` — written report (problem, design, modules, screenshots, conclusion)
- `presentation.pptx` — slide deck for the demo
- `screenshots/` — capture the boot screen, login, desktop, Gantt chart, memory
  map, Banker's safe sequence, disk head-movement chart, page-fault table, etc.

## Suggested report outline

1. **Introduction** — what MiniOS Simulator is and which OS concepts it covers.
2. **Objectives** — learning goals (scheduling, memory, deadlocks, disk, paging,
   IPC, file system, shell).
3. **System Design** — three-layer architecture (`core` / `apps` / `algorithms`)
   and the boot → login → desktop flow (see the main README).
4. **Implementation** — how each algorithm works, with code highlights.
5. **Results / Screenshots** — annotated screenshots of each module.
6. **Testing** — the `tests/` unit-test suite and the textbook values it verifies.
7. **Conclusion & Future Work** — preemptive scheduling, segmentation,
   networking, multi-core, etc.
