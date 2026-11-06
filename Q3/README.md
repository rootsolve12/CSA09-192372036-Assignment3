# Q3 Resource safety and debugger evidence

## Aim

Compare a faulty manual close path, a corrected finally-based version and try-with-resources.

## Design and analysis

ResourceSafety opens one output BufferedWriter plus one TrackedReader at a time. TrackedReader wraps a real file reader; its counter records open readers, not arbitrary OS handles. The writer is closed in every implemented path. The valid store totals are storeA=60 and storeB=90; both correct implementations produce the same report.

The failing input is storeBad.txt with BAD_ROW after a valid row. In manual_bad, read throws before reader.close, so the current reader leaks. manual_fixed closes it in finally, and try-with-resources closes it automatically. Observed reader counts are 1, 0 and 0. Demonstration leaks are explicitly closed after counting so subsequent tests are independent.

A real jdb session is retained in results/debugger_raw.txt and its cleaned transcript. A breakpoint at ResourceSafety.java line 44 is reached first for storeA and then storeBad. At the second stop locals identifies the live reader, where records the call stack, and print ResourceSafety.open reports 1. next skips reader.close at line 45 and reaches the writer finally at line 52: this is the actual leak path. It is not a simulated debugger transcript.

TWR closes resources in reverse creation order. A processing IOException remains primary while failing close B and then close A are recorded as suppressed exceptions. Explicit finally code must preserve the primary throwable and attach close failures if it needs the same semantics; a simple close in finally can mask it.

TWR alone does not ensure report completeness, validation, atomic publication, adequate disk space or recovery. This implementation stages a temporary report, deletes it on processing failure and preserves the previous complete summary. The replacement move is not advertised as crash-atomic on every filesystem; a durable production design needs an appropriate atomic move, fsync and recovery protocol.

For f sequential store files with total input length L, processing is O(L+f). Correct sequential designs hold O(1) handles (reader plus writer). This faulty design leaks one reader on a failing invocation; repeated uncleaned failures can accumulate O(f) handles. A version that never closes any readers may retain O(f) handles in one report. Output staging requires O(report length) disk space, distinct from open-handle count.

## Run

```bash
python tools/run.py Q3
```

Run from the repository root. On Windows, `py` can replace `python`. Java 17+ JDK and Python 3 are required. Both supplied before/after programs are built into isolated directories.

## Executed results

```text
REPORT MATCH: storeA.txt:60|storeB.txt:90|
FAILURE manual_bad: Bad sales row in inputs/storeBad.txt; open_readers=1
FAILURE manual_fixed: Bad sales row in inputs/storeBad.txt; open_readers=0
FAILURE twr: Bad sales row in inputs/storeBad.txt; open_readers=0
PRIMARY: processing failed
SUPPRESSED: close B
SUPPRESSED: close A
PASS: identical reports; leaks bad=1 fixed=0 twr=0; previous summary preserved
Real jdb breakpoint and next trace: line 44 -> line 52; open readers=1
```


## Evidence files

- `results/execution.txt`: full stdout/stderr from real execution.
- `results/checks.txt`: compact outcome summary.
- `results/environment.json`: actual JVM, execution origin and parameters.
- `screenshots/compiler.jpg` and `screenshots/output.jpg`: real terminal captures.
- Task-specific CSV files and stack/debugger traces are retained where applicable.

Execution took place in the workspace, not on the student device. Each student must personally rerun and understand every task. Individual pair-work contributions are not invented.
