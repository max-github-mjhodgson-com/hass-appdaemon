# Kitchen Control Script.
#
# Kettle will listen for the power level to reach boiling state and set a power switch off timer. 
# Will send a Telegram message when the kettle has boiled.
#
# Max Hodgson 2023
# Version: 18052023.01

import appdaemon.plugins.hass.hassapi as hass

import os
#import time

from datetime import datetime
import globals_module as globals

class Kitchen(hass.Hass):

  # Monitors:
  
  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)
    
    # Load external AppDaemon libraries:
    self.function_library = self.get_app("function_library")

    self.kettle_gone_to_zero_handler = 0
    self.kettle_message_sent = 0
    self.dishwasher_trigger = 0
    self.dishwasher_status_select = "input_select.dishwasher_status"
    self.dishwasher_end_timer = "timer.dishwasher_off_timeout"

    # State monitors:
    self.kettle_power_on = self.listen_state(self.on_kettle_on, globals.kettle, new = "on", old = "off")
    self.kettle_power_off = self.listen_state(self.on_kettle_off, globals.kettle, new = "off", old = "on")
    self.kettle_power_threshold_handler = self.listen_state(self.on_kettle_power_threshold_reached, globals.kettle_threshold, new = "on", old = "off", duration = "10")
    self.listen_state(self.on_dishwasher_status_change, "sensor.teckin07_instant_power", duration = 10)
    self.listen_state(self.on_dishwasher_finished, "timer.dishwasher_finished_timeout")
    self.listen_state(self.on_dishwasher_off, self.dishwasher_end_timer, duration = 600, immediate = True)

    # Event monitors:
    self.kettle_power_timer_started = self.listen_event(self.on_kettle_timer_start, "timer.started", entity_id = globals.kettle_timer )
    self.kettle_power_timer_finished_handler = self.listen_event(self.on_kettle_timer_finished, "timer.finished", entity_id = globals.kettle_timer )
    self.listen_for_kettle_on_button_press_handler = self.listen_state(self.on_button_press_turn_kettle_on, "input_button.kettle_on")
    
    # Timed events:
    self.run_daily(self.timed_kettle_on, "14:50:00")

###############################################################################################################
# Callback functions:
###############################################################################################################
  def on_kettle_on(self, entity, attribute, old, new, cb_args):
    self.log("Kettle power switched ON.")
    #if function_library.is_house_occupied() == 1:
    #  self.call_service("timer/start", entity_id = globals.kettle_timer, duration = "300")
    if self.kettle_gone_to_zero_handler != 0:
      try:
        self.cancel_listen_state(self.kettle_gone_to_zero_handler)
      except Exception:
        self.log("No open timer event being listened for.")
      else:
        self.log("Was set_value.")
        #self.set_value(self.kettle_gone_to_zero_handler, 0)
        pass
      finally:
       self.log("Kettle reset to zero listener was cancelled.")

  def on_kettle_off(self, entity, attribute, old, new, cb_args):
    self.log("Kettle power switched OFF.")
    self.call_service("timer/cancel", entity_id = globals.kettle_timer)
    self.kettle_message_sent = 0
    #self.log(self.kettle_gone_to_zero_handler)
    #if self.kettle_gone_to_zero_handler != 0:
    #  self.log(self.kettle_gone_to_zero_handler)

  def on_kettle_timer_start(self, event, data, cb_args):
    self.log("Kettle timer started.")
    self.turn_on(globals.kettle_timer_active)
    
  def on_kettle_timer_finished(self, event, data, cb_args):
    self.log("Kettle timer finished.")
    self.call_service("switch/turn_off", entity_id = globals.kettle)
    self.turn_off(globals.kettle_timer_active)

  def on_kettle_power_threshold_reached(self, entity, attribute, old, new, cb_args):
    self.log("Kettle Power Threshold Reached.")
    self.log(self.kettle_power_threshold_handler)
    self.kettle_gone_to_zero_handler = self.listen_state(self.on_kettle_return_to_zero, globals.kettle_threshold, new = "off", old = "on", duration = "10", oneshot = "true")
    #self.call_service("timer/start", entity_id = globals.kettle_timer)
    
  def on_kettle_return_to_zero(self, entity, attribute, old, new, cb_args):
    self.log("Kettle has returned to zero.")
    self.log(self.kettle_gone_to_zero_handler)
    self.call_service("timer/start", entity_id = globals.kettle_timer, duration = "1")
    if self.kettle_message_sent == 0:
      self.call_service(globals.max_telegram, title = "Kettle Alert", message = "The kettle has boiled.")
      for notify_kitchen_users in [globals.max_app, globals.hall_panel_app]:
        self.call_service(notify_kitchen_users, title = "Kettle has boiled.",\
                                                message = "TTS",\
                                                data = {"media_stream": "alarm_stream",\
                                                        "tts_text": "Kettle has boiled.",\
                                                        "confirmation": "true",\
                                                        "timeout": 30 })
      self.kettle_message_sent = 1
    #if self.kettle_gone_to_zero_handler != 0:
    #  self.cancel_listen_state(self.kettle_gone_to_zero_handler)

  def on_button_press_turn_kettle_on(self, entity, attribute, old, new, cb_args):
    self.log("Kettle Button Pressed.")
    self.turn_on(globals.kettle)

  def on_dishwasher_status_change(self, entity, attribute, old, new, cb_args):
    self.log(old)
    self.log(new)
    if str(old) != "unavailable" and str(new) != "unavailable" and old != None and new != None:
      self.log("Dishwasher status change.")
      self.log("Dishwasher new: " + str(new))
      self.log("Dishwasher old: " + str(old))
      current_dishwasher_state = self.get_state(self.dishwasher_status_select)
      self.log("Current dishwasher state: " + str(current_dishwasher_state))
      if (int(old) == 0 and int(new) > 50) and current_dishwasher_state == "Off":
        self.select_option(self.dishwasher_status_select,"Running")
        self.log("Dishwasher has started.")
      if int(new) > 1500:
        self.select_option(self.dishwasher_status_select,"Running (Heating)")
        self.log("Dishwasher is heating.")
      if int(old) > 1500 and int(new) < 90:
        self.select_option(self.dishwasher_status_select,"Running")
        self.log("Dishwasher has stopped heating.")
      if int(old) == 1 and int(new) == 0:
        self.call_service("timer/start", entity_id = self.dishwasher_end_timer)
        self.log("Dishwasher finish timer started.")
        self.select_option(self.dishwasher_status_select,"Running")
      if int(new) == 1 and int(old) == 0:
        #self.call_service("timer/cancel", entity_id = "timer.dishwasher_finished_timeout")
        self.call_service("timer/start", entity_id = self.dishwasher_end_timer)
        self.log("Dishwasher finish timer restarted.")
        self.select_option(self.dishwasher_status_select,"Running")

  def on_dishwasher_finished(self, entity, attribute, old, new, cb_args):
    self.select_option(self.dishwasher_status_select, "Finished")
    self.log("Dishwasher has finished.")
    
  def on_dishwasher_off(self, entity, attribute, old, new, cb_args):
    if old != "unavailable" and new != "unavailable" and old != None:
      self.log("Dishwasher finished timeout.")
      self.select_option(self.dishwasher_status_select, "Off")

  def timed_kettle_on(self, cb_args):
    house_mode_state = self.function_library.is_house_occupied()
    if house_mode_state == 1:
      self.turn_on(globals.kettle)

###############################################################################################################
# Other functions:
###############################################################################################################

  