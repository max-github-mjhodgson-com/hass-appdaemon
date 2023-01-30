# Car Fordpass Control Script
# Max Hodgson 2023

import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import timedelta
from datetime import datetime
import globals

# Fordpass message formats:
# SecuriAlert - Driver door opened: 07/18/2022 06:50:42 AM
# Date and Time:
# 01/23/2023 09:32:19 AM


class Car(hass.Hass):

  def initialize(self):
    self.log("=" * globals.log_partition_line_length)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    global FunctionLibrary  
    FunctionLibrary = self.get_app("function_library")

    global GarageLibrary
    GarageLibrary = self.get_app("garage")
    
    global longterm_update_handler
    self.longterm_update_handler = 0
    global shortterm_update_handler
    self.shortterm_update_handler = 0
    global longterm_time_gap
    longterm_time_gap = 4 # Hours
    global shortterm_time_gap
    shortterm_time_gap = 5 # Minutes

    global ignition_status
    ignition_status = self.get_state(globals.car_ignition_status)
    if ignition_status != "unavailable":
      self.log("Initial ignition status: " + ignition_status)
    else:
      self.log("Car data is unavailable.")

    global lock_status
    lock_status = self.get_state(globals.car_lock)
    if lock_status != "unavailable":
      self.log("Initial door lock status: " + lock_status)

    global window_status
    window_status = self.get_state(globals.car_window_position, attribute="state")
    if window_status != "unavailable":
      self.log("Window status: " + str(window_status))

    global alarm_status
    alarm_status = self.get_state(globals.car_alarm)
    if alarm_status != "unavailable":
      self.log("Initial alarm status: " + alarm_status)

    global battery_status
    battery_status = self.get_state(globals.car_battery)
    self.log(battery_status)
    if battery_status == "STATUS_LOW":
      self.log("Car battery is low.")
      self.enable_long_timer()
    
    #global current_message_count
    current_message_count = self.get_state(globals.car_messages)
    if current_message_count != "unavailable":
      securialert_status, message_new, return_message = self.get_fordpass_messages(current_message_count)
      self.log("securialert_status: " + securialert_status)
      self.log("message_new: " + message_new)
      self.log ("Return message: " + return_message)

    # Get current car position
    global car_current_position_longitude
    car_current_position_longitude = self.get_state(globals.car_tracker, attribute="longitude")
    self.log("Longtitude: " + str(car_current_position_longitude))
    global car_current_position_latitude
    car_current_position_latitude = self.get_state(globals.car_tracker, attribute="latitude")
    self.log("Latitude: " + str(car_current_position_latitude))
    global car_position_current_zone
    car_position_current_zone = self.get_state(globals.car_tracker)
    self.log("Car postition current zone (if any): " + str(car_position_current_zone))
    global car_position_last_change
    car_position_last_change = self.get_state(globals.car_tracker, attribute="timestamp")
    self.log("Car position last change: " + str(car_position_last_change))
    
    #if ignition_status == "Off" or alarm_status == "SET":
    if alarm_status == "SET" and window_status == "Closed":
      self.log("Run long term timer.")
      self.enable_long_timer()
    elif alarm_status == "NOTSET":
    #elif ignition_status == "run":
      self.log("Short term timer.")
      self.enable_short_timer()

    self.unlock_handle = self.listen_state(self.on_car_unlocked, globals.car_lock, old = "locked", new = "unlocked", duration = 30)
    self.lock_handle = self.listen_state(self.on_car_locked, globals.car_lock, old = "unlocked", new = "locked", duration = 30)
    self.ignition_handle01 = self.listen_state(self.on_ignition_change, globals.car_ignition_status)
    self.listen_for_ford_pass_refresh_button = self.listen_state(self.on_button_refresh_status_pressed, globals.car_refresh_button)
    self.listen_state(self.on_message_count_change, globals.car_messages)
    #, old = current_message_count)
    self.listen_state(self.on_battery_state_changed, globals.car_battery)
    self.alarm_off_handle = self.listen_state(self.on_car_alarm_change, globals.car_alarm_status, new = "NOTSET", old = "SET")
    self.car_tracker_zone_change_handler = self.listen_state(self.on_zone_change, globals.car_tracker, duration = 30)
    self.car_window_state_handler = self.listen_state(self.on_window_state_change, globals.car_window_position, attribute = "state")

