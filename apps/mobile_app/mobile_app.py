# Mobile App Script.
# Listens for click events from the mobile app.
#
# Currently only garage controls.
#
# (C) 2023 Max Hodgson
# Version: 19062023.01

import appdaemon.plugins.hass.hassapi as hass
import os
import time

import globals_module as globals

from datetime import datetime

class Mobile_App(hass.Hass):

  # Monitors:
  # Mobile app events.

  # Needs:
  # globals.py
  # Garage App.
  #
  
  
  def initialize(self):
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    this_script = os.path.basename(__file__)
    self.log("=" * globals.log_partition_line_length)
    self.log(this_script + " running at {}.".format(now))
    self.log("=" * globals.log_partition_line_length)
    
    # Load external AppDaemon libraries:
    
    # Garage function library.
    self.garage_library = self.get_app("garage")
    
    # State monitors
    # None.

    # Event Monitors
    self.listen_event(self.on_mobile_app_click_event, event="mobile_app_notification_action")

  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################

  def on_mobile_app_click_event(self, event_name, data, kwargs):
    action_clicked = data["action"]
    match action_clicked:
      case globals.android_click_action_open_garage_door:
        self.garage_library.open_garage()
      case globals.android_click_action_power_off_garage_door:
        self.garage_library.switch_off_garage_door()
      case globals.android_click_action_close_garage_door:
        self.garage_library.close_garage_and_power_off()
      case globals.android_click_action_close_garage_door_in_5_minutes:
        self.log("Close garage door in 5 minutes.")
        self.set_value(globals.garage_input_number_garage_close_timer, 5)
      case globals.android_app_action_open_garage_door_in_5_minutes:
        self.log("Open garage door in 5 minutes.")
        self.set_value(globals.garage_input_number_garage_open_timer, 5)


###############################################################################################################
# Other functions:
###############################################################################################################
