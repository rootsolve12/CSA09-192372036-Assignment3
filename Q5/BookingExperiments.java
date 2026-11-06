import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.concurrent.locks.ReentrantLock;

public class BookingExperiments {
    interface Booking { boolean book(int seat); }
    static class Unsafe implements Booking {
        final boolean[] seats; Unsafe(int size){seats=new boolean[size];}
        public boolean book(int seat){if(seats[seat])return false;seats[seat]=true;return true;}
    }
    static final class MethodBooking extends Unsafe {
        MethodBooking(int size){super(size);}
        public synchronized boolean book(int seat){return super.book(seat);}
    }
    static final class BlockBooking extends Unsafe {
        final Object lock=new Object(); BlockBooking(int size){super(size);}
        public boolean book(int seat){synchronized(lock){return super.book(seat);}}
    }
    static final class AtomicBooking implements Booking {
        final AtomicBoolean[] seats;
        AtomicBooking(int size){seats=new AtomicBoolean[size];Arrays.setAll(seats,i->new AtomicBoolean());}
        public boolean book(int seat){return seats[seat].compareAndSet(false,true);}
    }
    static final class LockBooking extends Unsafe {
        final ReentrantLock lock=new ReentrantLock();LockBooking(int size){super(size);}
        public boolean book(int seat){lock.lock();try{return super.book(seat);}finally{lock.unlock();}}
    }
    static final class MapBooking implements Booking {
        final ConcurrentHashMap<Integer,Boolean> seats=new ConcurrentHashMap<>();
        public boolean book(int seat){return seats.putIfAbsent(seat,Boolean.TRUE)==null;}
    }
    static Booking create(String type,int size){
        return switch(type){case "unsafe"->new Unsafe(size);case "method"->new MethodBooking(size);
            case "block"->new BlockBooking(size);case "atomic"->new AtomicBooking(size);
            case "lock"->new LockBooking(size);default->new MapBooking();};
    }
    static void forcedRace() throws Exception {
        for(int trial=1;trial<=10;trial++) {
            boolean[] seats=new boolean[10];CyclicBarrier[] gates=new CyclicBarrier[10];
            Arrays.setAll(gates,i->new CyclicBarrier(2));AtomicInteger sold=new AtomicInteger();
            List<Thread> users=new ArrayList<>();
            for(int i=0;i<20;i++) { final int seat=i%10;
                Thread t=new Thread(()->{if(!seats[seat]){
                    try{gates[seat].await(5,TimeUnit.SECONDS);}catch(Exception e){throw new RuntimeException(e);}
                    seats[seat]=true;sold.incrementAndGet();}});users.add(t);t.start();
            }
            for(Thread t:users)t.join();
            System.out.println("FORCED_RACE,trial="+trial+",successful_sales="+sold+",unique_seats=10,duplicate_sales="+(sold.get()-10));
            if(sold.get()!=20)throw new AssertionError("Forced interleaving failed");
        }
    }
    static long batch(String type,ExecutorService pool) throws Exception {
        Booking screen=create(type,1000);List<Future<Integer>> jobs=new ArrayList<>();
        for(int worker=0;worker<8;worker++) {
            final int id=worker;
            jobs.add(pool.submit(()->{int sold=0;for(int i=id*1250;i<(id+1)*1250;i++)if(screen.book(i%1000))sold++;return sold;}));
        }
        int sold=0;for(Future<Integer> job:jobs)sold+=job.get();
        if(!type.equals("unsafe")&&sold!=1000)throw new AssertionError(type+" sold="+sold);
        return sold;
    }
    public static void main(String[] args) throws Exception {
        forcedRace();ExecutorService pool=Executors.newFixedThreadPool(8);
        try {
            System.out.println("kind,strategy,run,attempts,elapsed_ns,sales");
            for(String type:List.of("unsafe","method","block","atomic","lock","map")) {
                for(int i=0;i<3;i++)batch(type,pool);
                long total=0;
                for(int run=1;run<=5;run++){
                    long start=System.nanoTime();long sales=batch(type,pool);long elapsed=System.nanoTime()-start;
                    total+=elapsed;System.out.println("RAW,"+type+","+run+",10000,"+elapsed+","+sales);
                }
                System.out.println("MEAN,"+type+",0,10000,"+(total/5.0)+",see_raw");
            }
        }finally{pool.shutdown();if(!pool.awaitTermination(5,TimeUnit.SECONDS))pool.shutdownNow();}
        System.out.println("PASS: forced race reproduced ten times; synchronized/atomic/lock/map variants retain 1000 unique sales");
    }
}
