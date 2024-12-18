# Global Variables
#
# Imports secrets_module.py
# The format of secrets is the same as this one.
# The variables can then be refered to as secrets.variable to be able to use them.
# Secrets is not uploaded to the git repo.
#
import appdaemon.plugins.hass.hassapi as hass
import secrets_module as secrets

persons_group = "group.persons"
mobile_app_users = secrets.mobile_app_users

# Max
person_max = secrets.person_max
maxs_cars = secrets.maxs_cars
max_phone = secrets.max_phone
max_phone_tracker = secrets.max_phone
user01_automation_library = secrets.user01_automation_library
working_day_template = secrets.working_day_template
working_day_max = secrets.working_day_template + "max"
telegram_chat_id = secrets.telegram_chat_id
log_partition_line_length = 40

# Ping updates
device_tracker_pings = secrets.device_tracker_pings #  A dictionary of device_tracker entries.

# Debug switch:
debug_switch = "input_boolean.appdaemon_debug"

# Main URL
home_assistant_url = secrets.home_assistant_hostname

# Notifications
max_app = secrets.max_app
max_telegram = secrets.max_telegram
max_app_note_9 = secrets.max_app_note_9
notify_max_all = "notify/max_all"
hall_panel_app = "notify/mobile_app_hall_panel"
telegram_security_alerts = secrets.telegram_security_alerts
telegram_garage_alerts = secrets.telegram_garage_alerts

# Misc
dark_sensor = "binary_sensor.dark"

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
garage_door_power_timer_duration = "600"
garage_door_no_motion_timer_duration = "3600"
garage_input_boolean_garage_airgap = "input_boolean.garage_airgap"

# Doorbell Specific
doorphone_alert_channel = "Doorphone"
doorphone_doorbell_tag = "doorbell"
frontdoor_motion_timer = "timer.front_door_motion"
doorphone_power_poe_injector = "switch.unifi_switch_hall_grandstream_doorphone_poe"
reboot_start_time = "01:29:00"
reboot_end_time = "01:35:00"
frigate_hostname = secrets.frigate_hostname
frigate_port = "5000"
frigate_external_hostname = secrets.frigate_external_hostname
doorphone_reboot_time_sensor = "binary_sensor.doorphone_reboot_time"
front_doorbell_person_sensor = "binary_sensor.front_doorbell_person_occupancy"
doorphone_ping = "binary_sensor.door_phone_ping"

# RFID Cards:
cards_garage_door = secrets.cards_garage_door

# CCTV:
cctv_media_location = "/homeassistant/media/cctv"
front_doorbell = "front_doorbell"
frontdoor_camera = "camera." + front_doorbell
frigate_port = "5000"
frigate_current_frontdoor_pic_url =  "http://" + secrets.frigate_hostname + ":" + frigate_port + "/api/front_doorbell/latest.jpg"
#doorbell_pressed_picture = "/config/tmp/doorbell_pressed.jpg"
front_doorbell_person_detection_switch = "input_boolean.person_detection_front_doorbell"
lovelace_cctv_tab = "/lovelace/10"
front_motion_detection_off_input_number = "input_number.turn_off_person_detection_front_doorbell"
persons_in_zone_count = {front_doorbell: "sensor.garden_person_count"}
camera_details = { "front_doorbell" : {
                                        "location": "Front Doorbell",
                                        "sensor": "sensor.cctv_front_doorbell_last_event_id",
                                        "friendly_name": "Front Doorbell Last Event ID",
                                        "detection_message": "Person detected at frontdoor.",
                                        "notification_switch": "input_boolean.person_detection_front_doorbell",
                                        "frigate_url": "http://" + secrets.frigate_hostname + ":" + frigate_port + "/api/front_doorbell/latest.jpg",
                                        "persons_in_zone_count": "sensor.garden_person_count",
                                        "notification_text": "Person detected at frontdoor.",
                                        "app_notification_title": "Doorphone Alert",
                                        "app_channel": "Front_Door",
                                        },
                }

