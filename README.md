# Autonomous Car with Mobile App Monitoring

A comprehensive IoT autonomous vehicle system featuring real-time monitoring, navigation AI, and Android app integration.

## 📋 Project Overview

This project implements a smart autonomous vehicle system that combines computer vision, sensor fusion, and mobile app monitoring. The system consists of a Raspberry Pi-based vehicle controller and an Android monitoring application that provides real-time telemetry, control capabilities, and trip history tracking.

## 🏗️ System Architecture

### Core Components

- **Raspberry Pi Controller**: Main vehicle control system with autonomous navigation
- **Android Mobile App**: Real-time monitoring and manual control interface
- **Vision System**: Computer vision for lane detection and traffic sign recognition
- **Sensor Integration**: Ultrasonic sensors for obstacle detection
- **Motor Control**: Precise motor control for vehicle movement
- **Communication**: Wi-Fi and Bluetooth communication protocols

## 🚗 Raspberry Pi System

### Key Features

- **Autonomous Navigation**: AI-powered navigation with lane following and obstacle avoidance
- **Computer Vision**: Real-time processing for traffic lights, signs, and lane detection
- **Sensor Fusion**: Integration of multiple sensors for comprehensive environmental awareness
- **Communication Hub**: Multi-protocol communication (Wi-Fi, Bluetooth) with mobile app
- **Performance Monitoring**: System health monitoring with temperature and resource tracking
- **Emergency Safety**: Multiple safety systems including emergency stop functionality

### Core Modules

```
Raspberry Files/
├── main.py                 # Main system controller
├── core/
│   ├── motor_controller.py # Motor control and movement
│   ├── navigation_ai.py    # AI navigation decisions
│   ├── sensor_manager.py   # Sensor data collection
│   └── vision_system.py    # Computer vision processing
├── communication/
│   ├── ble_handler.py      # Bluetooth communication
│   ├── protocol_manager.py # Communication protocols
│   └── wifi_handler.py     # Wi-Fi communication
└── utils/
    ├── config_manager.py   # Configuration management
    ├── logger.py          # Logging system
    └── performance_monitor.py # System monitoring
```

## 📱 Android Mobile App

### Features

- **Real-time Monitoring**: Live vehicle status, battery, motor, and temperature monitoring
- **Trip History**: Comprehensive trip tracking with efficiency metrics
- **Manual Control**: Remote manual control capabilities
- **Notifications**: Real-time alerts for system status and emergencies
- **Data Visualization**: Intuitive dashboard with status indicators

### Key Components

- **MainActivity**: Main dashboard with real-time vehicle status
- **CarDataManager**: Data management and communication with vehicle
- **MonitoringService**: Background service for continuous monitoring
- **Trip Management**: Trip recording and history tracking
- **Notification System**: Alert system for critical events

## 🛠️ Installation & Setup

### Raspberry Pi Setup

1. **Hardware Requirements**:
   - Raspberry Pi 4B or higher
   - Camera module
   - Ultrasonic sensors
   - Motor driver board
   - DC motors
   - Power supply

2. **Software Installation**:
   ```bash
   # Install required dependencies
   pip install opencv-python numpy
   pip install RPi.GPIO
   pip install bluetooth-python
   
   # Clone and setup the project
   git clone <repository-url>
   cd Autonomous-Car-with-Mobile-App-Monitoring/Raspberry\ Files
   python main.py
   ```

### Android App Setup

1. **Requirements**:
   - Android Studio
   - Android SDK API 24+
   - Device with Android 7.0+

2. **Build Instructions**:
   ```bash
   cd Mobile\ App
   ./gradlew build
   ./gradlew installDebug
   ```

## 🔧 Configuration

### Vehicle Configuration

The system uses a configuration manager for easy customization:

- **Vision Settings**: Camera resolution, detection thresholds
- **Motor Control**: Speed limits, turn parameters
- **Communication**: Network settings, connection protocols
- **Safety Parameters**: Emergency stop conditions, obstacle distances

### App Configuration

- **Connection Settings**: Vehicle IP address and communication protocols
- **Notification Preferences**: Alert thresholds and notification types
- **Display Options**: Update intervals and data visualization

## 🚀 Usage

### Starting the System

1. **Power on the Raspberry Pi** and ensure all sensors are connected
2. **Run the main controller**:
   ```bash
   python main.py
   ```
3. **Launch the Android app** and connect to the vehicle
4. **Monitor real-time data** through the app dashboard

### Operating Modes

- **Autonomous Mode**: AI-controlled navigation with obstacle avoidance
- **Manual Override**: Direct control through the mobile app
- **Emergency Stop**: Immediate halt for safety situations

## 📊 Features

### Autonomous Navigation
- Lane detection and following
- Traffic light recognition
- Stop sign detection
- Obstacle avoidance
- Speed limit recognition

### Mobile Monitoring
- Real-time battery status
- Motor performance tracking  
- System temperature monitoring
- Trip history and analytics
- Remote emergency stop

### Safety Systems
- Multiple emergency stop mechanisms
- Temperature monitoring
- Battery health tracking
- Connection loss detection
- Performance degradation alerts

## 🔧 Technical Specifications

### Performance
- **Control Loop**: 20Hz main control frequency
- **Vision Processing**: Real-time frame processing
- **Communication**: Low-latency telemetry streaming
- **Response Time**: <100ms emergency stop response

### Connectivity
- **Wi-Fi**: Primary communication channel
- **Bluetooth**: Backup communication protocol
- **Range**: Up to 100m outdoor range

## 📈 Monitoring & Analytics

### Real-time Metrics
- Battery level and health
- Motor status and performance
- System temperature
- Communication status
- Navigation decisions

### Trip Analytics
- Distance traveled
- Average speed
- Battery efficiency
- Trip duration
- Route optimization data

## 🛡️ Safety Features

- **Emergency Stop**: Multiple trigger mechanisms
- **Obstacle Detection**: Real-time collision avoidance
- **System Monitoring**: Continuous health checks
- **Communication Failsafe**: Automatic stop on connection loss
- **Temperature Protection**: Thermal shutdown protection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔍 Troubleshooting

### Common Issues

- **Connection Problems**: Check Wi-Fi network and IP configuration
- **Camera Issues**: Verify camera module connection and permissions
- **Motor Control**: Check power supply and motor driver connections
- **App Crashes**: Ensure proper network permissions and connection settings

### Debug Mode

Enable debug logging in the configuration for detailed system information and troubleshooting.
