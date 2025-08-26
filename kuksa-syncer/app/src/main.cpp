#include <iostream>
#include <memory>
#include "utils.h"
#include "calculator.h"

int main(int argc, char* argv[]) {
    try {
        std::cout << "C++ Project Starting..." << std::endl;
        
        utils::StringProcessor processor;
        Calculator calc;
        
        // Process command line arguments
        if (argc > 1) {
            std::string input = argv[1];
            std::string result = processor.process(input);
            std::cout << "Processed: " << result << std::endl;
            
            auto parts = processor.split(result, ' ');
            std::cout << "Split into " << parts.size() << " parts" << std::endl;
        }
        
        // Test calculator
        double result = calc.add(10.0, 20.0);
        std::cout << "10 + 20 = " << result << std::endl;
        
        std::cout << "Application completed successfully!" << std::endl;
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}