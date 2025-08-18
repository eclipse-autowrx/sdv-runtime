#pragma once
#include <string>

class Logger {
public:
    static void log(const std::string& message);
    static void error(const std::string& message);
};