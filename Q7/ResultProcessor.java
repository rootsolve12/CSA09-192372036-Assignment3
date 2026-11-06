import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

public class ResultProcessor {
    record Outcome(String id,boolean success,int score,String detail) {}
    static final class ScoreException extends Exception {ScoreException(String message){super(message);}}
    static Outcome compute(Path path) throws IOException,ScoreException {
        try(BufferedReader reader=Files.newBufferedReader(path)) {
            String text=reader.readLine();int score;
            try{score=Integer.parseInt(text);}catch(NumberFormatException e){throw new ScoreException("Invalid numeric score");}
            if(score<0||score>100)throw new ScoreException("Score outside 0..100");
            return new Outcome(path.getFileName().toString(),true,score,score>=50?"PASS":"FAIL_GRADE");
        }
    }
    static Map<String,Outcome> process(List<Path> files,int workers) throws InterruptedException {
        ExecutorService pool=Executors.newFixedThreadPool(workers);
        ConcurrentHashMap<String,Outcome> results=new ConcurrentHashMap<>();
        List<Future<Outcome>> futures=new ArrayList<>();
        Set<String> ids=new HashSet<>();
        for(Path file:files)if(!ids.add(file.getFileName().toString()))throw new IllegalArgumentException("Duplicate file identity");
        try {
            for(Path file:files)futures.add(pool.submit((Callable<Outcome>)()->{
                Outcome result;
                try{result=compute(file);}
                catch(IOException|ScoreException e){result=new Outcome(file.getFileName().toString(),false,-1,e.getClass().getSimpleName()+": "+e.getMessage());}
                results.put(result.id(),result);return result;
            }));
            for(int i=0;i<futures.size();i++) {
                try{futures.get(i).get();}
                catch(ExecutionException e){Path file=files.get(i);Throwable cause=e.getCause();
                    if(cause instanceof Error)throw (Error)cause;
                    results.put(file.getFileName().toString(),new Outcome(file.getFileName().toString(),false,-1,"Unexpected "+cause.getClass().getSimpleName()));}
            }
            if(results.size()!=files.size())throw new AssertionError("Incomplete summary");
            return results;
        } finally {
            pool.shutdown();
            if(!pool.awaitTermination(10,TimeUnit.SECONDS)){pool.shutdownNow();if(!pool.awaitTermination(10,TimeUnit.SECONDS))throw new IllegalStateException("Workers did not terminate");}
        }
    }
    static List<Path> dataset(Path dir,int n) throws IOException {
        Files.createDirectories(dir);List<Path> files=new ArrayList<>();
        for(int i=0;i<n;i++){
            Path path=dir.resolve(String.format(Locale.ROOT,"score%05d.txt",i));files.add(path);
            if(i%100==0){Files.deleteIfExists(path);continue;}
            Files.writeString(path,i%100==1?"CORRUPT":i%100==2?"110":Integer.toString(i%101));
        }
        return files;
    }
    static long successes(Map<String,Outcome> values){return values.values().stream().filter(Outcome::success).count();}
    static void writeOutcomes(Map<String,Outcome> values) throws IOException {
        List<String> rows=new ArrayList<>();rows.add("file,status,score,detail");
        values.values().stream().sorted(Comparator.comparing(Outcome::id)).forEach(r->rows.add(
                r.id()+","+(r.success()?"SUCCESS":"FAILURE")+","+r.score()+","+r.detail().replace(',',';')));
        Files.write(Path.of("results/outcomes.csv"),rows);
    }
    public static void main(String[] args) throws Exception {
        List<Path> small=List.of(Path.of("inputs/valid80.txt"),Path.of("inputs/valid0.txt"),
            Path.of("inputs/corrupt.txt"),Path.of("inputs/range.txt"),Path.of("inputs/missing.txt"));
        Map<String,Outcome> checked=process(small,2);
        if(successes(checked)!=2||checked.size()!=5)throw new AssertionError("Hand counts");
        System.out.println("HAND_CHECK total=5,success=2,failure=3");
        List<Path> files=dataset(Path.of("generated"),10000);
        System.out.println("kind,pool,run,files,elapsed_ns,success,failure");
        Map<Integer,Double> means=new LinkedHashMap<>();
        for(int workers:new int[]{1,2,4,8}) {
            process(files,workers);long total=0;
            for(int run=1;run<=5;run++) {
                long start=System.nanoTime();Map<String,Outcome> results=process(files,workers);
                long elapsed=System.nanoTime()-start;long success=successes(results);
                if(results.size()!=10000||success!=9700)throw new AssertionError("Injected-failure counts");
                total+=elapsed;
                System.out.println("RAW,"+workers+","+run+",10000,"+elapsed+","+success+","+(10000-success));
                if(workers==1&&run==1)writeOutcomes(results);
            }
            means.put(workers,total/5.0);
            System.out.println("MEAN,"+workers+",0,10000,"+(total/5.0)+",9700,300");
        }
        int best=means.entrySet().stream().min(Map.Entry.comparingByValue()).orElseThrow().getKey();
        System.out.println("RECOMMEND_FOR_THIS_RUN pool="+best+"; based on lowest five-run mean, not a universal optimum");
        System.out.println("PASS: all pools complete 10000 files; 9700 successes and 300 isolated failures; hand set verified");
    }
}
