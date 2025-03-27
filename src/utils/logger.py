from datetime import datetime
import os

color_lightgray = "\033[37m"
color_blue = "\033[34m"
color_reset = "\033[0m"
color_red = "\033[31m"
color_yellow = "\033[33m"
color_green = "\033[32m"
color_lime = "\033[92m"
color_purple = "\033[35m"

@staticmethod
def setup(thefilename, devmode):
    global filename
    global DEV_MODE
    if devmode:
        filename = os.path.splitext("utils." + os.path.basename(__file__))[0]
        DEV_MODE = True
        warn("Development mode enabled.")
        
    filename = thefilename

# 3/22/2025 Just realized how fucking stupid this is. I'm going to fix it later.
def get_current_filename():
    return f"{color_purple}{filename}{color_reset}"

@staticmethod
def info(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_blue}INFO{color_reset}     {get_current_filename()} {message}")

@staticmethod
def success(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_lime}OK{color_reset}       {get_current_filename()} {message}")

@staticmethod
def warn(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_yellow}WARN{color_reset}     {get_current_filename()} {message}")

@staticmethod
def error(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_red}ERR{color_reset}      {get_current_filename()} {message}")

@staticmethod
def debug(message):
    if DEV_MODE:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{color_lightgray}{current_time} {color_green}DBG{color_reset}      {get_current_filename()} {message}")