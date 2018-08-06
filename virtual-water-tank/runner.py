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
from importlib import import_module
from datetime import datetime
from pkg_resources import resource_filename
from bottle import Bottle, static_file, request, HTTPResponse, template, TEMPLATE_PATH
from twisted.internet import reactor
from .config import HARDWARE_CONFIG
from .scheduler import SCHEDULER
from .sms import send_sms
import RPi.GPIO as GPIO


class Runner(object):

    def __init__(self):

        self.project_name = "Watering System"

        board_name = HARDWARE_CONFIG.kit
        board_module = "{0}.hardware.{1}".format(__package__, board_name)
        board_class_name = "{0}Board".format(board_name.capitalize())
        self.board = getattr(import_module(board_module), board_class_name)()
        GPIO.setmode(GPIO.BOARD)

        self.schedule = {}

        self.water_level = []

        resource_package = __name__
        package_root = resource_filename(resource_package, "")
        TEMPLATE_PATH.insert(0, package_root)

        self.server = Bottle()
        self.server.route("/", callback=self.serve_index)
        self.server.route("/styles.css", callback=self.serve_css)
        self.server.route("/on", callback=self.get_on)
        self.server.route("/off", callback=self.get_off)
        self.server.route("/schedule", method="GET", callback=self.get_schedule)
        self.server.route("/schedule", method="PUT", callback=self.put_schedule)

        GPIO.setup(self.board.FLOW_PIN, GPIO.IN)
        GPIO.add_event_detect(self.board.FLOW_PIN, GPIO.BOTH, callback=self.flow_changed, bouncetime=300)

        GPIO.setup(self.board.PUMP_PIN, GPIO.IN)
        GPIO.add_event_detect(self.board.PUMP_PIN, GPIO.BOTH, callback=self.pump_changed, bouncetime=300) 

        GPIO.setup(self.board.TEST_PIN, GPIO.IN)
        GPIO.add_event_detect(self.board.TEST_PIN, GPIO.BOTH, callback=self.test_change, bouncetime=300)

        self.monitor_water_level_job = SCHEDULER.add_job(
            self.monitor_water_level,
            "interval",
            seconds=10
        )

        self.monitor_flow_job = SCHEDULER.add_job(
            self.monitor_flow,
            "interval",
            seconds=10
        )

    def start(self):
        """
        Start runner.
        """

        self.monitor_water_level()

        reactor.callInThread(lambda: self.server.run(
            host="0.0.0.0",
            port=3000
        ))

    # hardware methods

    def monitor_water_level(self):

        water_level_value = self.board.sample_water_level()

        print("Running scheduled water level check. Water level: {0}".format(water_level_value))

        self.water_level.append({
            "time": datetime.utcnow(),
            "value": water_level_value
        })

        self.water_level = self.water_level[-20:]

    def monitor_flow(self):

        flow_value = self.board.sample_flow()

        current_hour = datetime.utcnow().hour

        print("Running scheduled flow check. Flow: {0}".format(flow_value))

        flow_condition = self.schedule.get(str(current_hour), {
            "on": True,
            "off": False
        })

        flow_assertion = True if flow_condition["on"] else False

        if flow_assertion:
            self.check_on()
        else:
            self.check_off()

    def stop_water_flow(self, channel):
        print("\nTurning flow off\n")
        self.board.flow_off()

    def start_water_flow(self, channel):
        print("\nTurning flow on\n")
        self.board.flow_on()

    def check_on(self):

        # assert on condition
        if not self.board.detect_flow():
            print("Flow on check failed.\n")
        else:
            print("Flow on check passed.\n")

    def check_off(self):

        # assert off condition
        if not self.board.detect_nonflow():
            print("Flow off check failed.\n")
        else:
            print("Flow off check passed.\n")

    def alert(self):

        print("Watering alert triggered.")
        self.board.write_message("Watering system alert")
        send_sms("Watering system alert.")

    # server methods

    def serve_index(self):
        """
        Serve the 'index.html' file.
        """

        output = template("index", water_level=self.water_level)
        return output

    def serve_css(self):
        """
        Serve the 'styles.css' file.
        """

        resource_package = __name__
        resource_path = "styles.css"
        package_root = resource_filename(resource_package, "")
        return static_file(resource_path, root=package_root)

    def get_on(self):

        print("Received manual pump on.")
        self.board.pump_on()
        return HTTPResponse(status=200)

    def get_off(self):

        print("Received manual pump off.")
        self.board.pump_off()
        return HTTPResponse(status=200)

    def flow_changed(self, channel):
        if (GPIO.input(self.board.FLOW_PIN)):
            self.start_water_flow(self)
        else:
            self.stop_water_flow(self)

    def pump_changed(self, channel):
        if (GPIO.input(self.board.PUMP_PIN)):
            self.get_on()
        else:
            self.get_off()

    def test_change(self, channel):
        if (GPIO.input(self.board.TEST_PIN)):
            print("yeet test")
        else:
            print("ohhh noo")

    def get_schedule(self):

        return {
            "data": self.schedule
        }

    def put_schedule(self):

        print("Received updated pump schedule.")
        self.schedule = request.json
        return HTTPResponse(status=200)
