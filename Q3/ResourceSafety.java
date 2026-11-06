import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ResourceSafety {
    static int open;
    static final List<TrackedReader> leaked = new ArrayList<>();
    static final class TrackedReader extends BufferedReader {
        boolean closed;
        TrackedReader(Path path) throws IOException { super(Files.newBufferedReader(path)); open++; }
        @Override public void close() throws IOException {
            if (!closed) { try { super.close(); } finally { closed=true; open--; } }
        }
    }
    static int read(BufferedReader reader, Path file) throws IOException {
        String line; int sum=0;
        while ((line=reader.readLine()) != null) {
            try { sum+=Integer.parseInt(line); }
            catch (NumberFormatException e) { throw new IOException("Bad sales row in " + file, e); }
        }
        return sum;
    }
    static String generate(List<Path> inputs, String mode, Path target) throws IOException {
        Path temporary = Path.of(target + ".tmp");
        try {
            if (mode.equals("twr")) {
                try (BufferedWriter writer=Files.newBufferedWriter(temporary)) {
                    for (Path file:inputs) {
                        System.out.println("READ " + mode + " " + file);
                        try (TrackedReader reader=new TrackedReader(file)) {
                            writer.write(file.getFileName()+":"+read(reader,file)); writer.newLine();
                        }
                    }
                }
            } else {
                BufferedWriter writer=null;
                try {
                    writer=Files.newBufferedWriter(temporary);
                    for (Path file:inputs) {
                        System.out.println("READ " + mode + " " + file);
                        TrackedReader reader=new TrackedReader(file);
                        if (mode.equals("manual_bad")) {
                            leaked.add(reader);
                            int total=read(reader,file); // debugger leak checkpoint
                            reader.close();
                            writer.write(file.getFileName()+":"+total); writer.newLine();
                        } else {
                            try { writer.write(file.getFileName()+":"+read(reader,file)); writer.newLine(); }
                            finally { reader.close(); }
                        }
                    }
                } finally { if (writer != null) writer.close(); }
            }
            Files.move(temporary,target,StandardCopyOption.REPLACE_EXISTING);
            return Files.readString(target);
        } catch (IOException e) { Files.deleteIfExists(temporary); throw e; }
    }
    static final class FailingClose implements AutoCloseable {
        final String name;
        FailingClose(String name) { this.name=name; }
        public void close() throws IOException { throw new IOException("close "+name); }
    }
    public static void main(String[] args) throws Exception {
        List<Path> good=List.of(Path.of("inputs/storeA.txt"),Path.of("inputs/storeB.txt"));
        List<Path> failing=List.of(good.get(0),Path.of("inputs/storeBad.txt"));
        Path target=Path.of("results/summary.txt");
        String a=generate(good,"manual_fixed",target), b=generate(good,"twr",target);
        if (!a.equals(b)||open!=0) throw new AssertionError("Different successful reports");
        System.out.println("REPORT MATCH: " + a.replace('\n','|'));
        for (String mode:List.of("manual_bad","manual_fixed","twr")) {
            try { generate(failing,mode,target); throw new AssertionError("Bad file accepted"); }
            catch (IOException e) {
                System.out.println("FAILURE " + mode + ": " + e.getMessage()+"; open_readers="+open);
                int expected=mode.equals("manual_bad")?1:0;
                if (open!=expected) throw new AssertionError("Resource count");
                if (!Files.readString(target).equals(a)) throw new AssertionError("Partial report published");
            }
            for (TrackedReader reader:leaked) reader.close();
            leaked.clear();
        }
        try (FailingClose first=new FailingClose("A"); FailingClose second=new FailingClose("B")) {
            throw new IOException("processing failed");
        } catch (IOException e) {
            System.out.println("PRIMARY: "+e.getMessage());
            for (Throwable suppressed:e.getSuppressed()) System.out.println("SUPPRESSED: "+suppressed.getMessage());
            if (e.getSuppressed().length!=2 || !e.getSuppressed()[0].getMessage().equals("close B"))
                throw new AssertionError("Suppression/close order");
        }
        System.out.println("PASS: identical reports; leaks bad=1 fixed=0 twr=0; previous summary preserved");
    }
}