# Squeezeboxes:
squeezebox_power_off_duration = "7200"
squeezebox_dining = "media_player.dining_room"
squeezebox_spare_bedroom = "media_player.spare_bedroom"
squeezebox_transporter = "media_player.transporter"
squeezebox_pioneer_amp = "media_player.pioneer_amp"
#squeezebox_transporter_power = "switch.teckin07"
squeezebox_transporter_power = "switch.xenon01_l3"
squeezebox_transporter_timer = "timer.squeezebox_transporter_auto_power_off"
squeezebox_office = "media_player.b3_office"
# Nested dictionary of SB locations, remote functions and power controls.
players = { "lounge":       {
                                "squeezebox_id": squeezebox_transporter,
                                "power": squeezebox_transporter_power,
                                "power_off_timer": squeezebox_transporter_timer,
                                "friendly_name": "Transporter",
                                "friendly_location": "Lounge",
                                "remote_location": "remote.lounge",
                                "remote_amp": "pioneer_amp",
                                "remote_amp_input": "input_tuner",
                                "remote_type": "ir",
                                "local": True,
                                "off_duration": 3600,
                                "idle_duration": 600,
                                "paused_duration": 600,
                            },
            "spare_bedroom": {
                                "squeezebox_id": squeezebox_spare_bedroom,
                                #"power": "none",
                                "friendly_name": "Spare Bedroom Radio",
                                "friendly_location": "Spare Bedroom",
                                "local": True,
                                "off_duration": 2,
                                "idle_duration": 600,
                                "paused_duration": 600,
                            },
            "dining_room": { 
                                "squeezebox_id": squeezebox_dining,
                                #"power": "none",
                                "friendly_name": "Dining Room",
                                "friendly_location": "Dining Room",
                                "remote_location": "remote.lounge",
                                "remote_amp": "pioneer_amp",
                                "remote_amp_input": "input_ld",
                                "remote_type": "ir",
                                "local": True,
                                "off_duration": 3600,
                                "idle_duration": 600,
                                "paused_duration": 600,
                            },
            "office":       {
                                "squeezebox_id": squeezebox_office,
                                "power": "none",
                                "friendly_name": "Office",
                                "friendly_location": "Office",
                                "remote_location": "none",
                                "remote_amp": "none",
                                "remote_amp_input": "none",
                                "remote_type": "none",
                                "local": False,
                                "off_duration": 2,
                                "idle_duration": 600,
                                "paused_duration": 600,
                            },
            "pioneer_amp": {
                                "squeezebox_id": squeezebox_pioneer_amp,
                                "power": "none",
                                "power_off_timer": "none",
                                "friendly_name": "Pioneer Amplifier",
                                "friendly_location": "Lounge",
                                "remote_location": "remote.lounge",
                                "remote_amp": "pioneer_amp",
                                "remote_amp_input": "input_vcr_1",
                                "remote_type": "ir",
                                "local": True,
                                "off_duration": 3600,
                                "idle_duration": 600,
                                "paused_duration": 600,
                            },
          }
playlists = secrets.playlists
tv_power = "switch.teckin05"

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
kettle_timer = "timer.kettle_auto_switch_off"
kettle_threshold = "binary_sensor.kettle_power_threshold"

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
android_app_click_action_confirm_location_notification = "confirm_location_notification"

android_app_action_open_garage_door = {"action":android_click_action_open_garage_door, "title":"Open Door"}
android_app_action_switch_off_garage_door = {"action":android_click_action_power_off_garage_door, "title":"Power OFF"}
android_app_action_close_garage_door = {"action":android_click_action_close_garage_door, "title":"Close Door"}
android_app_action_close_garage_door_in_5_minutes = {"action":android_click_action_close_garage_door_in_5_minutes, "title":"Close Door in 5 Minutes"}
android_app_action_open_garage_door_in_5_minutes = {"action":android_click_action_open_garage_door_in_5_minutes, "title":"Open Door in 5 Minutes"}
android_app_action_confirm_notification = {"action":android_app_click_action_confirm_location_notification, "title":"Confirm Location Notification"}

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
lounge_string_light = "light.lifx_strip_1"
lounge_string_light_timer = "timer.lounge_strip_light_timeout"
lounge_string_light_duration = "600"
lounge_light_sensor = "sensor.ep1_lounge_illuminance"
lounge_light_level = 0.6
lounge_mmwave_sensor = "binary_sensor.ep1_lounge_mmwave"
lounge_occupancy_sensor = "binary_sensor.ep1_lounge_occupancy"

