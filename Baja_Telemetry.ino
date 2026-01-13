/*
 * Arduino Packet Manager
 * 
 * Packet Structure:
 * [0] Slave Address (1 byte)
 * [1] Data Type     (1 byte)
 * [2] Payload Length (1 byte)
 * [3..N] Payload    (variable length)
 *
 * Example: Slave=0x01, DataType=0x02, Length=4, Payload={0xAA, 0xBB, 0xCC, 0xDD}
 * Full Packet: [0x01][0x02][0x04][0xAA][0xBB][0xCC][0xDD]
 */

#include <Arduino.h>

// ============================================================================
// CONFIGURATION & CONSTANTS
// ============================================================================

#define SERIAL_BAUD_RATE 9600
#define MAX_PAYLOAD_SIZE 64
#define NUM_SENSORS 2

// Data type constants
#define DATA_TYPE_TEMPERATURE 0x01
#define DATA_TYPE_HUMIDITY 0x02
#define DATA_TYPE_PRESSURE 0x03
#define DATA_TYPE_LIGHT 0x04
#define DATA_TYPE_GENERIC 0xFF

// ============================================================================
// PACKET STRUCTURE
// ============================================================================

typedef struct {
  uint8_t slave_address;
  uint8_t data_type;
  uint8_t payload_length;
  uint8_t payload[MAX_PAYLOAD_SIZE];
} Packet;

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

Packet current_packet;
uint8_t sensor_pins[NUM_SENSORS];
uint8_t num_sensors = 0;

// ============================================================================
// INITIALIZATION FUNCTION
// ============================================================================

/**
 * Initialize the packet manager with slave address and data type
 * 
 * @param slave_addr The slave address for this Arduino device (0x00 - 0xFF)
 * @param data_type The type of data being transmitted (see DATA_TYPE_* constants)
 */
void packet_init(uint8_t slave_addr, uint8_t data_type) {
  // Initialize serial communication
  Serial.begin(SERIAL_BAUD_RATE);
  
  // Set packet header information
  current_packet.slave_address = slave_addr;
  current_packet.data_type = data_type;
  current_packet.payload_length = 0;
  
  // Debug output
  Serial.print("Packet initialized: Slave=0x");
  Serial.print(slave_addr, HEX);
  Serial.print(" DataType=0x");
  Serial.println(data_type, HEX);
}

// ============================================================================
// SENSOR DATA ACQUISITION FUNCTION
// ============================================================================

/**
 * Register a sensor connected to an analog pin
 * This should be called during setup for each sensor
 * 
 * @param pin The analog pin number (e.g., A0, A1)
 */
void add_sensor(uint8_t pin) {
  if (num_sensors < NUM_SENSORS) {
    sensor_pins[num_sensors] = pin;
    num_sensors++;
    pinMode(pin, INPUT);
    Serial.print("Sensor added on pin ");
    Serial.println(pin);
  } else {
    Serial.println("ERROR: Maximum sensors reached!");
  }
}

/**
 * Read sensor data from all registered sensors
 * Returns a pointer to the raw sensor reading
 * 
 * @param sensor_index Index of the sensor to read (0 to NUM_SENSORS-1)
 * @return The analog reading (0-1023) from the sensor
 */
uint16_t read_sensor_data(uint8_t sensor_index) {
  if (sensor_index >= num_sensors) {
    Serial.println("ERROR: Invalid sensor index!");
    return 0;
  }
  
  uint16_t reading = analogRead(sensor_pins[sensor_index]);
  
  // Optional: Serial debug output
  Serial.print("Sensor ");
  Serial.print(sensor_index);
  Serial.print(" reading: ");
  Serial.println(reading);
  
  return reading;
}

/**
 * Read all sensor data into a single stream
 * This function reads all registered sensors sequentially
 * 
 * @param data_buffer Pointer to buffer where sensor data will be stored
 * @return Number of bytes written to the buffer
 */
uint8_t read_all_sensors(uint8_t* data_buffer) {
  uint8_t bytes_written = 0;
  
  for (uint8_t i = 0; i < num_sensors; i++) {
    uint16_t reading = read_sensor_data(i);
    
    // Store as 2 bytes (big-endian format: high byte first, then low byte)
    data_buffer[bytes_written++] = (uint8_t)(reading >> 8);   // High byte
    data_buffer[bytes_written++] = (uint8_t)(reading & 0xFF); // Low byte
    
    if (bytes_written >= MAX_PAYLOAD_SIZE) {
      Serial.println("WARNING: Payload buffer full!");
      break;
    }
  }
  
  return bytes_written;
}

// ============================================================================
// PACKET CREATION FUNCTION
// ============================================================================

/**
 * Packetize data stream into the defined packet format
 * 
 * Packet structure:
 *   Byte 0: Slave Address
 *   Byte 1: Data Type
 *   Byte 2: Payload Length
 *   Bytes 3+: Payload data
 * 
 * @param data_stream Pointer to the raw data to packetize
 * @param data_length Number of bytes in the data stream
 * @return Pointer to the completed packet structure
 */