###############################################################################################################
# Callback functions:
###############################################################################################################
  def on_car_unlocked(self, entity, attribute, old, new, kwargs):
    self.log("Car Unlocked.")
    lock_status = new
    ignition_status = self.get_state(globals.car_ignition_status)
    self.log("Ignition status: " + ignition_status)
    alarm_status = self.get_state(globals.car_alarm_status)
    self.log("Alarm status: " + alarm_status)
    if FunctionLibrary.is_house_occupied == 2 and FunctionLibrary.is_car_at_home == 0:
      self.log("Car unlocked and we are asleep.")
      self.call_service(globals.max_app, title = "Car unlocked.",\
                                         message = "TTS",\
                                         data = {"media_stream": "alarm_stream_max",\
                                                 "tts_text": "WARNING: Car has been unlocked."})
      # Check in x hours if car is still unlocked, if ignition is off.

  def on_car_locked(self, entity, attribute, old, new, kwargs):
    ignition_status = self.get_state(globals.car_ignition_status)
    if ignition_status == "Off":
      self.log("Car locked.")
    elif ignition_status == "Run":
      self.log("Car auto-locked.")

  def on_car_alarm_change(self, entity, attribute, old, new, kwargs):
    if old == "SET":
      self.log("Alarm Unset.")
      if new == "NOTSET":
        self.log("Car alarm is OFF.")
        self.enable_short_timer()
        #self.set_state("sensor.fordpass_alarm_sensor", state="disarmed", attributes = {"friendly_name": "Ford Pass Alarm Sensor"})
        self.call_service(globals.max_app, title = "Car alarm disarmed.",\
                                           message = "TTS",\
                                          data = {"media_stream": "alarm_stream_max",\
                                                  "tts_text": "Car alarm has been disarmed."})
      elif new == "SET":
        self.log("Car alarm is SET.")
        # and windows are closed?
        window_status = self.get_state(globals.car_window_position, attribute="all")
        if window_status == "closed":
          self.enable_long_timer()
        elif window_status == "open":
          self.log("Windows are still open.")
          self.enable_short_timer()

  def on_ignition_change(self, entity, attribute, old, new, kwargs):
    if old != "unavailable" or new != "unavailable":
      self.log("On ignition change: " + str(old))
      ignition_status = new
      self.log("Ignition status has changed: " + ignition_status)
      lock_status = self.get_state(globals.car_lock)
      self.log("Lock status: " + lock_status)
      # To do:
      # Get and store current location.
      # Compare current location to test if car is moving.

  def on_battery_state_changed(self, entity, attribute, old, new, kwargs):
    if new == "STATUS_LOW" and old != "unavailable":
      self.log("Car battery is low.")
      ignition_status = self.get_state(globals.car_ignition_status)
      if ignition_status == "Off":
        self.enable_long_timer()
      self.call_service(globals.max_app, title = "Car battery is low.",\
                                         message = "TTS",\
                                         data = {"media_stream": "alarm_stream",\
                                                 "tts_text": "Car battery is low."})

  def on_button_refresh_status_pressed(self, entity, attribute, old, new, kwargs):
    self.log("Refresh pressed.")
    self.call_service(globals.car_refresh) 

  def on_message_count_change(self, entity, attribute, old, new, kwargs):
    current_message_count = self.get_state(globals.car_messages)
    self.log("Old message count: " + str(old))
    self.log("New message count: " + str(new))
    if old != "unavailable" or new != "unavailable":
      if new > old:
        self.log("New message has arrived.")
        current_message_count = self.get_state(globals.car_messages)
        securialert_status, message_new, return_message = self.get_fordpass_messages(current_message_count)
        self.log("securialert_status: " + securialert_status)  # To do: Raise a noticable notification
        self.log("message_new: " + message_new) # To do: Raise a notification if message is newer than x hours.
        self.log ("Return message: " + return_message)
        self.log("Current number of messages: " + current_message_count)
      elif new < old:
        self.log("Message deleted. Current number of messages: " + str(current_message_count))

  def on_zone_change(self, entity, attribute, old, new, kwargs):
    if old != "unavailable" or new != "unavailable":
      self.log("Zone changed: " + new)
      if old == "Home_b":
        self.log("Home B departed.")
      if old == "home":
        self.log("Home L departed.")
        GarageLibrary.close_garage_and_power_off()
      if old == "PBM":
        self.log("PBM Location departed.")
      if new == "home":
        self.log("Home L arrived.")
        GarageLibrary.switch_on_garage_door()
      elif new == "Home_B":
        self.log("Home B arrived.")
      elif new == "PBM":
        self.log("PBM Location arrived.")
    else:
      self.log("Current/Previous Location unavailable")
  
  def on_window_state_change(self, entity, attribute, old, new, kwargs):
      alarm_status = self.get_state(globals.car_alarm_status)
      if alarm_status == "SET":
        self.log("Window state has changed: " + str(new))
        if old == "Open" and new == "Closed":
          # To do: Change sensor to turn off builtin Home Assistant alerts.
          self.log("Windows closed.")
          self.enable_long_timer()
        elif old == "Closed" and new == "Open":
          # To do: Change sensor to turn on builtin Home Assistant alerts.
          self.log("Windows opened.")
          self.enable_short_timer()
  
  def run_update_car_status(self, kwargs):
    self.get_car_status()
    
