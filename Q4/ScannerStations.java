import java.util.*;
import java.util.concurrent.*;

public class ScannerStations {
    static final class Station extends Thread {
        final int batch; final List<String> order; int scanned;
        Station(String name,int batch,List<String> order) { super(name);this.batch=batch;this.order=order; }
        public void run() { scanned=scan(getName(),batch,order); }
    }
    static int scan(String station,int batch,List<String> order) {
        try { Thread.sleep(2); }
        catch (InterruptedException e) { Thread.currentThread().interrupt(); return 0; }
        order.add(station+"@"+Thread.currentThread().getName());
        return batch;
    }
    static void trials(String mode) throws InterruptedException {
        for (int run=1;run<=10;run++) {
            List<String> order=Collections.synchronizedList(new ArrayList<>());
            Thread[] threads=new Thread[4]; int[] totals=new int[4];
            for (int i=0;i<4;i++) {
                final int id=i;
                if (mode.equals("Thread")) threads[i]=new Station("Station"+i,25,order);
                else threads[i]=new Thread(()->totals[id]=scan("Station"+id,25,order),"Runnable"+i);
                if (mode.equals("priority")) threads[i].setPriority(i==0?Thread.MAX_PRIORITY:Thread.MIN_PRIORITY);
                threads[i].start();
            }
            for (Thread t:threads) t.join();
            int total=0;
            for (int i=0;i<4;i++) total+=mode.equals("Thread")?((Station)threads[i]).scanned:totals[i];
            if (total!=100) throw new AssertionError("Final total before completion");
            System.out.println("ORDER,"+mode+","+run+","+String.join(";",order)+",total="+total);
        }
    }
    public static void main(String[] args) throws Exception {
        for (String mode:List.of("Thread","Runnable","priority")) trials(mode);
        List<String> order=new ArrayList<>();
        Thread direct=new Thread(()->scan("direct",1,order),"NotStarted");
        direct.run();
        System.out.println("DIRECT_RUN: "+order+"; thread state="+direct.getState()+"; alive="+direct.isAlive());
        if (direct.getState()!=Thread.State.NEW || !order.get(0).contains("@main")) throw new AssertionError("run/start");
        CountDownLatch entered=new CountDownLatch(1);
        Thread sleeper=new Thread(()->{entered.countDown();try{Thread.sleep(200);}catch(InterruptedException e){Thread.currentThread().interrupt();}},"Lifecycle");
        System.out.println("STATE before start="+sleeper.getState());
        sleeper.start();entered.await();
        long until=System.nanoTime()+100_000_000L;
        while(sleeper.getState()!=Thread.State.TIMED_WAITING && System.nanoTime()<until) Thread.onSpinWait();
        System.out.println("STATE after start="+sleeper.getState()+"; alive="+sleeper.isAlive());
        sleeper.join();System.out.println("STATE after join="+sleeper.getState()+"; alive="+sleeper.isAlive());
        ExecutorService pool=Executors.newFixedThreadPool(4);
        try {
            List<Future<Integer>> futures=new ArrayList<>();
            for(int i=0;i<4;i++) futures.add(pool.submit(()->25));
            int total=0;for(Future<Integer> f:futures)total+=f.get();
            if(total!=100)throw new AssertionError("Executor total");
            System.out.println("EXECUTOR total="+total);
        } finally {pool.shutdown();if(!pool.awaitTermination(5,TimeUnit.SECONDS))pool.shutdownNow();}
        System.out.println("PASS: 30 ordering trials, run/start distinction, lifecycle and executor totals");
    }
}
