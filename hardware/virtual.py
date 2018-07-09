# Copyright (c) 2015 - 2016 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function
from .board import Board
import RPi.GPIO as GPIO
import csv
import os


class VirtualBoard(Board):

    """
    Board class for virtual hardware.
    """
    HIGH_SENSOR_PIN = 11
    LOW_SENSOR_PIN = 19
    FLOW_PIN = 13
    PUMP_PIN = 15

    LOW_WATER_LEVEL = 70
    HIGH_WATER_LEVEL = 80
    MAX_WATER_LEVEL = 100
    FLOW_RATE = 8

    def __init__(self):

        super(VirtualBoard, self).__init__()

        self.flowing = False
        self.flow = self.FLOW_RATE
        self.water_level = 75
        self.increasing = True
        self.water_levels = []
        self.water_level_index = 0
        self.pump_rate = 0
        self.water_level_arr_size = 0

        self.pump = False

        self.init_water_levels()
        self.init_pin_values()

    def init_water_levels(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))

        with open(dir_path + "/water_data.csv") as water_data_csv:
            counter = 0
            readCSV = csv.reader(water_data_csv, delimiter=',')

            for row in readCSV:
                self.water_levels.append(float(row[0]))
                counter += 1

            self.water_level_arr_size = counter

    def init_pin_values(self):

        # Initialize GPIO pins for use
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.HIGH_SENSOR_PIN, GPIO.OUT)
        GPIO.setup(self.LOW_SENSOR_PIN, GPIO.OUT)
        GPIO.setup(self.FLOW_PIN, GPIO.OUT)
        GPIO.setup(self.PUMP_PIN, GPIO.OUT)

        # Initialize low sensor pin as on
        GPIO.output(self.LOW_SENSOR_PIN, GPIO.HIGH)

        # Initialize high sensor pin as off
        GPIO.output(self.HIGH_SENSOR_PIN, GPIO.LOW)

        # Initialize flow pin as on
        GPIO.output(self.FLOW_PIN, GPIO.HIGH)

        # Initialize pump pin as on
        GPIO.output(self.PUMP_PIN, GPIO.HIGH)

        # reset to input (from PLC) after initializing pin values
        GPIO.setup(self.FLOW_PIN, GPIO.IN)
        GPIO.setup(self.PUMP_PIN, GPIO.IN)


    def update_hardware_state(self):
        """
        Update hardware state.
        """

        pass

    # hardware functions
    def pump_on(self):
        self.pump = True

    def pump_off(self):
        self.pump = False

    def get_flow(self):
        return self.flow

    def set_flow(flow):
        self.flow = flow

    def get_water_level(self):
        return self.water_level

    def set_water_level(water_level):
        self.water_level = water_level

    def flow_on(self):
        self.flowing = True
        self.flow = self.FLOW_RATE

    def flow_off(self):
        self.Flowing = False
        self.flow = 0

    def detect_flow(self):
        return True if self.flow > 1 else False

    def detect_nonflow(self):
        return True if self.flow <= 0.5 else False

    def sample_water_level(self):
        self.updateWaterLevel()
        return self.water_level

    def sample_flow(self):
        return self.flow

    def updateWaterLevel(self):

        if (GPIO.input(self.PUMP_PIN)):
            self.water_level += (self.flow - self.water_levels[self.water_level_index])
            self.water_level_index += 1

            if self.water_level_index >= self.water_level_arr_size:
                self.water_level_index = 0
        else:
            self.water_level += self.flow

        if self.water_level >= self.HIGH_WATER_LEVEL:
            GPIO.output(self.HIGH_SENSOR_PIN, GPIO.HIGH)
            print("High water level")
        elif self.water_level <= self.LOW_WATER_LEVEL:
            GPIO.output(self.LOW_SENSOR_PIN, GPIO.LOW)
            print("Low water level")
        else:
            GPIO.output(self.HIGH_SENSOR_PIN, GPIO.LOW)
            GPIO.output(self.LOW_SENSOR_PIN, GPIO.HIGH)
            print("Normal water level")

        # if self.HIGH_WATER_LEVEL - self.water_level > self.FLOW_RATE:
        #     self.flow_on()
        # else:
        #     self.flow_off()

    def write_message(self, message, line=0):
        """
        Write message to LCD screen.
        """

        message = message.ljust(16)
        print("\n " + message + "\n")

    def change_background(self, color):
        """
        Change LCD screen background color.
        """

        colors = {
            "red": lambda: self.screen.setColor(255, 0, 0),
            "purple": lambda: self.screen.setColor(255, 0, 255),
            "blue": lambda: self.screen.setColor(0, 0, 255),
            "green": lambda: self.screen.setColor(0, 255, 0),
            "yellow": lambda: self.screen.setColor(255, 255, 0),
            "white": lambda: self.screen.setColor(255, 255, 255)
        }
        colors.get(color, colors["white"])()
