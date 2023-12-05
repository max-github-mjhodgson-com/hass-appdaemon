# Car Fordpass Control App
#
# Version: 10052023.01
# Max Hodgson 2023

import appdaemon.plugins.hass.hassapi as hass

import os
import time

import globals_module as globals

#from datetime import timedelta
from datetime import date, datetime
from geopy.geocoders import Nominatim


# Fordpass message formats:
# SecuriAlert - Driver door opened: 07/18/2022 06:50:42 AM
# Date and Time:
# 01/23/2023 09:32:19 AM


class Car(hass.Hass):

  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)

    # Load external app libraries:    
    self.function_library = self.get_app("function_library")
    self.garage_library = self.get_app("garage")
    
    # Setup some variables:
    self.longterm_update_handler = 0
    self.shortterm_update_handler = 0
    self.longterm_time_gap = 4 # Hours
    self.shortterm_time_gap = 5 # Minutes
    self.data_unavailable_message = "Car data is unavailable."
    

    # Initial setup:
    self.ignition_status = self.get_state(globals.car_ignition_status)
    if self.ignition_status != "unavailable":
      self.log("Initial ignition status: " + self.ignition_status)
    else:
      self.log(self.data_unavailable_message)
  
    self.lock_status = self.get_state(globals.fordpass_car_lock)
    if self.lock_status != "unavailable":
      self.log("Initial door lock status: " + self.lock_status)
    else:
      self.log(self.data_unavailable_message)

    self.window_status = self.get_state(globals.car_window_position, attribute = "state")
    if self.window_status != "unavailable":
      self.log("Window status: " + str(self.window_status))
    else:
      self.log(self.data_unavailable_message)

    self.alarm_status = self.get_state(globals.car_alarm_status)
    if self.alarm_status != "unavailable":
      self.log("Initial alarm status: " + self.alarm_status)
    else:
      self.log(self.data_unavailable_message)
    if self.alarm_status in globals.fordpass_alarm_armed and self.window_status == "Closed":
       self.log("Run long term timer.")
       self.enable_long_timer()
    elif self.alarm_status == globals.fordpass_alarm_disarmed:
       self.log("Short term timer.")
       self.enable_short_timer()
    

    self.battery_status = self.get_state(globals.fordpass_battery_level)
    if self.battery_status != "unavailable":
      #self.log(battery_status)
      if int(self.battery_status) <= 50:
        self.log("Car battery is low.")
        self.enable_long_timer()
    else:
      self.log(self.data_unavailable_message)
    
    self.current_message_count = self.get_state(globals.car_messages)
    if self.current_message_count != "unavailable":
      securialert_status, message_new, return_message = self.get_fordpass_messages(self.current_message_count)
      self.log("securialert_status: " + securialert_status)
      self.log("message_new: " + message_new)
      self.log ("Return message: " + return_message)

    # Get current car position
    self.car_current_position_longitude = self.get_state(globals.car_tracker, attribute="longitude")
    self.log("Longtitude: " + str(self.car_current_position_longitude))
    self.car_current_position_latitude = self.get_state(globals.car_tracker, attribute="latitude")
    self.log("Latitude: " + str(self.car_current_position_latitude))
    self.car_position_current_zone = self.get_state(globals.car_tracker)
    self.log("Car postition current zone (if any): " + str(self.car_position_current_zone))
    self.car_position_last_change = self.get_state(globals.car_tracker, attribute = "timestamp")
    self.log("Car position last change: " + str(self.car_position_last_change))

    # State monitors:
    self.unlock_handler = self.listen_state(self.on_car_unlocked, globals.fordpass_car_lock, old = "locked", new = "unlocked", duration = 30)
    self.lock_handler = self.listen_state(self.on_car_locked, globals.fordpass_car_lock, old = "unlocked", new = "locked", duration = 30)
    self.ignition_handler01 = self.listen_state(self.on_ignition_change, globals.car_ignition_status)
    self.listen_for_ford_pass_refresh_button = self.listen_state(self.on_button_refresh_status_pressed, globals.car_refresh_button)
    self.listen_state(self.on_message_count_change, globals.car_messages)
    self.listen_state(self.on_battery_state_changed, globals.fordpass_battery_level)
    self.alarm_off_handler = self.listen_state(self.on_car_alarm_change, globals.car_alarm_status) #, new = "NOTSET", old = "SET")
    self.new_refresh_state_selected_handler = self.listen_state(self.on_refresh_state_changed, globals.fordpass_refresh_status)

    self.car_tracker_entity = self.get_entity(globals.car_tracker)
    self.car_tracker_zone_change_handler = self.car_tracker_entity.listen_state(self.on_zone_change, duration = 30)
    
    self.car_window_state_handler = self.listen_state(self.on_window_state_change, globals.car_window_position, attribute = "state")
    self.refresh_status_change = self.listen_state(self.on_refresh_status_change, globals.fordpass_refresh_status, new = "Off") #, old = lambda x : x not in ["unknown", "unavailable"], duration = 10)
    #self.car_left_unlocked_handler = self.listen_state(self.on_car_left_unlocked, )
    
    # Reset counter:
    reset_counter_handler = self.run_daily(self.on_is_it_the_first_of_the_month, "00:01:00")

