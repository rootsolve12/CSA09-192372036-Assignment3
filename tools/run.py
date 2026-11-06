#!/usr/bin/env python3
from pathlib import Path
import subprocess,shutil,sys,argparse,time,json,csv,re
ROOT=Path(__file__).resolve().parents[1]
SPECS={
'Q1':[('ATM','.',['ATM.java']),('UncaughtTrace','.',['UncaughtTrace.java'])],
'Q2':[('StorageDemo','.',['StorageDemo.java']),('ExamPortal','.',['ExamPortal.java'])],
'Q3':[('ResourceSafety','.',['ResourceSafety.java'])],
'Q4':[('ScannerStations','.',['ScannerStations.java']),('DaemonDemo','.',['DaemonDemo.java'])],
'Q5':[('SeatBooking','before',['SeatBooking.java']),('SeatBooking','after',['SeatBooking.java']),('BookingExperiments','.',['BookingExperiments.java'])],
'Q6':[('TokenCounter','.',['TokenCounter.java']),('TokenCounter','if_variant',['TokenCounter.java']),('CoordinationExperiments','.',['CoordinationExperiments.java'])],
'Q7':[('ResultProcessor','.',['ResultProcessor.java'])]}
def compiler():return ['javac'] if shutil.which('javac') else ['java','-m','jdk.compiler/com.sun.tools.javac.Main']
def target(q,main,variant):return ROOT/q/'build'/variant.replace('.','main')/main
def compile_task(q):
 for main,variant,sources in SPECS[q]:
  source=ROOT/q/(variant if variant!='.' else '')
  out=target(q,main,variant);out.mkdir(parents=True,exist_ok=True)
  result=subprocess.run(compiler()+['-g','-encoding','UTF-8','-d',str(out)]+[str(source/f) for f in sources],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stdout+result.stderr)
  print('COMPILE PASS: '+q+'/'+variant+'/'+main,flush=True)

def invoke(q,main,variant,args=(),expected_exit=0):
 cmd=['java','-Xms128m','-Xmx512m','-cp',str(target(q,main,variant)),main,*args]
 proc=subprocess.run(cmd,cwd=ROOT/q,capture_output=True,text=True,timeout=180)
 text=proc.stdout+proc.stderr
 if (expected_exit==0 and proc.returncode!=0) or (expected_exit!=0 and proc.returncode==0):
  raise RuntimeError('Unexpected exit: '+str(proc.returncode)+'\n'+text)
 return text,proc.returncode

