#pragma once
#include <string>
#include <iostream>

class Vehicle {
private:
    std::string id;
    std::string type;
    double batteryLevel;
    double speed;
    bool engineRunning;

public:
    Vehicle(const std::string& vehicleId, const std::string& vehicleType, double initialBattery);
    
    void startEngine();
    void stopEngine();
    void accelerate(double targetSpeed);
    void updateBattery(double newLevel);
    void displayInfo() const;
    void displayStatus() const;
    
    // Getters
    const std::string& getId() const { return id; }
    double getSpeed() const { return speed; }
    double getBatteryLevel() const { return batteryLevel; }
    bool isEngineRunning() const { return engineRunning; }
};