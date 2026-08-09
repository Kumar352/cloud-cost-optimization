import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;

import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;

import org.apache.hadoop.mapreduce.Job;

import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

public class CloudCostDriver extends Configured implements Tool {

    @Override
    public int run(String[] args) throws Exception {

        if (args.length != 2) {

            System.err.println(
                    "Usage: CloudCostDriver <input> <output>");

            return 2;
        }

        Configuration configuration =
                getConf();

        Job job =
                Job.getInstance(
                        configuration,
                        "Cloud Cost Optimization Analysis");

        job.setJarByClass(
                CloudCostDriver.class);

        // Mapper
        job.setMapperClass(
                CloudCostMapper.class);

        // Reducer
        job.setReducerClass(
                CloudCostReducer.class);

        // Mapper output types
        job.setMapOutputKeyClass(
                Text.class);

        job.setMapOutputValueClass(
                DoubleWritable.class);

        // Final output types
        job.setOutputKeyClass(
                Text.class);

        job.setOutputValueClass(
                DoubleWritable.class);

        // HDFS input
        FileInputFormat.addInputPath(
                job,
                new Path(args[0]));

        // HDFS output
        FileOutputFormat.setOutputPath(
                job,
                new Path(args[1]));

        return job.waitForCompletion(true)
                ? 0
                : 1;
    }

    public static void main(
            String[] args)
            throws Exception {

        int result =
                ToolRunner.run(
                        new Configuration(),
                        new CloudCostDriver(),
                        args);

        System.exit(result);
    }
}