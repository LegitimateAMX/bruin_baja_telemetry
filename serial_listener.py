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
        if not os.path.exists(path):
            os.makedirs(path)
    
    def connect(self, port=None): #need to enter a default port
        self.port = port
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout) #opens port and creates a serial connection
        print("Serial connection created.")
    
    def disconnect(self):
        if self.ser:
            self.ser.close() #close the serial connection
            print("Serial connection closed.")
        else:
            print("Serial connection not created yet.")
    
    def listen(self): #send packet data to csv file
        if not self.ser():
            print("Serial connection not created yet.")
            return
        while True:
            ser_bytes = self.ser.readline() #readline() depends on newline character
            decoded_bytes = ser_bytes.decode('utf-8').strip() #decode
            with open(self.path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(decoded_bytes)