###############################################################################################################
# Callback functions:
###############################################################################################################
  def on_car_unlocked(self, entity, attribute, old, new, kwargs):
    self.log("Car Unlocked.")
    # Testing:
    #self.call_service(globals.max_app, title = "Car unlocked.",\
    #                                     message = "TTS",\
    #                                     data = {"media_stream": "alarm_stream_max",\
    #                                             "tts_text": "WARNING: Car has been unlocked."})
    lock_status = new
    ignition_status = self.get_state(globals.car_ignition_status)
    self.log("Ignition status: " + ignition_status)
    alarm_status = self.get_state(globals.car_alarm_status)
    self.log("Alarm status: " + alarm_status)
    if self.function_library.is_house_occupied == 2 and self.function_library.is_car_at_home == 0:
      self.log("Car unlocked and we are asleep.")
      self.call_service(globals.max_app, title = "Car unlocked.",\
                                         message = "TTS",\
                                         data = {"media_stream": "alarm_stream_max",\
                                                 "tts_text": "WARNING: Car has been unlocked."})
      # Check in x hours if car is still unlocked, if ignition is off.
      # Create conditions to sound a house alarm.

  def on_car_locked(self, entity, attribute, old, new, kwargs):
    ignition_status = self.get_state(globals.car_ignition_status)
    if ignition_status == "Off":
      self.log("Car locked.")
    elif ignition_status == "Run":
      self.log("Car auto-locked.")

  def on_car_alarm_change(self, entity, attribute, old, new, kwargs):
    self.log("Car alarm status change, new, old: " +str(new) + ", " + str(old))
    window_status = self.get_state(globals.car_window_position, attribute = "state")
    self.log("Window status: " + str(window_status))
    if old in globals.fordpass_alarm_armed and new == globals.fordpass_alarm_disarmed:
      self.log("Car alarm is disarmed.")
      self.enable_short_timer()
      car_kit_connected = self.get_state(globals.max_phone_bluetooth, attribute = "connected_paired_devices")
      self.log("Car kit: " + str(car_kit_connected))
      if globals.max_car_kit in car_kit_connected:
        self.log("Car kit connected, not sending alert.")
      else:
        #self.set_state("sensor.fordpass_alarm_sensor", state="disarmed", attributes = {"friendly_name": "Ford Pass Alarm Sensor"})
        self.call_service(globals.max_app, title = "Car alarm disarmed.",\
                                           message = "TTS",\
                                           data = {"media_stream": "alarm_stream_max",\
                                                   "tts_text": "Car alarm has been disarmed."})
    if new in globals.fordpass_alarm_armed : # and old == "UNSET":
       self.log("Car alarm is ARMED.")
       # and windows are closed?
       if window_status == "Closed":
         self.log("Windows are closed.")
         self.enable_long_timer()
       elif window_status == "Open":
         self.log("Windows are still open.")
         self.enable_short_timer()

  def on_ignition_change(self, entity, attribute, old, new, kwargs):
    if old != "unavailable" or new != "unavailable":
      self.log("On ignition change: " + str(old))
      ignition_status = new
      self.log("Ignition status has changed: " + ignition_status)
      lock_status = self.get_state(globals.fordpass_car_lock)
      self.log("Lock status: " + lock_status)
      if new == "RUN":
        self.log("Car engine run.")
        self.enable_short_timer()
      # To do:
      # Get and store current location.
      # Compare current location to test if car is moving.

  def on_battery_state_changed(self, entity, attribute, old, new, kwargs):
    if old != "unavailable" or new != "unavailable":
      if int(new) <= 50:
        self.log("Car battery is low.")
        ignition_status = self.get_state(globals.car_ignition_status)
        if ignition_status == "Off":
          self.enable_long_timer()
        self.call_service(globals.max_app,  title = "Car battery is low.",\
                                            message = "TTS",\
                                            data = {"media_stream": "alarm_stream",\
                                                    "tts_text": "Car battery is low."})

  def on_button_refresh_status_pressed(self, entity, attribute, old, new, kwargs):
    self.log("Refresh pressed.")
    self.call_service(globals.car_refresh)
    self.call_service("counter/increment", entity_id = globals.fordpass_refresh_counter)
    self.run_in(self.run_update_car_status, 30)

  def on_message_count_change(self, entity, attribute, old, new, kwargs):
    current_message_count = self.get_state(globals.car_messages)
    self.log("Old message count: " + str(old))
    self.log("New message count: " + str(new))
    if old == "unavailable" or new == "unavailable":
      self.log("Invalid new or old value.")
    else:
      if new > old:
        self.log("New message has arrived.")
        current_message_count = self.get_state(globals.car_messages)
        securialert_status, message_new, return_message = self.get_fordpass_messages(current_message_count)  # Securialert is no longer working.
        self.log("securialert_status: " + securialert_status)  # To do: Raise a noticable notification
        if securialert_status == "on":
          self.log("Security alert: " + str(return_message))
        self.log("message_new: " + message_new) # To do: Raise a notification if message is newer than x hours.
        self.log ("Return message: " + return_message)
        self.log("Current number of messages: " + current_message_count)
      elif new < old:
        self.log("Message deleted. Current number of messages: " + str(current_message_count))

  def on_zone_change(self, entity, attribute, old, new, kwargs):
    zone_arrived = False
    if old != "unavailable" and new != "unavailable":
      self.log("Zone changed: (New): " + new + "(Old): " + old)
      if old == "Home_b":
        self.log("Home B departed.")
      if old == "Home":
        self.log("Home L departed.")
        self.garage_library.close_garage_and_power_off()
      if old == "PBM":
        self.log("PBM Location departed.")
      if new == "Home":
        self.log("Home L arrived.")
        zone_arrived = True
        self.garage_library.switch_on_garage_door()
      elif new == "Home_B":
        self.log("Home B arrived.")
        zone_arrived = True
      elif new == "PBM":
        self.log("PBM Location arrived.")
        zone_arrived = True
    else:
      self.log("Current/Previous Location unavailable")
    if zone_arrived == True:
      self.call_service(globals.max_app, message = "request_location_update")
  
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

  def on_refresh_state_changed(self, entity, attribute, old, new, kwargs):
    self.log("Refresh state changed.")
    self.log("Old: " + str(old))
    self.log("New: " + str(new))
    if old == "Off":
      match new:
        case "Long Timer":
          self.log("Long timer selected.")
          self.enable_long_timer()
        case "Short Timer":
          self.log("Short timer selected.")
          self.enable_short_timer()
  
