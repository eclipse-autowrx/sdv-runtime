#include <iostream>

// Missing closing brace will cause syntax error
class BrokenClass {
public:
    void method() {
        std::cout << "This has syntax errors" << std::endl;
    // Missing closing brace for method
    
// Missing closing brace for class

int main() {
    // This won't compile due to above errors
    BrokenClass obj;
    obj.method();
    return 0;
}