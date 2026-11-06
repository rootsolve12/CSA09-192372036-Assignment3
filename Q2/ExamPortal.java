import java.io.*;
import java.nio.file.*;

public class ExamPortal {
    static class ExamException extends Exception {
        ExamException(String message) { super(message); }
        ExamException(String message, Throwable cause) { super(message, cause); }
    }
    static final class WindowClosed extends ExamException {
        WindowClosed() { super("Exam window closed"); }
    }
    static final class NotRegistered extends ExamException {
        NotRegistered() { super("Student not registered"); }
    }
    static final class FileTooLarge extends ExamException {
        FileTooLarge() { super("Answer exceeds 500 KiB limit"); }
    }
    static final class SubmissionStorageException extends ExamException {
        SubmissionStorageException(String message, Throwable cause) { super(message, cause); }
    }
    static void storage(Path file) throws SubmissionStorageException {
        try { Files.readAllBytes(file); }
        catch (IOException e) { throw new SubmissionStorageException("Submission could not be stored", e); }
    }
    static void service(boolean registered, long sizeKb, Path file) throws ExamException {
        if (sizeKb < 0) throw new IllegalArgumentException("Negative file metadata");
        if (!registered) throw new NotRegistered();
        if (sizeKb > 500) throw new FileTooLarge();
        storage(file);
    }
    static String controller(boolean open, boolean registered, long sizeKb, Path file) {
        try {
            if (!open) throw new WindowClosed();
            service(registered, sizeKb, file);
            return "ACCEPTED";
        } catch (ExamException e) {
            System.out.println("STUDENT MESSAGE: " + e.getMessage());
            if (e.getCause() != null) {
                System.out.println("getCause(): " + e.getCause().getClass().getSimpleName());
                e.printStackTrace(System.out);
            }
            return e.getClass().getSimpleName();
        }
    }
    public static void main(String[] args) throws ExamException {
        Path good = Path.of("inputs/answer.txt"), missing = Path.of("inputs/missing.txt");
        String[] observed = {
            controller(true,true,120,good), controller(false,true,120,good),
            controller(true,false,120,good), controller(true,true,800,good),
            controller(true,true,120,missing)
        };
        String[] expected = {"ACCEPTED","WindowClosed","NotRegistered","FileTooLarge","SubmissionStorageException"};
        for (int i=0;i<expected.length;i++) {
            System.out.println("CASE " + i + ": " + observed[i]);
            if (!expected[i].equals(observed[i])) throw new AssertionError("Portal case " + i);
        }
        try { service(true,-1,good); throw new AssertionError("Negative metadata accepted"); }
        catch (IllegalArgumentException expectedBug) { System.out.println("Unchecked metadata bug rejected"); }
        ExamException withoutCause = new ExamException("Storage failed without preserved cause");
        System.out.println("Cause lost on rethrow: " + withoutCause.getCause());
        try { System.out.println(withoutCause.getCause().getMessage()); }
        catch (NullPointerException e) { System.out.println("Unchanged Cause print would throw NullPointerException"); }
        System.out.println("PASS: portal rules, layered propagation and cause preservation");
    }
}
