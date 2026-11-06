public class UncaughtTrace {
    static int parseAccount(String value) { return Integer.parseInt(value); }
    static void service() { parseAccount("not-an-account"); }
    public static void main(String[] args) { service(); }
}