###############################################################################################################
# Other functions:
###############################################################################################################

  def run_update_car_status(self, kwargs):
    self.get_car_status()

  def on_is_it_the_first_of_the_month(self, kwargs):
    todays_date = date.today()
    todays_day = todays_date.day
    current_counter = int(self.get_state(globals.fordpass_refresh_counter))
    if current_counter > int(19000):
      self.turn_on(globals.fordpass_refresh_disable)
    if todays_day == 1:
      self.log("It is counter reset day today.")
      self.call_service("counter/reset", entity_id = globals.fordpass_refresh_counter)
      self.turn_off(globals.fordpass_refresh_disable)

  def on_refresh_status_change(self, entity, attribute, old, new, kwargs):
    self.log("Refresh status switched off.")
    self.log("Four hour handler id: " + str(self.longterm_update_handler))
    self.log("Five minute handler id: " + str(self.shortterm_update_handler))
    if self.longterm_update_handler != 0:
      self.log("Long term handler is active.")
      cancel_handler = self.longterm_update_handler
    elif self.shortterm_update_handler != 0:
      self.log("Short term handler is active.")
      cancel_handler = self.shortterm_update_handler
    self.log("Cancel handler: " + str(cancel_handler))
    self.cancel_listen_state(cancel_handler)

  def on_tyre_pressure_low(self, entity, attribute, old, new, cb_args):
    self.log("Car tyre pressure low.")
    #self.set_state("sensor.fordpass_alarm_sensor", state="disarmed", attributes = {"friendly_name": "Ford Pass Alarm Sensor"})

  def on_car_left_unlocked(self, entity, attribute, old, new, cb_args):
    self.log("Car left unlocked.")
    if self.function_library.is_car_at_home == 0:
      car_location = self.get_state(globals.car_tracker)
      self.log("Car is at: " + str(car_location))
    
