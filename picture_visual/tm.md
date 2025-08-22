```c
#include <iostream>
#include <filesystem>
#include <vector>
#include <opencv2/opencv.hpp>

namespace fs = std::filesystem;

// 显示程序标题
void displayHeader(cv::Mat& canvas, int width) {
    std::string title = "Image Viewer";
    cv::rectangle(canvas, cv::Point(0, 0), cv::Point(width, 60), cv::Scalar(30, 30, 50), cv::FILLED);
    
    int baseline = 0;
    cv::Size textSize = cv::getTextSize(title, cv::FONT_HERSHEY_DUPLEX, 1.5, 3, &baseline);
    cv::Point textOrg((width - textSize.width) / 2, 45);
    
    cv::putText(canvas, title, textOrg, cv::FONT_HERSHEY_DUPLEX, 1.5, cv::Scalar(255, 215, 0), 3);
}

// 显示目录信息和图片计数
void displayDirectoryInfo(cv::Mat& canvas, const std::string& dir, int imgCount, int width) {
    std::string info = "Directory: " + dir + " - " + std::to_string(imgCount) + " images found";
    
    // 裁剪过长的路径
    if (info.length() > 80) {
        info = "Directory: ..." + info.substr(info.length() - 77);
    }
    
    cv::putText(canvas, info, cv::Point(20, 90), 
                cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(220, 220, 220), 1);
    
    // 绘制分割线
    cv::line(canvas, cv::Point(0, 100), cv::Point(width, 100), cv::Scalar(60, 60, 80), 2);
}

// 显示操作说明
void displayInstructions(cv::Mat& canvas, int width, int height) {
    std::string instructions = "Press ESC to exit | SPACE to reload | + to zoom in | - to zoom out";
    cv::rectangle(canvas, cv::Point(0, height - 40), cv::Point(width, height), cv::Scalar(30, 30, 50), cv::FILLED);
    cv::putText(canvas, instructions, cv::Point(20, height - 10), 
                cv::FONT_HERSHEY_SIMPLEX, 0.55, cv::Scalar(200, 200, 100), 1);
}

// 拼接图片
cv::Mat createCollage(const std::vector<cv::Mat>& images, int imagesPerRow, int thumbWidth, int thumbHeight) {
    if (images.empty()) {
        return cv::Mat::zeros(500, 800, CV_8UC3);
    }

    // 计算网格大小
    int numRows = (images.size() + imagesPerRow - 1) / imagesPerRow;
    
    // 创建画布
    cv::Mat collage = cv::Mat::zeros(
        numRows * thumbHeight, 
        imagesPerRow * thumbWidth, 
        CV_8UC3
    );

    // 填充背景
    collage.setTo(cv::Scalar(45, 45, 55));

    int index = 0;
    for (int i = 0; i < numRows; i++) {
        for (int j = 0; j < imagesPerRow; j++) {
            if (index >= images.size()) break;

            // 调整图片大小
            cv::Mat thumb;
            cv::resize(images[index], thumb, cv::Size(thumbWidth, thumbHeight));
            
            // 创建带边框的缩略图
            cv::Mat borderedThumb = cv::Mat::zeros(thumb.rows + 10, thumb.cols + 10, CV_8UC3);
            borderedThumb.setTo(cv::Scalar(30, 30, 40));
            thumb.copyTo(borderedThumb(cv::Rect(5, 5, thumb.cols, thumb.rows)));
            
            // 添加图片名称
            std::string filename = fs::path(images[index++]).filename().string();
            if (filename.length() > 20) {
                filename = filename.substr(0, 17) + "...";
            }
            
            cv::putText(borderedThumb, filename, cv::Point(10, borderedThumb.rows - 10), 
                        cv::FONT_HERSHEY_SIMPLEX, 0.4, cv::Scalar(180, 180, 250), 1);
            
            // 添加到拼接图像
            borderedThumb.copyTo(
                collage(cv::Rect(
                    j * thumbWidth, 
                    i * thumbHeight, 
                    thumbWidth, 
                    thumbHeight
                ))
            );
        }
    }
    
    return collage;
}

int main() {
    // 设置图片目录（可修改为您的图片路径）
    std::string directory = "../images";
    
    // 默认参数
    int thumbWidth = 240;    // 缩略图宽度
    int thumbHeight = 180;   // 缩略图高度
    int imagesPerRow = 4;    // 每行图片数量
    double scale = 1.0;      // 缩放因子
    
    // 主循环
    while (true) {
        // 获取图片列表
        std::vector<cv::Mat> images;
        std::vector<std::string> imagePaths;
        
        for (const auto& entry : fs::directory_iterator(directory)) {
            if (fs::is_regular_file(entry.path())) {
                std::string ext = entry.path().extension().string();
                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                
                if (ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".bmp") {
                    cv::Mat img = cv::imread(entry.path().string());
                    if (!img.empty()) {
                        images.push_back(img);
                        imagePaths.push_back(entry.path().string());
                    }
                }
            }
        }

        // 创建拼接图像
        cv::Mat collage = createCollage(images, imagesPerRow, thumbWidth, thumbHeight);
        
        // 创建完整画布（包含标题和信息）
        int canvasWidth = std::max(800, collage.cols);
        int canvasHeight = collage.rows + 150; // 额外空间用于标题和信息
        
        cv::Mat canvas = cv::Mat::zeros(canvasHeight, canvasWidth, CV_8UC3);
        canvas.setTo(cv::Scalar(45, 45, 55));
        
        // 添加UI元素
        displayHeader(canvas, canvasWidth);
        displayDirectoryInfo(canvas, directory, images.size(), canvasWidth);
        displayInstructions(canvas, canvasWidth, canvasHeight);
        
        // 放置拼接图像
        collage.copyTo(canvas(cv::Rect(0, 110, collage.cols, collage.rows)));
        
        // 调整显示大小
        cv::Mat display;
        cv::resize(canvas, display, cv::Size(), scale, scale);
        
        // 显示图像
        cv::imshow("Image Viewer", display);
        
        // 处理键盘输入
        int key = cv::waitKey(0);
        
        // 退出
        if (key == 27) { // ESC
            break;
        }
        // 重新加载
        else if (key == 32) { // SPACE
            continue;
        }
        // 放大
        else if (key == '+' || key == '=') {
            scale *= 1.1;
        }
        // 缩小
        else if (key == '-' || key == '_') {
            scale *= 0.9;
            if (scale < 0.5) scale = 0.5;
        }
        // 每行显示更多图片
        else if (key == ']' || key == '}') {
            imagesPerRow++;
            if (imagesPerRow > 8) imagesPerRow = 8;
        }
        // 每行显示更少图片
        else if (key == '[' || key == '{') {
            imagesPerRow--;
            if (imagesPerRow < 1) imagesPerRow = 1;
        }
    }

    return 0;
}
```