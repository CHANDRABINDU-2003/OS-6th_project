# 🖥️ MiniOS Simulator

A desktop-style **Operating System concepts simulator** built in Python with
Tkinter. It packages nearly every major topic of an undergraduate OS course —
CPU scheduling, memory management, deadlocks, disk scheduling, page replacement,
process lifecycle, IPC, a virtual file system, and a shell — into a single,
clickable mini "operating system" with a boot sequence, login, themed desktop,
kernel log, and a system monitor.

> Built for an Operating Systems course project. **No third-party dependencies**
> — just Python 3 and the standard library.

---

## ✨ Features

### OS Concepts
| App | Concept | What it shows |
|-----|---------|---------------|
| 🧠 **Scheduler** | CPU Scheduling | FCFS, SJF, Priority, Round Robin, **Multilevel Queue** + Gantt chart, turnaround/waiting times |
| 💾 **Memory** | Memory Management & Paging | Contiguous allocation (First/Best/Worst Fit) + **virtual memory paging** with address translation |
| 🔗 **Deadlock** | Deadlock Avoidance | **Banker's Algorithm** safe-state check + safe sequence + Resource Allocation Graph |
| 📀 **Disk Sched** | Disk Scheduling | **FCFS, SSTF, SCAN, C-SCAN, LOOK** with head-movement visualization + total seek |
| 📄 **Page Repl** | Virtual Memory | **FIFO, LRU, Optimal** with page faults/hits/hit-ratio and a step-by-step frame table |
| 🔁 **Proc State** | Process Lifecycle | Animated New → Ready → Running → Waiting → Terminated transitions |
| 📨 **IPC** | Inter-Process Comm. | **Shared Memory, Message Queues, Pipes** demos |

### System
| App | What it shows |
|-----|---------------|
| 📁 **Files** | Hierarchical virtual file system on a virtual disk (`data/disk.json`) |
| 💻 **Shell** | Unix-like terminal (`ls`, `cd`, `cat`, `mkdir`, `touch`, …) sharing the same disk |
| 📊 **Task Mgr** | Live process list (incl. running apps) with CPU/memory gauges |
| 📈 **Monitor** | System Monitor Dashboard — real-time CPU / memory / disk gauges + active processes |
| 📜 **Kernel Log** | Live feed of kernel events (boot, launches, logins, …) |
| 🎨 **Themes** | Theme Manager — switch between **Midnight, Light, Matrix, Dracula** live |

### Utilities
🧮 **Calculator** · 📝 **Notepad** · 🕑 **Clock**

Plus a **boot animation**, **user authentication** (login screen), a themed
**desktop** with categorized icons, and a taskbar with clock, current user,
logout, and shutdown.

---

## 🚀 Getting Started

### Requirements
- Python **3.8+**
- Tkinter (bundled with standard Python; Debian/Ubuntu: `sudo apt install python3-tk`)

### Run
```bash
cd minios
python main.py
```
Boot → **login** (default `admin` / `admin`, or `user` / `user`) → desktop.

### Run the tests
```bash
python -m unittest discover -s tests
```

---

## 🗂️ Project Structure

```text
MiniOS_Simulator/
├── main.py                 # Entry point (boot → login → desktop)
│
├── core/
│   ├── kernel.py           # Central state: auth, process registry, stats
│   ├── logger.py           # Kernel logger (live event feed)
│   ├── login.py            # User authentication screen
│   ├── boot.py             # Boot animation & startup sequence
│   └── desktop.py          # Desktop interface (icons, taskbar, launcher, theming)
│
├── apps/                   # GUI applications (each a tk.Toplevel)
│   ├── scheduler.py        disk_scheduler.py   system_monitor.py
│   ├── memory.py           page_replacement.py kernel_log.py
│   ├── filesystem.py       process_state.py    theme_manager.py
│   ├── shell.py            ipc.py              calculator.py
│   ├── taskmanager.py      deadlock.py         notepad.py / clock.py
│
├── algorithms/             # Pure logic (no Tkinter — unit-testable)
│   ├── cpu_scheduling.py   bankers.py          disk_algo.py
│   ├── memory_algorithms.py page_replacement_algo.py  ipc_algo.py
│
├── data/                   # disk.json, notes.txt, users.json, processes.json,
│                           #   logs.txt, settings.json
├── assets/                 # icons/, wallpapers/, themes/
├── docs/                   # report, presentation, screenshots/
├── tests/                  # test_scheduler.py, test_memory.py, test_filesystem.py
├── utils.py                # Theme system, widget factories, paths, helpers
├── requirements.txt
└── README.md
```

### Architecture

The codebase is split into three clean layers so each OS component can be built
and tested independently:

- **`algorithms/`** — pure functions with no GUI (e.g. `cpu_scheduling.fcfs`,
  `bankers.is_safe`, `disk_algo.scan`). These are covered by `tests/`.
- **`apps/`** — thin Tkinter front-ends that call into `algorithms/` and render
  the results. Every app is a `tk.Toplevel` subclass launched by the desktop.
- **`core/`** — the kernel, logger, boot, login and desktop that wire it all
  together.

### Program Flow
```text
main.py
   └─ core/boot.py        (animation)
        └─ core/login.py  (authentication)
             └─ core/desktop.py
                  ├── OS Concepts:  scheduler · memory · deadlock · disk · page · proc · ipc
                  ├── System:       files · shell · taskmgr · monitor · kernel log · themes
                  └── Utilities:    calculator · notepad · clock
                       └─ Logout → login   |   Shutdown → exit
```

---

## 🔐 Default Accounts
| Username | Password | Role |
|----------|----------|------|
| `admin`  | `admin`  | admin |
| `user`   | `user`   | standard |

Edit `data/users.json` to add accounts.

---

## ✅ Verified

- All 12+ algorithm/app modules byte-compile.
- `tests/` (17 unit tests) pass — scheduling conservation, memory allocation
  (first/best/worst fit), paging translation, and the virtual file system.
- Algorithm outputs match textbook references (e.g. Banker's safe sequence
  `P1→P3→P4→P0→P2`; disk seek totals FCFS 640 / SSTF 236 / SCAN 331 / C-SCAN
  382 / LOOK 299; page faults FIFO 10 / LRU 9 / Optimal 7).
- Full GUI integration test: boot → login → desktop opens all 16 apps and live
  theme switching works.

---

## 🛠️ Extending

- New app: subclass `tk.Toplevel` in `apps/`, then register it in the
  `self.apps` list in [core/desktop.py](core/desktop.py).
- New algorithm: add a pure function in `algorithms/` and a test in `tests/`.
- New theme: add a palette to `THEMES` in [utils.py](utils.py).

---

## 📄 License
Educational project — free to use and modify for learning purposes.
