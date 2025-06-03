using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;
using SixLabors.ImageSharp.Processing;
using System;
using System.Collections.Generic;
using System.Linq;

public class YoloOnnxDetector
{
    private InferenceSession _session;
    private int _inputWidth = 640;
    private int _inputHeight = 640;

    public YoloOnnxDetector(string onnxPath)
    {
        var opts = new SessionOptions();
        opts.AppendExecutionProvider_CUDA(); // ← 用 CUDA
        _session = new InferenceSession(onnxPath, opts);
    }

    public float[,,] Predict(string imagePath)
    {
        var image = Image.Load<Rgb24>(imagePath);
        image.Mutate(x => x.Resize(_inputWidth, _inputHeight));
        var input = new DenseTensor<float>(new[] { 1, 3, _inputHeight, _inputWidth });

        for (int y = 0; y < _inputHeight; y++)
        {
            for (int x = 0; x < _inputWidth; x++)
            {
                var pixel = image[x, y];
                input[0, 0, y, x] = pixel.R / 255f;
                input[0, 1, y, x] = pixel.G / 255f;
                input[0, 2, y, x] = pixel.B / 255f;
            }
        }

        var inputs = new List<NamedOnnxValue>
        {
            NamedOnnxValue.CreateFromTensor("images", input)
        };

        var results = _session.Run(inputs);
        var output = results.First().AsTensor<float>();

        /*var outputData = new float[dims[0], dims[1], dims[2]];

        var e = output.GetEnumerator();
        for (int i = 0; i < dims[0]; i++)
            for (int j = 0; j < dims[1]; j++)
                for (int k = 0; k < dims[2]; k++)
                {
                    e.MoveNext();
                    outputData[i, j, k] = e.Current;
                }
        */
        var outputArray = output.ToArray(); // 一維陣列，flatten
        var dims = output.Dimensions.ToArray(); // e.g. [1, 84, 8400]
        var outputData = new float[dims[0], dims[1], dims[2]];

        int index = 0;
        for (int i = 0; i < dims[0]; i++)
        {
            for (int j = 0; j < dims[1]; j++)
            {
                for (int k = 0; k < dims[2]; k++)
                {
                    outputData[i, j, k] = outputArray[index++];
                }
            }
        }
        return outputData;
    }

    public class YoloDetection
    {
        public int ClassId { get; set; }
        public float Confidence { get; set; }
        public float X { get; set; }  // 中心 X
        public float Y { get; set; }  // 中心 Y
        public float Width { get; set; }
        public float Height { get; set; }

        public override string ToString() =>
            $"Class: {ClassId}, Conf: {Confidence:F2}, X:{X:F1}, Y:{Y:F1}, W:{Width:F1}, H:{Height:F1}";
    }

    public List<YoloDetection> ParseYoloV8Output(float[,,] output, int numClasses = 79, float confThreshold = 0.25f)
    {
        var results = new List<YoloDetection>();

        int channels = output.GetLength(1); // 84
        int boxes = output.GetLength(2);    // 8400

        for (int i = 0; i < boxes; i++)
        {
            float x = output[0, 0, i];
            float y = output[0, 1, i];
            float w = output[0, 2, i];
            float h = output[0, 3, i];
            float objectness = Sigmoid(output[0, 4, i]);

            for (int cls = 0; cls < numClasses; cls++)
            {
                float classProb = Sigmoid(output[0, 5 + cls, i]);
                float conf = objectness * classProb;

                if (conf > confThreshold)
                {
                    results.Add(new YoloDetection
                    {
                        ClassId = cls,
                        Confidence = conf,
                        X = x,
                        Y = y,
                        Width = w,
                        Height = h
                    });
                }
            }
        }

        return results.OrderByDescending(d => d.Confidence).ToList();
    }

    private static float Sigmoid(float x) => 1f / (1f + (float)Math.Exp(-x));


}