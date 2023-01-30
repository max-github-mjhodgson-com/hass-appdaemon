# Global Variables
import secrets

# Max
person_max = secrets.person_max

# Notifications
max_app = secrets.max_app
max_telegram = secrets.max_telegram
max_app_note_9 = secrets.max_app_note_9
notify_max_all = "notify/max_all"

# Garage Specific
garage_door_power_switch = "switch.teckin02"
garage_light_entity = "light.garage_light"
garage_door_entity = "cover.garage_door"
garage_motion_sensor = "binary_sensor.multisensor_6_home_security_motion_detection"
garage_light_timer = "timer.garage_light_motion"
garage_door_power_timer = "timer.garage_door_auto_power"
garage_door_no_motion_timer = "timer.garage_door_auto_close_no_motion"
garage_alert_channel = "Garage"
garage_door_alert_tag = "garage-door"
garage_light_sensor = "sensor.multisensor_6_illuminance"
garage_temperature_sensor = "sensor.multisensor_6_air_temperature"
garage_humidity_sensor = "sensor.multisensor_6_humidity"
garage_notify_app = "notify/garage_app"
garage_input_number_garage_close_timer = "input_number.garage_door_close_timer"
garage_input_number_garage_open_timer = "input_number.garage_door_open_timer"
garage_light_off_timer_duration = "120"

# Doorbell Specific
doorphone_alert_channel = "Doorphone"
doorphone_doorbell_tag = "doorbell"
frontdoor_motion_timer = "timer.front_door_motion"
doorphone_power_poe_injector = "switch.silvercrest01_l3"
reboot_start_time = "01:29:00"
reboot_end_time = "01:35:00"
frigate_hostname = secrets.frigate_hostname
frigate_port = "5000"

# RFID Cards:
cards_garage_door = secrets.cards_garage_door

# CCTV:
cctv_media_location = "/config/media/cctv"
#frontdoor_camera = "camera.front_door"
frontdoor_camera = "camera.front_doorbell"
frigate_port = "5000"
frigate_current_frontdoor_pic_url =  "http://" + secrets.frigate_hostname + ":" + frigate_port + "/api/front_doorbell/latest.jpg"
#doorbell_pressed_picture = "/config/tmp/doorbell_pressed.jpg"

# Squeezeboxes:
squeezebox_dining = "media_player.dining_room"
squeezebox_spare_bedroom = "media_player.spare_bedroom"
squeezebox_transporter = "media_player.transporter"
squeezebox_transporter_power = "switch.teckin07"
squeezebox_transporter_timer = "timer.squeezebox_transporter_auto_power_off"
# Nested dictionary of SB locations, remote functions and power controls.
players = { "lounge": { "squeezebox_id": squeezebox_transporter,
                        "power": squeezebox_transporter_power,
                        "power_off_timer": squeezebox_transporter_timer,
                        "friendly_name": "Transporter",
                        "friendly_location": "Lounge",
                        "remote_location": "remote.lounge",
                        "remote_amp": "pioneer_amp",
                        "remote_amp_input": "input_tuner",
                        "remote_type": "ir"},
            "spare_bedroom": { "squeezebox_id": squeezebox_spare_bedroom,
                                #"power": "none",
                                "friendly_name": "Spare Bedroom Radio",
                                "friendly_location": "Spare Bedroom"},
            "dining_room": { "squeezebox_id": squeezebox_dining,
                                #"power": "none",
                                "friendly_name": "Dining Room",
                                "friendly_location": "Dining Room",
                                "remote_location": "remote.lounge",
                                "remote_amp": "pioneer_amp",
                                "remote_amp_input": "input_ld",
                                "remote_type": "ir"}
          }

# House Mode:
house_mode_selector = "input_select.house_mode_l"
house_occupied = ['Home', 'Just Arrived']  #, 'Sleep']
house_not_occupied = ['Out', 'Away', 'Just Left', 'Pre-arrival']
house_sleep = ['Sleep']

# NFC Tags:
ha_tag_car_keys_set_01 = secrets.ha_tag_car_keys_set_01
tag_id_car_keys_set_01 = secrets.tag_id_car_keys_set_01
esp_light_blue_magnetic_tag = secrets.esp_light_blue_magnetic_tag

# Sets of Tags:
car_keys_set_01 = [ha_tag_car_keys_set_01, tag_id_car_keys_set_01]
esp_tags = [esp_light_blue_magnetic_tag, tag_id_car_keys_set_01]

# Tags for Things:
garage_door_nfc_tags = [car_keys_set_01]

# Tag reader ID's:
max_phone = secrets.max_phone
test_reader = secrets.test_reader

