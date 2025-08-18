#ifndef FCW_TYPES_H
#define FCW_TYPES_H

#include <string>
#include <chrono>
#include <iomanip>
#include <sstream>

// FCW System Configuration
#define FCW_VERSION "1.0.0-sdv-runtime-demo"
#define WARNING_TTC_THRESHOLD 3.0    // seconds
#define CRITICAL_TTC_THRESHOLD 1.5   // seconds  
#define MAX_DETECTION_RANGE 200.0    // meters

// Vehicle State Structure
struct VehicleState {
    double speed;      // km/h
    double position;   // meters
    int lane_id;       // lane number
    
    VehicleState(double s = 0.0, double p = 0.0, int l = 1) 
        : speed(s), position(p), lane_id(l) {}
};

// FCW Engine Class
class FCWEngine {
public:
    // Calculate Time-to-Collision
    double calculateTTC(double distance, double relative_speed_kmh) {
        if (relative_speed_kmh <= 0) {
            return 999.0; // No collision risk
        }
        
        // Convert km/h to m/s
        double relative_speed_ms = relative_speed_kmh / 3.6;
        
        // TTC = distance / relative_speed
        double ttc = distance / relative_speed_ms;
        
        return ttc;
    }
    
    // Assess risk level based on TTC
    std::string assessRiskLevel(double ttc_seconds) {
        if (ttc_seconds < CRITICAL_TTC_THRESHOLD) {
            return "CRITICAL";
        } else if (ttc_seconds < WARNING_TTC_THRESHOLD) {
            return "WARNING";
        } else if (ttc_seconds < 5.0) {
            return "LOW";
        } else {
            return "NONE";
        }
    }
    
    // Update vehicle positions (simulation)
    void updateVehiclePositions(VehicleState& ego, VehicleState& front) {
        // Simulate position updates based on speed
        double time_step = 0.01; // 10ms
        ego.position += (ego.speed / 3.6) * time_step;      // Convert km/h to m/s
        front.position += (front.speed / 3.6) * time_step;
    }
};

// Utility function for timestamp
std::string getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%H:%M:%S");
    ss << '.' << std::setfill('0') << std::setw(3) << ms.count();
    
    return ss.str();
}

#endif // FCW_TYPES_H