###############################################################################################################
# Other functions:
###############################################################################################################
  def refresh_car_status(self, kwargs):
    self.log("Refresh car status.")
    battery_level = int(self.get_state(globals.fordpass_battery_level))
    if self.get_state(globals.fordpass_refresh_disable) == "off" or battery_level < 52: 
      self.call_service(globals.car_refresh)
      self.call_service("counter/increment", entity_id = globals.fordpass_refresh_counter)
      self.log("Four hour handler id: " + str(self.longterm_update_handler))
      self.log("Five minute handler id: " + str(self.shortterm_update_handler))
      self.run_in(self.run_update_car_status, 30)
    else:
      self.log("Refresh disabled.")

  def get_car_status(self):
    ignition_status = self.get_state(globals.car_ignition_status)
    alarm_status = ""
    window_status = ""
    if ignition_status != "unavailable":
      self.log("=" * 60)
      self.log("Current car status:")
      deepsleep_status = self.get_state(globals.fordpass_deep_sleep)
      if deepsleep_status == globals.fordpass_car_deepsleep_on:
        self.log("Car is in deepsleep mode, data will be out of date.")
      self.log("Ignition state: " + str(ignition_status))
      lock_status = self.get_state(globals.fordpass_car_lock)
      self.log("Lock state: " + str(lock_status))
      alarm_status = self.get_state(globals.car_alarm_status)
      self.log("Alarm status: " + alarm_status)
      window_status = self.get_state(globals.car_window_position, attribute="state")
      self.log("Window status: " + str(window_status))
      global door_status
      door_status = self.get_state(globals.car_door_status, attribute="state")
      self.log("Door status: " + str(door_status))
      battery_status = self.get_state(globals.fordpass_battery_level)
      self.log("Battery level: " + str(battery_status))
      battery_voltage = self.get_state(globals.fordpass_battery_voltage)
      self.log("Battery voltage: " + str(battery_voltage))
      self.car_current_position_longitude = self.get_state(globals.car_tracker, attribute="longitude")
      self.car_current_position_latitude = self.get_state(globals.car_tracker, attribute="latitude")
      self.log("Longitude: " + str(self.car_current_position_longitude) + " , Latitude: " + str(self.car_current_position_latitude))
      self.car_position_current_zone = self.get_state(globals.car_tracker)
      self.log("Car position current zone (if any): " + str(self.car_position_current_zone))
      self.car_position_last_change = self.get_state(globals.car_tracker, attribute="timestamp")
      self.log("Car position last change: " + str(self.car_position_last_change))
      #self.car_direction - self.get_state(globals.fordpass_car_direction)
      #self.log("Car direction: " + str(self.car_direction))
    else:
      self.log("Car data unavailable.")
    self.log("=" * 60)
    return alarm_status, window_status

  def enable_short_timer(self):
    if self.get_state(globals.fordpass_refresh_disable) != "Off":
      self.log("Enabling Short Term Timer.")
      self.log("Long-term handler: " +str(self.longterm_update_handler))
      if self.longterm_update_handler != 0:
        self.log("Cancelling long timer.")
        self.cancel_timer(self.longterm_update_handler)
      if self.shortterm_update_handler == 0:
        self.log("Timer disabled.")
        self.shortterm_update_handler = self.run_every(self.refresh_car_status, "now", self.shortterm_time_gap * 60)
      self.longterm_update_handler = 0
      self.select_option(globals.fordpass_refresh_status, "Short Timer")
    else:
      self.log("Auto refresh is disabled, not setting up any timers.")

  def enable_long_timer(self):
    if self.get_state(globals.fordpass_refresh_disable) != "Off":
      self.log("Enabling Long Term Timer.")
      self.log("Short-term handler: " +str(self.shortterm_update_handler))
      if self.shortterm_update_handler != 0:
        self.log("Cancelling short timer.")
        self.cancel_timer(self.shortterm_update_handler)
      self.log("Long timer handler: " + str(self.longterm_update_handler))
      if self.longterm_update_handler == 0:
        self.longterm_update_handler = self.run_every(self.refresh_car_status, "now", self.longterm_time_gap * 60 * 60)
      self.shortterm_update_handler = 0
      self.select_option(globals.fordpass_refresh_status, "Long Timer")
    else:
      self.log("Auto refresh is disabled, not setting up any timers.")
  
  def get_fordpass_messages(self, number_of_messages):
    self.log("Number of messages:" + str(number_of_messages))    
    securialert_status = "off"
    message_new = "off"  # To do
    return_message = "None"

    #current_messages = self.get_state(globals.car_messages, attribute = "all")
    #self.log("Current messages: " + str(current_messages))

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
      if first_message == "SecuriAlert will no longer be available ":
        pass
      else:
        self.log("First message: " + first_message)
        securialert_status = "on"
        alert_item_start = first_message.index("-") + 2
        if first_message.find(":") == True:
          alert_item_end = first_message.index(":")
        else:
          alert_item_end = len(first_message)
          alert_item = first_message[alert_item_start:]
          self.log("Alert item: " + str(alert_item))
          alert_sub_item = alert_item.split("- ")
          self.log("Alert sub-item: " + str(alert_sub_item))
          #alert_date = first_message[alert_item_end + 2:alert_item_end + 10]
          alert_date_and_time = message_date_and_time.split(" ",1)
          alert_date = alert_date_and_time[0]
          self.log("Alert Date: " + str(alert_date))
          #alert_time = first_message[alert_item_end + 13:alert_item_end + 24]
          alert_time = alert_date_and_time[1]
          self.log("Alert Time: " + str(alert_time))
          self.log("SecuriAlert")
          return_message = alert_item
    # self.set_state("sensor.fordpass_last_message", state="Messages", attributes = {"friendly_name": "Ford Pass Last Message", "detail": None, "last_message": first_message})
    # TO DO: Clear alert in x hours.
    return securialert_status, message_new, return_message

  def lock_car(self):
    self.log("I will lock the car.")
    self.call_service("lock/lock", entity_id = globals.fordpass_car_lock)

  def unlock_car(self):
    self.log("I will unlock the car.")
    self.call_service("lock/unlock", entity_id = globals.fordpass_car_lock)

  def get_car_address(self):
    current_location = (self.get_state(globals.car_tracker, attribute = "latitude"), self.get_state(globals.car_tracker, attribute = "longitude"))
    geolocator = Nominatim(user_agent = "appdaemon")
    car_address = geolocator.reverse(current_location)
    return car_address