# Kitchen Kettle
kettle = "switch.teckin06"
kettle_timer = "timer.kettle_auto_switch_off"
kettle_timer_active = "input_boolean.kettle_timer_active"

# Asterisk:
asterisk_host = secrets.asterisk_host  # IP Address of Asterisk Server
asterisk_server_port = secrets.asterisk_server_port  # Port of Asterisk Server.  AMI default port is 5038.
asterisk_manager_username = secrets.asterisk_manager_username  # username for Asterisk AMI as configured in /etc/asterisk/manager_additional.conf
asterisk_manager_secret = secrets.asterisk_manager_secret  # password for Asterisk AMI as configured in /etc/asterisk/manager_additional.conf
doorphone_extension_number = secrets.doorphone_extension_number

# Mobile App:
android_click_action_open_garage_door = "open_garage_door"
android_click_action_close_garage_door = "close_garage_door"
android_click_action_power_off_garage_door = "garage_power_off"
android_click_action_close_garage_door_in_5_minutes = "close_garage_door_in_5_minutes"
android_click_action_open_garage_door_in_5_minutes = "open_garage_door_in_5_minutes"

android_app_action_open_garage_door = {"action":android_click_action_open_garage_door, "title":"Open Door"}
android_app_action_switch_off_garage_door = {"action":android_click_action_power_off_garage_door, "title":"Power OFF"}
android_app_action_close_garage_door = {"action":android_click_action_close_garage_door, "title":"Close Door"}
android_app_action_close_garage_door_in_5_minutes = {"action":android_click_action_close_garage_door_in_5_minutes, "title":"Close Door in 5 Minutes"}
android_app_action_open_garage_door_in_5_minutes = {"action":android_click_action_open_garage_door_in_5_minutes, "title":"Open Door in 5 Minutes"}

# Lights:
porch_light = "light.porch_old"
porch_light_timer = "timer.porch_light_auto_dim"
porch_light_dim_value = 30
landing_light = "light.landing"
dining_table_light = "light.dining_table"
lounge_main_light = "light.lounge_main"
lounge_lamp = "light.lounge_lamp"
dining_lamp = "light.dining_lamps"
christmas_tree = "switch.christmas_tree"
christmas_wall_lights = "switch.christmas_wall_lights"

# Lounge Lamp Select Names
lounge_lamp_select_name = "Lounge Lamp" 
dining_lamp_select_name = "Dining Lamp"
lounge_lamps_input_select = "input_select.lounge_dining_lamp_link_master"

# Light Groups (without the "group." bit):
all_lights = "lights"
outside = "outside"
lounge = "lounge"

# Sunset Sensor Entity:
next_sunset = "sensor.nextsunset"

# Remote control functions:
lounge_remote = "remote.lounge"
remote_control = { "pioneer_amp": {"location": "lounge", "power_on": "power_on", "power_off": "power_off", "mute": "mute", "volume_up": "vol_up", "volume_down": "vol_down"},
                   "humax_pvr": {"location": "lounge", "mute": "mute", "power_on": "0"},
                 }

# Hall power controls:
huawei_4g_router = "switch.silvercrest01_l1"
draytek_router = "switch.silvercrest02_l2"
doorphone_power = "switch.silvercrest01_l3"

kettle_timer = "timer.kettle_auto_switch_off"
kettle_threshold = "binary_sensor.kettle_power_threshold"

# Calendar Stuff:
#vacation_max = secrets.vacation_max
vacation_calendars = { "max": secrets.vacation_max}
away_calendars = { "max": secrets.away_max}
house_calendar = secrets.house_calendar

workday_sensor = "binary_sensor.workday_l"
travel_time_to_pbm = secrets.travel_time_to_pbm
travel_time_from_pbm = secrets.travel_time_from_pbm

person_detection_switch = "input_boolean.person_detection_frontdoor"

# Ford Pass
car_alarm = "sensor.fordpass_alarm"
car_lock = "lock.fordpass_doorlock"
car_battery = "sensor.fordpass_battery"
car_messages = "sensor.fordpass_messages"
car_ignition_status = "sensor.fordpass_ignitionstatus"
car_alarm_status = "sensor.fordpass_alarm"
car_refresh_button = "input_button.refresh_ford_pass_status"
car_tracker = secrets.max_car_tacker
car_refresh = "fordpass/refresh_status"
car_distance_to_empty = "sensor.fordpass_distance_to_empty"
car_window_position = "sensor.fordpass_windowposition"
car_door_status = "sensor.fordpass_doorstatus"

# Zones
pbm_zone = secrets.pbm_zone

# Test
imported_secret = secrets.test_secret + " Wombat"

log_partition_line_length = 40
