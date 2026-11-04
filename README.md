# MessMind — Smart Food Waste Monitor

An ECE engineering project designed to monitor, analyze, and reduce hostel mess food waste using automated student recognition and load-cell weight tracking.

## Overview
**MessMind** helps campus mess administrations reduce food waste through accountability and data-driven kitchen planning. By pairing student identification with precise weight sensors at waste drop-off points, the system logs leftover food per student, per meal, and across the hostel.

## Key Features
- **Real-Time Analytics Dashboard**: Visualizes daily waste totals, per-student averages, waste goal limits, and 7-day trends.
- **Quick Capture & Event Logging**: Simulates student face recognition (ESP32-CAM) and waste container load-cell weight recording (HX711).
- **Student History Records**: Searchable log showing student names, registration IDs, meal types (Breakfast, Lunch, Dinner), exact waste weight in grams, and high-waste alerts.
- **CSV Data Export**: Easily export waste data for administrative review and statistical analysis.

## Hardware Architecture (Integration Roadmap)
1. **Face Recognition Module**: ESP32-CAM module to capture and identify students at the disposal counter.
2. **Weight Measurement Module**: HX711 load cell sensor to measure the incremental weight added to the disposal bin.
3. **Microcontroller / Gateway**: Arduino / ESP32 sending data over WiFi/HTTP to the central dashboard.

## Tech Stack
- **Frontend**: HTML5, Modern Vanilla JavaScript, CSS3 Design Tokens
- **Hardware Integration Target**: ESP32-CAM, HX711, Arduino
