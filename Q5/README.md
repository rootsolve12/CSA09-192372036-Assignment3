# Q5 Seat booking races

## Aim

Reproduce a check-then-book race and compare synchronization mechanisms.

## Design and analysis

The supplied SeatBooking is executed ten times without synchronization and ten times with the synchronized TODO method. An uninstrumented race may fail to appear in a short run; bookingsMade itself is also subject to lost updates, so its value alone does not prove safety.

BookingExperiments separately forces an unsafe interleaving using a per-seat CyclicBarrier: two users read free before either writes booked. An AtomicInteger outside the broken critical section counts successful claims reliably. All ten trials produce 20 claims for ten seats, i.e. ten duplicate sales each. This controlled schedule demonstrates the defect without claiming it is a natural incidence rate.

Critical section: test availability and change that same seat's state as one atomic operation. MethodBooking locks this. BlockBooking locks a dedicated final object for the whole check/update. The two versions protect the same work in this test; results do not establish that a block is inherently faster. A static synchronized method would lock the Class object, suitable only for genuinely shared class-level state, and would unnecessarily serialize independent screens if used indiscriminately.

The timing experiment has eight reusable executor workers and 10,000 requests contending for 1,000 seats. Each strategy has three warmups and five measured batches. Each batch includes new booking state allocation, task submission, coordination and result collection; pool creation is outside timing. Method, block, AtomicBoolean CAS, ReentrantLock and ConcurrentHashMap.putIfAbsent must each return exactly 1,000 successful claims. Unsafe success in these timings is not evidence of correctness.

For 20 independent screens use independent per-screen booking state and lock, or per-seat CAS for a simple binary state. Multi-seat reservations, payment and database transactions need additional atomic business rules. A single global lock is not justified by these tests.

A booking's uncontended state update is O(1), but blocked wait under contention is not bounded by O(1) wall time. CAS uses one success-or-fail attempt here; failed attempts return false rather than spinning. Each array-based version stores O(s) state for s seats; AtomicBoolean[] adds one object per seat. A ReentrantLock adds a lock and waiter state; a ConcurrentHashMap adds entry/table overhead for sold seats. Counter and fairness costs depend on contention and scheduling.

## Run

```bash
python tools/run.py Q5
```

Run from the repository root. On Windows, `py` can replace `python`. Java 17+ JDK and Python 3 are required. Both supplied before/after programs are built into isolated directories.

## Executed results

```text
SeatBooking_before_run1: Seats sold: 10
SeatBooking_before_run2: Seats sold: 10
SeatBooking_before_run3: Seats sold: 10
SeatBooking_before_run4: Seats sold: 10
SeatBooking_before_run5: Seats sold: 10
SeatBooking_before_run6: Seats sold: 10
SeatBooking_before_run7: Seats sold: 10
SeatBooking_before_run8: Seats sold: 10
SeatBooking_before_run9: Seats sold: 10
SeatBooking_before_run10: Seats sold: 10
SeatBooking_after_run1: Seats sold: 10
SeatBooking_after_run2: Seats sold: 10
SeatBooking_after_run3: Seats sold: 10
SeatBooking_after_run4: Seats sold: 10
SeatBooking_after_run5: Seats sold: 10
SeatBooking_after_run6: Seats sold: 10
SeatBooking_after_run7: Seats sold: 10
SeatBooking_after_run8: Seats sold: 10
SeatBooking_after_run9: Seats sold: 10
SeatBooking_after_run10: Seats sold: 10
PASS: forced race reproduced ten times; synchronized/atomic/lock/map variants retain 1000 unique sales
Forced race: 10/10 trials sold 20 claims for 10 unique seats
```

## Measured evidence

| strategy | Mean batch ms | Sample CV |
|---|---:|---:|
| unsafe | 0.6857 | 68.6% |
| method | 0.4406 | 25.2% |
| block | 0.8914 | 65.3% |
| atomic | 0.2047 | 20.5% |
| lock | 0.7024 | 43.3% |
| map | 2.0213 | 60.6% |

CV is sample standard deviation divided by mean. Compare all raw runs; high variation weakens small speed differences. These are classroom experiments, not JMH measurements.

## Evidence files

- `results/execution.txt`: full stdout/stderr from real execution.
- `results/checks.txt`: compact outcome summary.
- `results/environment.json`: actual JVM, execution origin and parameters.
- `screenshots/compiler.jpg` and `screenshots/output.jpg`: real terminal captures.
- Task-specific CSV files and stack/debugger traces are retained where applicable.

Execution took place in the workspace, not on the student device. Each student must personally rerun and understand every task. Individual pair-work contributions are not invented.
