cmake_minimum_required(VERSION 3.10)
project(ImageCollageViewer)

set(CMAKE_CXX_STANDARD 17)

find_package(OpenCV REQUIRED)

add_executable(ImageCollageViewer main.cpp)
target_link_libraries(ImageCollageViewer ${OpenCV_LIBS})