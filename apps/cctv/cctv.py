# CCTV App
# Max Hodgson 2023

import appdaemon.plugins.hass.hassapi as hass
import time, requests
from datetime import timedelta
from datetime import datetime
import globals

class Cctv(hass.Hass):

  def initialize(self):
    self.log("=" * globals.log_partition_line_length)
    now = datetime.strftime(self.datetime(), '%H:%M %p, %a %d %b')
    self.log("running at {}.".format(now))
    
    #Set up some variables:
    global frigate_camera_url
    frigate_camera_url = "http://" + globals.frigate_hostname + ":" + globals.frigate_port + "/api/"  #+ camera_location +"/latest.jpg"

    global FunctionLibrary  
    FunctionLibrary = self.get_app("function_library")


###############################################################################################################
  # Other functions:
###############################################################################################################

 # Take a picture.
  def get_picture_from_frigate(self, camera_id, picture_type):   #, picture_caption):
    #self.log("Take picture: " + picture_type)
    snapshot_filename = globals.cctv_media_location + "/" + camera_id + "/latest/" + camera_id + "_" + picture_type + ".jpg"
    #self.log(snapshot_filename)
    image_timestamp = datetime.strftime(self.datetime(), '%Y%m%d_%H%M%S')
    directory_datestamp = datetime.strftime(self.datetime(), '%Y/%b/%d-%a')
    timed_snapshot_filename = globals.cctv_media_location + "/" + camera_id +"/" + directory_datestamp + "/" + camera_id + "_" + picture_type + "." + image_timestamp + ".jpg"
    #self.log(timed_snapshot_filename)
    self.get_latest_camera_picture(image_url = frigate_camera_url + camera_id + "/latest.jpg", image_filename = timed_snapshot_filename)
    self.get_latest_camera_picture(image_url = frigate_camera_url + camera_id + "/latest.jpg", image_filename = snapshot_filename)
    return timed_snapshot_filename, snapshot_filename

  def get_latest_camera_picture(self, kwargs):
    #self.log("Get latest camera picture.")
    #self.log("kwargs:")
    #self.log(kwargs)
    image_url = kwargs["image_url"]
    image_filename = kwargs["image_filename"]
    img_data = requests.get(image_url).content
    with open(image_filename, 'wb') as handler:
      handler.write(img_data)

    