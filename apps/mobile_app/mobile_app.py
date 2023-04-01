# Mobile App Script.
# Listens for events from the mobile app.
#
# Currently only garage controls.
#
# (C) 2023 Max Hodgson
# Version: 13022023.01

import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime
import globals_module as globals

class Mobile_App(hass.Hass):

  # Monitors:
  # Mobile app events.

  # Needs:
  # globals.py
  # Garage App.
  #
  
  
  def initialize(self):
    self.log("=" * globals.log_partition_line_length)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    # Load external AppDaemon libraries:
    #global FunctionLibrary  
    #FunctionLibrary = self.get_app("function_library")

    # Garage function library.
    global GarageLibrary
    GarageLibrary = self.get_app("garage")
     
    # State monitors
    # None!

    # Event Monitors
    self.listen_event(self.on_mobile_app_click_event, event="mobile_app_notification_action")

  ###############################################################################################################
  # Callback functions:
  ###############################################################################################################

  def on_mobile_app_click_event(self, event_name, data, kwargs):
    #self.log(data)
    action_clicked = data["action"]
    if action_clicked == globals.android_click_action_open_garage_door:
      GarageLibrary.open_garage()
    elif action_clicked == globals.android_click_action_power_off_garage_door:
      GarageLibrary.switch_off_garage_door()
    elif action_clicked == globals.android_click_action_close_garage_door:
      GarageLibrary.close_garage_and_power_off()
    elif action_clicked == globals.android_click_action_close_garage_door_in_5_minutes:
      self.log("Close garage door in 5 minutes.")
      self.set_value(globals.garage_input_number_garage_close_timer, 5)
    elif action_clicked == globals.android_app_action_open_garage_door_in_5_minutes:
      self.log("Open garage door in 5 minutes.")
      self.set_value(globals.garage_input_number_garage_open_timer, 5)


###############################################################################################################
# Other functions:
###############################################################################################################
