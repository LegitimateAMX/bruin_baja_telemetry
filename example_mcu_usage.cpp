// example_mcu_usage.cpp
// Example MCU usage - demonstrates reading from sensors and packetizing data

#include "mcu_packetizer.h"
#include <stdio.h>  // For demonstration only - remove for real MCU

// Simulated sensor read functions (replace with actual ADC reads)
uint8_t read_temperature_sensor() {
    return 25;  // 25°C
}

uint8_t read_humidity_sensor() {
    return 60;  // 60%
}

uint8_t read_pressure_sensor() {
    return 1013;  // hPa (will be cast to uint8_t)
}

float read_voltage_sensor() {
    return 3.3f;  // 3.3V
}

void transmit_packet(const uint8_t* data, uint16_t length) {
    // Replace with actual UART/SPI transmission
    // Example: uart_send_bytes(UART1, data, length);
    printf("Transmitting packet of %d bytes: ", length);
    for (uint16_t i = 0; i < length; i++) {
        printf("%02X ", data[i]);
    }
    printf("\n");
}

int main() {
    uint8_t buffer[512];
    
    // Example 1: Packetize integer sensor readings
    {
        SensorPacket packet;
        packet_init(&packet, 1, DATA_TYPE_INT, 3);  // Slave 1, int type, 3 variables
        
        packet_add_int(&packet, read_temperature_sensor());
        packet_add_int(&packet, read_humidity_sensor());
        packet_add_int(&packet, read_pressure_sensor());
        
        int16_t packet_len = packet_serialize(&packet, buffer);
        if (packet_len > 0) {
            transmit_packet(buffer, packet_len);
        }
    }
    
    // Example 2: Packetize float sensor readings
    {
        SensorPacket packet;
        packet_init(&packet, 2, DATA_TYPE_FLOAT, 2);  // Slave 2, float type, 2 variables
        
        packet_add_float(&packet, read_voltage_sensor());
        packet_add_float(&packet, 2.5f);  // Current
        
        int16_t packet_len = packet_serialize(&packet, buffer);
        if (packet_len > 0) {
            transmit_packet(buffer, packet_len);
        }
    }

    return 0;
}