###############################################################################################################
# Other functions:
###############################################################################################################
  def refresh_car_status(self, kwargs):
    self.log("Refresh car status.")
    self.call_service(globals.car_refresh)
    self.log("Four hour handler id: " + str(self.longterm_update_handler))
    self.log("Five minute handler id: " + str(self.shortterm_update_handler))
    self.run_in(self.run_update_car_status, 30)

  def get_car_status(self):
    ignition_status = self.get_state(globals.car_ignition_status)
    if ignition_status != "unavailable":
      self.log("=" * 60)
      self.log("Current car status:")
      self.log("Ignition state: " + str(ignition_status))
      lock_status = self.get_state(globals.car_lock)
      self.log("Lock state: " + str(lock_status))
      alarm_status = self.get_state(globals.car_alarm)
      self.log("Alarm status: " + alarm_status)
      window_status = self.get_state(globals.car_window_position, attribute="state")
      self.log("Window status: " + str(window_status))
      global door_status
      door_status = self.get_state(globals.car_door_status, attribute="state")
      self.log("Door status: " + str(door_status))
      battery_status = self.get_state(globals.car_battery)
      self.log("Battery status: " + str(battery_status))
      car_current_position_longitude = self.get_state(globals.car_tracker, attribute="longitude")
      car_current_position_latitude = self.get_state(globals.car_tracker, attribute="latitude")
      self.log("Longitude: " + str(car_current_position_longitude) + " , Latitude: " + str(car_current_position_latitude))
      car_position_current_zone = self.get_state(globals.car_tracker)
      self.log("Car postition current zone (if any): " + str(car_position_current_zone))
      car_position_last_change = self.get_state(globals.car_tracker, attribute="timestamp")
      self.log("Car position last change: " + str(car_position_last_change))
    else:
      self.log("Car data unavailable.")
    self.log("=" * 60)
    return alarm_status, window_status

  def enable_short_timer(self):
    self.log("Enabling Short Term Timer.")
    if self.longterm_update_handler != 0:
      self.log("Cancelling long timer.")
      self.cancel_timer(self.longterm_update_handler)
    self.shortterm_update_handler = self.run_every(self.refresh_car_status, "now", shortterm_time_gap * 60)
    self.longterm_update_handler = 0

  def enable_long_timer(self):
    self.log("Enabling Long Term Timer.")
    if self.shortterm_update_handler != 0:
      self.log("Cancelling short timer.")
      self.cancel_timer(self.shortterm_update_handler)
    self.longterm_update_handler = self.run_every(self.refresh_car_status, "now", longterm_time_gap * 60 * 60)
    self.shortterm_update_handler = 0

  
  def get_fordpass_messages(self, number_of_messages):
    self.log("Number of messages:" + str(number_of_messages))
    
    securialert_status = "off"
    message_new = "off"  # To do
    return_message = "None"

    current_messages = self.get_state(globals.car_messages, attribute = "all")
    self.log("Current messages: " + str(current_messages))

    current_messages = self.get_state(globals.car_messages, attribute = "all")
    self.log("Current messages: " + str(current_messages))
    message_list = current_messages["attributes"]
    self.log(message_list.keys())
    first_message = list(message_list.keys())[0]
    message_date_and_time = list(message_list.values())[0]
    self.log("Message date and time: " + str(message_date_and_time))
    self.log("First message: " + str(first_message))

    if first_message == "Remote features disabled to preserve battery":
      self.log("Remote features disabled.")
      return_message = first_message
    elif first_message == "Tyre Pressure Monitor System Warning":
      self.log("Tyre pressure warning.")
      return_message = first_message
    elif first_message.find("SecuriAlert") != -1:
      securialert_status = "on"
      alert_item_start = first_message.index("-") + 2
      alert_item_end = first_message.index(":")
      alert_item = first_message[alert_item_start:alert_item_end]
      self.log("Alert Item: " + str(alert_item))
      alert_date = first_message[alert_item_end + 2:alert_item_end + 10]
      self.log("Alert Date: " + str(alert_date))
      alert_time = first_message[alert_item_end + 13:alert_item_end + 24]
      self.log("Alert Time" + str(alert_time))
      self.log("SecuriAlert")
      return_message = alert_item
    # self.set_state("sensor.fordpass_last_message", state="Messages", attributes = {"friendly_name": "Ford Pass Last Message", "detail": None, "last_message": first_message})
    # TO DO: Clear alert in x hours.
    return securialert_status, message_new, return_message
