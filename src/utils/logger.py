from datetime import datetime


color_lightgray = "\033[37m"
color_blue = "\033[34m"
color_reset = "\033[0m"
color_red = "\033[31m"
color_yellow = "\033[33m"
color_green = "\033[32m"
color_lime = "\033[92m"

@staticmethod
def info(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_blue}INFO{color_reset}     {message}")

@staticmethod
def success(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_lime}OK{color_reset}       {message}")

@staticmethod
def warning(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_yellow}WARN{color_reset}     {message}")

@staticmethod
def error(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_red}ERR{color_reset}      {message}")

@staticmethod
def debug(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color_lightgray}{current_time} {color_green}DBG{color_reset}      {message}")