def run(q):
 out=ROOT/q/'results';out.mkdir(exist_ok=True);compile_task(q)
 version=subprocess.run(['java','-version'],capture_output=True,text=True)
 (out/'environment.json').write_text(json.dumps({'task':q,'name':'B Hitesh Roy','register_number':'192372036','execution_origin':'ChatGPT workspace; not student-device execution','executed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'java':(version.stdout+version.stderr).strip(),'jvm_options':['-Xms128m','-Xmx512m'],'compile':' '.join(compiler())+' -g -encoding UTF-8','measured_runs':5 if q in ('Q5','Q7') else None},indent=2)+'\n')
 combined=[];checks=[];raw=[]
 for main,variant,sources in SPECS[q]:
  cases=[((),0,1)]
  if main=='UncaughtTrace':cases=[((),1,1)]
  if main=='DaemonDemo':cases=[(('true',),0,1),(('false',),0,1)]
  if main=='TokenCounter' and variant=='if_variant':cases=[((),0,i) for i in range(1,11)]
  if main=='SeatBooking':cases=[((),0,i) for i in range(1,11)]
  for args,exit_code,trial in cases:
   label=main+('_'+variant if variant!='.' else '')+('_'+args[0] if args else '')+(('_run'+str(trial)) if main=='SeatBooking' or variant=='if_variant' else '')
   if variant=='if_variant':
    try:
     proc=subprocess.run(['java','-cp',str(target(q,main,variant)),main],cwd=ROOT/q,capture_output=True,text=True,timeout=3)
     text=proc.stdout+proc.stderr;code=proc.returncode
    except subprocess.TimeoutExpired:
     text='TIMEOUT after 3 seconds; flawed if-guard process terminated\n';code=124
   else:text,code=invoke(q,main,variant,args,exit_code)
   if main=='StorageDemo' and text.strip()!='Saved answer01.pdf\nError: Could not store answer02.pdf\nCause: Disk quota exceeded':raise AssertionError('Storage output')
   if main=='TokenCounter' and variant=='.' and text.strip()!='Sum of tokens collected: 210 (expected 210)':raise AssertionError('Token output')
   if main=='SeatBooking' and variant=='after' and text.strip()!='Seats sold: 10':raise AssertionError('Seat output')
   if main=='DaemonDemo' and (('WORK_DONE' in text)==(args[0]=='true')):raise AssertionError('Daemon evidence')
   (out/(label+'.txt')).write_text(text)
   combined+=['=== '+label+' (exit '+str(code)+') ===',text]
   if main in ('StorageDemo','TokenCounter','SeatBooking','DaemonDemo'):checks.append(label+': '+text.strip().replace('\n',' | '))
   if main=='ATM':
    checks.append('ATM paths=8; finally markers='+str(text.count('FINALLY:')))
    if text.count('FINALLY:')!=8:raise AssertionError('Finally count')
   if main=='UncaughtTrace':checks.append('UncaughtTrace exited nonzero with NumberFormatException (expected)')
   for line in text.splitlines():
    if line.startswith(('RAW,','MEAN,')):raw.append(next(csv.reader([line])))
    if line.startswith(('PASS:','HAND_CHECK','RECOMMEND','DEADLOCK DETECTED','ORDERED transfers','TRY_LOCK','NOTIFY_ONLY','REPORT MATCH','FAILURE manual','FAILURE twr','PRIMARY:','SUPPRESSED:','DIRECT_RUN:','STATE ','EXECUTOR total')):checks.append(line)
   if main=='ScannerStations':
    orders=[line for line in text.splitlines() if line.startswith('ORDER,')]
    (out/'station_orders.csv').write_text('kind,mode,trial,completion_order,total\n'+'\n'.join(orders)+'\n')
    if len(orders)!=30:raise AssertionError('Ten trials for each thread mode')
    checks.append('Station completion orders recorded: 10 Thread + 10 Runnable + 10 priority trials')
   if main=='BookingExperiments':
    forced=[line for line in text.splitlines() if line.startswith('FORCED_RACE')]
    if len(forced)!=10:raise AssertionError('Forced race repetitions')
    checks.append('Forced race: 10/10 trials sold 20 claims for 10 unique seats')
 if q=='Q1':
  bad=ROOT/q/'build/invalid';bad.mkdir(exist_ok=True)
  (bad/'CatchOrder.java').write_text((ROOT/q/'inputs/CatchOrder.java.txt').read_text())
  proc=subprocess.run(compiler()+['-d',str(bad),str(bad/'CatchOrder.java')],capture_output=True,text=True)
  if proc.returncode==0:raise AssertionError('Unreachable catch unexpectedly compiled')
  (out/'catch_order_compiler_error.txt').write_text(proc.stdout+proc.stderr)
  checks.append('Broad-before-narrow catch rejected by Java compiler (expected)')
 if raw:
  header='kind,strategy,run,attempts,elapsed_ns,sales' if q=='Q5' else 'kind,pool,run,files,elapsed_ns,success,failure'
  with (out/'measurements.csv').open('w',newline='') as f:
   writer=csv.writer(f);writer.writerow(header.split(','));writer.writerows(raw)
 (out/'execution.txt').write_text('\n'.join(combined)+'\n')
 (out/'checks.txt').write_text('\n'.join(checks)+'\n')
 print(q+' EXECUTION PASS',flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('task',nargs='?',choices=list(SPECS));p.add_argument('--compile-only',action='store_true');args=p.parse_args()
 for q in ([args.task] if args.task else SPECS):
  if args.compile_only:compile_task(q)
  else:run(q)
if __name__=='__main__':main()
