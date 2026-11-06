public class SeatBooking {
    private final boolean[] booked;
    private int bookingsMade=0;
    SeatBooking(int seats) { booked=new boolean[seats]; }
    synchronized void book(int seat) {
        if (!booked[seat]) { booked[seat]=true; bookingsMade++; }
    }
    public static void main(String[] args) throws InterruptedException {
        SeatBooking screen=new SeatBooking(10);
        Thread[] users=new Thread[100];
        for(int i=0;i<users.length;i++) {
            final int seat=i%10;
            users[i]=new Thread(()->screen.book(seat));users[i].start();
        }
        for(Thread t:users)t.join();
        System.out.println("Seats sold: "+screen.bookingsMade);
    }
}
