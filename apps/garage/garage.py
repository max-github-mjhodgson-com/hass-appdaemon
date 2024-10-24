# Garage Control App
#
# Max Hodgson 2024
# Version: 010824.01
#
# This will montor:
# Garage door open.
# Garage door closed.
# Garage motion (for light etc).
# Garage door power on.
# Garage door power off.
# Garage Light on.
# Garage Light off.
# Garage Door Timer
# Garage Door Power Timer
# Android App Click Events.
#
# Listens for these events:
#   power_on_garage_door_and_open
#   close_garage_and_power_off
# Events:
#  garage_open_air_gap
#
# It also provides open, close and status functions to other Appdeamon apps.
#

import appdaemon.plugins.hass.hassapi as hass
import os, time

import globals_module as globals

from datetime import datetime

class Garage(hass.Hass):
 
  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)
    
    # Load external AppDaemon libraries: 
    self.function_library = self.get_app("function_library")
    
    # In seconds, how long the garage door should take to close:
    self.garage_door_close_time_check = 30

    self.log(globals.garage_input_number_garage_close_timer)
    self.log(globals.garage_input_number_garage_open_timer)
    self.set_value(globals.garage_input_number_garage_close_timer, 0)
    self.set_value(globals.garage_input_number_garage_open_timer, 0)

    # Setup variables:
    self.run_in_the_future_handler = 0
    self.airgap_close_handler = 0
    self.air_gap_time_delay = 1.7

    # State monitors
    self.listen_state(self.on_garage_door_open, globals.garage_door_entity, new = "open", old = "closed", immediate = True)
    self.listen_state(self.on_garage_door_closed, globals.garage_door_entity, new = "closed", old = "open", immediate = True)
    self.listen_state(self.on_garage_door_power_off, globals.garage_door_power_switch, new = "off", old = "on", immediate = True)
    self.listen_state(self.on_garage_door_power_on, globals.garage_door_power_switch, new = "on", old = "off", immediate = True)
    self.listen_state(self.on_motion_detected, globals.garage_motion_sensor, new = "on", old = "off")
    self.listen_state(self.on_motion_not_detected, globals.garage_motion_sensor, new = "off", old = "on") 
    self.listen_state(self.on_garage_light_on, globals.garage_light_entity, new = "on", old = "off", immediate = True)
    self.listen_state(self.on_garage_light_off, globals.garage_light_entity, new = "off", old = "on" , immediate = True)
    self.listen_state(self.auto_close_timer_events, "timer.garage_door_auto_close_no_motion")
    self.listen_state(self.on_button_power_on_and_open_garage, 'input_button.power_on_garage_door_and_open')
    #self.listen_for_power_on_garage_door_and_open_button_press_handler = self.listen_state(self.button_test_press, 'input_button.power_on_garage_door_and_open')
    self.listen_state(self.on_button_close_garage_and_power_off, 'input_button.close_garage_door_and_power_off')

    # Event Monitors
    self.listen_event(self.on_garage_door_power_timer_finished, "timer.finished", entity_id = globals.garage_door_power_timer )
    self.listen_event(self.on_garage_light_timer_finished, "timer.finished", entity_id = globals.garage_light_timer ) 
    self.listen_event(self.on_garage_door_no_motion_timer_finished, "timer.finished", entity_id = globals.garage_door_no_motion_timer )
    #self.listen_for_garage_power_on_and_open_event_handler = self.listen_event(self.on_power_on_and_open_garage, "power_on_garage_door_and_open")
    #self.listen_for_garage_door_close_and_power_off_event_handler = self.listen_event(self.on_close_garage_and_power_off, "close_garage_door_and_power_off")
    self.listen_event(self.on_open_air_gap, "garage_open_air_gap") # Listen for event fired from Home Assistant frontend.
    self.listen_event(self.on_test_event, "garage_test_event")
    
    # Timed Tasks:
    self.run_at(self.close_door, "sunset")

  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################
  # When Garage Door Opens.
  def on_garage_door_open(self, entity, attribute, old, new, cb_args):
    self.log("Garage Door Opened.")
    self.log("Cancelling 'open time' listener.")
    anyone_at_home = self.function_library.is_house_occupied()
    try:
      self.cancel_listen_event(self.garage_open_time_handler)
    except Exception:
      self.log("No open time event being listened for.")
    else:
      self.set_value(globals.garage_input_number_garage_open_timer, 0)
    finally:
      self.log("Open time listener was cancelled.")
    self.garage_close_time_handler = self.listen_state(self.on_close_time_select, globals.garage_input_number_garage_close_timer)
    #self.garage_door_timer_handler = self.listen_event(self.on_garage_door_no_motion_timer_finished, "timer.finished", entity_id =  "timer.garage_door_auto_close_no_motion" )
    if anyone_at_home != 1:  # 0 is Out, 1 is Home, 2 is Asleep.
      door_power_state = self.get_state(globals.garage_door_power_switch)
      if door_power_state == 'off':
        self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door has been forced OPEN (without power).")
        # To do: Make a call to the alarm app.
      else:
        if old == "closed":
          door_message = "Garage door has been opened."
          self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)
          self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer)
        else:
          door_message = "Garage door is open."
        self.call_service(globals.max_telegram, title = "Garage Alert", message = door_message)
        self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = door_message,\
                                       data = {"channel":"Garage",\
                                               "tag":globals.garage_door_alert_tag,\
                                               "actions":[globals.android_app_action_close_garage_door,\
                                                          globals.android_app_action_close_garage_door_in_5_minutes\
                                                         ]\
                                              }\
                      )
    
    #self.set_value("input_boolean.garage_airgap", 'off')  # This needs an "open" and "closed" identifier.

    if self.get_state(globals.garage_input_boolean_garage_airgap) != 'on':
      dark_state = self.get_state(globals.dark_sensor)
      if dark_state == 'on':
        self.log("Garage open and it's dark.")
        self.garage_light_on()
      else:
        self.log("Turning garage light off.")
        self.garage_light_off()

  # When Garage Door Closes.
  def on_garage_door_closed(self, entity, attribute, old, new, cb_args):
     self.log("Garage door closed.")
     self.log("Attempting to cancel close time listener.")
     try:
       self.cancel_listen_event(self.garage_close_time_handler)
     except Exception:
       self.log("No close timer event being listened for.")
     else:
       self.set_value(globals.garage_input_number_garage_close_timer, 0)
       self.log("Close time listener was cancelled.")
     self.garage_open_time_handler = self.listen_state(self.on_open_time_select, globals.garage_input_number_garage_open_timer)
     if old == "open":
      if self.function_library.is_house_occupied() == 0:  # 0 is Out, 1 is Home, 2 is Asleep. 
       self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door has been CLOSED.")
      self.call_service(globals.max_app, title = "Garage Alert",\
                                         message = "Garage Door Closed.",\
                                         data    = {"channel":"Garage",\
                                                    "tag":globals.garage_door_alert_tag,\
                                                    "actions":[globals.android_app_action_switch_off_garage_door,\
                                                               globals.android_app_action_open_garage_door\
                                                              ]\
                                                    }\
                      )
     self.call_service("timer/cancel", entity_id = globals.garage_door_no_motion_timer)
     self.call_service("timer/start", entity_id = globals.garage_door_power_timer)
     self.turn_off(globals.garage_input_boolean_garage_airgap)
  
  def on_garage_light_on(self, entity, attribute, old, new, cb_args):
    self.log("Garage Light Turned ON.")
    self.call_service("timer/start", entity_id = globals.garage_light_timer)

  def on_garage_light_off(self, entity, attribute, old, new, cb_args):
    self.log("Garage light turned OFF.")
    self.call_service("timer/cancel", entity_id = globals.garage_light_timer)
    
  def on_garage_door_power_off(self, entity, attribute, old, new, cbargs):
    if old == "on":
      self.log("Garage door powered OFF.")
      if self.function_library.is_house_occupied() != 1:  # If house is occupied, don't send a Telegram message.
        self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage door power switched OFF.")
      self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = "Garage door power switched OFF",\
                                       data = {"channel":"Garage",\
                                               "tag":globals.garage_door_alert_tag\
                                              }\
                      )
      self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)
    
  def on_garage_door_power_on(self, entity, attribute, old, new, cb_args):
    if old == "off":
      self.log("Garage Door Powered ON.")
      power_message = "Garage door power switched on."
    else:
      power_message = "Garage door power is on."
    house_mode = self.get_state(globals.house_mode_selector)
    if self.function_library.is_house_occupied() == 0:  # If house is occupied, don't send a Telegram message.
      self.call_service(globals.max_telegram, title = "Garage Alert", message = power_message)
    self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = power_message,\
                                       data = {"channel":"Garage",\
                                               "tag":globals.garage_door_alert_tag,\
                                               "actions":[globals.android_app_action_open_garage_door,
                                                          globals.android_app_action_switch_off_garage_door,
                                                          globals.android_app_action_open_garage_door_in_5_minutes\
                                                         ]\
                                              }\
                      )
    door_state = self.get_state(globals.garage_door_entity)
    if door_state == "closed":
      self.call_service("timer/start", entity_id = globals.garage_door_power_timer)

  # Power Timer Completed.
  def on_garage_door_power_timer_finished(self, event, data, cb_args):
    self.log("Garage door power timer finished.")
    self.switch_off_garage_door()

  # Long term timer timeout, close the garage door.
  def on_garage_door_no_motion_timer_finished(self, event, data, cb_args):
    self.log("Garage door no-motion longterm timer finished.")
    door_open_closed_state = self.get_state(globals.garage_door_entity)
    if door_open_closed_state != "closed":
      door_power_state = self.get_state(globals.garage_door_power_switch)
      if door_power_state == 'off':
        self.log("garage.py: Close garage door, power is off, switching ON.")
        self.turn_on(globals.garage_door_power_switch)
      self.log("Closing door, after longterm timer.")
      self.run_in(self.on_close_garage_and_power_off, 3)
      self.run_in(self.check_door_is_closed_and_try_to_reclose, 60)

  # Input select close time.
  def on_close_time_select(self, entity, attribute, old, new, cb_args):
    time_selected = int(float(new))
    if time_selected == 0:
      self.log("Garage close time cancelled.")
      if self.run_in_the_future_handler != 0:
        try:
          self.cancel_timer(self.run_in_the_future_handler)
        except Exception:
          self.log("No listener to cancel.")
        door_state = self.check_if_garage_closed()
        if door_state == "open":
          self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer)
    else:
      self.log("Garage close time selected.")
      self.log(time_selected)
      time_selected_seconds = int(float(time_selected)) * 60
      #self.log(time_selected_seconds)
      #self.run_in_the_future_handler = self.run_in(self.close_garage_and_power_off, time_selected_seconds)
      self.run_in_the_future_handler = self.run_in(self.on_set_timer_close_garage_and_power_off, time_selected_seconds)
      self.log(self.run_in_the_future_handler)
      door_state = self.check_if_garage_closed()
      if door_state == "open":
        self.call_service("timer/cancel", entity_id = globals.garage_door_no_motion_timer)

  # Input select open time.
  def on_open_time_select(self, entity, attribute, old, new, cb_args):
    door_power_state = self.get_state(globals.garage_door_power_switch)
    time_selected = int(float(new))
    if time_selected == 0:
      self.log("Cancelling timer.")
      try:
        self.cancel_timer(self.run_in_the_future_handler)
      except Exception:
        self.log("No listener to cancel.")
      else:
        self.log("Garage open time cancelled.")
      if door_power_state == 'on':
        self.call_service("timer/start", entity_id = globals.garage_door_power_timer)
    else:
      self.log("Garage open time selected.")
      self.log(time_selected)
      time_selected_seconds = int(float(time_selected)) * 60
      self.run_in_the_future_handler = self.run_in(self.on_set_timer_power_on_and_open_garage, time_selected_seconds)
      self.log(self.run_in_the_future_handler)
      if door_power_state == 'on':
        self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)

  # Motion Detected:
  def on_motion_detected(self, entity, attribute, old, new, cb_args):
    if old != "unavailable" and new != "unavailable":
      self.log("Garage Motion Detected.")
      dark_state = self.get_state(globals.dark_sensor)
      door_state = self.get_state(globals.garage_door_entity)
      anyone_home = self.function_library.is_house_occupied()
      garage_airgap = self.get_state(globals.garage_input_boolean_garage_airgap)
      match door_state:
        case "closed":
          self.log("Garage door is CLOSED.")
          house_mode = self.get_state(globals.house_mode_selector)
          if anyone_home == 1:
            light_level = self.get_state(globals.garage_light_sensor)
            if str(light_level) != "unavailable":
              if int(float(light_level)) < 200:
                self.garage_light_on()
                self.call_service("timer/start", entity_id = globals.garage_light_timer, duration = globals.garage_light_off_timer_duration)
              else:
                self.log("Light level high.")
            power_state = self.get_state(globals.garage_door_power_switch)
            if power_state == "On":
              self.log("Garage door power is on, extending timer.")
              self.call_service("timer/start", entity_id = globals.garage_door_power_timer, duration = globals.garage_door_power_timer_duratio)
          else:
            self.log("Garage PIR Sensor Actvated.")
            self.call_service(globals.max_telegram, title = "Garage Alert", message = "PIR Sensor detected motion in the garage.")
        case "open":
          self.log("Garage door is OPEN.")
          close_timer_state = "null"
          if anyone_home == 1:
            self.log("Reset close timer.")
            close_timer_state = self.get_state(globals.garage_door_no_motion_timer)
          if close_timer_state != "paused":
            self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer, duration = globals.garage_door_no_motion_timer_duration)
          if dark_state == 'on':
            if anyone_home == 1:
              self.log("Door OPEN and it's dark (and someone is at home).")
              self.garage_light_on()
            else:
              self.log("Door OPEN and it's dark (and nobody is at home).")
  
  # Motion has ceased to be detected.
  def on_motion_not_detected(self, entity, attribute, old, new, cb_args):
    """This will log when motion has stopped being detected."""
    self.log("Garage Motion Un-Detected.")

  # Garage light timer completed.
  def on_garage_light_timer_finished(self, event, data, cb_args):
      self.log("Garage light timer finished.")
      self.turn_off(globals.garage_light_entity)

  def on_set_timer_power_on_and_open_garage(self, cb_args):
    self.log("Open timer called.")
    self.power_on_and_open_garage()

  def on_set_timer_close_garage_and_power_off(self, cb_args):
    self.log("Closed timer called.")
    self.close_garage_and_power_off()

  def on_button_power_on_and_open_garage(self, entity, attribute, old, new, cb_args):
    self.power_on_and_open_garage()
  
  def on_button_close_garage_and_power_off(self, entity, attribute, old, new, cb_args):
    self.close_garage_and_power_off()

  def on_open_air_gap(self, event_name, data, cb_args):
    self.open_air_gap()

  def on_test_event(self, event_name, data, cb_args):
    self.log("Test event.")

  def auto_close_timer_events(self, entity, attribute, old, new, cb_args):
    self.log("Timer event: " + str(old) + " - " + str(new))
    if self.check_if_garage_closed() == "closed":
      self.log("Garage is closed. Cancel timer.")
    else:
      if old == "paused" and new == "active":
        self.log("Timer restarted")
      if old == "active" and new == "paused":
        self.log("Timer paused.")

  def button_test_press(self, entity, attribute, old, new, cb_args):
    self.log("Test press.")

  def on_power_on_and_open_garage(self, cb_args):
    self.log("On Power on and open garage event.")
    self.power_on_and_open_garage()

  def on_close_garage_and_power_off(self, cb_args):
    self.log("On close garage and power off event.")
    self.close_garage_and_power_off()

  def on_run_open_garage(self, cb_args):
    self.open_garage()

  def on_run_open_air_gap_step_one(self, cb_args):
    #self.log("Air gap step 1a.")
    current_house_mode = self.get_state(globals.house_mode_selector)
    if current_house_mode in ["away"]:
      self.log("House is in Away mode. Not opening airgap.")
    else:
      #self.log("Air gap step 1b.")
      self.open_garage()
      time.sleep(self.air_gap_time_delay)
      #self.log("Air gap step 1c.")
      self.close_garage() # This doesn't actually close the door, it just presses the close button to stop the door mid-flight. 
      #self.log("Air gap step 1d.")
      self.run_in(self.on_run_open_air_gap_step_two, 30)

  def on_run_open_air_gap_step_two(self, cb_args):
    #self.log("Air gap step 2a.")
    current_house_mode = self.get_state(globals.house_mode_selector)
    #self.call_service("timer/start", entity_id = globals.garage_door_power_timer, duration = "18000") # 5 Hours.
    if current_house_mode in ["out"]:
      self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)
      self.airgap_close_handler = self.run_at(self.close_garage_and_power_off, "sunset - 01:00:00")
      self.switch_off_garage_door()
      
  def close_door(self, cb_args):
    self.log("Closed door at sunset.")
    current_house_mode = self.get_state(globals.house_mode_selector)
    if current_house_mode in ["out", "away", "sleep"]:
      door_state = door_open_closed_state = self.get_state(globals.garage_door_entity)
    if door_open_closed_state != "closed":
      self.close_garage_and_power_off()

