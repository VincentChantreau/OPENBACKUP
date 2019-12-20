import csv

import mysql
import mysql.connector as mariadb
from mysqlx import errorcode



class interaction():
    def __init__(self, config_file):
        config_data = config_file
        self.mariadb_connection = mariadb.connect(**config_data)
        print("Initialisation done, config file loaded, connected to database")
        self.cursor = self.mariadb_connection.cursor(buffered=True)

    allowed_type = ["switch", "router", "firewall"]

    # [1] Add Device

    def add_device_to_db(self):
        ip_address = input("IP Address of the device : ")
        device_name = input("Device's name : ")
        device_type = input("Device type (switch, router, firewall) : ")
        device_location = input("Device location (leave blank if no location strategy) : ")
        if ip_address and device_name and device_type in self.allowed_type:
            # SQL QUERY
            try:
                add_device = "INSERT INTO device_list (ip_address,device_name, device_type, device_location) VALUES ('{}','{}','{}','{}')".format(
                    ip_address, device_name, device_type, device_location)
                self.cursor.execute(add_device)
                self.mariadb_connection.commit()
                print("Device successfully added to the Database")
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    print("This device already exist in the database")
        else:
            print("Please correctly set the parameters")

    # [2] Change IP

    def change_device_ip(self):
        old_ip = input("First, input the actual ip assigned to the device : ")
        # SQL QUERY
        get_name = "SELECT device_name FROM device_list WHERE ip_address = '{}'".format(old_ip)
        self.cursor.execute(get_name)
        result_name = self.cursor.fetchall()
        for row in result_name:
            name = "".join(row)
        new_ip = input("You can now enter the new IP address for " + name + " : ")
        set_ip = "UPDATE device_list SET ip_address = '{}' WHERE ip_address = '{}'".format(new_ip, old_ip)
        self.cursor.execute(set_ip)
        self.mariadb_connection.commit()
        print("Device " + name + " is now at : " + new_ip)

    # [3] Change Name

    def change_device_name(self):
        old_name = input("First, input the actual name assigned to the device : ")
        # SQL QUERY
        get_ip = "SELECT ip_address FROM device_list WHERE device_name = '{}'".format(old_name)
        self.cursor.execute(get_ip)
        result_ip = self.cursor.fetchall()
        for row in result_ip:
            ip = "".join(row)
        new_name = input("You can now enter the new name for the device at " + ip)
        set_name = "UPDATE device_list SET device_name = '{}' WHERE device_name = '{}'".format(new_name, old_name)
        self.cursor.execute(set_name)
        self.mariadb_connection.commit()
        print("Device name is now " + new_name + " at " + ip)

    # [4] List All Devices

    def list(self, type):
        if type == "all":
            get_devices = "SELECT device_name,ip_address FROM device_list"
        else:
            get_devices = "SELECT device_name,ip_address FROM device_list WHERE device_type = '{}'".format(type)
        self.cursor.execute(get_devices)
        all_devices = self.cursor.fetchall()
        device_list = []
        print("\nList of all devices : \n")
        for row in all_devices:
            device_list.append(" - ".join(row))

        for device in device_list:
            print(device)
        print("\n")

    # [5] Add device with a csv file
    # The csv layout need to be : ip,name,type,location
    # type must be switch,router or firewall

    def add_device_csv_list(self):
        print("Please place your CSV file in the IMPORT folder, and name it import_device.csv")
        launch = input("Are you ready to proceed ? (y/n) : ")
        launch.lower()

        if launch == "y" or launch == "yes":
            print("Launch ok")
            # opening csv file
            # catch exception <!>
            with open("IMPORT/import_device.csv") as host_list:
                readfile = csv.reader(host_list, delimiter=',')
                device_list = list(readfile)
                # catch exception indexerror if the csv is not correctly formatted
                try:
                    for i in range(len(device_list)):
                        # Assign values from the list
                        ip_address = device_list[i][0]
                        device_name = device_list[i][1]
                        device_type = device_list[i][2]
                        device_location = device_list[i][3]
                        # Check if the values are set and if device_type is allowed
                        if ip_address and device_name and device_type in self.allowed_type:
                            # SQL QUERY
                            try:
                                # Insert the value in the DB
                                add_device = "INSERT INTO device_list (ip_address,device_name, device_type, device_location) VALUES ('{}','{}','{}','{}')".format(
                                    ip_address, device_name, device_type, device_location)
                                self.cursor.execute(add_device)
                                self.mariadb_connection.commit()
                                print("Device successfully added to the Database")
                            except mysql.connector.Error as err:
                                if err.errno == errorcode.ER_DUP_ENTRY:
                                    # If the device is already declared in the table, inform the user
                                    print("This device already exist in the database")
                        else:
                            # inform user on error(s) in the csv file
                            print("Error on line : " + str(i) + " - bad device type or missing parameter(s)")
                except IndexError:
                    # inform user on bad formatting of the csv file
                    print("Bad CSV formating on line : " + str(i))

        elif launch == "n" or launch == "no":
            print("Imported aborted by the user")

        else:
            print("Please enter y or n")

    def call_back_conf(self):
        # Calling back the lastest configuration file and print it to the screen or save it to a file named "device_name-date.txt"
        # in the folder DOWNLOADED_CONFIGURATION Reformatting the conf file (single quote issue)
        # SQL QUERY
        device_name = input("Please enter the device's name : ")
        parsed_config_raw = ""
        parsed_config = ""
        date_data = ""
        date = ""
        try:

            # get the config data
            get_config = "SELECT config FROM {} WHERE backup_id=(SELECT MAX(backup_id) FROM {})".format(device_name,
                                                                                                        device_name)
            self.cursor.execute(get_config)
            parsed_config_raw = self.cursor.fetchall()
            # Get the date of the backup to add it to the file name
            get_date = "SELECT date FROM {} WHERE backup_id=(SELECT MAX(backup_id) FROM {})".format(device_name,
                                                                                                    device_name)
            self.cursor.execute(get_date)
            date_data = self.cursor.fetchall()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_NO_SUCH_TABLE:
                print("This device has no backup in the database or is not declared in the device list")

        for row in date_data:
            raw_date = row[0]
            # print(str(date))

        for row in parsed_config_raw:
            parsed_config = ("".join(row))
        full_date = str(raw_date)
        # Truncate full because of Windows file system that don't accept ":" in filename ...
        date = full_date[0:10]
        config = parsed_config.replace("²@", "'")
        # Ask user if he want to show or save the config as a file
        choice = input("Type SHOW for printing configuration to screen or SAVE to save it in the "
                       "DOWNLOADED_CONFIGURATION folder as " + device_name + "-" + date + ".txt : ")

        if choice and choice == "SHOW":
            print(config)

        elif choice and choice == "SAVE":
            # create a file and writing the conf data in it
            try:
                config_file = open("DOWNLOADED_CONFIGURATION/" + device_name + "-" + date + ".txt", "w+")
                config_file.write(config)
                config_file.close()
                print("File saved")
            except FileNotFoundError or PermissionError:
                print("An error happened when trying to create the file, please check permissions")
        else:
            print("Please type SHOW or SAVE")

    def trigger_backup(self, state):
        if state == "on" or state == "off":
            try:
                activate_scheduler_and_backup = "UPDATE `config` SET `backup_state` = '{}'".format(state)
                self.cursor.execute(activate_scheduler_and_backup)
                self.mariadb_connection.commit()
                print("Backup service successfully set to " + state)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_FK_COLUMN_CANNOT_CHANGE:
                    print("Cannot change backup service's state")


        else:
            print("Please precise a state to set to the backup service (on or off)")

    def set_backup_interval(self,interval):
        if int(interval) > 1 :
            try:
                set_interval = "UPDATE `config` SET `backup_interval` = '{}'".format(interval)
                self.cursor.execute(set_interval)
                self.mariadb_connection.commit()
                print("Backup interval successfully set to " + interval + " seconds")
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_FK_COLUMN_CANNOT_CHANGE:
                    print("Cannot change backup service's state")
        else:
            print("Please set an interval value superior to 1 second")

    # Mercredi Import CSV, download config (de_pars) locally, push back config ( maybe just the difference ? with no in
    # front of new command ?)
