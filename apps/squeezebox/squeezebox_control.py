# Squeezebox Control Script.
#
# Version 15Apr24.1
#
# Max Hodgson (2024)
#
# This will listen for events on the events bus.
#
# Requires a nested dictionary of SB locations, remote functions and power controls called "players". See globals file.
# Will control Hifi devices through a Broadlink IR remote.

import appdaemon.plugins.hass.hassapi as hass
import globals_module as globals
import time  # , datetime
from datetime import datetime

class SqueezeboxControl(hass.Hass):

  def initialize(self):

    self.log("=" * 30)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
 
    sb_transporter_power_status = self.get_state(globals.squeezebox_transporter_power)
    sb_transporter_playing_status = self.get_state(globals.squeezebox_transporter)
    if sb_transporter_power_status == "on" and sb_transporter_playing_status != "playing":
       self.log("Transporter is currently powered ON, but not playing. Starting timer.")
       self.call_service("timer/start", entity_id = globals.squeezebox_transporter_timer, duration = globals.squeezebox_power_off_duration)

    self.log(self.find_remote_amp("pioneer_amp"))
    #self.listen_state(self.squeezebox_started_playing, globals.squeezebox_dining, new = "playing", duration = 1)
    sb_transporter_powered_off_handler = self.listen_state(self.call_squeezebox_transporter_power_off, globals.squeezebox_transporter, new = "off", duration = globals.squeezebox_power_off_duration) # Transporter power off after 1 hour.
    sb_transporter_off_after_one_hour_handler = self.listen_state(self.call_squeezebox_transporter_power_off, globals.squeezebox_transporter, new = "off", duration = 3600) # Transporter power off after 1 hour.
    sb_transporter_started_playing_handler = self.listen_state(self.call_squeezebox_transporter_started_playing, globals.squeezebox_transporter, new = "playing", duration = 2)
    sb_transporter_stopped_playing_handler = self.listen_state(self.on_squeezebox_stopped_playing, globals.squeezebox_transporter, new = ["idle", "paused"], old = lambda x: x not in ["unknown", "unavailable"], duration = 600)
    
    sb_transporter_status_handler = self.listen_state(self.on_sb_transporter_status_change, globals.squeezebox_transporter, new = ["on", "off"], old = lambda x: x not in ["unknown", "unavailable"], duration = 2)
    sb_transporter_power_off_handler = self.listen_state(self.on_sb_transporter_powered_off, globals.squeezebox_transporter_power, new = "off", duration = 2)
    sb_transporter_power_off_timer_completed_handler = self.listen_event(self.call_sb_transporter_power_timer_completed, "timer.finished", entity_id = globals.squeezebox_transporter_timer)

    # Touch:
    sb_touch_paused_handler = self.listen_state(self.on_sb_activity, globals.squeezebox_dining, new = "paused", duration = 2700) # This one has a different timeout currently.
    sb_touch_off_handler = self.listen_state(self.on_sb_activity, globals.squeezebox_dining, new = "off", duration = 30)
    sb_touch_idle_handler = self.listen_state(self.on_sb_activity, globals.squeezebox_dining, new = "idle", duration = 300)
    sb_touch_started_playing_handler = self.listen_state(self.on_sb_touch_started_playing, globals.squeezebox_dining, new = "playing", duration = 2)

    # Spare Bedroom Radio
    sb_bedroom_radio_paused_handler = self.listen_state(self.on_sb_activity, globals.squeezebox_spare_bedroom, new = "paused", duration = 1200)

    # Events:
    listen_for_playlist = self.listen_event(self.call_sb_playlist, "sb_playlist")
    listen_for_sb_command = self.listen_event(self.on_sb_command, "sb_control")
    # Events to listen for:
    # restartserver
    # sb_playlist
    # sb_control

    #clear_dining_room_playlist = self.run_daily(self.sb_playlist_clear(globals.squeezebox_dining), "04:00:00")
     
  #########################################################################################################################################
  # Callbacks:
  #########################################################################################################################################
  def call_squeezebox_transporter_power_off(self, entity, attribute, old, new, kwargs):
     self.log("Transporter has switched off.")
     self.power_off_squeezebox(globals.squeezebox_transporter_power)
     self.call_service("timer/start", entity_id = globals.squeezebox_transporter_timer, duration = globals.squeezebox_power_off_duration)

  def call_squeezebox_transporter_started_playing(self, entity, attribute, old, new, kwargs):
    self.log("Transporter has started playing.")
    self.log("Entity:" + entity)
    self.call_service("timer/cancel", entity_id = globals.squeezebox_transporter_timer)
    self.switch_on_pioneer_amp()
    self.select_input_on_pioneer_amp(globals.squeezebox_transporter)

  def on_squeezebox_stopped_playing(self, entity, attribute, old, new, cb_args):
    squeezebox_device = entity
    self.log(f"{squeezebox_device} has stopped playing.")
    self.call_service("media_player/turn_off", entity_id = squeezebox_device)

  def on_sb_transporter_stopped_playing(self, entity, attribute, old, new, kwargs):
    self.log("Transporter has stopped playing.")
    self.call_service("media_player/turn_off", entity_id = globals.squeezebox_transporter)

  def on_sb_transporter_status_change(self, entity, attribute, old, new, kwargs):
    if new == "on":
      self.log("Transporter Turned ON.")
      self.call_service("timer/start", entity_id = globals.squeezebox_transporter_timer, duration = globals.squeezebox_power_off_duration)
    elif new == "off":
      self.log("Transporter Turn OFF.") 
      self.call_service("timer/start", entity_id = globals.squeezebox_transporter_timer, duration = globals.squeezebox_power_off_duration)

  def on_sb_transporter_powered_off(self, entity, attribute, old, new, kwargs):
     if old != "unavailable":
      self.log("Transporter Powered OFF.")
      self.call_service("timer/cancel", entity_id = globals.squeezebox_transporter_timer)
      self.switch_off_pioneer_amp()

  def call_sb_transporter_power_timer_completed(self, event, data, kwargs):
     self.log("Timer completed.")
     self.power_off_squeezebox(globals.squeezebox_transporter_power)

  def on_sb_touch_started_playing(self, entity, attribute, old, new, kwargs):
    self.log("Squeezebox Touch has started playing.")
    self.log("Entity:" + entity)
    #self.call_service("timer/cancel", entity_id = globals.squeezebox_transporter_timer)
    self.switch_on_pioneer_amp()
    self.select_input_on_pioneer_amp(globals.squeezebox_dining)

  def on_sb_activity(self, entity, attribute, old, new, kwargs):
    if old != "unavailable" and new != "unavailable":
      squeezebox_device = entity
      self.log("Call Squeezebox Activity.")
      if new == "off":
        self.log(squeezebox_device + " turned off.")
        self.switch_off_pioneer_amp()
      if new == "idle":
        self.log("Squeezebox idle.")
        self.call_service("media_player/turn_off", entity_id = entity)
      if old == "playing" and new == "paused":
        self.log("Gone from playing to paused.")
        self.turn_off(squeezebox_device)
        if squeezebox_device in [globals.squeezebox_dining, globals.squeezebox_transporter]:
          self.switch_off_pioneer_amp()

  def call_sb_playlist(self, event_name, data, kwargs):
     self.log("call_sb_playlist called.")
     self.log(event_name)
     self.log(data)
     playlist_to_send = data["playlist"]
     self.log("Playlist: " + playlist_to_send)
     squeezebox_location = data["sb_device"]
     self.log("Location: " + squeezebox_location)
     if squeezebox_location in globals.players.keys():
        squeezebox_destination_device = globals.players[squeezebox_location]["squeezebox_id"]
        self.log("Media Player: " + squeezebox_destination_device)
        if "power" in globals.players[squeezebox_location].keys():
           squeezebox_power_device = globals.players[squeezebox_location]["power"]
           self.log(squeezebox_power_device)
           if self.get_state(squeezebox_power_device) == "off":
             self.log("Squeezebox is powered off.")
             self.turn_on(squeezebox_power_device)
             self.run_in(self.sb_playlist_cb, 120, playlist = playlist_to_send, squeezebox_device = squeezebox_destination_device)
        squeezebox_connection_status = self.get_state(squeezebox_destination_device)
        self.log("Squeezebox device status: " + str(squeezebox_connection_status))
        if squeezebox_connection_status != "Disconnected":
          self.sb_playlist(playlist_to_send, squeezebox_destination_device)
        else:
          self.log("Squeezebox is disconnected.")

  def on_sb_command(self, event_name, data, kwargs):
    command_action = data["command"]
    match command_action:
      case "restartserver":
        self.log("Server restart requested.")
        self.call_service("squeezebox/call_method", entity_id = globals.squeezebox_spare_bedroom, command = "restartserver")

  def sb_playlist_cb(self, kwargs):
    self.log("sb_playlist_cb called.")
    playlist = kwargs["playlist"]
    squeezebox_device = kwargs["squeezebox_device"]
    self.log(squeezebox_device)
    self.sb_playlist(playlist, squeezebox_device)

  #########################################################################################################################################
  # Functions:
  #########################################################################################################################################
  def power_off_squeezebox(self, squeezebox_device):
    self.turn_off(squeezebox_device)

  def power_on_squeezebox(self, squeezebox_device):
    self.log("Turn ON: " + squeezebox_device)
    self.turn_on(squeezebox_device)
  
  def sb_playlist(self, playlist, squeezebox_device):
    self.log("1. sb_playlist called.")
    self.log("2. Media Device: " + squeezebox_device)
    self.log("Play " + playlist + " on " + squeezebox_device)
    self.call_service("squeezebox/call_method", entity_id = squeezebox_device, command = "playlist", parameters = ["resume", playlist])

  def sb_playlist_clear(self, squeezebox_device):
    self.log("Clearing playlist")
    self.call_service("squeezebox/call_method", entity_id = squeezebox_device, command = "playlist", parameters = "clear")

  def switch_on_pioneer_amp(self):
    device_name = "pioneer_amp"
    remote_location = self.find_remote_location(device_name)
    self.call_service("remote/send_command", entity_id = remote_location, device = device_name, command ="power_on")
  
  def switch_off_pioneer_amp(self):
    device_name = "pioneer_amp"
    remote_location = self.find_remote_location(device_name)
    self.call_service("remote/send_command", entity_id = remote_location, device = device_name, command ="power_off")

  def find_remote_location(self, device_name):
    for player_location in globals.players:
      device_id = globals.players[player_location]["remote_amp"]
      if device_name in device_id:
        remote_location = globals.players[player_location]["remote_location"]
        break
    return remote_location

  def select_input_on_pioneer_amp(self, media_player_name):
    for player_location in globals.players:
      player_id = globals.players[player_location]["squeezebox_id"]
      self.log(player_id)
      if media_player_name in player_id:
        input_name = globals.players[player_location]["remote_amp_input"]
        remote_location = globals.players[player_location]["remote_location"]
        remote_device_id = globals.players[player_location]["remote_amp"]
        self.log(input_name)
        break
    self.call_service("remote/send_command", entity_id = remote_location, device = remote_device_id, command = input_name)

  def find_remote_amp(self, amp_name):
    all_locations = []
    all_players = []
    for player_location in globals.players:
      if "remote_amp" in globals.players[player_location].keys():
        remote_amp = globals.players[player_location]["remote_amp"]
        if remote_amp == amp_name:
          player_name = globals.players[player_location]["squeezebox_id"]
          all_locations.append(str(player_location))
          all_players.append(player_name)
    return all_locations, all_players

  def get_currently_playing_song(self, location):
    media_artist = "No player found."
    media_title = "No player found."
    for player_location in globals.players:
      if player_location == location:
        player_id = globals.players[player_location]["squeezebox_id"]
        media_artist = self.get_state(player_id, attribute = "media_artist")
        if media_artist != None:
          media_title = self.get_state(player_id, attribute ="media_title")
        else:
          media_artist = "No artist."
          media_title = "No title."
    return media_artist, media_title