# Lounge Lamp Select Names
lounge_lamp_select_name = "Lounge Lamp" 
dining_lamp_select_name = "Dining Lamp"
lounge_lamps_input_select = "input_select.lounge_dining_lamp_link_master"
lounge_fan = "switch.xenon01_l2"

# Light Groups (without the "group." bit):
all_lights = "lights"
outside = "outside"
lounge = "lounge"

# Sunset Sensor Entity:
next_sunset = "sensor.nextsunset"

# Remote control functions:
lounge_remote = "remote.lounge"
remote_control = {
                    "pioneer_amp": {"location": "lounge", "power_on": "power_on", "power_off": "power_off", "mute": "mute", "volume_up": "vol_up", "volume_down": "vol_down"},
                    "humax_pvr": {"location": "lounge", "mute": "mute", "power_on": "button_0"},
                 }

# Network device power controls:
#huawei_4g_router = "switch.silvercrest01_l1"
unifi_main_switch_power = "switch.silvercrest02_l1"
draytek_router_power = "switch.silvercrest02_l2"
switch_cab_usb_power = "switch.silvercrest02_l3"
#doorphone_power = "switch.silvercrest01_l3"


# Calendar Stuff:
#vacation_max = secrets.vacation_max
vacation_calendars = { "max": secrets.vacation_max}
away_calendars = { "max": secrets.away_max}
house_calendar = secrets.house_calendar
non_working_days_csv_path = "/config/apps/misc_automations/non_working_days.csv"

workday_sensor = "binary_sensor.workday_l"
travel_time_to_pbm = secrets.travel_time_to_pbm
travel_time_from_pbm = secrets.travel_time_from_pbm
travel_time_to_work = secrets.travel_time_to_work
travel_time_from_work = secrets.travel_time_from_work
work_carpark_zone = secrets.work_carpark_zone

person_detection_switch = "input_boolean.person_detection_frontdoor"

# Ford Pass
fordpass_car_lock = "lock.fordpass_doorlock"
car_messages = "sensor.fordpass_messages"
car_ignition_status = "sensor.fordpass_ignitionstatus"
car_alarm_status = "sensor.fordpass_alarm"
car_refresh_button = "input_button.refresh_ford_pass_status"
car_tracker = secrets.car_tracker
car_refresh = "fordpass/poll_api"   #"fordpass/refresh_status"
car_distance_to_empty = "sensor.fordpass_distance_to_empty"
car_window_position = "sensor.fordpass_windowposition"
car_door_status = "sensor.fordpass_doorstatus"
max_car_kit = secrets.max_car_kit
fordpass_refresh_counter = "counter.ford_pass_refresh"
fordpass_refresh_disable = "input_boolean.fordpass_refresh_disable"
fordpass_refresh_status = "input_select.fordpass_car_refresh_interval_timer"
fordpass_tyre_state = "sensor.fordpass_tirepressure"
fordpass_tyre_pressure_front_right = "sensor.fordpass_tyre_pressure_front_right"
fordpass_tyre_pressure_front_left = "sensor.fordpass_tyre_pressure_front_left"
fordpass_tyre_pressure_rear_right = "sensor.fordpass_tyre_pressure_rear_right"
fordpass_tyre_pressure_rear_left = "sensor.fordpass_tyre_pressure_rear_left"
fordpass_tyre_pressure_front_recommended = 2.4
fordpass_tyre_pressure_rear_recommended = 2.4
car_home_locations = secrets.car_home_locations
fordpass_car_direction = "sensor.fordpass_compass_direction"
fordpass_deep_sleep = "sensor.fordpass_deepsleep"
fordpass_outside_temp = "sensor.fordpass_outsidetemp"
fordpass_battery_voltage = "sensor.fordpass_battery_voltage"
fordpass_battery_level = "sensor.fordpass_battery"
fordpass_distance_to_empty = "sensor.fordpass_distance_to_empty"
fordpass_fuel_level = "sensor.fordpass_fuel"
fordpass_odometer = "sensor.fordpass_odometer"
fordpass_car_deepsleep_on = "ACTIVE"
fordpass_car_deepsleep_off = "DISABLED"
fordpass_alarm_armed = ["ARMED", "PREARMED"]
fordpass_alarm_disarmed = "DISARMED"
fordpass_door_lock_type = "sensor.fordpass_door_lock_type"
fordpass_engine_start_mileage = "sensor.fordpass_engine_start_mileage"
fordpass_last_trip_mileage = "sensor.fordpass_last_trip_mileage"
fordpass_lock_check_timer = "timer.car_lock_check"
fordpass_lock_timer_duration = "300"

    
max_phone_bluetooth = secrets.max_phone_bluetooth
diskstation_id = "switch.b3_diskstation01"

