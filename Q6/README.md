# Q6 Deadlock and token coordination

## Aim

Detect a real lock cycle, prevent it and validate bounded producer-consumer communication.

## Design and analysis

Two opposite wallet transfers acquire their first monitors and rendezvous at a barrier before requesting the other. ThreadMXBean detects a real two-thread deadlock and records ownership/wait information. These intentionally blocked threads are daemon demonstrations so the JVM can terminate; they are not production recovery logic.

The four Coffman conditions are mutual exclusion, hold-and-wait, no preemption and circular wait. Ordered transfers always acquire the smaller unique wallet id before the larger, removing circular wait. Four workers complete 4,000 ordered transfers and preserve total balance 2,000. The sample only uses distinct wallets with distinct ids; a general API must enforce that identity invariant. The tryLock alternative releases acquired locks in finally and reports skipped attempts after timeout. Avoiding indefinite blocking does not ensure every transfer succeeds or prevent livelock without an appropriate retry policy.

The supplied TokenCounter has both TODOs completed using synchronized methods, while predicates and notifyAll; its sum is 210. A separate two-producer/two-consumer counter records 200 transitions and verifies each size is within 0..5. The trace is captured under the same monitor as state updates.

wait must hold the monitor and sit in a while loop because another thread may consume the condition before a woken thread reacquires the lock, and wakeups may be spurious. wait releases the monitor; sleep does not. notify wakes one arbitrary waiter. With both producers and consumers waiting on one monitor, it can select a waiter whose condition is still false and leave useful work asleep. Ten notify-only trials record actual stalls or successful completion; zero observed stalls does not establish liveness. notifyAll plus condition loops rechecks every relevant waiter but cannot promise fair scheduling.

Both while guards in the supplied class are also replaced with if in if_variant/TokenCounter.java and run ten times with a bounded external process timeout. Observed output may happen to match 210; the separate deterministic two-consumer example always exposes a size of -1 after only one item is added. It demonstrates why an observed successful if-guard run is insufficient.

ArrayBlockingQueue of capacity five is implemented as an alternative and yields sum 210. Its put/take do O(1) queue work but can wait indefinitely for a condition unless timed/cancelled. The monitor buffer and BlockingQueue use O(capacity) storage, plus waiting threads. Ordered transfer does O(1) balance work and can wait for locks; a timed tryLock attempt is bounded by its requested waits plus scheduling overhead. Library queues are generally less error-prone than hand-written condition signalling.

## Run

```bash
python tools/run.py Q6
```

Run from the repository root. On Windows, `py` can replace `python`. Java 17+ JDK and Python 3 are required. Both supplied before/after programs are built into isolated directories.

## Executed results

```text
TokenCounter: Sum of tokens collected: 210 (expected 210)
TokenCounter_if_variant_run1: Sum of tokens collected: 135 (expected 210)
TokenCounter_if_variant_run2: Sum of tokens collected: 210 (expected 210)
TokenCounter_if_variant_run3: Sum of tokens collected: 210 (expected 210)
TokenCounter_if_variant_run4: Sum of tokens collected: 60 (expected 210)
TokenCounter_if_variant_run5: Sum of tokens collected: 210 (expected 210)
TokenCounter_if_variant_run6: Sum of tokens collected: 210 (expected 210)
TokenCounter_if_variant_run7: Sum of tokens collected: 185 (expected 210)
TokenCounter_if_variant_run8: Sum of tokens collected: 135 (expected 210)
TokenCounter_if_variant_run9: Sum of tokens collected: 210 (expected 210)
TokenCounter_if_variant_run10: Sum of tokens collected: 210 (expected 210)
DEADLOCK DETECTED: 2 threads
ORDERED transfers=4000,total_balance=2000
TRY_LOCK skipped=235,total_balance=2000
NOTIFY_ONLY observed_stalls=0/10; a successful run does not prove liveness
PASS: deadlock detected, ordering prevents it, token bounds hold, if guards fail, BlockingQueue sum=210
```


## Evidence files

- `results/execution.txt`: full stdout/stderr from real execution.
- `results/checks.txt`: compact outcome summary.
- `results/environment.json`: actual JVM, execution origin and parameters.
- `screenshots/compiler.jpg` and `screenshots/output.jpg`: real terminal captures.
- Task-specific CSV files and stack/debugger traces are retained where applicable.

Execution took place in the workspace, not on the student device. Each student must personally rerun and understand every task. Individual pair-work contributions are not invented.
