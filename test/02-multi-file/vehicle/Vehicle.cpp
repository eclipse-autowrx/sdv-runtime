#include "Vehicle.h"
#include "../utils/Logger.h"
#include <iostream>

Vehicle::Vehicle(const std::string& id, const std::string& type) 
    : id(id), type(type), speed(0), isRunning(false) {
    Logger::log("Vehicle " + id + " created (" + type + ")");
}

void Vehicle::start() {
    isRunning = true;
    Logger::log("Vehicle " + id + " started");
}

void Vehicle::stop() {
    isRunning = false;
    speed = 0;
    Logger::log("Vehicle " + id + " stopped");
}

void Vehicle::accelerate(int targetSpeed) {
    if (isRunning) {
        speed = targetSpeed;
        Logger::log("Vehicle " + id + " accelerated to " + std::to_string(speed) + " km/h");
    }
}

void Vehicle::displayInfo() const {
    std::cout << "=== Vehicle Info ===" << std::endl;
    std::cout << "ID: " << id << std::endl;
    std::cout << "Type: " << type << std::endl;
    std::cout << "Speed: " << speed << " km/h" << std::endl;
    std::cout << "Running: " << (isRunning ? "Yes" : "No") << std::endl;
}