# Zones
pbm_zone = secrets.pbm_zone

# Movement and Occupancy sensors:
house_movement_sensors = "group.house_movement_sensors"
lounge_mmwave = "binary_sensor.ep1_lounge_mmwave"
lounge_sensor_light = "light.ep1_lounge2_mmwave_led"
lounge_pir = ""
lounge_occupancy = ""
security_zone_1 = ["lounge"]
security_zone_2 = ["landing"]
out_away_zones = [security_zone_1]
sleep_zones = [security_zone_1, security_zone_2]

# Network:
network_vpn_ping_status = "binary_sensor.vpn_remote_endpoint_b"
network_gateway_ping_status = "binary_sensor.draytek_router_gateway_ping"
network_remote_gateway_ping_status = "binary_sensor.virgin_gateway_ping"
network_modem_ping_status = "binary_sensor.virgin_modem_ping"
network_edgeswitch_ping_status = "binary_sensor.edgeswitch_loft_ping"
network_remote_dns1_ping_status = "binary_sensor.remote_dns_test_1_ping_8_8_8_8"


# App notification channels:
weather_channel = "Weather_Notfication"

# Android TV:
android_tv_app_details =    {
                                "Off":
                                {
                                    "ID": "None",
                                    "Exec": "",
                                    "Input_Select": "1",
                                },

                                "Home Screen":
                                {   "ID": "com.google.android.tvlauncher",
                                    "Exec": "adb shell am start -a android.intent.action.MAIN -c android.intent.category.HOME",
                                    "Input_Select": "1",
                                },

                                "Amazon Prime Video":
                                {
                                    "ID": "com.amazon.amazonvideo.livingroom",
                                    "Exec": "",
                                    "Input_Select": "0",
                                },

                                "Front Doorbell Stream":
                                {   "ID": "None",
                                    "Exec": "am start -a android.intent.action.VIEW -d " + secrets.front_doorbell_stream + " -n org.videolan.vlc/.gui.video.VideoPlayerActivity",
                                    "Input_Select": "0",
                                },

                                "IP Cam Viewer":
                                {   "ID": "com.rcreations.WebCamViewerPaid",
                                    "Exec": "am start -a android.intent.action.VIEW -n com.rcreations.WebCamViewerPaid/.IpCamViewerActivity",                                    "Input_Select": "1",\
                                },

                                "IPlayer":
                                {
                                    "ID": "com.nvidia.bbciplayer",
                                    "Exec": "",
                                    "Input_Select": "0",
                                },

                                "Jellyfin":
                                {
                                    "ID": "",
                                    "Exec": "am start -a android.intent.action.VIEW -n org.jellyfin.androidtv/.ui.startup.StartupActivity",
                                    "Input_Select": "0",
                                },

                                "Kodi":
                                {
                                    "ID": "org.xbmc.kodi",
                                    "Exec": "am start -a android.intent.action.VIEW -d -n org.xbmc.kodi/.Splash",
                                    "Input_Select": "1",
                                },

                                "Netflix":
                                {
                                    "ID": "com.netflix.ninja",
                                    "Exec": "am start -a android.intent.action.VIEW -n android.intent.action.VIEW -d -n com.netflix.ninja/.MainActivity",
                                    "Input_Select": "0",
                                },

                                "Nvidia Games":
                                {
                                    "ID": "",
                                    "Exec": "am start -a android.intent.action.VIEW -n com.nvidia.tegrazone3/com.nvidia.geforcenow.MallActivity",
                                    "Input_Select": "1",
                                },
                                
                                "PlutoTV":
                                {
                                    "ID": "tv.pluto.android",
                                    "Exec": "am start -a android.intent.action.VIEW -n tv.pluto.android/.leanback.controller.LeanbackSplashOnboardActivity",
                                    "Input_Select": "1",
                                },

                                "Sideload Launcher":
                                {
                                    "ID": "eu.chainfire.tv.sideloadlauncher",
                                    "Exec": "",
                                    "Input_Select": "0",
                                },

                                "Sky News":
                                {
                                    "ID": "com.onemainstream.skynews.android",
                                    "Exec": "am start -a android.intent.action.VIEW -n android.intent.action.VIEW -d -n com.onemainstream.skynews.android/.common.splash.SplashActivity",
                                    "Input_Select": "1",
                                },

                                "Smart Tube": 
                                {
                                    "ID": "com.teamsmart.videomanager.tv",
                                    "Exec": "am start -a android.intent.action.VIEW -n com.teamsmart.videomanager.tv/com.liskovsoft.smartyoutubetv2.tv.ui.main.SplashActivity",
                                    "Input_Select": "1",
                                },
                                
                                "Steam Link":
                                {
                                    "ID": "com.valvesoftware.steamlink",
                                    "Exec": "am start -a android.intent.action.VIEW -n com.valvesoftware.steamlink/com.valvesoftware.steamlink.SteamShellActivity",
                                    "Input_Select": "1",
                                },

                                "Twitch Video":
                                {
                                    "ID": "com.fgl27.twitch",
                                    "Exec": "am start -a android.intent.action.VIEW -n com.fgl27.twitch/.PlayerActivity",
                                    "Input_Select": "1",
                                },

                                "VLC":
                                {
                                    "ID": "org.videolan.vlc",
                                    "Exec": "am start -a android.intent.action.VIEW -n org.videolan.vlc/.StartActivity",
                                    "Input_Select": "1",
                                },
                            }

