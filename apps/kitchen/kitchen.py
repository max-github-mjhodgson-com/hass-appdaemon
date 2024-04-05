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

    # State monitors.
    self.kettle_power_on = self.listen_state(self.on_kettle_on, globals.kettle, new = "on", old = "off")
    self.kettle_power_off = self.listen_state(self.on_kettle_off, globals.kettle, new = "off", old = "on")
    self.kettle_power_threshold_handler = self.listen_state(self.on_kettle_power_threshold_reached, globals.kettle_threshold, new = "on", old = "off", duration = "10")
    self.dishwash_status_change_handler = self.listen_state(self.on_dishwasher_status_change, "sensor.teckin07_instant_power", duration = 10)

    # Event monitors.
    self.kettle_power_timer_started = self.listen_event(self.on_kettle_timer_start, "timer.started", entity_id = globals.kettle_timer )
    self.kettle_power_timer_finished_handler = self.listen_event(self.on_kettle_timer_finished, "timer.finished", entity_id = globals.kettle_timer )
    self.listen_for_kettle_on_button_press_handler = self.listen_state(self.on_button_press_turn_kettle_on, "input_button.kettle_on")

###############################################################################################################
# Callback functions:
###############################################################################################################
  def on_kettle_on(self, entity, attribute, old, new, kwargs):
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

  def on_kettle_off(self, entity, attribute, old, new, kwargs):
    self.log("Kettle power switched OFF.")
    self.call_service("timer/cancel", entity_id = globals.kettle_timer)
    self.kettle_message_sent = 0
    #self.log(self.kettle_gone_to_zero_handler)
    #if self.kettle_gone_to_zero_handler != 0:
    #  self.log(self.kettle_gone_to_zero_handler)

  def on_kettle_timer_start(self, event, data, kwargs):
    self.log("Kettle timer started.")
    self.turn_on(globals.kettle_timer_active)
    
  def on_kettle_timer_finished(self, event, data, kwargs):
    self.log("Kettle timer finished.")
    self.call_service("switch/turn_off", entity_id = globals.kettle)
    self.turn_off(globals.kettle_timer_active)

  def on_kettle_power_threshold_reached(self, entity, attribute, old, new, kwargs):
    self.log("Kettle Power Threshold Reached.")
    self.log(self.kettle_power_threshold_handler)
    self.kettle_gone_to_zero_handler = self.listen_state(self.on_kettle_return_to_zero, globals.kettle_threshold, new = "off", old = "on", duration = "10", oneshot = "true")
    #self.call_service("timer/start", entity_id = globals.kettle_timer)
    
  def on_kettle_return_to_zero(self, entity, attribute, old, new, kwargs):
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

  def on_button_press_turn_kettle_on(self, entity, attribute, old, new, kwargs):
    self.log("Kettle Button Pressed.")
    self.turn_on(globals.kettle)

  def on_dishwasher_status_change(self, entity, attribute, old, new, kwargs):
    dishwasher_status_select = "input_select.dishwasher_status"
    
    if old != "unavailable" and new != "unavailable":
      self.log("Dishwasher status change.")
      self.log("Dishwasher new: " + str(new))
      self.log("Dishwasher old: " + str(old))
      current_dishwasher_state = self.get_state(dishwasher_status_select)
      match new:
        case 0:
          self.log("Dishwasher is off.")
          self.select_option(dishwasher_status_select, "Off")
          if old > 0:
            self.log("Dishwasher has finished.")
            self.select_option(dishwasher_status_select, "Finished")
            self.dishwasher_trigger = 0
        case 1:
          if old == "0":
            self.log("Dishwasher is running.")
            self.select_option(dishwasher_status_select,"Running")
        case _ if int(new) > 50:
          self.log("Dishwasher has started.")
          self.select_option(dishwasher_status_select,"Running")
          self.dishwasher_trigger = 1
        case _ if int(new) > 1900:
          self.log("Dishwasher is running (heating).")
          self.select_option(dishwasher_status_select,"Running (Heating)")
          self.dishwasher_trigger = 1

    # Start power > 1900

###############################################################################################################
# Other functions:
###############################################################################################################

  