# Kitchen Control Script.
#
# Kettle will listen for the power level to reach boiling state and set a power switch off timer. 
# Will send a Telegram message when the kettle has boiled.
#
# Max Hodgson 2023
# Version: 02012023.01

import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime
import globals_module as globals

class Kitchen(hass.Hass):

  # Monitors:
  
  def initialize(self):
    self.log("=" * 30)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    # Load external AppDaemon libraries:
    global FunctionLibrary  
    FunctionLibrary = self.get_app("function_library")

    global kettle_gone_to_zero_handler
    kettle_gone_to_zero_handler = 0
    #global kettle_message_sent
    self.kettle_message_sent = 0

    # State monitors.
    self.kettle_power_on = self.listen_state(self.on_kettle_on, globals.kettle, new = "on", old = "off")
    self.kettle_power_off = self.listen_state(self.on_kettle_off, globals.kettle, new = "off", old = "on")
    self.kettle_power_threshold_handler = self.listen_state(self.on_kettle_power_threshold_reached, globals.kettle_threshold, new = "on", old = "off", duration = "10")

    # Event monitors.
    self.kettle_power_timer_started = self.listen_event(self.on_kettle_timer_start, "timer.started", entity_id = globals.kettle_timer )
    self.kettle_power_timer_finished_handler = self.listen_event(self.on_kettle_timer_finished, "timer.finished", entity_id = globals.kettle_timer )
    self.listen_for_kettle_on_button_press_handler = self.listen_state(self.on_button_press_turn_kettle_on, "input_button.kettle_on")

###############################################################################################################
# Callback functions:
###############################################################################################################
  def on_kettle_on(self, entity, attribute, old, new, kwargs):
    self.log("Kettle power switched ON.")
    #if FunctionLibrary.is_house_occupied() == 1:
    #  self.call_service("timer/start", entity_id = globals.kettle_timer, duration = "300")
    if kettle_gone_to_zero_handler != 0:
      try:
        self.cancel_listen_state(kettle_gone_to_zero_handler)
      except Exception:
        self.log("No open timer event being listened for.")
      else:
        self.set_value(kettle_gone_to_zero_handler, 0)
      finally:
       self.log("Kettle reset to zero listener was cancelled.")

  def on_kettle_off(self, entity, attribute, old, new, kwargs):
    self.log("Kettle power switched OFF.")
    self.call_service("timer/cancel", entity_id = globals.kettle_timer)
    self.kettle_message_sent = 0
    #self.log(kettle_gone_to_zero_handler)
    #if kettle_gone_to_zero_handler != 0:
    #  self.log(kettle_gone_to_zero_handler)

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
    kettle_gone_to_zero_handler = self.listen_state(self.on_kettle_return_to_zero, globals.kettle_threshold, new = "off", old = "on", duration = "10", oneshot = "true")
    #self.call_service("timer/start", entity_id = globals.kettle_timer)
    
  def on_kettle_return_to_zero(self, entity, attribute, old, new, kwargs):
    self.log("Kettle has returned to zero.")
    self.log(kettle_gone_to_zero_handler)
    self.call_service("timer/start", entity_id = globals.kettle_timer, duration = "1")
    if self.kettle_message_sent == 0:
      self.call_service(globals.max_telegram, title = "Kettle Alert", message = "The kettle has boiled.")
      self.call_service(globals.max_app, title = "Kettle has boiled.",\
                                       message = "TTS",\
                                       data = {"media_stream": "alarm_stream",\
                                               "tts_text": "Kettle has boiled."})
      self.kettle_message_sent = 1
    #if kettle_gone_to_zero_handler != 0:
    #  self.cancel_listen_state(kettle_gone_to_zero_handler)

  def on_button_press_turn_kettle_on(self, entity, attribute, old, new, kwargs):
    self.log("Kettle Button Pressed.")
    self.turn_on(globals.kettle)

###############################################################################################################
# Other functions:
###############################################################################################################

  