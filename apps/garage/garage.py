# Garage Control Script.
# Max Hodgson 2021
# Version: 02092021.01

import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime
import globals

class Garage(hass.Hass):

  # Monitors:
  # Garage door open.
  # Garage door closed.
  # Garage motion (for light etc).
  # Garage door power on.
  # Garage door power off.
  # Garage Light on.
  # Garage Light off.
  # Android App Click Events.

  # Listens for these events:
  #   power_on_garage_door_and_open
  #   close_garage_and_power_off
  # Events:
  #  garage_open_air_gap
  
  def initialize(self):
    self.log("=" * globals.log_partition_line_length)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    # Load external AppDaemon libraries:
    global FunctionLibrary  
    FunctionLibrary = self.get_app("function_library")
    
    global garage_door_close_time_check
    garage_door_close_time_check = 30  # In seconds, how long the garage door should take to close.

    #global run_in_the_future_handler
    #run_in_the_future_handler = 0
    
    global garage_close_time_handler
    global garage_open_time_handler

    self.set_value(globals.garage_input_number_garage_close_timer, 0)
    self.set_value(globals.garage_input_number_garage_open_timer, 0)

    # Startup sanity checks:
    initial_power_state = self.get_state(globals.garage_door_power_switch)
    initial_no_motion_timer_state = self.get_state(globals.garage_door_no_motion_timer)
    initial_power_timer_state = self.get_state(globals.garage_door_power_timer)
    initial_door_state = self.check_if_garage_closed()
    if initial_door_state == "closed":
      self.garage_open_time_handler = self.listen_state(self.on_open_time_select, globals.garage_input_number_garage_open_timer)
      if initial_power_state == "on" and initial_power_timer_state != "active":
        self.call_service("timer/start", entity_id = globals.garage_door_power_timer)
    else:
      self.garage_close_time_handler = self.listen_state(self.on_close_time_select, globals.garage_input_number_garage_close_timer)
      if initial_no_motion_timer_state != "active":
        self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer)


    # State monitors
    self.handle1 = self.listen_state(self.on_garage_door_open, globals.garage_door_entity, new = "open", old = "closed")
    self.handle2 = self.listen_state(self.on_garage_door_closed, globals.garage_door_entity, new = "closed", old = "open")
    self.handle5 = self.listen_state(self.on_garage_door_power_off, globals.garage_door_power_switch, new = "off", old = "on")
    self.handle6 = self.listen_state(self.on_garage_door_power_on, globals.garage_door_power_switch, new = "on", old = "off")
    self.listen_state(self.on_motion_detected, globals.garage_motion_sensor, old = "off")
    self.listen_state(self.on_motion_not_detected, globals.garage_motion_sensor, new = "off") 
    self.garage_light_on_handler = self.listen_state(self.on_garage_light_on, globals.garage_light_entity, new = "on", old = "off")
    self.garage_light_off_handler = self.listen_state(self.on_garage_light_off, globals.garage_light_entity, new = "off", old = "on")
    self.door_auto_close_timer_handler = self.listen_state(self.auto_close_timer_events, "timer.garage_door_auto_close_no_motion")
    self.listen_for_power_on_garage_door_and_open_button_press_handler = self.listen_state(self.on_button_power_on_and_open_garage, 'input_button.power_on_garage_door_and_open')
    #self.listen_for_power_on_garage_door_and_open_button_press_handler = self.listen_state(self.button_test_press, 'input_button.power_on_garage_door_and_open')
    self.listen_for_close_garage_door_and_power_off_button_press_handler = self.listen_state(self.on_button_close_garage_and_power_off, 'input_button.close_garage_door_and_power_off')

    
    # Event Monitors
    self.power_timer_finished_handler = self.listen_event(self.on_garage_door_power_timer_finished, "timer.finished", entity_id = globals.garage_door_power_timer )
    self.light_timer_finished_handler = self.listen_event(self.on_garage_light_timer_finished, "timer.finished", entity_id = globals.garage_light_timer ) 
    self.listen_event(self.on_garage_door_no_motion_timer_finished, "timer.finished", entity_id = globals.garage_door_no_motion_timer )
    #self.listen_for_garage_power_on_and_open_event_handler = self.listen_event(self.on_power_on_and_open_garage, "power_on_garage_door_and_open")
    #self.listen_for_garage_door_close_and_power_off_event_handler = self.listen_event(self.on_close_garage_and_power_off, "close_garage_door_and_power_off")
    self.listen_for_garage_door_open_air_gap_handler = self.listen_event(self.on_open_air_gap, "garage_open_air_gap")
    self.listen_for_test_handler = self.listen_event(self.on_test_event, "garage_test_event")

  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################
  # When Garage Door Opens.
  def on_garage_door_open(self, entity, attribute, old, new, kwargs):
    self.log("Garage Door Opened.")
    self.log("Cancelling 'open time' listener.")
    #self.log(timer_running(self.garage_open_time_handler))
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
    if FunctionLibrary.is_house_occupied() != 1:  # 0 is Out, 1 is Home, 2 is Asleep.
      door_power_state = self.get_state(globals.garage_door_power_switch)
      if door_power_state == 'off':
        self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door has been forced OPEN (without power).")
      else:
        self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door has been OPENED.")
    self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = "Garage Door Opened.",\
                                       data = {"channel":"Garage",\
                                               "tag":globals.garage_door_alert_tag,\
                                               "actions":[globals.android_app_action_close_garage_door,\
                                                          globals.android_app_action_close_garage_door_in_5_minutes\
                                                         ]\
                                              }\
                      )
    self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)
    self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer)
    #self.set_value("input_boolean.garage_airgap", 'off')  # This needs an "open" and "closed" identifier.

    if self.get_state("input_boolean.garage_airgap") != 'on':
      self.log("garage_airgap is off.")
      dark_state = self.get_state('binary_sensor.dark')
      self.log(dark_state)
      if dark_state == 'on':
        self.log("Garage open and it's dark.")
        self.garage_light_on()
      else:
        self.log("Turning garage light off.")
        self.garage_light_off()

  # When Garage Door Closes.
  def on_garage_door_closed(self, entity, attribute, old, new, kwargs):
    self.log("Garage door closed.")
    self.log("Cancelling close time listener.")
    try:
      self.cancel_listen_event(self.garage_close_time_handler)
    except Exception:
      self.log("No close time event being listened for.")
    else:
      self.set_value(globals.garage_input_number_garage_close_timer, 0)
    finally:
      self.log("Close time listener was cancelled.")
    self.garage_open_time_handler = self.listen_state(self.on_open_time_select, globals.garage_input_number_garage_open_timer)
    if FunctionLibrary.is_house_occupied() == 0:  # 0 is Out, 1 is Home, 2 is Asleep. 
      self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door has been CLOSED.")
    self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = "Garage Door Closed.",\
                                       data = {"channel":"Garage",\
                                               "tag":globals.garage_door_alert_tag,\
                                               "actions":[globals.android_app_action_switch_off_garage_door,\
                                                          globals.android_app_action_open_garage_door\
                                                         ]\
                                              }\
                      )
    self.call_service("timer/cancel", entity_id = globals.garage_door_no_motion_timer)
    self.call_service("timer/start", entity_id = globals.garage_door_power_timer)
    self.turn_off("input_boolean.garage_airgap")
  
  def on_garage_light_on(self, entity, attribute, old, new, kwargs):
    self.log("Garage Light Turned ON.")
    self.call_service("timer/start", entity_id = globals.garage_light_timer)

  def on_garage_light_off(self, entity, attribute, old, new, kwargs):
    self.log("Garage Light Turned OFF.")
    self.call_service("timer/cancel", entity_id = globals.garage_light_timer)
    
  def on_garage_door_power_off(self, entity, attribute, old, new, kwargs):
    self.log("Garage Door Powered OFF.")
    if FunctionLibrary.is_house_occupied() != 1:  # If house is occupied, don't send a Telegram message.
      self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door Power Switched OFF.")
    self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = "Garage Door Power Switched OFF",\
                                       data = {"channel":"Garage",\
                                               "tag":globals.garage_door_alert_tag\
                                              }\
                      )
    self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)
    
  def on_garage_door_power_on(self, entity, attribute, old, new, kwargs):
    self.log("Garage Door Powered ON.")
    house_mode = self.get_state(globals.house_mode_selector)
    #self.log(house_mode)
    if FunctionLibrary.is_house_occupied() == 0:  # If house is occupied, don't send a Telegram message.
    #  if house_mode == "Just Arrived":
      self.call_service(globals.max_telegram, title = "Garage Alert", message = "Garage Door Power Switched ON.")
    self.call_service(globals.max_app, title = "Garage Alert",\
                                       message = "Garage Door Power Switched ON",\
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
  def on_garage_door_power_timer_finished(self, event, data, kwargs):
    self.log("Garage Door Power Timer Finished.")
    #self.turn_off(globals.garage_door_power_switch)
    self.switch_off_garage_door()

  # Long term timer timeout, close the garage door.
  def on_garage_door_no_motion_timer_finished(self, event, data, kwargs):
    self.log("Garage Door No-Motion Longterm Timer Finished.")
    door_power_state = self.get_state(globals.garage_door_power_switch)
    if door_power_state == 'off':
      self.log("garage.py: Close garage door, power is off, switching ON.")
      self.turn_on(globals.garage_door_power_switch)
    self.log("garage.py: Closing door, after longterm timer.")
    self.run_in(self.close_garage_and_power_off, 3)
    self.run_in(self.check_door_is_closed_and_try_to_reclose, 60)

  # Input select close time.
  def on_close_time_select(self, entity, attribute, old, new, kwargs):
    #global run_in_the_future_handler
    time_selected = int(float(new))
    if time_selected == 0:
      self.log("Garage close time cancelled.")
      if run_in_the_future_handler != 0:
        try:
          self.cancel_timer(run_in_the_future_handler)
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
      #run_in_the_future_handler = self.run_in(self.close_garage_and_power_off, time_selected_seconds)
      run_in_the_future_handler = self.run_in(self.on_set_timer_close_garage_and_power_off, time_selected_seconds)
      self.log(run_in_the_future_handler)
      door_state = self.check_if_garage_closed()
      if door_state == "open":
        self.call_service("timer/cancel", entity_id = globals.garage_door_no_motion_timer)

  # Input select open time.
  def on_open_time_select(self, entity, attribute, old, new, kwargs):
    door_power_state = self.get_state(globals.garage_door_power_switch)
    #global run_in_the_future_handler
    time_selected = int(float(new))
    if time_selected == 0:
      self.log("Cancelling timer.")
      try:
        self.cancel_timer(run_in_the_future_handler)
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
      run_in_the_future_handler = self.run_in(self.on_set_timer_power_on_and_open_garage, time_selected_seconds)
      self.log(run_in_the_future_handler)
      if door_power_state == 'on':
        self.call_service("timer/cancel", entity_id = globals.garage_door_power_timer)

  # Motion Detected:
  def on_motion_detected(self, entity, attribute, old, new, kwargs):
    self.log("Garage Motion Detected.")
    dark_state = self.get_state('binary_sensor.dark')
    door_state = self.get_state(globals.garage_door_entity)
    anyone_home = FunctionLibrary.is_house_occupied()
    #sun_pos = self.get_state("sun.sun")
    #self.log(sun_pos)
    if door_state == "closed":
      self.log("Garage door is CLOSED.")
      house_mode = self.get_state(globals.house_mode_selector)
      if house_mode == "Just Arrived":
        self.log("Just arrived, switching on garage door power.")
        self.switch_on_garage_door()
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
          self.call_service("timer/start", entity_id = globals.garage_door_power_timer, duration = "600")
      else:
        self.log("Garage PIR Sensor Actvated.")
        self.call_service(globals.max_telegram, title = "Garage Alert", message = "PIR Sensor detected motion in the garage.")
    elif door_state == "open":
      self.log("Garage door is OPEN.")
      close_timer_state = "null"
      if anyone_home == 1:
        self.log("Reset close timer.")
        close_timer_state = self.get_state(globals.garage_door_no_motion_timer)
      #self.log(close_timer_state)
      if close_timer_state != "paused":
        self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer, duration = "3600")
    if door_state == "open" and dark_state == 'on':
      if anyone_home == 1:
        self.log("Door OPEN and it's dark (and someone is at home).")
        self.garage_light_on()
      else:
        self.log("Door OPEN and it's dark (and nobody is at home).")
  
  # Motion has ceased to be detected.
  def on_motion_not_detected(self, entity, attribute, old, new, kwargs):
    """This will log when motion has stopped being detected."""
    self.log("Garage Motion Un-Detected.")

  # Garage light timer completed.
  def on_garage_light_timer_finished(self, event, data, kwargs):
      self.log("Garage light timer finished.")
      self.turn_off(globals.garage_light_entity)

  def on_set_timer_power_on_and_open_garage(self, kwargs):
    self.log("Open timer called.")
    self.power_on_and_open_garage()

  def on_set_timer_close_garage_and_power_off(self, kwargs):
    self.log("Closed timer called.")
    self.close_garage_and_power_off()

  def on_button_power_on_and_open_garage(self, entity, attribute, old, new, kwargs):
    self.power_on_and_open_garage()
  
  def on_button_close_garage_and_power_off(self, entity, attribute, old, new, kwargs):
    self.on_close_garage_and_power_off()

  def on_open_air_gap(self, event_name, data, kwargs):
    self.open_air_gap()

  def on_test_event(self, event_name, data, kwargs):
    self.log("Test event.")

  def auto_close_timer_events(self, entity, attribute, old, new, kwargs):
    self.log("Timer event.")
    if old == "paused" and new == "active":
      self.log("Timer restarted")
    if old == "active" and new == "paused":
      self.log("Timer paused.")

  def button_test_press(self, entity, attribute, old, new, kwargs):
    self.log("Test press.")

  def on_power_on_and_open_garage(self, kwargs):
    self.log("On Power on and open garage event.")
    self.power_on_and_open_garage()

  def on_close_garage_and_power_off(self, kwargs):
    self.log("On close garage and power off event.")
    self.close_garage_and_power_off()

  def on_run_open_garage(self, kwargs):
    self.open_garage()

  def on_run_open_air_gap_step_one(self, kwargs):
    self.log("Air gap step 1.")
    self.open_garage()
    self.run_in(self.on_run_open_air_gap_step_two, 2)

  def on_run_open_air_gap_step_two(self, kwargs):
    self.log("Air gap step 2.")
    self.close_garage()

