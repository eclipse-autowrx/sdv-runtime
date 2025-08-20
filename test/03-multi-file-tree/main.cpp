#include <iostream>
#include "math/calculator.h"
#include "utils/logger.h"

int main() {
    Logger::info("Multi-file project starting");
    
    Calculator calc;
    int result = calc.add(10, 5);
    
    std::cout << "10 + 5 = " << result << std::endl;
    
    Logger::info("Multi-file project completed");
    return 0;
}