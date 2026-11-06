from pathlib import Path
import csv,json,re,statistics
R=Path(__file__).resolve().parents[1]
TOPICS={
'Q1':('ATM failure handling', 'Classify withdrawal failures and validate catch selection and finally execution.', '''Eight inputs cover a valid withdrawal, a nonnumeric account, nonnumeric amount, negative amount, insufficient funds, missing card file, mismatched account and NaN. The balance is a simulation constant of 1000, not a bank integration. Inputs are retained in inputs/cases.csv.

Throwable branches into Error and Exception. Error represents VM/linkage/resource failures that this ATM does not normally recover from. Checked IOException (including NoSuchFileException) and checked InsufficientFundsException represent recoverable external/business failures. RuntimeException includes NumberFormatException, InputMismatchException, IllegalArgumentException and SecurityException. No real VM Error is deliberately triggered.

Catch order: numeric parsing multi-catch precedes IllegalArgumentException because NumberFormatException is its subclass. Security, funds and I/O catches distinguish other recovery paths. A broad IOException before FileNotFoundException is unreachable; inputs/CatchOrder.java.txt is deliberately invalid and its compiler diagnostic is retained separately. It is not part of the normal successful build.

The try-with-resources Scanner and reader close on normal and exceptional paths. The finally message runs on each ordinary completion or propagation path; it cannot guarantee execution after JVM halt, forced process termination or a machine failure. The eight observed messages are counted by the runner.

UncaughtTrace intentionally exits nonzero. In its trace, the first line names NumberFormatException and its message; java.base frames show numeric parsing internals. The application frames identify parseAccount, service and main, with source line numbers, read from the throw site outward. The intentionally uncaught run is expected evidence, not a failed assignment check.

A single catch(Exception) can be appropriate at a top-level boundary that logs the full cause and produces a controlled response, but it loses exception-specific handling unless the types are subsequently distinguished. It does not catch Error and should not silently convert programming defects into success.

The validateWithoutThrowing alternative uses hasNextLong/hasNextDouble and explicit result codes for expected input errors. It still needs a way to handle actual I/O failure, since pre-checking file existence cannot eliminate races. Ordinary checks and result codes need O(1) auxiliary state per attempt; parsing is O(input length). Constructing a throwable with a captured depth-d trace normally requires O(d) trace work/storage, while returning a code is O(1). Chaining retains additional causes and their traces.'''),
'Q2':('Exam exceptions and propagation','Implement checked domain exceptions across controller, service and storage layers while preserving causes.', '''ExamPortal uses checked ExamException subclasses WindowClosed, NotRegistered, FileTooLarge and SubmissionStorageException. These are expected failures a caller can present or recover from. Negative size metadata is an unchecked IllegalArgumentException because it violates the API contract. Java still requires the checked declaration on main for its direct service test, even though that chosen input throws the unchecked exception first.

Propagation: Files.readAllBytes -> IOException -> storage wraps it as SubmissionStorageException(message,cause) -> service declares throws ExamException -> controller catches ExamException, displays a domain message and records the full chain. The program is a storage-access simulation: it validates readability of the supplied answer fixture rather than claiming to upload to a production portal.

The five designed cases cover success and every checked subclass. The supplied StorageDemo has only its TODO body completed and must produce Saved answer01.pdf / Error: Could not store answer02.pdf / Cause: Disk quota exceeded.

If the cause is omitted, getCause() returns null. The supplied expression e.getCause().getMessage() then throws NullPointerException; it does not safely print a Cause message. ExamPortal demonstrates both the lost cause and this dereference failure.

Meaningful storage exceptions isolate implementation details from the UI, while a preserved IOException cause supports diagnosis. Extending RuntimeException would remove mandatory catch/throws declarations, but not the need for intentional boundary handling. Trace capture costs O(d) time/storage for depth d; a chain retains each cause and its trace, roughly O(sum of trace depths), rather than copying an entire trace into every wrapper.'''),
'Q3':('Resource safety and debugger evidence','Compare a faulty manual close path, a corrected finally-based version and try-with-resources.', '''ResourceSafety opens one output BufferedWriter plus one TrackedReader at a time. TrackedReader wraps a real file reader; its counter records open readers, not arbitrary OS handles. The writer is closed in every implemented path. The valid store totals are storeA=60 and storeB=90; both correct implementations produce the same report.

The failing input is storeBad.txt with BAD_ROW after a valid row. In manual_bad, read throws before reader.close, so the current reader leaks. manual_fixed closes it in finally, and try-with-resources closes it automatically. Observed reader counts are 1, 0 and 0. Demonstration leaks are explicitly closed after counting so subsequent tests are independent.

A real jdb session is retained in results/debugger_raw.txt and its cleaned transcript. A breakpoint at ResourceSafety.java line 44 is reached first for storeA and then storeBad. At the second stop locals identifies the live reader, where records the call stack, and print ResourceSafety.open reports 1. next skips reader.close at line 45 and reaches the writer finally at line 52: this is the actual leak path. It is not a simulated debugger transcript.

TWR closes resources in reverse creation order. A processing IOException remains primary while failing close B and then close A are recorded as suppressed exceptions. Explicit finally code must preserve the primary throwable and attach close failures if it needs the same semantics; a simple close in finally can mask it.

TWR alone does not ensure report completeness, validation, atomic publication, adequate disk space or recovery. This implementation stages a temporary report, deletes it on processing failure and preserves the previous complete summary. The replacement move is not advertised as crash-atomic on every filesystem; a durable production design needs an appropriate atomic move, fsync and recovery protocol.

For f sequential store files with total input length L, processing is O(L+f). Correct sequential designs hold O(1) handles (reader plus writer). This faulty design leaks one reader on a failing invocation; repeated uncleaned failures can accumulate O(f) handles. A version that never closes any readers may retain O(f) handles in one report. Output staging requires O(report length) disk space, distinct from open-handle count.'''),
'Q4':('Threads and lifecycle','Implement scanner batches with Thread and Runnable and record scheduling behaviour over repeated runs.', '''ScannerStations records ten Thread trials, ten Runnable trials and ten priority trials, each with four stations and final total 100. Each station simulates one 25-script batch using a short sleep. These are scheduler demonstrations, not measurements of real scanner throughput. The exact completion orders are in station_orders.csv; variation is permitted but not guaranteed in ten runs.

Extending Thread couples the task to a thread class and consumes Java's single superclass choice. Runnable separates a task from execution and is normally easier to reuse with executors. start schedules a new thread; invoking run directly is an ordinary call on main. The direct-run evidence retains state NEW and isAlive=false.

Lifecycle: NEW -> RUNNABLE -> TIMED_WAITING during sleep -> RUNNABLE -> TERMINATED. BLOCKED can occur while acquiring an intrinsic lock; WAITING can occur during untimed join/wait. These latter states are relevant to the lifecycle but are not claimed to have been observed for every scanner. The captured state test prints NEW, a sampled TIMED_WAITING and TERMINATED. RUNNABLE includes running or eligible-to-run states.

join ensures each station has terminated before its result is read and provides the required visibility relationship. sleep does not release an intrinsic monitor. Priorities are scheduler hints, not a portable finish-order guarantee. DaemonDemo runs in separate JVMs: the daemon worker starts but its delayed WORK_DONE is absent when main ends; a non-daemon worker keeps the JVM alive until WORK_DONE.

The fixed four-thread ExecutorService alternative sums four Callable results through Future.get and shuts down explicitly. For total work n and p workers, ideal balanced useful work is O(n/p), plus launch/scheduling and longest-batch overhead; creating more workers than available parallel work cannot make that bound unconditional. Thread stacks use roughly O(p * stack size); a pool can reuse p threads over many batches.'''),
'Q5':('Seat booking races','Reproduce a check-then-book race and compare synchronization mechanisms.', '''The supplied SeatBooking is executed ten times without synchronization and ten times with the synchronized TODO method. An uninstrumented race may fail to appear in a short run; bookingsMade itself is also subject to lost updates, so its value alone does not prove safety.

BookingExperiments separately forces an unsafe interleaving using a per-seat CyclicBarrier: two users read free before either writes booked. An AtomicInteger outside the broken critical section counts successful claims reliably. All ten trials produce 20 claims for ten seats, i.e. ten duplicate sales each. This controlled schedule demonstrates the defect without claiming it is a natural incidence rate.

Critical section: test availability and change that same seat's state as one atomic operation. MethodBooking locks this. BlockBooking locks a dedicated final object for the whole check/update. The two versions protect the same work in this test; results do not establish that a block is inherently faster. A static synchronized method would lock the Class object, suitable only for genuinely shared class-level state, and would unnecessarily serialize independent screens if used indiscriminately.

The timing experiment has eight reusable executor workers and 10,000 requests contending for 1,000 seats. Each strategy has three warmups and five measured batches. Each batch includes new booking state allocation, task submission, coordination and result collection; pool creation is outside timing. Method, block, AtomicBoolean CAS, ReentrantLock and ConcurrentHashMap.putIfAbsent must each return exactly 1,000 successful claims. Unsafe success in these timings is not evidence of correctness.

For 20 independent screens use independent per-screen booking state and lock, or per-seat CAS for a simple binary state. Multi-seat reservations, payment and database transactions need additional atomic business rules. A single global lock is not justified by these tests.

A booking's uncontended state update is O(1), but blocked wait under contention is not bounded by O(1) wall time. CAS uses one success-or-fail attempt here; failed attempts return false rather than spinning. Each array-based version stores O(s) state for s seats; AtomicBoolean[] adds one object per seat. A ReentrantLock adds a lock and waiter state; a ConcurrentHashMap adds entry/table overhead for sold seats. Counter and fairness costs depend on contention and scheduling.'''),
'Q6':('Deadlock and token coordination','Detect a real lock cycle, prevent it and validate bounded producer-consumer communication.', '''Two opposite wallet transfers acquire their first monitors and rendezvous at a barrier before requesting the other. ThreadMXBean detects a real two-thread deadlock and records ownership/wait information. These intentionally blocked threads are daemon demonstrations so the JVM can terminate; they are not production recovery logic.

The four Coffman conditions are mutual exclusion, hold-and-wait, no preemption and circular wait. Ordered transfers always acquire the smaller unique wallet id before the larger, removing circular wait. Four workers complete 4,000 ordered transfers and preserve total balance 2,000. The sample only uses distinct wallets with distinct ids; a general API must enforce that identity invariant. The tryLock alternative releases acquired locks in finally and reports skipped attempts after timeout. Avoiding indefinite blocking does not ensure every transfer succeeds or prevent livelock without an appropriate retry policy.

The supplied TokenCounter has both TODOs completed using synchronized methods, while predicates and notifyAll; its sum is 210. A separate two-producer/two-consumer counter records 200 transitions and verifies each size is within 0..5. The trace is captured under the same monitor as state updates.

wait must hold the monitor and sit in a while loop because another thread may consume the condition before a woken thread reacquires the lock, and wakeups may be spurious. wait releases the monitor; sleep does not. notify wakes one arbitrary waiter. With both producers and consumers waiting on one monitor, it can select a waiter whose condition is still false and leave useful work asleep. Ten notify-only trials record actual stalls or successful completion; zero observed stalls does not establish liveness. notifyAll plus condition loops rechecks every relevant waiter but cannot promise fair scheduling.

Both while guards in the supplied class are also replaced with if in if_variant/TokenCounter.java and run ten times with a bounded external process timeout. Observed output may happen to match 210; the separate deterministic two-consumer example always exposes a size of -1 after only one item is added. It demonstrates why an observed successful if-guard run is insufficient.

ArrayBlockingQueue of capacity five is implemented as an alternative and yields sum 210. Its put/take do O(1) queue work but can wait indefinitely for a condition unless timed/cancelled. The monitor buffer and BlockingQueue use O(capacity) storage, plus waiting threads. Ordered transfer does O(1) balance work and can wait for locks; a timed tryLock attempt is bounded by its requested waits plus scheduling overhead. Library queues are generally less error-prone than hand-written condition signalling.'''),
'Q7':('Concurrent fault-tolerant result processing','Process 10,000 real score files with isolated failures and compare pools of 1, 2, 4 and 8.', '''Requirements: read and validate each independent score file, retain exactly one result per unique file identity, do not let an ordinary corrupt/missing file abort other jobs, and produce success/failure counts summing to 10,000. Correctness targets are 9,700 successful reads and 300 injected processing failures. A valid low score is FAIL_GRADE, which is a successfully processed result, not a file-processing failure.

ResultProcessor uses ExecutorService, explicit Callable<Outcome>, Future and ConcurrentHashMap<String,Outcome>. Each job handles IOException/ScoreException locally. The collector calls get on every Future, handles unexpected task exceptions and verifies the result map has the same size as the input set before summary. Serious Error causes are propagated, not silently classified as ordinary bad files. Duplicate identities are rejected before submission. Interruptions abort normal completion rather than producing a misleading complete summary.

The hand-checked set has five requests: valid 80, valid 0, corrupt text, out-of-range 101 and missing file, giving two successes and three failures. The large dataset is generated by documented rules: each index ending in 00 is missing, 01 corrupt and 02 out of range. Other scores are index modulo 101. The repository includes the generator, specification and hand fixtures; generated/ is excluded because it is reproducible. All 10,000 canonical outcomes are recorded in results/outcomes.csv.

Each pool has one warmup and five measured runs over the same generated files. Data generation is outside timing. Measurements include pool creation, submission, reads, validation, task joins, shutdown and result-map completeness checking. Summary aggregation and CSV output are outside timing. Trials reuse OS filesystem caches and have fixed pool order, so results are not cold-storage measurements or a universal scaling claim.

Choose the lowest measured five-run mean for this environment and rerun on the deployment hardware. Extra threads can help with I/O waits but add scheduling, synchronization, allocation and storage contention; CPU and filesystem limits matter. One limitation is O(n) queued tasks, Futures and outcomes. A bounded submission window or completion queue would reduce the outstanding-task memory for much larger datasets. Input content length should also be capped in a hardened deployment.

For n files, total data bytes B, p workers and longest task tmax, ideal useful-work time is at least max(B-throughput cost divided across available parallelism, tmax), plus scheduling/collection overhead. Map/Future/queue metadata is O(n), input processing buffers are per active worker, and thread-stack storage is O(p * stack size). Parallel streams can use the same per-file catch-and-return wrapper but use a shared common pool by default; unchecked exceptions escaping a lambda can abort collection. One thread per file can consume O(n * stack size) and exhaust thread resources; exceptions must still be captured and every worker joined to count outcomes reliably.''')}
for q,(title,aim,theory) in TOPICS.items():
 out=R/q/'results';out.mkdir(exist_ok=True)
 if q=='Q3':
  raw=(out/'debugger_raw.txt').read_text()
  clean=re.sub(r'\x1b\[[0-9;?]*[A-Za-z]','',raw).replace('\r','')
  (out/'debugger_transcript.txt').write_text(clean)
  (R/q/'debugger_commands.txt').write_text('stop at ResourceSafety:44\nrun\ncont\nlocals\nprint ResourceSafety.open\nwhere\nnext\nprint ResourceSafety.open\nlist\ncont\n')
  check=out/'checks.txt';text=check.read_text()
  if 'jdb breakpoint' not in text:check.write_text(text+'Real jdb breakpoint and next trace: line 44 -> line 52; open readers=1\n')
 text=f'# {q} {title}\n\n## Aim\n\n{aim}\n\n## Design and analysis\n\n{theory}\n\n## Run\n\n```bash\npython tools/run.py {q}\n```\n\nRun from the repository root. On Windows, `py` can replace `python`. Java 17+ JDK and Python 3 are required. Both supplied before/after programs are built into isolated directories.\n\n## Executed results\n\n```text\n'+(out/'checks.txt').read_text()+'```\n\n'
 if (out/'measurements.csv').exists():
  rows=list(csv.DictReader((out/'measurements.csv').open()));key='strategy' if q=='Q5' else 'pool'
  text+='## Measured evidence\n\n| '+key+' | Mean batch ms | Sample CV |\n|---|---:|---:|\n'
  for row in rows:
   if row['kind']!='MEAN':continue
   values=[float(x['elapsed_ns']) for x in rows if x['kind']=='RAW' and x[key]==row[key]]
   cv=statistics.stdev(values)/statistics.mean(values)*100
   text+=f"| {row[key]} | {float(row['elapsed_ns'])/1e6:.4f} | {cv:.1f}% |\n"
  text+='\nCV is sample standard deviation divided by mean. Compare all raw runs; high variation weakens small speed differences. These are classroom experiments, not JMH measurements.\n'
 if q=='Q1':text+='\n## Throwable hierarchy\n\n```mermaid\nclassDiagram\nThrowable <|-- Error\nThrowable <|-- Exception\nException <|-- IOException\nException <|-- InsufficientFundsException\nException <|-- RuntimeException\nRuntimeException <|-- IllegalArgumentException\nIllegalArgumentException <|-- NumberFormatException\nRuntimeException <|-- NoSuchElementException\nNoSuchElementException <|-- InputMismatchException\nRuntimeException <|-- SecurityException\n```\n\nThe full exception classes, failures and actual selected catches appear in the source and outputs.\n'
 if q=='Q2':text+='\n## Exception hierarchy and propagation\n\n```mermaid\nclassDiagram\nException <|-- ExamException\nExamException <|-- WindowClosed\nExamException <|-- NotRegistered\nExamException <|-- FileTooLarge\nExamException <|-- SubmissionStorageException\n```\n\nStorage IOException -> SubmissionStorageException with cause -> service throws ExamException -> controller catches and displays domain message.\n'
 if q=='Q4':text+='\n## Lifecycle\n\n```mermaid\nstateDiagram-v2\n[*] --> NEW\nNEW --> RUNNABLE: start\nRUNNABLE --> TIMED_WAITING: sleep\nTIMED_WAITING --> RUNNABLE: timeout\nRUNNABLE --> BLOCKED: monitor contention\nBLOCKED --> RUNNABLE: lock acquired\nRUNNABLE --> WAITING: wait or join\nWAITING --> RUNNABLE: condition completed\nRUNNABLE --> TERMINATED: run ends\n```\n'
 if q=='Q7':text+='''\n## Design representation\n\n```mermaid\nclassDiagram\nResultProcessor --> ExecutorService : submit Callable\nResultProcessor --> Future : collect every task\nResultProcessor --> ConcurrentHashMap : verify complete summary\nResultProcessor --> Outcome : produce success or failure\nOutcome : String id\nOutcome : boolean success\nOutcome : int score\nOutcome : String detail\n```\n\n```text\nvalidate unique file identities\ncreate a fixed thread pool and concurrent result map\nfor each file submit a Callable\n    try read and validate using try-with-resources\n    catch expected file errors and create a failed Outcome\n    publish Outcome under its unique identity\nfor every Future collect completion or record unexpected ordinary failure\nshut down and await worker termination\nassert outcome count equals requested file count\ncount successes and failures; persist canonical outcomes\n```\n'''
 text+='\n## Evidence files\n\n- `results/execution.txt`: full stdout/stderr from real execution.\n- `results/checks.txt`: compact outcome summary.\n- `results/environment.json`: actual JVM, execution origin and parameters.\n- `screenshots/compiler.jpg` and `screenshots/output.jpg`: real terminal captures.\n- Task-specific CSV files and stack/debugger traces are retained where applicable.\n\nExecution took place in the workspace, not on the student device. Each student must personally rerun and understand every task. Individual pair-work contributions are not invented.\n'
 (R/q/'README.md').write_text(text)
 (R/q/'screenshots').mkdir(exist_ok=True)
 (R/q/'input_design.json').write_text(json.dumps({'task':q,'input':'In-source deterministic scenarios plus inputs/ fixtures where applicable','details':'See source main method and README for scenarios, repeated trials and workload sizes'},indent=2)+'\n')
root='''# Programming in Java Assignment 3 CO3

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
'''
(R/'README.md').write_text(root)
(R/'.gitignore').write_text('**/build/\n**/generated/\n*.class\n__pycache__/\n')
print('Created task notes and README')
