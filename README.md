# Programming in Java Assignment 3 CO3

| Field | Value |
|---|---|
| Name | B Hitesh Roy |
| Register number | 192372036 |
| Course | CSA09 / CSA0923 Programming with Java |
| Repository | https://github.com/rootsolve12/CSA09-192372036-Assignment3 |
| Tested JVM | OpenJDK 21.0.13; source requires Java 17+ |
| Mode | Pair work; partner identity and actual contribution record to be supplied |

## Contents

Q1–Q7 implemented and executed, including every supplied Complete the Code program. Code, input fixtures, full logs, stack traces, debugger evidence, raw measurements and terminal screenshots are included. The Word/PDF report is deferred as requested.

## Execute

```bash
java -version
javac -version
python tools/run.py
```

On Windows use `py tools/run.py` if appropriate. Run one task with `python tools/run.py Q5`. Install a Java 17+ JDK and Python 3. There are no external Java libraries. The runner can invoke the bundled jdk.compiler module if the javac launcher is absent. Separate build directories prevent duplicate class conflicts. Generated 10,000-file data is recreated by Q7 and excluded from version control.

## Task index

| Task | Evidence |
|---|---|
| [Q1](Q1/README.md) | Eight ATM paths, finally counts, intentional uncaught trace and rejected catch order |
| [Q2](Q2/README.md) | Supplied expected output, portal rule cases and preserved/lost causes |
| [Q3](Q3/README.md) | Actual jdb trace, leaked-reader counts, suppressed errors and equivalent reports |
| [Q4](Q4/README.md) | 30 station trials, priorities, lifecycle, direct run, daemon subprocesses and executor |
| [Q5](Q5/README.md) | Supplied before/after runs, ten forced races, six strategy timing experiments |
| [Q6](Q6/README.md) | Detected deadlock, ordered/timed transfers, token traces, notify and if-guard trials |
| [Q7](Q7/README.md) | Five-file hand check, 10,000-file outcomes, pools 1/2/4/8 with five measured runs |

## Reproduce the debugger trace

After running Q3, open a terminal in Q3 and run:

```bash
java -m jdk.jdi/com.sun.tools.example.debug.tty.TTY -sourcepath . -classpath build/main/ResourceSafety ResourceSafety
```

Enter `debugger_commands.txt` commands interactively, waiting for each breakpoint/step before continuing. The first line-44 stop is the good file; continue to reach storeBad. The repository contains the actual saved session. Normal `tools/run.py Q3` runs the resource tests, not an interactive debugger.

## Evidence interpretation

All checked-in execution evidence originates in this workspace, not the student's PC. Thread orders, timings, identity hashes and scheduler-dependent outcomes can differ on rerun. A race not appearing in the original program is not proof of safety; the forced schedule is separate evidence. A notify-only run completing does not establish liveness. Intentionally faulty variants are labelled, bounded where appropriate and excluded from normal expected-output assertions.

Five measured runs are retained for each Q5/Q7 case, with warmups described in the task notes. Fixed test order, filesystem caching, small samples and runtime noise limit speed conclusions. The processor's current fastest pool is an environment-specific observation. Raw canonical outcomes are stored for all 10,000 requested file identities.

The assignment requires both students to execute all seven tasks in their own repositories and complete an honest individual contribution record. No partner identity, personal execution or work on separate days is fabricated. Task commits record actual preparation. Report creation and GCR/SIMATS submission will be handled later.
