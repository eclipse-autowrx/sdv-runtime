#include "vehicle.h"
#include <iomanip>

Vehicle::Vehicle(const std::string& vehicleId, const std::string& vehicleType, double initialBattery) 
    : id(vehicleId), type(vehicleType), batteryLevel(initialBattery), speed(0.0), engineRunning(false) {
}

void Vehicle::startEngine() {
    if (!engineRunning) {
        engineRunning = true;
        std::cout << "[" << id << "] Engine started" << std::endl;
    } else {
        std::cout << "[" << id << "] Engine already running" << std::endl;
    }
}

void Vehicle::stopEngine() {
    if (engineRunning) {
        engineRunning = false;
        speed = 0.0;
        std::cout << "[" << id << "] Engine stopped" << std::endl;
    } else {
        std::cout << "[" << id << "] Engine already stopped" << std::endl;
    }
}

void Vehicle::accelerate(double targetSpeed) {
    if (engineRunning) {
        speed = targetSpeed;
        std::cout << "[" << id << "] Accelerated to " << speed << " km/h" << std::endl;
        
        // Simulate battery consumption
        double consumption = speed * 0.1;
        batteryLevel -= consumption;
        if (batteryLevel < 0) batteryLevel = 0;
    } else {
        std::cout << "[" << id << "] Cannot accelerate - engine not running" << std::endl;
    }
}

void Vehicle::updateBattery(double newLevel) {
    batteryLevel = newLevel;
    std::cout << "[" << id << "] Battery updated to " << std::fixed << std::setprecision(1) 
              << batteryLevel << "%" << std::endl;
}

void Vehicle::displayInfo() const {
    std::cout << "\nVehicle Information:" << std::endl;
    std::cout << "  ID: " << id << std::endl;
    std::cout << "  Type: " << type << std::endl;
    std::cout << "  Initial Battery: " << std::fixed << std::setprecision(1) 
              << batteryLevel << "%" << std::endl;
}

void Vehicle::displayStatus() const {
    std::cout << "\nCurrent Status:" << std::endl;
    std::cout << "  Speed: " << speed << " km/h" << std::endl;
    std::cout << "  Battery: " << std::fixed << std::setprecision(1) 
              << batteryLevel << "%" << std::endl;
    std::cout << "  Engine: " << (engineRunning ? "Running" : "Stopped") << std::endl;
}