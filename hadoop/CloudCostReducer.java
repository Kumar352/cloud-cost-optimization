import java.io.IOException;

import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

public class CloudCostReducer
        extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {

    private final DoubleWritable result =
            new DoubleWritable();

    @Override
    public void reduce(
            Text key,
            Iterable<DoubleWritable> values,
            Context context)
            throws IOException, InterruptedException {

        double total = 0.0;

        for (DoubleWritable value : values) {
            total += value.get();
        }

        total = Math.round(total * 100.0) / 100.0;

        result.set(total);

        context.write(key, result);
    }
}