Packet* packetize_data(uint8_t* data_stream, uint8_t data_length) {
  // Validate payload size
  if (data_length > MAX_PAYLOAD_SIZE) {
    Serial.println("ERROR: Data length exceeds maximum payload size!");
    current_packet.payload_length = 0;
    return &current_packet;
  }
  
  // Copy payload data into packet
  for (uint8_t i = 0; i < data_length; i++) {
    current_packet.payload[i] = data_stream[i];
  }
  
  // Set payload length
  current_packet.payload_length = data_length;
  
  // Debug output
  Serial.print("Packet created: Length=");
  Serial.println(data_length);
  
  return &current_packet;
}

// ============================================================================
// SERIAL OUTPUT FUNCTION
// ============================================================================

/**
 * Transmit the packet over serial using Serial.write()
 * This function sends the complete packet structure sequentially:
 * 1. Slave address byte
 * 2. Data type byte
 * 3. Payload length byte
 * 4. Payload bytes (as specified by payload length)
 */
void output_packet() {
  // Send slave address
  Serial.write(current_packet.slave_address);
  
  // Send data type
  Serial.write(current_packet.data_type);
  
  // Send payload length
  Serial.write(current_packet.payload_length);
  
  // Send payload bytes
  for (uint8_t i = 0; i < current_packet.payload_length; i++) {
    Serial.write(current_packet.payload[i]);
  }
  
  // Optional: Add delay to allow serial buffer to flush
  // delay(10);
  
  // Debug output (human-readable format)
  print_packet_debug();
}

/**
 * Print packet information in human-readable format (for debugging)
 * Displays the packet in hexadecimal format
 */
void print_packet_debug() {
  Serial.print("[DEBUG] Packet sent: ");
  Serial.print("0x");
  Serial.print(current_packet.slave_address, HEX);
  Serial.print(" 0x");
  Serial.print(current_packet.data_type, HEX);
  Serial.print(" 0x");
  Serial.print(current_packet.payload_length, HEX);
  Serial.print(" | Payload: ");
  
  for (uint8_t i = 0; i < current_packet.payload_length; i++) {
    Serial.print("0x");
    Serial.print(current_packet.payload[i], HEX);
    if (i < current_packet.payload_length - 1) {
      Serial.print(" ");
    }
  }
  Serial.println();
}

// ============================================================================
// EXAMPLE USAGE - ARDUINO SKETCH
// ============================================================================

/*void setup() {
  // Initialize packet manager with slave address 0x01 and data type for temperature
  packet_init(0x01, DATA_TYPE_TEMPERATURE);
  
  // Register sensors (analog pins A0 and A1)
  add_sensor(A0);
  add_sensor(A1);
  
  delay(1000); // Allow serial to initialize
}

void loop() {
  // Read all sensor data into a buffer
  uint8_t sensor_data[MAX_PAYLOAD_SIZE];
  uint8_t data_length = read_all_sensors(sensor_data);
  
  // Packetize the sensor data
  packetize_data(sensor_data, data_length);
  
  // Transmit the packet via serial
  output_packet();
  
  // Wait before next transmission
  delay(1000); // 1 second interval
}*/

// THIS IS FOR TESTING WITH PLACEHOLDERS

void setup() {
  packet_init(0x01, DATA_TYPE_GENERIC);  // placeholder addr + type
  delay(200);
}

void loop() {
  // Deterministic payload (software-only test)
  uint8_t payload[] = { 0xAA, 0xBB, 0xCC, 0xDD };

  packetize_data(payload, sizeof(payload));
  output_packet();   // sends bytes via Serial.write() and then prints debug text

  delay(1000);
}

// ============================================================================
// OPTIONAL: RECEIVING FUNCTION (for multi-Arduino communication)
// ============================================================================

/**
 * Receive and parse a packet from serial
 * This function can be used if this Arduino needs to receive packets
 * from another device or Arduino
 * 
 * @param received_packet Pointer to a Packet structure to store received data
 * @return true if a valid packet was received, false otherwise
 */
bool receive_packet(Packet* received_packet) {
  // Check if data is available on serial port
  if (Serial.available() < 3) {
    return false; // Not enough bytes for even header
  }
  
  // Read header bytes
  received_packet->slave_address = Serial.read();
  received_packet->data_type = Serial.read();
  received_packet->payload_length = Serial.read();
  
  // Validate payload length
  if (received_packet->payload_length > MAX_PAYLOAD_SIZE) {
    Serial.println("ERROR: Received packet payload exceeds maximum size!");
    return false;
  }
  
  // Read payload bytes
  // Note: This is a simple implementation. For production use,
  // consider implementing a timeout to avoid hanging
  uint8_t bytes_read = 0;
  while (bytes_read < received_packet->payload_length) {
    if (Serial.available()) {
      received_packet->payload[bytes_read] = Serial.read();
      bytes_read++;
    }
  }
  
  Serial.print("Packet received from slave 0x");
  Serial.print(received_packet->slave_address, HEX);
  Serial.print(" - Type: 0x");
  Serial.println(received_packet->data_type, HEX);
  
  return true;
}
