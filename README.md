# hass-appdaemon
This is a repo for my Home Assistant Appdaemon Python code.
I don't use many automations in the Home Assistant Frontend. 99% of my automations are in Appdaemon (due to the complexity).
All of these are under active development and experimentation.

Areas covered are Grandstream SIP Doorphone, CCTV, House Mode, Garage, Calendar, Kitchen and Car (using Fordpass).

App Descriptions:

##Doorphone

This app interfaces with a Grandstream GDS3710 SIP Doorphone. Home Assistant receives events from the doorphone via webhooks, This creates a sensor, which can then be monitored. Each event passed from the doorphone carrys an identifier number, for example: 500 for doorbell or 900 for motion detected (using the internal motion detector). The Appdeamon app will action the events and grab pictures (from the camera), send messages, etc.


##CCTV.

This listens to a Frigate installation via MQTT and decodes the data it revceives to be able to extract labels, event IDs, zones and objects.


##House Mode

This controls the mode that the house is currently in. This is based on an input_select in Home Assistant, the modes are Home, Out (short a short time), Away (for a long time), Sleep, Pre-arrival, Scheduled arrival, Just Arrived, Just Left and Pre-departure. It will change modes when people enter or leave, or other modes timeout. It will also run automations based on the current mode.
