import java.io.*;
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.concurrent.locks.*;

public class CoordinationExperiments {
    static final class Wallet {
        final int id;int balance=1000;final ReentrantLock lock=new ReentrantLock();
        Wallet(int id){this.id=id;}
    }
    static void deadlock() throws Exception {
        Wallet a=new Wallet(1),b=new Wallet(2);CyclicBarrier gate=new CyclicBarrier(2);
        Thread[] pair=new Thread[2];
        for(int i=0;i<2;i++){final Wallet first=i==0?a:b,second=i==0?b:a;
            pair[i]=new Thread(()->{synchronized(first){try{gate.await();}catch(Exception e){throw new RuntimeException(e);}
                synchronized(second){first.balance--;second.balance++;}}},"Deadlock"+i);
            pair[i].setDaemon(true);pair[i].start();
        }
        ThreadMXBean bean=ManagementFactory.getThreadMXBean();long[] ids=null;
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);
        while(ids==null&&System.nanoTime()<deadline){ids=bean.findDeadlockedThreads();Thread.yield();}
        if(ids==null)throw new AssertionError("Deadlock not detected");
        System.out.println("DEADLOCK DETECTED: "+ids.length+" threads");
        for(ThreadInfo info:bean.getThreadInfo(ids,true,true))System.out.println(info);
        // Daemon demonstration threads remain blocked; process termination cleans them up.
    }
    static void ordered(Wallet from,Wallet to,int amount){
        Wallet low=from.id<to.id?from:to,high=from.id<to.id?to:from;
        synchronized(low){synchronized(high){if(from.balance>=amount){from.balance-=amount;to.balance+=amount;}}}
    }
    static boolean timed(Wallet from,Wallet to) throws InterruptedException {
        if(!from.lock.tryLock(5,TimeUnit.MILLISECONDS))return false;
        try{if(!to.lock.tryLock(5,TimeUnit.MILLISECONDS))return false;
            try{if(from.balance==0)return false;from.balance--;to.balance++;return true;}
            finally{to.lock.unlock();}}
        finally{from.lock.unlock();}
    }
    static final class Counter {
        final int[] values=new int[5];int size,in,out;final boolean notifyAll;
        final List<String> trace=new ArrayList<>();
        Counter(boolean all){notifyAll=all;}
        void wake(){if(notifyAll)notifyAll();else notify();}
        synchronized void put(int value) throws InterruptedException {
            while(size==5)wait();values[in]=value;in=(in+1)%5;size++;
            trace.add("put,"+value+","+size);wake();
        }
        synchronized int take() throws InterruptedException {
            while(size==0)wait();int value=values[out];out=(out+1)%5;size--;
            trace.add("take,"+value+","+size);wake();return value;
        }
    }
    static boolean counterTrial(boolean all,boolean save) throws Exception {
        Counter c=new Counter(all);AtomicInteger sum=new AtomicInteger();List<Thread> threads=new ArrayList<>();
        for(int id=0;id<2;id++){final int who=id;
            threads.add(new Thread(()->{try{for(int i=1;i<=50;i++)c.put(who*50+i);}catch(InterruptedException e){Thread.currentThread().interrupt();}}));
            threads.add(new Thread(()->{try{for(int i=0;i<50;i++)sum.addAndGet(c.take());}catch(InterruptedException e){Thread.currentThread().interrupt();}}));
        }
        for(Thread t:threads){t.setDaemon(true);t.start();}
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);
        for(Thread t:threads){long ms=Math.max(1,TimeUnit.NANOSECONDS.toMillis(deadline-System.nanoTime()));t.join(ms);}
        boolean complete=threads.stream().noneMatch(Thread::isAlive);
        if(!complete){for(Thread t:threads)t.interrupt();for(Thread t:threads)t.join(1000);}
        if(complete&&sum.get()!=5050)throw new AssertionError("Token sum");
        for(String row:c.trace){int size=Integer.parseInt(row.substring(row.lastIndexOf(',')+1));if(size<0||size>5)throw new AssertionError("Capacity");}
        if(save){List<String> csv=new ArrayList<>();csv.add("operation,token,size");csv.addAll(c.trace);Files.write(Path.of("results/counter_trace.csv"),csv);}
        System.out.println("COUNTER notifyAll="+all+",complete="+complete+",sum="+sum+",events="+c.trace.size());return complete;
    }
    static void ifGuardFailure() throws Exception {
        class Broken {
            int size;final CountDownLatch waiting=new CountDownLatch(2);
            synchronized void take() throws InterruptedException {
                if(size==0){waiting.countDown();wait();}
                size--;notifyAll();
            }
            synchronized void put(){size++;notifyAll();}
        }
        for(int trial=1;trial<=10;trial++){
            Broken b=new Broken();Thread[] consumers=new Thread[2];
            for(int i=0;i<2;i++){consumers[i]=new Thread(()->{try{b.take();}catch(InterruptedException e){Thread.currentThread().interrupt();}});consumers[i].start();}
            if(!b.waiting.await(3,TimeUnit.SECONDS))throw new AssertionError("Consumers not waiting");
            b.put();for(Thread t:consumers)t.join(3000);
            if(Arrays.stream(consumers).anyMatch(Thread::isAlive)||b.size!=-1)throw new AssertionError("If-guard schedule");
            System.out.println("IF_GUARD trial="+trial+",size="+b.size+" (invalid)");
        }
    }
    public static void main(String[] args) throws Exception {
        deadlock();Wallet a=new Wallet(1),b=new Wallet(2);Thread[] transfers=new Thread[4];
        for(int i=0;i<4;i++){final int id=i;transfers[i]=new Thread(()->{for(int k=0;k<1000;k++)ordered(id%2==0?a:b,id%2==0?b:a,1);});transfers[i].start();}
        for(Thread t:transfers)t.join(5000);
        if(Arrays.stream(transfers).anyMatch(Thread::isAlive)||a.balance+b.balance!=2000)throw new AssertionError("Ordered transfer");
        System.out.println("ORDERED transfers=4000,total_balance="+(a.balance+b.balance));
        AtomicInteger skipped=new AtomicInteger();
        for(int i=0;i<4;i++){final int id=i;transfers[i]=new Thread(()->{try{for(int k=0;k<100;k++)if(!timed(id%2==0?a:b,id%2==0?b:a))skipped.incrementAndGet();}catch(InterruptedException e){Thread.currentThread().interrupt();}});transfers[i].start();}
        for(Thread t:transfers)t.join(5000);
        if(Arrays.stream(transfers).anyMatch(Thread::isAlive)||a.balance+b.balance!=2000)throw new AssertionError("Timed transfer");
        System.out.println("TRY_LOCK skipped="+skipped+",total_balance="+(a.balance+b.balance));
        if(!counterTrial(true,true))throw new AssertionError("notifyAll timeout");
        int stalls=0;for(int trial=0;trial<10;trial++)if(!counterTrial(false,false))stalls++;
        System.out.println("NOTIFY_ONLY observed_stalls="+stalls+"/10; a successful run does not prove liveness");
        ifGuardFailure();
        ArrayBlockingQueue<Integer> queue=new ArrayBlockingQueue<>(5);
        Thread producer=new Thread(()->{try{for(int i=1;i<=20;i++)queue.put(i);}catch(InterruptedException e){Thread.currentThread().interrupt();}});
        producer.start();int sum=0;for(int i=0;i<20;i++)sum+=queue.take();producer.join();
        if(sum!=210)throw new AssertionError("BlockingQueue alternative");
        System.out.println("PASS: deadlock detected, ordering prevents it, token bounds hold, if guards fail, BlockingQueue sum=210");
    }
}
