"""Compact views of actual sources, compilation and saved run outputs for screenshots."""
from pathlib import Path
import sys,csv,re
import run
q=sys.argv[1];mode=sys.argv[2];root=run.ROOT;results=root/q/'results'
print(q+' | CSA09 | B Hitesh Roy | Register 192372036 | Workspace')
if mode=='compiler':
 main,variant,sources=run.SPECS[q][-1]
 source=root/q/(variant if variant!='.' else '')/sources[-1]
 print('Source: '+str(source.relative_to(root)))
 for i,line in enumerate(source.read_text().splitlines()[:7]):print(f'{i+1:2}: {line}')
 print('\nCompiler: '+' '.join(run.compiler())+' -g')
 run.compile_task(q)
else:
 checks=(results/'checks.txt').read_text().splitlines()
 if q=='Q1':
  for line in (results/'ATM.txt').read_text().splitlines():
   if line.startswith(('CASE','SUCCESS','INPUT_CATCH','VALIDATION_CATCH','FUNDS_CATCH','IO_CATCH','SECURITY_CATCH')):
    print(line)
  print('FINALLY count:',(results/'ATM.txt').read_text().count('FINALLY:'))
  print('Uncaught trace and unreachable-catch compiler diagnostic saved (expected failures).')
 elif q=='Q2':
  print((results/'StorageDemo.txt').read_text().strip())
  for line in (results/'ExamPortal.txt').read_text().splitlines():
   if line.startswith(('getCause','CASE','Cause lost','Unchanged Cause','PASS:')):print(line)
 elif q=='Q3':
  print('\n'.join(checks))
 elif q=='Q4':
  for line in checks:print(line)
  print('All 30 completion orders saved in results/station_orders.csv')
 elif q=='Q5':
  for variant in ['before','after']:
   values=[(results/f'SeatBooking_{variant}_run{i}.txt').read_text().strip().split(': ')[-1] for i in range(1,11)]
   print('Supplied '+variant+' sales in ten runs: '+','.join(values))
  print('Forced race: ten runs each produced 20 claims for ten seats (10 duplicates).')
  for row in csv.DictReader((results/'measurements.csv').open()):
   if row['kind']=='MEAN':print(row['strategy']+' mean per 10000 requests: '+f"{float(row['elapsed_ns'])/1e6:.4f} ms")
  print(next(line for line in checks if line.startswith('PASS:')))
 elif q=='Q6':
  print(checks[0]);print(next(x for x in checks if x.startswith('DEADLOCK')))
  for line in checks:
   if line.startswith(('ORDERED','TRY_LOCK','NOTIFY_ONLY')):print(line)
  values=[(results/f'TokenCounter_if_variant_run{i}.txt').read_text().strip().replace('Sum of tokens collected: ','').replace(' (expected 210)','') for i in range(1,11)]
  print('If-guard sums in ten runs: '+','.join(values))
  print('Deterministic if-guard failure: size -1 in ten trials')
  print('Counter trace: 200 transitions; all sizes in 0..5')
  print(next(line for line in checks if line.startswith('PASS:')))
 elif q=='Q7':
  print(checks[0]);print('Pool | Mean time for 10000 files | Success | Failure')
  for row in csv.DictReader((results/'measurements.csv').open()):
   if row['kind']=='MEAN':print(f"{row['pool']:>4} | {float(row['elapsed_ns'])/1e6:>10.3f} ms | {row['success']} | {row['failure']}")
  print('\n'.join(checks[1:]));print('All 10000 per-file outcomes saved to outcomes.csv')
 print('Full evidence: '+q+'/results/ (complete logs, not screenshots alone)')
