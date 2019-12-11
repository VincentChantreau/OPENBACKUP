import csv

import mysql
import mysql.connector as mariadb
from mysqlx import errorcode


class interaction:

    mariadb_connection = mariadb.connect(user='root', password='azerty', database='OPENBACKUP', host="10.2.2.105")
    cursor = mariadb_connection.cursor(buffered=True)
    # allowed_type = ["switch", "router", "firewall"]
    #SQL QUERY
    try:
        get_device_type_list = "SELECT type FROM device_type"
        cursor.execute(get_device_type_list)
        mariadb_connection.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_NO_SUCH_TABLE:
            print("Table device_type not found")
    allowed_type = list(cursor.fetchall())

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
        print("Device name is now " + new_name + " at " + ip)

    # [4] List All Devices

    def list_all_devices(self,type):
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
                try:
                    for i in range(len(device_list)):
                        # for j in range (len(device_list[i])):
                        #     print(device_list[i][j])
                        ip_address = device_list[i][0]
                        device_name = device_list[i][1]
                        device_type = device_list[i][2]
                        device_location = device_list[i][3]
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
                            print("Error on line : " + str(i) + " - bad device type or missing parameter(s)")
                except IndexError:
                    print("Bad CSV formating on line : " + str(i))

        elif launch == "n" or launch == "no":
            print("Launch nok")

        else:
            print("Please enter y or n")

    def __init__(self):
        print("Initialisation done, connected to database")

    # Mercredi Import CSV, download config (de_pars) locally, push back config ( maybe just the difference ? with no in
    # front of new command ?)
