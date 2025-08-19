// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 08: STL Containers - Advanced C++ standard library usage
const testConfig = require('../utils/test-config');

const TEST_NAME = '08 STL Containers - Standard Library Features';

const FILES = [
    {
        type: "folder",
        name: "stl_demo",
        items: [
            {
                type: "file", 
                name: "main.cpp",
                content: `#include <iostream>
#include "containers/vector_demo.h"
#include "containers/map_demo.h"
#include "algorithms/sort_demo.h"

int main() {
    std::cout << "=== STL Containers & Algorithms Demo ===" << std::endl;
    
    // Vector operations
    std::cout << "\\n1. Vector Operations:" << std::endl;
    VectorDemo::runDemo();
    
    // Map operations  
    std::cout << "\\n2. Map Operations:" << std::endl;
    MapDemo::runDemo();
    
    // Algorithm operations
    std::cout << "\\n3. Algorithm Operations:" << std::endl;
    SortDemo::runDemo();
    
    std::cout << "\\n=== STL Demo Completed ===" << std::endl;
    return 0;
}`
            },
            {
                type: "folder",
                name: "containers",
                items: [
                    {
                        type: "file",
                        name: "vector_demo.h",
                        content: `#pragma once
#include <vector>

class VectorDemo {
public:
    static void runDemo();
private:
    static void showVector(const std::vector<int>& vec, const std::string& label);
};`
                    },
                    {
                        type: "file",
                        name: "vector_demo.cpp", 
                        content: `#include "vector_demo.h"
#include <iostream>
#include <algorithm>

void VectorDemo::runDemo() {
    std::vector<int> numbers = {5, 2, 8, 1, 9, 3};
    showVector(numbers, "Original");
    
    // Add elements
    numbers.push_back(7);
    numbers.push_back(4);
    showVector(numbers, "After push_back");
    
    // Sort
    std::sort(numbers.begin(), numbers.end());
    showVector(numbers, "After sort");
    
    // Find element
    auto it = std::find(numbers.begin(), numbers.end(), 8);
    if (it != numbers.end()) {
        std::cout << "Found 8 at position: " << (it - numbers.begin()) << std::endl;
    }
    
    // Size info
    std::cout << "Vector size: " << numbers.size() << ", capacity: " << numbers.capacity() << std::endl;
}

void VectorDemo::showVector(const std::vector<int>& vec, const std::string& label) {
    std::cout << label << ": [";
    for (size_t i = 0; i < vec.size(); ++i) {
        std::cout << vec[i];
        if (i < vec.size() - 1) std::cout << ", ";
    }
    std::cout << "]" << std::endl;
}`
                    },
                    {
                        type: "file",
                        name: "map_demo.h",
                        content: `#pragma once
#include <map>
#include <string>

class MapDemo {
public:
    static void runDemo();
private:
    static void showMap(const std::map<std::string, int>& m, const std::string& label);
};`
                    },
                    {
                        type: "file",
                        name: "map_demo.cpp",
                        content: `#include "map_demo.h"
#include <iostream>

void MapDemo::runDemo() {
    std::map<std::string, int> vehicleCount;
    
    // Insert data
    vehicleCount["Tesla"] = 150;
    vehicleCount["BMW"] = 200;
    vehicleCount["Audi"] = 175;
    vehicleCount["Mercedes"] = 220;
    
    showMap(vehicleCount, "Vehicle counts");
    
    // Update value
    vehicleCount["Tesla"] += 25;
    std::cout << "Updated Tesla count: " << vehicleCount["Tesla"] << std::endl;
    
    // Find and erase
    auto it = vehicleCount.find("Audi");
    if (it != vehicleCount.end()) {
        std::cout << "Removing Audi (had " << it->second << " vehicles)" << std::endl;
        vehicleCount.erase(it);
    }
    
    showMap(vehicleCount, "After removal");
    
    std::cout << "Total brands: " << vehicleCount.size() << std::endl;
}

void MapDemo::showMap(const std::map<std::string, int>& m, const std::string& label) {
    std::cout << label << ":" << std::endl;
    for (const auto& pair : m) {
        std::cout << "  " << pair.first << ": " << pair.second << std::endl;
    }
}`
                    }
                ]
            },
            {
                type: "folder", 
                name: "algorithms",
                items: [
                    {
                        type: "file",
                        name: "sort_demo.h",
                        content: `#pragma once
#include <vector>
#include <string>

struct Vehicle {
    std::string brand;
    int year;
    double price;
    
    Vehicle(const std::string& b, int y, double p) : brand(b), year(y), price(p) {}
};

class SortDemo {
public:
    static void runDemo();
private:
    static void showVehicles(const std::vector<Vehicle>& vehicles, const std::string& label);
};`
                    },
                    {
                        type: "file",
                        name: "sort_demo.cpp",
                        content: `#include "sort_demo.h"
#include <iostream>
#include <algorithm>

void SortDemo::runDemo() {
    std::vector<Vehicle> fleet = {
        Vehicle("Tesla Model 3", 2023, 45000),
        Vehicle("BMW i4", 2022, 52000),
        Vehicle("Audi e-tron", 2021, 68000),
        Vehicle("Mercedes EQC", 2023, 72000),
        Vehicle("Tesla Model S", 2022, 95000)
    };
    
    showVehicles(fleet, "Original fleet");
    
    // Sort by price
    std::sort(fleet.begin(), fleet.end(), [](const Vehicle& a, const Vehicle& b) {
        return a.price < b.price;
    });
    showVehicles(fleet, "Sorted by price (ascending)");
    
    // Sort by year (descending)
    std::sort(fleet.begin(), fleet.end(), [](const Vehicle& a, const Vehicle& b) {
        return a.year > b.year;
    });
    showVehicles(fleet, "Sorted by year (descending)");
    
    // Find most expensive
    auto maxPriceIt = std::max_element(fleet.begin(), fleet.end(), 
        [](const Vehicle& a, const Vehicle& b) {
            return a.price < b.price;
        });
    
    if (maxPriceIt != fleet.end()) {
        std::cout << "Most expensive: " << maxPriceIt->brand 
                  << " ($" << maxPriceIt->price << ")" << std::endl;
    }
}

void SortDemo::showVehicles(const std::vector<Vehicle>& vehicles, const std::string& label) {
    std::cout << label << ":" << std::endl;
    for (const auto& v : vehicles) {
        std::cout << "  " << v.brand << " (" << v.year << ") - $" << v.price << std::endl;
    }
}`
                    }
                ]
            }
        ]
    }
];

testConfig.runTest({
    testName: TEST_NAME,
    files: FILES,
    appName: 'STLDemo',
    run: true,
    timeout: 35000,
    expectedOutput: 'STL Containers'
});