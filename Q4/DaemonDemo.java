import java.util.concurrent.CountDownLatch;
public class DaemonDemo {
    public static void main(String[] args) throws InterruptedException {
        boolean daemon=Boolean.parseBoolean(args[0]);
        CountDownLatch started=new CountDownLatch(1);
        Thread station=new Thread(()->{
            System.out.println("WORKER_STARTED daemon="+Thread.currentThread().isDaemon());started.countDown();
            try { Thread.sleep(300); } catch(InterruptedException e){Thread.currentThread().interrupt();}
            System.out.println("WORK_DONE");
        });
        station.setDaemon(daemon);station.start();started.await();
        System.out.println("MAIN_END without join");
    }
}
