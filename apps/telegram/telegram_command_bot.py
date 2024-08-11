# Telegram bot.
#
# Can execute home automation functions from a Telegram messaging client from pre-authenticated users.
#
# Listens for input from telegram_command and telegram_callback events.
# Creates Telegram menus for when on mobile devices.
#
# Version: 0220724.1
#
# Max Hodgson 2024
#
import time, datetime 
import random
import os
import appdaemon.plugins.hass.hassapi as hass
import globals_module as globals

from datetime import datetime

class TelegramCommandBot(hass.Hass):

    def initialize(self):
        now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
        this_script = os.path.basename(__file__)
        self.log("=" * globals.log_partition_line_length)
        self.log(this_script + " running at {}.".format(now))
        self.log("=" * globals.log_partition_line_length)

        # Set up variables:
        self.last_message = ""
        self.reply_message = ""
        self.conversation_gap_timeout = 1800
        self.last_conversation = {}
        self.greeting_message = ["Hi", "Hello", "Greetings", "Good day", "Hey", "Bonjour", "Hola", "Hallo", "Hej", "Dia duit", "nuqneH"]
        self.valid_house_modes = ["away", "home", "out","pre-departure", "sleep"]
        
        # Telegram menu commands:
        self.exit_element = ["/exit"]
        self.menu_exit_element = "Exit Menu:" + str(self.exit_element[0])
        self.garage_light_on = ["/garage_light_on"]
        self.garage_light_off = ["/garage_light_off"]
        self.garage_door_power_timer_reset = ["/garage_door_power_timer_reset"]
        self.garage_door_power_timer_resume = ["/garage_door_power_timer_resume"]
        self.garage_door_power_timer_finish = ["/garage_door_power_timer_finish"]
        self.garage_door_power_timer_finish = ["/garage_door_power_timer_pause"]
        self.garage_door_close_and_power_off = ["/garage_door_close_and_power_off"]
        self.garage_door_power_on_and_open = ["/garage_power_on_door_and_open"]
        self.garage_door_power_on = ["/garage_door_power_on"]
        self.garage_door_power_off = ["/garage_door_power_off"]
        self.garage_door_timer_reset = ["/garage_door_timer_reset"]
        self.garage_door_timer_resume = ["/garage_door_timer_resume"]
        self.garage_door_timer_finish = ["/garage_door_timer_finish"]
        self.garage_door_timer_pause = ["/garage_door_timer_pause"]
        self.garage_door_airgap = ["/garage_door_airgap"]
        self.open_garage_door_in_10_minutes = ["/open_garage_door_in_10_minutes"]
        self.sb_playlist_command = "/sb_playlist"
        self.sb_playlist = [self.sb_playlist_command]
        self.sb_playlist_player_command = "/sb_playlist_player"
        self.sb_playlist_player = [self.sb_playlist_player_command]
        
        # Load external app libraries:
        self.function_library = self.get_app("function_library")
        self.garage_library = self.get_app("garage")
        #self.auto_lights_library = self.get_app("auto_lights")
        self.house_mode_library = self.get_app("house_mode")
        self.squeezebox_library = self.get_app("squeezebox_control")
        self.door_phone_library = self.get_app("doorphone")
        #self.car_library = self.get_app("car")
        self.cctv_library = self.get_app("cctv")
        self.misc_automations = self.get_app("misc_automations")

        # Listen for Telegram events:
        self.listen_event(self.on_receive_telegram_command, 'telegram_command')
        self.listen_event(self.on_receive_telegram_callback, 'telegram_callback')

    #################################################################################################
    def on_receive_telegram_command(self, event_id, payload_event, *args):
      self.log("Received text: " + str(event_id))
      self.log("Payload: " +str(payload_event))
      #self.log("Payload event ID: " + str(event_id))
      user_id = payload_event['user_id']
      command = payload_event['command']
      first_name = payload_event['from_first']
      chat_id = payload_event['chat_id']
      chat_timestamp = payload_event['date']
      bot_args = payload_event['args']
      number_of_arguments = len(bot_args)
      self.log("User ID: " +str(user_id))
      self.log("Message: " +str(command))
      self.log("First name: " + str(first_name))
      self.log("ChatID: " + str(chat_id))
      self.log("Timestamp: " + str(chat_timestamp))
      self.log("Arguments: " + str(bot_args))
      self.log("Number of arguments: " + str(number_of_arguments))

      bot_command_string = command.lower()  # To Do: Need to test if text.
      bot_command = bot_command_string.strip("/")
      self.log("Bot command: " + str(bot_command))
      
      # Say hello.
      self.start_of_conversation(user_id, first_name)
      time.sleep(0.125) # This is the only was you can do sub-second delays.

      match bot_command:
        case "diskstation":
          self.diskstation(user_id, number_of_arguments, bot_args)
        case "doorphone":
          self.doorphone(user_id, number_of_arguments, bot_args)
        case "garage":
          self.garage(user_id, number_of_arguments, bot_args)
        case "help":
          self.show_help(user_id, number_of_arguments, bot_args)
        case "house":
          self.house_mode(user_id, number_of_arguments, bot_args)
        case "humax":
          self.humax(user_id, number_of_arguments, bot_args)
        case "internet":
          self.internet(user_id, number_of_arguments, bot_args)
        case "kettle":
          self.kettle(user_id, number_of_arguments, bot_args)
        case "light":
          self.light(user_id, number_of_arguments, bot_args)
        case "media":
          self.media(user_id, number_of_arguments, bot_args, bot_command)
        case ("squeezebox"| "sb"):
          self.squeezebox(user_id, number_of_arguments, bot_args, bot_command)
        case ("sabnzbd"|"sab"):
          self.sabnzbd(user_id, number_of_arguments, bot_args, bot_command)
        case ("where"):
          self.where(user_id, number_of_arguments, bot_args, first_name, bot_command)
        case "markdown":
          self.send_markdown_message(user_id, "## _The Last Markdown Editor, Ever_")
        case _:
          self.send_message(user_id, "Command not found.")
    
    def on_receive_telegram_callback(self, event_id, payload_event, *args):
      self.log("Telegram Callback")
      user_id = payload_event['user_id']
      message = payload_event['message']
      message_id = message["message_id"]
      data = payload_event['data']
      id = payload_event['id']
      chat_id = payload_event['chat_id']
      self.log("Message: " +str(message))
      self.log("Message ID: " +str(message_id))
      self.log("Data: " + str(data))
      self.log("ID: " + str(id))
      self.log("Chat ID: " +str(chat_id))

      menu_timeout = 60
      self.log(data.split())
      match data.split():
        case self.exit_element:
          self.delete_message(chat_id, message_id)
        case self.garage_door_power_on_and_open:
          menu_timeout = 30
          self.garage_library.power_on_and_open_garage()
        case self.garage_door_close_and_power_off:
          menu_timeout = 5
          self.garage_library.close_garage_and_power_off()
        case self.garage_door_power_on:
          menu_timeout = 120
          self.garage_library.switch_on_garage_door()
        case self.garage_door_power_off:
          menu_timeout = 1
          self.garage_library.switch_off_garage_door()
        case self.garage_door_timer_reset:
          menu_timeout = 5
          self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer, duration = globals.garage_door_no_motion_timer_duration) 
          self.send_message(user_id, "Resetting garage door timer.")
        case self.garage_door_timer_resume:
          self.call_service("timer/start", entity_id = globals.garage_door_no_motion_timer)
          self.send_message(user_id, "Resuming garage door timer.")
        case self.garage_door_timer_finish:
          menu_timeout = 5
          self.call_service("timer/finish", entity_id = globals.garage_door_no_motion_timer)
          self.send_message(user_id, "Finishing garage door timer.")
        case self.garage_door_timer_pause:
          menu_timeout = 5
          self.call_service("timer/pause", entity_id = globals.garage_door_no_motion_timer)
          self.send_message(user_id, "Pausing garage door timer.")
        case self.garage_light_on:
          menu_timeout = 5
          self.garage_library.garage_light_on()
        case self.garage_light_off:
          menu_timeout = 5
          self.garage_library.garage_light_off()
        case self.garage_door_power_timer_reset:
          menu_timeout = 5
          self.call_service("timer/start", entity_id = globals.garage_door_power_timer, duration = globals.garage_door_power_timer_duration)
          self.send_message(user_id, "Resetting garage door power timer.")
        case self.garage_door_power_timer_resume:
          menu_timeout = 5
          self.call_service("timer/start", entity_id = globals.garage_door_power_timer)
          self.send_message(user_id, "Resuming garage door power timer.")
        case self.garage_door_power_timer_finish:
          menu_timeout = 5
          self.call_service("timer/finish", entity_id = globals.garage_door_power_timer)
          self.send_message(user_id, "Finishing garage door power timer.")
        case self.open_garage_door_in_10_minutes:
           menu_timeout = 1
           self.set_value(globals.garage_input_number_garage_open_timer, 600)
        case self.garage_door_airgap:
          menu_timeout = 1
          self.garage_library.open_air_gap()
          self.send_message(user_id, "Opening garage door airgap.")
          self.call_service("timer/start", entity_id = globals.garage_door_power_timer, duration = "18000") # 5 Hours.
        case [self.sb_playlist_command, playlist_id]:
          self.playlist_name = self.extract_playlist_from_id(playlist_id)
          menu_timeout = 1
          self.show_playlist_device_menu(user_id)
        case [self.sb_playlist_player_command, player_id]:
          menu_timeout = 1
          playlist_text = "Playing " + str(self.playlist_name) + " on " + str(player_id) + "."
          self.send_message(user_id, playlist_text)
          self.log(playlist_text)
          self.squeezebox_library.sb_playlist(self.playlist_name, player_id)
        case _:
          self.log("Other option selected.")
          self.log(data)
          menu_timeout = 60
      self.run_in(self.on_close_menu_timer, menu_timeout, chat_id = chat_id, message_id = message_id)

    def on_close_menu_timer(self, cb_args):
      chat_id = cb_args["chat_id"]
      message_id = cb_args["message_id"]
      self.delete_message(chat_id, message_id)

    #################################################################################################    
    def send_message(self, user_id, message):
      self.call_service('telegram_bot/send_message',
                         target = user_id,
                         message = message)
    
    def delete_message(self, chat_id, message_id):
      self.call_service('telegram_bot/delete_message',
                         message_id = message_id,
                         chat_id = chat_id)

    def send_keyboard_menu(self, user_id, menu_title, message, keyboard):
      self.call_service('telegram_bot/send_message',
                         message = message,
                         title = menu_title,
                         target = user_id,
                         inline_keyboard = keyboard
                         )
    
    def send_html_message(self, user_id, message):
      self.call_service('telegram_bot/send_message',
                         target = user_id,
                         message = message,
                         parse_mode = "html")

    def send_markdown_message(self, user_id, message):
      self.call_service('telegram_bot/send_message',
                         target = user_id,
                         message = message,
                         parse_mode = "markdown")

    def send_video_by_url(self, user_id, message, url):
      self.call_service('telegram_bot/send_video',
                         target = user_id,
                         caption = message,
                         url = url)

    def start_of_conversation(self, user_id, user_name):
      if user_id not in self.last_conversation:
        self.last_conversation[user_id] = 0
      else:
        last_conversation_timestamp = self.last_conversation[user_id]

      # How long since last conversation?
      time_diff = time.time() - self.last_conversation[user_id]

      if time_diff > self.conversation_gap_timeout:
        # Say Hi to the user.
        hello_message = random.choice(self.greeting_message)
        self.send_message(user_id, hello_message + " " + str(user_name) + ",")
        self.last_conversation[user_id] = time.time()
        
    # Scan a dictionary of sensors and return the results.
    def scan_sensors(self, msg, sensors_to_scan):
      for template, sensor in sensors_to_scan.items():
              temp = self.get_state(sensor)
              msg += '  ' + template + ": " + temp + '\n'
      return msg

    def show_help(self, user_id, number_of_arguments, bot_args):
      self.log(bot_args)
      if number_of_arguments == 0:
        self.log("Show main help.")
        msg = 'Commands:' +'\n' 
        #msg += '/frontdoor pic' + '\t\t' + '-' + '\t' + 'Get a picture from the front door camera.' + '\n'
        msg += '/doorphone restart' + '\t' + '-' + '\t' + 'Doorphone controls.' + '\n'
        msg += '/garage status' + '\t' + '-' + '\t' + 'Get some environment details from the garage sensor.' + '\n'
        msg += '/garage door open' + '\t' + '-' + '\t' + 'Open the garage door.' + '\n'
        msg += '/garage door close' + '\t' + '-' + '\t' + 'Close the garage door.' + '\n'
        msg += '/house mode <out|away|home|sleep|pre-departure>' + '\t' + '-' + '\t' + 'Get or change current house mode.\n'
        msg += '/internet <drayek|virgin>' + '-' + '\t' + 'Internet information and controls' + '\n'
        msg += '/kettle on' + '\t' + '-' + '\t' + 'Turn on kettle power.' + '\n'
        msg += '/light status' + '\t' + '-' + '\t' + 'Get current light status.' + '\n'
        msg += '/media <playing>' + '\t' + '-' + '\t' + 'Media controls.' + '\n'
        msg += '/squeezebox, /sb <play|pause>|<playlist>\n'
        msg += '/sab <status|pause|resume>' + '\t' + '-' + '\t' + 'Control SabNZBD.' + '\n'
        self.send_message(user_id, msg)

    # Garage functions.
    def garage(self, user_id, number_of_arguments, bot_args):
      self.log(bot_args)
      garage_door_element = ""
      garage_door_status = self.get_state(globals.garage_door_entity)
      garage_door_power_element = ""
      garage_door_power_status = self.get_state(globals.garage_door_power_switch)
      garage_light_element = ""
      garage_light_status = self.get_state(globals.garage_light_entity)
      garage_door_timer_element = ""
      timer_running_status = ["active", "paused"]
      garage_door_close_timer = self.get_state(globals.garage_door_no_motion_timer)
      if garage_door_close_timer in timer_running_status:
        garage_door_timer_remaining = self.get_state(globals.garage_door_no_motion_timer, attribute = "remaining")     
      garage_door_power_timer_element_1 = ""
      garage_door_power_timer_element_2 = ""
      garage_door_power_timer_status = self.get_state(globals.garage_door_power_timer)
      if garage_door_power_timer_status in timer_running_status:
        garage_door_power_timer_remaining = self.get_state(globals.garage_door_power_timer, attribute = "remaining")
      garage_door_timer_element_1 = ""
      garage_door_timer_element_2 = ""
      garage_door_timer_element_3 = ""
      garage_door_open_in_10_minutes_element = ""
      garage_door_airgap_element = ""

      if number_of_arguments == 0:  # This controls the Telegram keyboard menus.
        match garage_door_status.lower():
          case "open":
            garage_door_element = self.create_menu_element("Close Door and Power Off", self.garage_door_close_and_power_off[0])
          case "closed":
            if garage_door_power_status.lower() == "off":
              garage_door_open_close_menu = "Power On and Open Door"
            elif garage_door_power_status.lower() == "on":
              garage_door_open_close_menu = "Open Door"
            garage_door_element = self.create_menu_element(garage_door_open_close_menu, self.garage_door_power_on_and_open[0])
            garage_door_open_in_10_minutes_element = self.create_menu_element("Open Door in 10 Minutes", self.open_garage_door_in_10_minutes[0])
            garage_door_airgap_element = self.create_menu_element("Open Airgap", self.garage_door_airgap[0])
          case _:
            garage_door_element = ""
        match garage_door_power_status.lower():
          case "on":
            garage_door_power_element = self.create_menu_element("Power Off Door", self.garage_door_power_off[0])
          case "off":
            garage_door_power_element = self.create_menu_element("Power On Door", self.garage_door_power_on[0])
          case _:
            garage_door_power_element = ""
        match garage_light_status.lower():
          case "on":
            garage_light_element = self.create_menu_element("Light Off", self.garage_light_off[0])
          case "off":
            garage_light_element = self.create_menu_element("Light On", self.garage_light_on[0])
          case _:
            garage_light_element = ""
        match garage_door_power_timer_status.lower():
          case "active":
            garage_door_power_timer_element_1 = self.create_menu_element("Reset Door Power Timer (" + garage_door_power_timer_remaining + ")", self.garage_door_power_timer_reset[0])
            garage_door_power_timer_element_2 = self.create_menu_element("Finish Door Power Timer (" + garage_door_power_timer_remaining + ")", self.garage_door_power_timer_finish[0])
          case "paused":
            garage_door_power_timer_element_1 = self.create_menu_element("Resume Door Power Timer (" + garage_door_power_timer_remaining + ")" , self.garage_door_power_timer_resume[0])
            garage_door_power_timer_element_2 = self.create_menu_element("Finish Door Power Timer (" + garage_door_power_timer_remaining + ")", self.garage_door_power_timer_finish[0])
        match garage_door_close_timer.lower():
          case "active":
            garage_door_timer_element_1 = self.create_menu_element("Reset Door Timer (" + garage_door_timer_remaining + ")", self.garage_door_timer_reset[0])
            garage_door_timer_element_2 = self.create_menu_element("Finish Door Timer (" + garage_door_timer_remaining + ")", self.garage_door_timer_finish[0])
            garage_door_timer_element_3 = self.create_menu_element("Pause Door Timer (" + garage_door_timer_remaining + ")", self.garage_door_timer_pause[0])
          case "paused":
            garage_door_timer_element_1 = self.create_menu_element("Resume Door Timer (" + garage_door_timer_remaining + ")", self.garage_door_timer_resume[0])
            garage_door_timer_element_2 = self.create_menu_element("Finish Door Timer (" + garage_door_timer_remaining + ")", self.garage_door_timer_finish[0])
        garage_menu = []
        garage_menu_elements = [  garage_door_element,
                                  garage_door_power_element,
                                  garage_light_element,
                                  garage_door_timer_element,
                                  garage_door_power_timer_element_1,
                                  garage_door_power_timer_element_2,
                                  garage_door_timer_element_1,
                                  garage_door_timer_element_2,
                                  garage_door_timer_element_3,
                                  garage_door_open_in_10_minutes_element,
                                  garage_door_airgap_element,
                                  self.menu_exit_element
                                ]
        for menu_item in garage_menu_elements:
          if menu_item != "":
            garage_menu.append(menu_item)
        self.log(garage_menu)
        self.send_keyboard_menu(user_id, "Garage Menu", "Please select an option below:", garage_menu)
      else:
        match bot_args[0]:
          # Garage help text.
          case "help":
            msg = "Help:\n"
            msg += " /garage - Show garage menu."
            msg += " /garage airgap\n garage status\n"
            msg += " /garage door on\n garage door off\n"
            msg += " /garage open <in> <number of minutes>\n"
            msg += " /garage close <in> <number of minutes>\n"
            #msg += " garage arrival <status|on|off>\n" # TBA
            self.send_message(user_id, msg)

          # Garage status.
          case "status":
            self.log("Garage Status.")
            self.send_garage_door_status_text(user_id)

          # Garage door controls.
          case "door":
            #timer_running_status = ["active", "paused"]
            #garage_door_power_timer_status = self.get_state(globals.garage_door_power_timer)
            #if garage_door_power_timer_status in timer_running_status:
            #  garage_door_power_timer_remaining = self.get_state(globals.garage_door_power_timer, attribute = "remaining")
            match number_of_arguments:
              case 1:
                #garage_door_status = self.get_state(globals.garage_door_entity)
                msg = "Garage door status: " + str(garage_door_status.capitalize())
                self.send_message(user_id, msg)
                msg = "Garage door power status: " + str(garage_door_power_status.capitalize())
                self.send_message(user_id, msg)
                garage_door_autoclose_timer_status = self.get_state(globals.garage_door_no_motion_timer)
                if garage_door_autoclose_timer_status != "idle":
                  msg = "Garage door auto-close timer status: " + str(garage_door_autoclose_timer_status)
                  self.log(msg)
                  self.send_message(user_id, msg)
                if garage_door_power_timer_status != "idle":
                  msg = "Garage door power timer status: " + str(garage_door_power_timer_status)
                  self.log(msg)
                  self.send_message(user_id, msg)
              case _ if number_of_arguments >2:
                match bot_args:
                  case ["door", "power", *power_activity]:
                    self.log("Power activities: " + str(power_activity[0]))
                    match power_activity[0]:
                      case ("on"|"off"):
                        msg = "Power control."
                      case "status":
                        msg = "Garage door power status: " + str(garage_door_power_status.capitalize()) + "\n"
                        msg += "Garage door power timer status: " + str(garage_door_power_timer_status.capitalize())
                        if garage_door_power_timer_status in timer_running_status:
                          msg += "\n" + "Garage door power timer remaining time: " + garage_door_power_timer_remaining
                    self.log(msg)
                    self.send_message(user_id, msg)
                  case ["door", "timer", *timer_activity]:
                    msg = "Timer activities: " + str(timer_activity[0])
                    match timer_activity[0]:
                      case "status":
                        msg = "Garage door power timer status: " + str(garage_door_power_timer_status.capitalize())
                        if garage_door_power_timer_status in timer_running_status:
                          msg += "\n" + "Garage door power timer remaining time: " + garage_door_power_timer_remaining
                        else:
                          msg = "Garage door power timer is not running."
                      case "pause":
                        if garage_door_power_timer_status == "running":
                          msg = "Garage door timer pause."
                          self.call_service("timer/pause", entity_id = globals.garage_door_power_timer)
                      case "reset":
                        msg = "Garage door timer reset."
                        self.call_service("timer/start", entity_id = globals.garage_door_power_timer, duration = globals.garage_door_power_timer_duration)
                      case "resume":
                        msg = "Garage door timer resume."
                        self.call_service("timer/start", entity_id = globals.garage_door_power_timer)
                      case _:
                        msg = "Error.\nHelp:\n /garage door timer <status|pause|reset|resume>"
                    self.log(msg)
                    self.send_message(user_id, msg)
          
          # Garage light controls.
          case "light":
            match number_of_arguments:
              case 1:
                msg = "Garage light is currently " + str(garage_light_status) + "."
              case 2:
                light_on_off = bot_args[1]
                msg = "Switching garage light "
                match light_on_off:
                  case "on":
                    self.garage_library.garage_light_on()
                    msg += "on."
                  case "off":
                    self.garage_library.garage_light_off()
                    msg += "off."
                  case _:
                    msg = "Unknown light state command."
            self.log(msg)
            self.send_message(user_id, msg)
          
          # Garage airgap controls.
          case "airgap":
            self.send_message(user_id, "Opening garage door airgap.")
            self.garage_library.open_air_gap()
          
          # Garage door open/close.
          case ("open"|"close"):
            open_close = bot_args[0]
            match number_of_arguments:
              case 1:
                self.log("Garage open/close.")
                self.open_close_garage_door(user_id, bot_args[0])
              case 3:
                if bot_args[1] == "in":
                  time_to_open_close = bot_args[2]
                  if time_to_open_close.isnumeric:
                    if time_to_open_close > 0:
                      msg = "Garage " + open_close + " in " + time_to_open_close + "minutes."
                    elif time_to_open_close == 0:
                      msg = "Cancelling garage " + open_close + " timer."  
                    match open_close:
                      case "open":
                        self.set_value(globals.garage_input_number_garage_open_timer, time_to_open_close)
                      case "close":
                        self.set_value(globals.garage_input_number_garage_close_timer, time_to_open_close)
                  else:
                    msg = "Error: Time value is not numeric."
                  self.log(msg)
                  self.send_message(user_id, msg)
              case _:
                self.send_message(user_id, "Input error.")

    # Get and send garage status information.
    def send_garage_door_status_text(self, user_id):
        sensors = { 'Door': globals.garage_door_entity,
                    'Door Power': globals.garage_door_power_switch,
                    'Light': globals.garage_light_entity,
                    'Humidity (%)': globals.garage_humidity_sensor,
                    'Temperature (C)': globals.garage_temperature_sensor,
                    'Light Level (Lux)': globals.garage_light_sensor,
                    'Garage Motion Status': globals.garage_motion_sensor,
                    'Garage Door Controller Ping Status': "binary_sensor.garage_pi_zero_ping",
                    "Garage Door Power Ping Status": "binary_sensor.teckin02_garage_door_power"
        }
        header = 'Garage state and sensors:\n\n'
        msg = self.scan_sensors(header, sensors)
        self.send_message(user_id, msg)
   
    # Open/Close Garage Door.
    def open_close_garage_door(self, user_id, door_function):
      self.log("Garage door open/close.")
      garage_door_state = self.garage_library.check_if_garage_closed()
      if garage_door_state == door_function:
        msg = "Garage door is already " + door_function + "."
      else:
        match door_function:
          case "open":
            msg = "Opening garage door."
            self.send_message(user_id, msg)
            self.garage_library.power_on_and_open_garage()
          case "close":
            msg = "Closing garage door."
            self.send_message(user_id, msg)
            self.garage_library.close_garage_and_power_off()

    # House mode.
    def house_mode(self, user_id, number_of_arguments, bot_args):
      current_house_mode = self.get_state(globals.house_mode_selector)
      #self.log("Current house mode: " + str(current_house_mode))
      msg = ""
      if bot_args[0] == "mode":
        if number_of_arguments == 1:
          house_mode_text = "The house is currently in: " + current_house_mode + " mode."
          self.send_message(user_id, house_mode_text)
          time.sleep(0.0125)
          if current_house_mode in ["Home", "Sleep"]:
            number_at_home = int(self.get_state("zone.home"))
            grammar_one = "is"
            match number_at_home:
              case 0:
                grammar_two = ""
                person_number = "nobody"
              case 1:
                grammar_two = "person"
                person_number = str(number_at_home)
              case _ if number_at_home > 1:
                grammar_one = "are"
                grammar_two = "people"
                person_number = str(number_at_home)
            msg = "There " + grammar_one + " currently " + person_number + " " + grammar_two + " at home."
        else:
          change_mode = bot_args[1]
          if change_mode != current_house_mode.lower():
            if change_mode in self.valid_house_modes:
              change_mode_to = change_mode.capitalize()
              msg = "Change house mode to: " + str(change_mode_to)
              self.select_option(globals.house_mode_selector, change_mode_to)
            else:
              msg = "Invalid house mode.\n Valid house modes are "
              for house_modes in range(len(self.valid_house_modes)):
                self.log(self.valid_house_modes[house_modes])
                msg += self.valid_house_modes[house_modes]
                msg += ", "
              msg = msg[:-2]
              msg += "."
          else:
            msg = "House is already in that mode."
      else:
        msg = "Invalid house command:\n"
        msg += "/house mode <house modes>"
      self.log(msg)
      self.send_message(user_id, msg)

    # Internet status and controls.
    def doorphone(self, user_id, number_of_arguments, bot_args):
      match number_of_arguments:
        case 0:
          msg = "Help: /doorphone <restart>"
          self.send_message(user_id, msg)
        case 1:
          match bot_args[0]:
            case "restart": # Power cycle doophone.
              msg = "Restarting doorphone."
              self.send_message(user_id, msg)
              self.call_service("switch/turn_off", entity_id = globals.doorphone_power) # This is set to automatically power back on.

    # Internet status and controls.
    def internet(self, user_id, number_of_arguments, bot_args):
      match number_of_arguments:
        case 0:
          msg = "Help: /internet <virgin|draytek>"
          self.send_message(user_id, msg)
        case 1:
          match bot_args[0]:
            case "virgin":
              virgin_ping = self.get_state("sensor.speedtest_ping")
              virgin_download_speed = self.get_state("sensor.speedtest_download")
              virgin_upload_speed = self.get_state("sensor.speedtest_upload")
              virgin_gateway_ping = self.get_state("binary_sensor.virgin_gateway_ping")
              virgin_modem_ping = self.get_state("binary_sensor.virgin_modem_ping")
              if "unavailable" in [str(virgin_ping), str(virgin_download_speed), str(virgin_upload_speed)]:
                self.send_message(user_id, "Speed test statistics are unavailable.")
              else:
                self.send_message(user_id, "Virgin ping response speed: " + str(virgin_ping))
                self.send_message(user_id, "Virgin download speed (Mbits/s): " + str(virgin_download_speed))
                self.send_message(user_id, "Virgin upload speed (Mbits/s): " + str(virgin_upload_speed))
              time.sleep(0.125)
              self.send_message(user_id, "Virgin gateway ping status: " + str(virgin_gateway_ping))
              self.send_message(user_id, "Virgin modem ping status: " + str(virgin_modem_ping))
            case "draytek":
              draytek_ping = self.get_state("binary_sensor.draytek_router_gateway_ping")
              self.send_message(user_id, "Draytek router ping status: " + str(draytek_ping))
              remote_dns_ping_1 = self.get_state("binary_sensor.remote_dns_test_1_ping_8_8_8_8")
              self.send_message(user_id, "Remote DNS 1 ping status: " + str(remote_dns_ping_1))
              remote_dns_ping_2 = self.get_state("binary_sensor.remote_dns_test_2_ping_9_9_9_9")
              self.send_message(user_id, "Remote DNS 2 ping status: " + str(remote_dns_ping_2))
              remote_vpn_endpoint_ping = self.get_state("binary_sensor.vpn_remote_endpoint_b")
              self.send_message(user_id, "Remote VPN ping status: " + str(remote_vpn_endpoint_ping))
        case _:
          self.log("Error text.")

    # Diskstation controls.
    def diskstation(self, user_id, number_of_arguments, bot_args):
      diskstation_status = self.get_state(globals.diskstation_id)
      match number_of_arguments:
        case 0:
          msg = "Diskstation is currently " + diskstation_status.lower() + "."
          self.log(msg)
          self.send_message(user_id, msg)
        case 1:
          match bot_args[0]:
            case "help":
              msg = "/diskstation <on|off>"
            case ("status"|"stat"):
              if diskstation_status == "off":
                msg = "Diskstation is currently off, cannot get status information."
              else:
                msg = "Diskstation status placeholder."
            case "on":
              self.log("on")
              if diskstation_status == "on":
                msg = "Diskstation is already on."
              else:
                msg = "Turning on Diskstation."
                self.turn_on(globals.diskstation_id)
            case "off":
              self.log("off")
              if diskstation_status == "off":
                msg = "Diskstation is already off."
              else:
                msg = "Turning off Diskstation."
                self.turn_off(globals.diskstation_id)
            case _:
              msg = "Invalid diskstation command."
          self.log(msg)
          self.send_message(user_id, msg)

    # SabNZBD controls.
    def sabnzbd(self, user_id, number_of_arguments, bot_args, bot_command):
      if number_of_arguments == 0:
        msg = "/sabnzbd status|purge|pause <in hours>|resume <in hours>|speed <speed in k,m or %>"
        self.send_message(user_id, msg)
      else:
        match bot_args[0]:
          # Get the current status.
          case "status":
            header = "SabNZBD Status:\n\n"
            sensors = { "Download Status": globals.sabnzbd_status,
                        "Download Speed": globals.sabnzbd_speed,
                        "Download Queue Count": globals.sabnzbd_queue_count,
                        "Amount Left to Download": globals.sabnzbd_left_to_download,
                        "Free Disk Space (Temp Directory)": globals.sabnzbd_free_disk_space,
                        "Total Disk Space": globals.sabnzbd_total_disk_space,
            }
            msg = self.scan_sensors(header, sensors)
            self.send_message(user_id, msg)

          # Pause downloads.
          case "pause":
            msg = "Pausing SabNZBD."
            #self.log(msg)
            self.send_message(user_id, msg)
            self.call_service("sabnzbd/pause", api_key = globals.sabnzbd_api_key)

          # Resume downloads.
          case "resume":
            match number_of_arguments:
              case 1:
                msg = "Resuming SabNZBD."
                #self.log(msg)
                self.send_message(user_id, msg)
                self.call_service("sabnzbd/resume", api_key = globals.sabnzbd_api_key)
              case 3:
                if bot_args[1] == "at" and bot_args != "":
                  time_to_resume = bot_args[2]
                  msg = "Resuming SabNZBD at " + time_to_resume + "."
                  self.misc_automations.pause_and_resume_sabnzbd_at(time_to_resume)
                  self.send_message(user_id, msg)

          # Purge old downloads.
          case "purge":
            msg = "Purging old SabNZBD downloads."
            #self.log(msg)
            self.send_message(user_id, msg)
            self.call_service(globals.sabnzbd_purge_command)

          # Set the download speed limit.
          case "speed":
            match number_of_arguments:
              case 1:
                current_download_speed = self.get_state(globals.sabnzbd_speed)
                msg = "Current SabNZBD download speed is " + str(current_download_speed) + "."
                #self.log(msg)
                #self.send_message(user_id, msg)
              case 2:
                speed_limit = str(bot_args[1])
                if speed_limit.isnumeric:
                  msg = "Set SabNZBD speed limit to " + str(speed_limit) + "."
                  self.call_service("sabnzbd/set_speed", speed = speed_limit, api_key = globals.sabnzbd_api_key)
                else:
                  msg = "Error: Speed limit value is not a number."
              #self.log(msg)
              #self.send_message(user_id, msg)
              case _:
                msg = "SabNZBD Speed Number Error."
            self.log(msg)
            self.send_message(user_id, msg)

    # Humax.
    def humax(self, user_id, number_of_arguments, bot_args):
      device_name = "humax_pvr"
      device_power_on_command = "power_on"
      humax_locations = {"lounge", "main_bedroom"}
      match number_of_arguments:
        case 0:
          msg = "/humax <location> <on|off|status>"
          self.send_message(user_id, msg)
        case _ if number_of_arguments > 1:
          if bot_args[0] in humax_locations:
            humax_function = 1
            remote_location = bot_args[0]
          else:
            humax_function = 0
            remote_location = "lounge"
            match bot_args[humax_function]:
              case "on":
                msg = "Powering on " + remote_location + " Humax."
                self.send_message(user_id, msg)
                self.call_service("remote/send_command", entity_id = "remote." + str(remote_location), device = device_name, command = device_power_on_command)
              case "off":
                self.log("Off")
              case "status":
                self.log("Status")
              case _:
                self.log("Error placeholder.")
  
    # Kettle controls.
    def kettle(self, user_id, number_of_arguments, bot_args):
      if number_of_arguments > 1:
        if bot_args[0] == "on":
          self.turn_kettle_on(user_id)
          msg = "Turning on Kettle."
        else:
          msg = "Parameter missing: /kettle on"
      else:
        msg = "Parameter missing: /kettle on"
      #self.log(msg)
      self.send_message(user_id, msg)

    # Light controls.
    def light(self, user_id, number_of_arguments, bot_args):
      match number_of_arguments:
        case 0:
          msg = "/light <status>\n"
          self.send_message(user_id, msg)
        case 1:
          match bot_args[0]:
            case ("status"|"stat"):
              self.log("I am working.")
              msg = "Error getting light status."
              all_lights_group = self.get_state("group.lights", attribute = "all")
              all_light_entities = all_lights_group["attributes"]
              lights = all_light_entities["entity_id"]
              light_state_pretty = "*Current light status:*\n\n"           
              for list in lights:
                clean_light_name = list.replace("_", "\_")
                light_state = self.get_state(list)
                light_state_pretty = light_state_pretty + clean_light_name + ": " + str(light_state) + "\n"
              msg = "\n" + light_state_pretty
          #self.log(msg)
          self.send_message(user_id, msg)

    # Squeezebox controls.
    def squeezebox(self, user_id, number_of_arguments, bot_args, bot_command):
      self.log("Squeezebox.")
      self.log(bot_args)
      msg = ""
      media_players = []
      match number_of_arguments:
        case 0:
          # To do: Show Squeezebox menu.
          pass
        case 1:
          match bot_args[0]:
            case "playlist":
              self.show_playlist_menu(user_id)

    def show_playlist_menu(self, user_id):
      # Requires a variable in the format: playlists = {"01":"Absolute Radio", "02":"BBC Radio 2",}, mine is located in the secrets file.
      self.log("Show playlist menu.")
      playlist_menu = []
      for playlist in globals.playlists:
        menu_name = str(globals.playlists[playlist])
        menu_element = self.sb_playlist[0] + " " + str(playlist)
        playlist_menu.append(menu_name + ":" + menu_element)
      playlist_menu.append(self.menu_exit_element)
      self.send_keyboard_menu(user_id, "Playlist Menu", "Please select a playlist below:", playlist_menu)

    def show_playlist_device_menu(self, user_id):
      # Requires the "players" dictionary variable located in the globals file.
      self.log("Show playlist device menu.")
      player_menu = []
      for player_location in globals.players:
        player_id = globals.players[player_location]["squeezebox_id"]
        player_name = globals.players[player_location]["friendly_name"]
        player_menu.append(player_name + ":" + str(self.sb_playlist_player[0]) + " " + player_id)
      player_menu.append(self.menu_exit_element)
      self.send_keyboard_menu(user_id, "Playlist Device Menu", "Please select a player device below:", player_menu)

    # Media controls.
    def media(self, user_id, number_of_arguments, bot_args, bot_command):
      msg = ""     
      match number_of_arguments:
        case 0:
          msg = "/media playing <location>\n"
          #self.send_message(user_id, msg)
        case 2:
          match bot_args[0]:
            case "playing":
              if bot_args[1] != "":
                location = bot_args[1]
                media_artist, media_track = self.squeezebox_library.get_currently_playing_song(location)
                msg = "Artist: " + media_artist + "\n"
                msg += "Track: " + media_track + "\n"
              else:
                msg = "Error: Squeezebox location missing."
        case _ if number_of_arguments >2:
