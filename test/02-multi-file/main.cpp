#include "vehicle/Vehicle.h"
#include "utils/Logger.h"
#include <iostream>

int main() {
    Logger::log("Starting Multi-File C++ Test");
    
    // Create and test vehicle
    Vehicle car("SDV-001", "Electric");
    car.start();
    car.accelerate(50);
    car.displayInfo();
    car.stop();
    
    Logger::log("Multi-File Test Completed Successfully");
    return 0;
}