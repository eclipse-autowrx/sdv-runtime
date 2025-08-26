#include "utils.h"
#include <algorithm>
#include <sstream>
#include <cctype>

namespace utils {

StringProcessor::StringProcessor() {}
StringProcessor::~StringProcessor() {}

std::string StringProcessor::process(const std::string& input) {
    std::string result = input;
    
    // Remove extra whitespace
    std::string::iterator new_end = std::unique(result.begin(), result.end(),
        [](char a, char b) { return a == ' ' && b == ' '; });
    result.erase(new_end, result.end());
    
    // Trim leading/trailing whitespace
    result.erase(0, result.find_first_not_of(" \t\n\r"));
    result.erase(result.find_last_not_of(" \t\n\r") + 1);
    
    return result;
}

std::vector<std::string> StringProcessor::split(const std::string& input, char delimiter) {
    std::vector<std::string> tokens;
    std::stringstream ss(input);
    std::string token;
    
    while (std::getline(ss, token, delimiter)) {
        if (!token.empty()) {
            tokens.push_back(token);
        }
    }
    
    return tokens;
}

std::string toUpperCase(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

std::string toLowerCase(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

bool startsWith(const std::string& str, const std::string& prefix) {
    if (prefix.length() > str.length()) return false;
    return str.compare(0, prefix.length(), prefix) == 0;
}

bool endsWith(const std::string& str, const std::string& suffix) {
    if (suffix.length() > str.length()) return false;
    return str.compare(str.length() - suffix.length(), suffix.length(), suffix) == 0;
}

} // namespace utils