#          self.log(bot_args)
#          self.log(bot_args[0])
          match bot_args[0]:
            case "playlist":
              playlist = bot_args[1]
              player = bot_args[2]
              msg = "Playlist: " + playlist + " on " + player + "."
      self.send_message(user_id, msg)

    def where(self, user_id, number_of_arguments, bot_args, user_name, bot_command):
      if number_of_arguments > 1:
        match bot_args:
          case ["am", ("i"| "I")]:
            self.log("Where am I?")
            person = "person." + user_name.lower()
            person_long = self.get_state(person, attribute = "longitude")
            person_lat = self.get_state(person, attribute = "latitude")
            street_address = self.misc_automations.get_address_from_long_lat(person_long, person_lat)
            self.call_service('telegram_bot/send_location',
                         target = user_id,
                         latitude = person_lat,
                         longitude = person_long)
            self.send_message(user_id, street_address)


    # This creates the Text and Activity string combinations for creating Telegram menus.
    def create_menu_element(self, menu_description_text, menu_activity):
      menu_element =  menu_description_text + ":" + menu_activity
      return menu_element

    def extract_playlist_from_id(self, playlist_id):
      for playlist in globals.playlists:
        if playlist_id == playlist:
          playlist_name = globals.playlists[playlist]
          return playlist_name
  