###############################################################################################################
# Other functions:
###############################################################################################################

  def close_garage(self):
    self.log("Garage Door CLOSE function called.")
    self.call_service("cover/close_cover", entity_id = globals.garage_door_entity)

  def open_garage(self):
    self.log("Garage Door OPEN function called.")
    self.call_service("cover/open_cover", entity_id = globals.garage_door_entity)

  def garage_light_off(self):
    self.log("Garage Light OFF function called.")
    self.turn_off(globals.garage_light_entity)
    #self.call_service("timer/cancel", entity_id = globals.garage_light_timer)

  def garage_light_on(self):
    self.log("Garage Light ON function called.")
    self.turn_on(globals.garage_light_entity)
    #self.call_service("timer/start", entity_id = globals.garage_light_timer)

  def switch_off_garage_door(self):
    self.log("Garage Door Power OFF function called.")
    self.turn_off(globals.garage_door_power_switch)

  def switch_on_garage_door(self):
    self.log("Garage Door Power ON function called.")
    self.turn_on(globals.garage_door_power_switch)

  def power_on_and_open_garage(self):
    self.log("Power ON and OPEN garage door.")
    door_state = self.check_if_garage_closed()
    if door_state == "open":
      self.log("Garage door is already OPEN.")
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
      new_closed_state = self.run_in(self.check_door_is_closed_and_try_to_reclose, garage_door_close_time_check)
      self.log(new_closed_state)  
    else:
        self.switch_off_garage_door()
    
  def check_if_garage_closed(self):
    door_state = self.get_state(globals.garage_door_entity)
    return door_state
  
  def check_door_is_closed_and_try_to_reclose(self, kwargs):
    door_state = self.check_if_garage_closed()
    if door_state != "closed":
        garage_door_not_closed_alert_text = "Garage door has not closed after " + str(garage_door_close_time_check) + " seconds."
        self.log(garage_door_not_closed_alert_text)
        self.call_service(globals.max_telegram, title = "Garage Alert", message = garage_door_not_closed_alert_text)
        self.close_garage()
    else:
      self.log("Power OFF door.")
      self.switch_off_garage_door()

  def open_air_gap(self):
    self.log("Garage door air gap called.")
    door_state = self.check_if_garage_closed()
    if door_state == "closed":
      self.switch_on_garage_door()
      self.run_in(self.on_run_open_air_gap_step_one, 2)
      self.turn_on("input_boolean.garage_airgap")


