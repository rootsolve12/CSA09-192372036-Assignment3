import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ATM {
    static class InsufficientFundsException extends Exception {
        InsufficientFundsException(String message) { super(message); }
    }
    static String withdraw(String input, Path card) {
        String outcome;
        try (Scanner scanner = new Scanner(input)) {
            long account = Long.parseLong(scanner.next());
            double amount = scanner.nextDouble();
            if (account <= 0 || !Double.isFinite(amount) || amount <= 0)
                throw new IllegalArgumentException("Positive account and finite amount required");
            try (BufferedReader reader = Files.newBufferedReader(card)) {
                if (!Long.toString(account).equals(reader.readLine()))
                    throw new SecurityException("Card does not match account");
            }
            if (amount > 1000) throw new InsufficientFundsException("Balance is 1000.00");
            outcome = "SUCCESS: dispensed " + amount;
        } catch (NumberFormatException | InputMismatchException e) {
            outcome = "INPUT_CATCH: " + e.getClass().getSimpleName();
        } catch (IllegalArgumentException e) {
            outcome = "VALIDATION_CATCH: " + e.getMessage();
        } catch (SecurityException e) {
            outcome = "SECURITY_CATCH: " + e.getMessage();
        } catch (InsufficientFundsException e) {
            outcome = "FUNDS_CATCH: " + e.getMessage();
        } catch (IOException e) {
            outcome = "IO_CATCH: " + e.getClass().getSimpleName();
        } finally {
            System.out.println("FINALLY: withdrawal attempt finished");
        }
        return outcome;
    }
    // Expected input failures can instead be represented explicitly.
    static int validateWithoutThrowing(String input) {
        try (Scanner scanner = new Scanner(input)) {
            if (!scanner.hasNextLong()) return -1;
            if (scanner.nextLong() <= 0) return -2;
            if (!scanner.hasNextDouble()) return -3;
            double amount = scanner.nextDouble();
            if (!Double.isFinite(amount) || amount <= 0) return -4;
            if (amount > 1000) return -5;
            return 0;
        }
    }
    public static void main(String[] args) throws IOException {
        Path inputs = Path.of("inputs");
        String[][] cases = {
            {"valid", "192372036 200", "SUCCESS"},
            {"letters_account", "abc 200", "INPUT_CATCH"},
            {"letters_amount", "192372036 abc", "INPUT_CATCH"},
            {"negative", "192372036 -1", "VALIDATION_CATCH"},
            {"over_balance", "192372036 1001", "FUNDS_CATCH"},
            {"missing_card", "192372036 20", "IO_CATCH"},
            {"wrong_card", "999 20", "SECURITY_CATCH"},
            {"not_finite", "192372036 NaN", "VALIDATION_CATCH"}
        };
        for (String[] test : cases) {
            System.out.println("CASE " + test[0]);
            String result = withdraw(test[1], inputs.resolve(
                    test[0].equals("missing_card") ? "missing.txt" : "card.txt"));
            System.out.println(result);
            if (!result.startsWith(test[2])) throw new AssertionError(test[0]);
        }
        if (validateWithoutThrowing("abc 1") != -1 || validateWithoutThrowing("1 20") != 0)
            throw new AssertionError("Error-code alternative");
        System.out.println("PASS: eight failure/success paths; finally runs for every attempt");
    }
}
