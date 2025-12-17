# serial_listener.py
# Example serial communication wrapper for real-time packet reception

import serial
import threading
from typing import Callable, Optional
from pc_depacketizer import depacketize, DepacketizationError, SensorPacket

class SensorPacketListener:
    """Serial listener for receiving and depacketizing sensor packets"""
    
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize serial connection
        
        Args:
            port: Serial port (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Baud rate (default 9600)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.running = False
        self.callback: Optional[Callable[[SensorPacket], None]] = None
    
    def connect(self) -> bool:
        """Connect to serial port"""
        try:
            self.serial_conn = serial.Serial(
                self.port, 
                self.baudrate, 
                timeout=self.timeout
            )
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port"""
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected")
    
    def set_callback(self, callback: Callable[[SensorPacket], None]) -> None:
        """Set callback function called when packet is received"""
        self.callback = callback
    
    def listen(self) -> None:
        """
        Listen for incoming packets (blocks until disconnect)
        Reads raw bytes and attempts to parse as sensor packets
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Not connected")
            return
        
        self.running = True
        print("Listening for packets...")
        
        while self.running:
            try:
                # Read available data
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    
                    try:
                        # Attempt to depacketize
                        packet = depacketize(data)
                        print(f"Received: {packet}")
                        
                        # Call user callback if set
                        if self.callback:
                            self.callback(packet)
                    
                    except DepacketizationError as e:
                        print(f"Depacketization error: {e}")
                        print(f"Raw data: {data.hex()}")
            
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
    
    def listen_async(self) -> threading.Thread:
        """
        Start listening in a background thread
        
        Returns:
            Thread object (already started)
        """
        thread = threading.Thread(target=self.listen, daemon=False)
        thread.start()
        return thread

# Example usage
if __name__ == "__main__":
    def on_packet_received(packet: SensorPacket) -> None:
        """Handle received packet"""
        print(f"\n✓ New packet from slave {packet.slave_address}:")
        for i, value in enumerate(packet.variables):
            print(f"  Variable {i}: {value}")
    
    # Create listener
    listener = SensorPacketListener(port='COM3', baudrate=9600)
    
    # Connect and set callback
    if listener.connect():
        listener.set_callback(on_packet_received)
        
        # Listen in background thread
        thread = listener.listen_async()
        
        try:
            # Keep main thread alive
            thread.join()
        except KeyboardInterrupt:
            print("\nStopping...")
            listener.disconnect()
