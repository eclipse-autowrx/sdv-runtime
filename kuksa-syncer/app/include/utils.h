#pragma once

#include <string>
#include <vector>

namespace utils {

class StringProcessor {
public:
    StringProcessor();
    ~StringProcessor();
    
    std::string process(const std::string& input);
    std::vector<std::string> split(const std::string& input, char delimiter);
};

// Utility functions
std::string toUpperCase(const std::string& str);
std::string toLowerCase(const std::string& str);
bool startsWith(const std::string& str, const std::string& prefix);
bool endsWith(const std::string& str, const std::string& suffix);

} // namespace utils