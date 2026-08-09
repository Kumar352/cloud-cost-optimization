import java.io.IOException;

import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

public class CloudCostMapper
        extends Mapper<Object, Text, Text, DoubleWritable> {

    private final Text outputKey = new Text();

    private final DoubleWritable outputValue =
            new DoubleWritable();

    @Override
    public void map(
            Object key,
            Text value,
            Context context)
            throws IOException, InterruptedException {

        String line = value.toString().trim();

        // Skip CSV header
        if (line.startsWith("Account_ID,")) {
            return;
        }

        // Skip empty lines
        if (line.isEmpty()) {
            return;
        }

        String[] fields = line.split(",", -1);

        /*
         * CSV structure:
         *
         * 0 = Account_ID
         * 1 = Cloud_Provider
         * 2 = Service
         * 3 = Region
         * 4 = Usage_Date
         * 5 = Usage_Hours
         * 6 = Data_Transfer_GB
         * 7 = Storage_GB
         * 8 = Monthly_Cost
         */

        if (fields.length < 9) {
            return;
        }

        String provider = fields[1].trim();
        String service = fields[2].trim();
        String region = fields[3].trim();

        double monthlyCost;

        try {

            monthlyCost =
                    Double.parseDouble(
                            fields[8].trim());

        } catch (NumberFormatException e) {

            return;
        }

        /*
         * Provider aggregation
         */

        outputKey.set(
                "PROVIDER|" + provider);

        outputValue.set(
                monthlyCost);

        context.write(
                outputKey,
                outputValue);

        /*
         * Service aggregation
         */

        outputKey.set(
                "SERVICE|" + service);

        context.write(
                outputKey,
                outputValue);

        /*
         * Region aggregation
         */

        outputKey.set(
                "REGION|" + region);

        context.write(
                outputKey,
                outputValue);
    }
}