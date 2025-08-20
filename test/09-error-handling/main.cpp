#include <iostream>
#include "missing_header.h"  // This header doesn't exist - will cause error

int main() {
    // This code should never execute due to compilation error
    UndefinedClass obj;  // Using undefined class
    obj.nonexistentMethod();
    
    std::cout << "This should not print" << std::endl;
    return 0;
}