using Microsoft.ML.OnnxRuntime;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using utility;
namespace my_yolo_detect_C_
{
    public partial class Form1 : Form
    {
        myinclude my = new myinclude();
        string PD = "";
        public Form1()
        {
            OrtEnv.Instance(); // ✅ 初始化 Logger 與 ORT 環境
            InitializeComponent();
            PD = my.pwd();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

            var modelPath = PD + "\\yolo11n.onnx";
            var imagePath = PD + "\\test.png";


            my.myC("modelPath: " + modelPath);

            var detector = new YoloOnnxDetector(modelPath);
            var result = detector.Predict(imagePath);

            Console.WriteLine($"模型輸出維度: {result.GetLength(0)} x {result.GetLength(1)} x {result.GetLength(2)}");
            Console.WriteLine($"第1筆輸出第1類別信心值: {result[0, 0, 4]}");  // 可自定列印項目
                    
            var detections = detector.ParseYoloV8Output(result, numClasses: 79, confThreshold: 0.3f);
            foreach (var d in detections.Take(10))
            {
                Console.WriteLine(d);
            }
            // 載入原始圖片
            var bitmap = new Bitmap(imagePath);
            using (Graphics g = Graphics.FromImage(bitmap))
            {
                foreach (var det in detections)
                {
                    DrawBox(g, det, bitmap.Width, bitmap.Height);
                }
            }
            pictureBox1.SizeMode = PictureBoxSizeMode.Zoom;
            pictureBox1.Image = bitmap;
        }
        private void DrawBox(Graphics g, YoloOnnxDetector.YoloDetection det, int imageW, int imageH)
        {
            // 還原預測框 (0~640) → 真實圖片尺寸
            float scaleX = imageW / 640f;
            float scaleY = imageH / 640f;

            float x = (det.X - det.Width / 2) * scaleX;
            float y = (det.Y - det.Height / 2) * scaleY;
            float w = det.Width * scaleX;
            float h = det.Height * scaleY;

            var pen = new Pen(Color.Red, 2);
            g.DrawRectangle(pen, x, y, w, h);

            var font = new Font("Arial", 12);
            string label = $"Class {det.ClassId}: {det.Confidence:P1}";
            g.DrawString(label, font, Brushes.Yellow, x, y - 20);
        }
    }
}
