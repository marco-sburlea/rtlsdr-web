import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
   
    BASE_DIR =  os.path.dirname(os.path.abspath(__file__))
    CAPTURES_DIR =   os.path.join(BASE_DIR, 'captures')
    BUGREPORTS_DIR = os.path.join(BASE_DIR, 'bugreports')

    RTL_SDR_PATH = '/usr/bin/rtl_sdr'
    RTL_POWER_PATH = '/usr/bin/rtl_power'
    LSUSB_PATH = '/usr/bin/lsusb'

    GAIN_MIN = 0
    GAIN_MAX = 49.6

    DEFAULT_SAMPLE_RATE = 2_048_000
    DEFAULT_CAPTURE_DURATION = 5
    DEFAULT_COOLDOWN = 30