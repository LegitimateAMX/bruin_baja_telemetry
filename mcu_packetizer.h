// mcu_packetizer.h
#ifndef MCU_PACKETIZER_H
#define MCU_PACKETIZER_H

#include <stdint.h>
#include <string.h>

// Data type codes
typedef enum {
    DATA_TYPE_INT = 0x01,
    DATA_TYPE_FLOAT = 0x02,
    DATA_TYPE_DOUBLE = 0x03
} DataType;

// Sensor packet structure
typedef struct {
    uint8_t slave_address;      // 1 byte
    uint8_t data_type;          // 1 byte
    uint8_t variable_count;     // 1 byte
    uint8_t payload[255 * 8];   // Max 255 values of 8 bytes (double)
    uint16_t payload_length;    // Actual payload length in bytes
} SensorPacket;

// Union for data conversion
typedef union {
    uint8_t u8;
    float f32;
    double f64;
    uint8_t bytes[8];
} DataValue;

/**
 * Initialize a packet with header information
 * @param packet: Pointer to packet structure
 * @param slave_addr: Slave address (0-255)
 * @param type: Data type (DATA_TYPE_INT, DATA_TYPE_FLOAT, DATA_TYPE_DOUBLE)
 * @param var_count: Number of variables
 * @return: 0 on success, -1 on error
 */
int8_t packet_init(SensorPacket* packet, uint8_t slave_addr, 
                   DataType type, uint8_t var_count);

/**
 * Add an 8-bit integer to the packet
 * @param packet: Pointer to packet structure
 * @param value: 8-bit value
 * @return: 0 on success, -1 on error
 */
int8_t packet_add_int(SensorPacket* packet, uint8_t value);

/**
 * Add a 32-bit float to the packet
 * @param packet: Pointer to packet structure
 * @param value: 32-bit float value
 * @return: 0 on success, -1 on error
 */
int8_t packet_add_float(SensorPacket* packet, float value);

/**
 * Add a 64-bit double to the packet
 * @param packet: Pointer to packet structure
 * @param value: 64-bit double value
 * @return: 0 on success, -1 on error
 */
int8_t packet_add_double(SensorPacket* packet, double value);

/**
 * Get the complete serialized packet
 * @param packet: Pointer to packet structure
 * @param buffer: Output buffer for serialized packet
 * @return: Total packet length (header + payload), or -1 on error
 */
int16_t packet_serialize(const SensorPacket* packet, uint8_t* buffer);

/**
 * Get the size of data type in bytes
 * @param type: Data type
 * @return: Size in bytes
 */
uint8_t get_type_size(DataType type);

#endif // MCU_PACKETIZER_H
