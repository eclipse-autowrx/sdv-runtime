#pragma once
#include <string>

class Vehicle {
private:
    std::string id;
    std::string type;
    int speed;
    bool isRunning;

public:
    Vehicle(const std::string& id, const std::string& type);
    
    void start();
    void stop();
    void accelerate(int targetSpeed);
    void displayInfo() const;
};