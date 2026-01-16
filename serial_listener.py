import serial
import os
import csv

class SerialListener:
    def __init__(self, port, baudrate=9600, timeout=1.0, path="./byte_data.csv"):
        self.port = port
        self.baudrate = baudrate #default
        self.timeout = timeout #default
        self.path = path
        self.ser = None
        
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def connect(self, port=None): #need to enter a default port
        self.port = port
        if (self.port):
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout) #opens port and creates a serial connection
            print("Serial connection created.")
    
    def disconnect(self):
        if self.ser:
            self.ser.close() #close the serial connection
            print("Serial connection closed.")
        else:
            print("Serial connection not created yet.")
    
    def listen(self): #send packet data to csv fileno 
        if not self.ser:
            print("Serial connection not created yet.")
            return
        while True:
            ser_bytes = self.ser.readline() #readline() depends on newline character
            with open(self.path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f"{b:02x}" for b in ser_bytes])

listener = SerialListener(port="/dev/ttyUSB0") #change port as needed
listener.connect()
try:
    listener.listen()
except KeyboardInterrupt:
    listener.disconnect()
    print("Disconnected.")             