#include "Logger.h"
#include <iostream>
#include <chrono>
#include <iomanip>

void Logger::log(const std::string& message) {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    std::cout << "[INFO] " << std::put_time(std::localtime(&time_t), "%H:%M:%S") 
              << " " << message << std::endl;
}

void Logger::error(const std::string& message) {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    std::cout << "[ERROR] " << std::put_time(std::localtime(&time_t), "%H:%M:%S") 
              << " " << message << std::endl;
}