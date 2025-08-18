#include <iostream>
#include <vector>
#include <chrono>
#include <cmath>

// Simple automotive example for testing
class VehicleSimulator {
private:
    double speed_kmh;
    double distance_m;
    std::vector<double> sensor_readings;
    
public:
    VehicleSimulator() : speed_kmh(0), distance_m(0) {}
    
    void updateSpeed(double new_speed) {
        speed_kmh = new_speed;
        std::cout << "Speed updated to: " << speed_kmh << " km/h" << std::endl;
    }
    
    void addSensorReading(double reading) {
        sensor_readings.push_back(reading);
        std::cout << "Sensor reading added: " << reading << " m" << std::endl;
    }
    
    double calculateTTC() {
        if (sensor_readings.empty() || speed_kmh <= 0) return -1;
        
        double avg_distance = 0;
        for (auto reading : sensor_readings) {
            avg_distance += reading;
        }
        avg_distance /= sensor_readings.size();
        
        double speed_ms = speed_kmh / 3.6; // Convert to m/s
        return avg_distance / speed_ms;
    }
    
    void displayStatus() {
        std::cout << "\n=== Vehicle Status ===" << std::endl;
        std::cout << "Speed: " << speed_kmh << " km/h" << std::endl;
        std::cout << "Sensor readings: " << sensor_readings.size() << std::endl;
        
        double ttc = calculateTTC();
        if (ttc > 0) {
            std::cout << "Time to Collision: " << ttc << " seconds" << std::endl;
            if (ttc < 3.0) {
                std::cout << "⚠️  WARNING: Collision risk!" << std::endl;
            }
        }
        std::cout << "===================" << std::endl;
    }
};

int main() {
    std::cout << "=== Simple Automotive C++ Test ===" << std::endl;
    
    VehicleSimulator vehicle;
    
    // Simulate vehicle movement
    vehicle.updateSpeed(60);
    vehicle.addSensorReading(50.0);
    vehicle.addSensorReading(45.0);
    vehicle.addSensorReading(40.0);
    
    vehicle.displayStatus();
    
    // Test collision scenario
    vehicle.updateSpeed(80);
    vehicle.addSensorReading(30.0);
    vehicle.addSensorReading(25.0);
    
    vehicle.displayStatus();
    
    std::cout << "\n✅ Automotive simulation completed!" << std::endl;
    return 0;
}