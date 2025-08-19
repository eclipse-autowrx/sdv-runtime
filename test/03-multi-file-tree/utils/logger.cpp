#include "logger.h"

void Logger::info(const std::string& message) {
    std::cout << "[INFO] " << message << std::endl;
}

void Logger::error(const std::string& message) {
    std::cout << "[ERROR] " << message << std::endl;
}