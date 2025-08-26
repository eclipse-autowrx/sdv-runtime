#include "calculator.h"
#include <stdexcept>

Calculator::Calculator() : lastOperation("") {}
Calculator::~Calculator() {}

double Calculator::add(double a, double b) {
    lastOperation = "add";
    return a + b;
}

double Calculator::subtract(double a, double b) {
    lastOperation = "subtract";
    return a - b;
}

double Calculator::multiply(double a, double b) {
    lastOperation = "multiply";
    return a * b;
}

double Calculator::divide(double a, double b) {
    if (b == 0.0) {
        throw std::invalid_argument("Cannot divide by zero");
    }
    lastOperation = "divide";
    return a / b;
}