###############################################################################################################
# Other functions:
###############################################################################################################

  def close_garage(self):
    self.log("Garage door close function called.")
    self.call_service("cover/close_cover", entity_id = globals.garage_door_entity, return_result = False)

  def open_garage(self):
    self.log("Garage door open function called.")
    self.call_service("cover/open_cover", entity_id = globals.garage_door_entity, return_result = False)

  def garage_light_off(self):
    self.log("Garage light off function called.")
    self.turn_off(globals.garage_light_entity)
    self.call_service("timer/cancel", entity_id = globals.garage_light_timer)

  def garage_light_on(self):
    self.log("Garage light on function called.")
    self.turn_on(globals.garage_light_entity)
    self.call_service("timer/start", entity_id = globals.garage_light_timer)

  def switch_off_garage_door(self):
    self.log("Garage door power off function called.")
    self.turn_off(globals.garage_door_power_switch)

  def switch_on_garage_door(self):
    self.log("Garage door power on function called.")
    self.turn_on(globals.garage_door_power_switch)

  def power_on_and_open_garage(self):
    self.log("Power on and open garage door.")
    door_state = self.check_if_garage_closed()
    if door_state == "open":
      self.log("Garage door is already open.")
    else:
      self.log("Garage door is closed, will power on and open.")
      self.switch_on_garage_door()
      self.run_in(self.on_run_open_garage, 2)

  def close_garage_and_power_off(self):
    self.log("Close door and power off called.")
    door_state = self.check_if_garage_closed()
    if door_state != "closed":
      self.close_garage()
      # Check if closed here.
      new_closed_state = self.run_in(self.check_door_is_closed_and_try_to_reclose, self.garage_door_close_time_check)
      self.log(new_closed_state)  
    else:
        self.switch_off_garage_door()
    
  def check_if_garage_closed(self):
    door_state = self.get_state(globals.garage_door_entity)
    self.log("Door state: " + str(door_state))
    return door_state
  
  def check_door_is_closed_and_try_to_reclose(self, kwargs):
    door_state = self.check_if_garage_closed()
    if door_state != "closed":
        garage_door_not_closed_alert_text = "Garage door has not closed after " + str(self.garage_door_close_time_check) + " seconds."
        self.log(garage_door_not_closed_alert_text)
        self.call_service(globals.max_telegram, title = "Garage Alert", message = garage_door_not_closed_alert_text)
        self.close_garage()
    else:
      self.log("Power off door.")
      self.switch_off_garage_door()

  # Open a small gap in the main door to allow airflow.
  def open_air_gap(self):
    self.log("Garage door air gap called.")
    door_state = self.check_if_garage_closed()
    if door_state == "closed":
      self.switch_on_garage_door()
      self.run_in(self.on_run_open_air_gap_step_one, 2)
      self.turn_on(globals.garage_input_boolean_garage_airgap)