notification_lights = {
    "Lounge": "light.lifx_strip_1",
    "Main Bedroom": "",
    "Office": "",
    "Kitchen": "",
    "Garage": "",
}

# Washing Machine (Miele):
washing_machine_programmes_end_time = "sensor.washing_machine_finish_at"
washing_machine_completed = "program_ended"

# Weather:
#weather = "weather.accuweather"
#weather = "sensor.pirateweather_precip"
weather = secrets.weather
has_it_rained_today_switch = "input_boolean.has_it_been_raining"
wind_bearing = "sensor.pirateweather_wind_bearing"
wind_direction_sensor = "sensor.pirateweather_wind_direction"

tranporter_session_power_flag = "sensor.transporter_weekend_power"
tranporter_session_power_flag_name = "Transporter powered up already this home session"

telegram_input_text_message = "input_text.telegram_message"
org_bl_input_text = secrets.org_bl_input_text

# SabNZBD
sabnzbd_api_key = secrets.sabnzbd_api_key
sabnzbd_url = secrets.sabnzbd_url
sabnzbd_speed = "sensor.sabnzbd_speed"
sabnzbd_status = "sensor.sabnzbd_status"
sabnzbd_total_disk_space = "sensor.sabnzbd_total_disk_space"
sabnzbd_free_disk_space = "sensor.sabnzbd_free_disk_space"
sabnzbd_queue_count = "sensor.sabnzbd_queue_count"
sabnzbd_left_to_download = "sensor.sabnzbd_left_to_download"
sabnzbd_purge_command = "rest_command/b3_jenkins_purge_download"

lock_ibm_laptop_button = secrets.lock_ibm_laptop_button

class Globals(hass.Hass):
    def initialize(self):
        self.log("Globals")
        secrets_app = self.get_app("secrets")
        self.log("Globals initialised.")
