# pc_depacketizer.py
import struct
from enum import IntEnum
from typing import Union, List, Tuple

class DataType(IntEnum):
    """Data type codes matching MCU"""
    INT = 0x01
    FLOAT = 0x02
    DOUBLE = 0x03

class DepacketizationError(Exception):
    """Exception raised during packet depacketization"""
    pass

class SensorPacket:
    """Represents a depacketized sensor packet"""
    
    def __init__(self, slave_address: int, data_type: DataType, variables: List[Union[int, float]]):
        self.slave_address = slave_address
        self.data_type = data_type
        self.variable_count = len(variables)
        self.variables = variables
    
    def __repr__(self) -> str:
        return (
            f"SensorPacket(slave={self.slave_address}, "
            f"type={self.data_type.name}, "
            f"variables={self.variables})"
        )
    
    def __str__(self) -> str:
        type_name = {
            DataType.INT: "int8",
            DataType.FLOAT: "float32",
            DataType.DOUBLE: "float64"
        }[self.data_type]
        
        return (
            f"Slave Address: {self.slave_address}\n"
            f"Data Type: {type_name}\n"
            f"Variable Count: {self.variable_count}\n"
            f"Values: {self.variables}"
        )

def get_type_size(data_type: DataType) -> int:
    """Get the size in bytes for a given data type"""
    sizes = {
        DataType.INT: 1,
        DataType.FLOAT: 4,
        DataType.DOUBLE: 8
    }
    if data_type not in sizes:
        raise DepacketizationError(f"Unknown data type code: 0x{data_type:02X}")
    return sizes[data_type]

def depacketize(packet_bytes: Union[bytes, bytearray, str]) -> SensorPacket:
    """
    Depacketize a sensor packet from bytes or hex string
    
    Args:
        packet_bytes: Raw packet bytes or hex string (e.g., "01021903...")
    
    Returns:
        SensorPacket object containing decoded data
    
    Raises:
        DepacketizationError: If packet format is invalid
    """
    
    # Convert hex string to bytes if needed
    if isinstance(packet_bytes, str):
        try:
            packet_bytes = bytes.fromhex(packet_bytes)
        except ValueError as e:
            raise DepacketizationError(f"Invalid hex string: {e}")
    
    # Ensure we have bytes
    if not isinstance(packet_bytes, (bytes, bytearray)):
        raise DepacketizationError("Packet must be bytes, bytearray, or hex string")
    
    # Check minimum length (3 header bytes)
    if len(packet_bytes) < 3:
        raise DepacketizationError(
            f"Packet too short: {len(packet_bytes)} bytes (minimum 3)"
        )
    
    # Parse header
    slave_address = packet_bytes[0]
    type_code = packet_bytes[1]
    variable_count = packet_bytes[2]
    
    # Validate type code
    try:
        data_type = DataType(type_code)
    except ValueError:
        raise DepacketizationError(
            f"Unknown data type code: 0x{type_code:02X}"
        )
    
    # Validate variable count
    if variable_count == 0 or variable_count > 255:
        raise DepacketizationError(
            f"Invalid variable count: {variable_count} (must be 1-255)"
        )
    
    # Parse payload
    payload = packet_bytes[3:]
    type_size = get_type_size(data_type)
    expected_payload_length = variable_count * type_size
    
    if len(payload) != expected_payload_length:
        raise DepacketizationError(
            f"Payload size mismatch: got {len(payload)} bytes, "
            f"expected {expected_payload_length} bytes "
            f"(type={data_type.name}, count={variable_count})"
        )
    
    # Decode variables
    variables: List[Union[int, float]] = []
    
    if data_type == DataType.INT:
        for i in range(variable_count):
            variables.append(payload[i])
    
    elif data_type == DataType.FLOAT:
        for i in range(variable_count):
            offset = i * 4
            value = struct.unpack('<f', payload[offset:offset + 4])[0]
            variables.append(value)
    
    elif data_type == DataType.DOUBLE:
        for i in range(variable_count):
            offset = i * 8
            value = struct.unpack('<d', payload[offset:offset + 8])[0]
            variables.append(value)
    
    return SensorPacket(slave_address, data_type, variables)

def depacketize_batch(packets_data: List[Union[bytes, str]]) -> List[SensorPacket]:
    """
    Depacketize multiple packets
    
    Args:
        packets_data: List of packet bytes or hex strings
    
    Returns:
        List of SensorPacket objects
    """
    return [depacketize(packet) for packet in packets_data]

# Example usage and integration with serial communication
if __name__ == "__main__":
    # Example 1: Direct hex string
    hex_packet = "01011903071e1c"  # 3 int values: 7, 30, 28
    packet = depacketize(hex_packet)
    print("Example 1 - Hex string:")
    print(packet)
    print()
    
    # Example 2: Bytes
    bytes_packet = bytes([0x01, 0x02, 0x02, 0x3f, 0x80, 0x00, 0x00, 0x40, 0x20, 0x00, 0x00])
    packet = depacketize(bytes_packet)
    print("Example 2 - Bytes:")
    print(packet)
    print()
    
    # Example 3: Error handling
    try:
        bad_packet = depacketize("0101")  # Too short
    except DepacketizationError as e:
        print(f"Expected error: {e}")
