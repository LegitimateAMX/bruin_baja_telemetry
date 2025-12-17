// mcu_packetizer.c
#include "mcu_packetizer.h"

// Helper function to get type size
uint8_t get_type_size(DataType type) {
    switch (type) {
        case DATA_TYPE_INT:
            return 1;
        case DATA_TYPE_FLOAT:
            return 4;
        case DATA_TYPE_DOUBLE:
            return 8;
        default:
            return 0;
    }
}

int8_t packet_init(SensorPacket* packet, uint8_t slave_addr, 
                   DataType type, uint8_t var_count) {
    if (packet == NULL || var_count == 0 || var_count > 255) {
        return -1;
    }

    packet->slave_address = slave_addr;
    packet->data_type = type;
    packet->variable_count = var_count;
    packet->payload_length = 0;

    return 0;
}

int8_t packet_add_int(SensorPacket* packet, uint8_t value) {
    if (packet == NULL || packet->data_type != DATA_TYPE_INT) {
        return -1;
    }

    // Check if we've reached variable count limit
    uint8_t current_count = packet->payload_length / get_type_size(DATA_TYPE_INT);
    if (current_count >= packet->variable_count) {
        return -1;
    }

    // Check payload size
    if (packet->payload_length + 1 > 255 * get_type_size(DATA_TYPE_INT)) {
        return -1;
    }

    packet->payload[packet->payload_length++] = value;
    return 0;
}

int8_t packet_add_float(SensorPacket* packet, float value) {
    if (packet == NULL || packet->data_type != DATA_TYPE_FLOAT) {
        return -1;
    }

    uint8_t type_size = get_type_size(DATA_TYPE_FLOAT);
    uint8_t current_count = packet->payload_length / type_size;
    
    if (current_count >= packet->variable_count) {
        return -1;
    }

    if (packet->payload_length + type_size > 255 * type_size) {
        return -1;
    }

    // Convert float to bytes (little-endian)
    DataValue dv;
    dv.f32 = value;
    for (uint8_t i = 0; i < type_size; i++) {
        packet->payload[packet->payload_length++] = dv.bytes[i];
    }

    return 0;
}

int8_t packet_add_double(SensorPacket* packet, double value) {
    if (packet == NULL || packet->data_type != DATA_TYPE_DOUBLE) {
        return -1;
    }

    uint8_t type_size = get_type_size(DATA_TYPE_DOUBLE);
    uint8_t current_count = packet->payload_length / type_size;
    
    if (current_count >= packet->variable_count) {
        return -1;
    }

    if (packet->payload_length + type_size > 255 * type_size) {
        return -1;
    }

    // Convert double to bytes (little-endian)
    DataValue dv;
    dv.f64 = value;
    for (uint8_t i = 0; i < type_size; i++) {
        packet->payload[packet->payload_length++] = dv.bytes[i];
    }

    return 0;
}

int16_t packet_serialize(const SensorPacket* packet, uint8_t* buffer) {
    if (packet == NULL || buffer == NULL) {
        return -1;
    }

    // Verify payload size matches expected
    uint8_t expected_payload_size = packet->variable_count * get_type_size(packet->data_type);
    if (packet->payload_length != expected_payload_size) {
        return -1;
    }

    // Write header (3 bytes)
    buffer[0] = packet->slave_address;
    buffer[1] = packet->data_type;
    buffer[2] = packet->variable_count;

    // Write payload
    memcpy(&buffer[3], packet->payload, packet->payload_length);

    return 3 + packet->payload_length;
}
