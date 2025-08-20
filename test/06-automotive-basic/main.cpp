#include <iostream>
#include "vehicle.h"

int main() {
    std::cout << "=== SDV Runtime Automotive Test ===" << std::endl;
    
    Vehicle car("SDV-001", "Electric", 85.0);
    
    car.displayInfo();
    car.startEngine();
    car.accelerate(60);
    car.updateBattery(78.5);
    car.displayStatus();
    car.stopEngine();
    
    std::cout << "=== Test Completed ===" << std::endl;
    return 0;
}