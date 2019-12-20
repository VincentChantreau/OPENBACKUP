import datetime
import hashlib
import secrets
import mysql
import json
import mysql.connector as mariadb
from mysqlx import errorcode
from netmiko import ConnectHandler


class Retrieve:

    def __init__(self, password):
        self.password = password
        config_file = {}
        try:
            with open('openbackup_config.json') as config:
                config_file = json.load(config)
        except FileNotFoundError:
            print("Error while reading config file, file not found !")
        try:
            config_data = config_file
            self.mariadb_connection = mariadb.connect(**config_data)
            self.cursor = self.mariadb_connection.cursor(buffered=True)
            print("Initialization done")
        except:
            print("Error while connecting to the Database")

    #LOG
    def log(self,data):
        # if os.path.isfile("LOG/backup.log"):
        with open('LOG/backup.log', "a+") as log:
            log.write("[" + str(datetime.datetime.now()) + "] : " + data + "\n")
            log.close()

    # SSH CONNECTION
    def connect_and_save_config(self,ip, password):
        try:
            device = ConnectHandler(device_type='cisco_ios', ip=ip, username='backup', password=password)
            output = device.send_command("show run view full")
        except TimeoutError:
            print("Connection to host : " + ip +" failed")
            self.log("Connection to host : " + ip +" failed")
        print("Running-configuration retrieved, closing connection to device")
        self.log("running config retrieved")
        device.disconnect()
        print("Writing configuration to a temporary file")
        self.log("Writing configuration to a temporary file")
        # write output to a temporary file
        path_to_temp_file = "TEMP/" + ip + ".temp"
        try:
            temp_config_file = open(path_to_temp_file, "w+")
            temp_config_file.write(output)
            temp_config_file.close()
        except FileNotFoundError or PermissionError:
            print("Error while opening/writing the temp file")
            self.log("Error while opening/writing the temp file")
    def calculate_hash_and_compare(self, temp_config_path, device_name, device_id):
        # First we check if there is an existing table in the DB for our device. If not, we create one
        temp_config = ""
        try:
            self.cursor.execute("SELECT * FROM {}".format(device_name))

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_NO_SUCH_TABLE:
                print("Table not found, creating a new one")
                self.log("Table not found, creating a new one")
                self.cursor.execute(
                    "CREATE TABLE {} (`device_id` int(32) unsigned NOT NULL,`backup_id` int(32) NOT NULL,`hash` text "
                    "NOT NULL,`date` datetime NOT NULL,`config` longtext NOT NULL,KEY `device_id` (`device_id`),"
                    "CONSTRAINT `{}_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `device_list` (`id`)) ENGINE=InnoDB "
                    "DEFAULT CHARSET=utf8mb4;".format(
                        device_name, device_name))
                self.mariadb_connection.commit()
                request_insert = "INSERT INTO {} (device_id,backup_id,hash) VALUES ('{}','0','0')".format(device_name,
                                                                                                          device_id)
                self.cursor.execute(request_insert)
                print("Table successfully created, continuing")
                self.log("Table successfully created, continuing")
            else:
                print("Existing table found, continuing")
                self.log("Existing table found, continuing")
        try:
            file = open(temp_config_path, "r")
            print("Successfully opened " + temp_config_path)
            self.log("Successfully opened " + temp_config_path)
            temp_config = file.read()
        except PermissionError:
            print("Error while reading temp file")
            self.log("Error while reading temp file")

        print("Reading done, converting into hash")
        self.log("Reading done, converting into hash")
        config = bytes(temp_config, encoding='utf-8')
        hash_object = hashlib.sha1(config)
        new_hash = hash_object.hexdigest()
        print("New hash : " + new_hash)
        self.log("New hash : " + new_hash)
        # Retrieve previous hash from DB
        previous_hash = ""
        request_prv_hash = "SELECT hash FROM {} WHERE backup_id=(SELECT MAX(backup_id) FROM {})".format(device_name,
                                                                                                        device_name)
        self.cursor.execute(request_prv_hash)
        result = self.cursor.fetchall()

        for row in result:
            previous_hash = "".join(row)
            print("Previous hash : " + previous_hash)
            self.log("Previous hash : " + previous_hash)
        # Compare both hash

        if not secrets.compare_digest(previous_hash, new_hash):
            # If True, no changes will be made.
            # If the new is != from the previous, push the new config file into the DB as a new row

            # Finding the latest backup entry in the table, and calculating the new backup_id Could be done in the DB
            # but with this technique we really use the last id ( which would not be the case with auto-incrementation)
            self.cursor.execute("SELECT MAX(backup_id) FROM %s" % (device_name))
            result = self.cursor.fetchall()
            for row in result:
                old_backup_id = ','.join(str(v) for v in row)

            new_backup_id = int(old_backup_id) + 1

            # date use datetime format on both side ( here and on the DB )
            date = datetime.datetime.now()

            # Opening the temporary conf file and then parse it to avoid single quote escape by replacing them with ²@,
            # and also removing the 2 first line of text
            config = open(temp_config_path, "r")
            new_config = config.read()
            first_parsed_config = new_config.replace("'", '²@').split('\n')[3:]
            # Then we join the parsed conf together
            second_parsed_config = "\n".join(first_parsed_config)
            parsed_config = second_parsed_config
            # Even if the configuration is changed when she's pushed in the DB , the previous hash was calculated with
            # the original config so that dosen't affect our hash comparison ! ;)
            add_new_config = (
                "INSERT INTO {} (device_id, backup_id, hash, config, date) VALUES ('{}','{}','{}','{}','{}')").format(
                device_name, device_id, new_backup_id, new_hash, parsed_config, date)
            self.cursor.execute(add_new_config)
            self.mariadb_connection.commit()  # without commiting the data are not pushed/saved in the DB, dkw.
            print("Successfully pushed new configuration into the Database !")
            self.log("Successfully pushed new configuration into the Database !")
        else:
            print("No changes were made, configuration still the same")
            self.log("No changes were made, configuration still the same")

    def get_ip_list(self):
        self.cursor.execute("SELECT ip_address FROM device_list")
        result_ip = self.cursor.fetchall()
        ip_list = []  # Creating a list to contain all IP address.
        for row in result_ip:
            ip_list.append("".join(row))
        return ip_list

    def get_name_list(self):
        self.cursor.execute("SELECT device_name FROM device_list")
        result_name = self.cursor.fetchall()
        name_list = []  # Creating a list to contain all names ( lining up with ip_list )
        for row in result_name:
            name_list.append("".join(row))
        return name_list

    def get_name(self, ip_address):
        self.cursor.execute("SELECT device_name FROM device_list WHERE ip_address = '{}'".format(ip_address))
        result_name = self.cursor.fetchall()
        name = ""
        for row in result_name:
            name = ("".join(row))
        return name

    def get_id(self, ip_address):
        self.cursor.execute("SELECT id FROM device_list WHERE ip_address = '{}'".format(ip_address))
        result_id = self.cursor.fetchall()
        for row in result_id:
            id = ','.join(str(v) for v in row)
        return id

    def get_interval(self):
        self.cursor.execute("SELECT backup_interval FROM config")
        result_interval = self.cursor.fetchall()
        for row in result_interval:
            interval = ','.join(str(v) for v in row)
        return interval

    def get_scheduler_state(self):
        try:
            self.cursor.execute("SELECT scheduler_state FROM config")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_NO_SUCH_INDEX:
                print("Unable to found state")
        result_state = self.cursor.fetchall()
        self.mariadb_connection.commit()
        state = ""
        for row in result_state:
            state = ("".join(row))
        return state

    def get_backup_state(self):
        try:
            self.cursor.execute("SELECT backup_state FROM config")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_NO_SUCH_INDEX:
                print("Unable to found state")
        result_state = self.cursor.fetchall()
        self.mariadb_connection.commit()
        state = ""
        for row in result_state:
            state = ("".join(row))
        return state

    # STANDALONE MODE
    def backup_all_device(self):
        i = 0
        name_list = self.get_name_list()
        ip_list = self.get_ip_list()
        for ip_address in ip_list:
            self.log("****** BACKUPING " + ip_address + " ******")
            print("Connection to : " + ip_address)
            self.log("Connection to : " + ip_address)
            # save sh run to ip.temp
            self.connect_and_save_config(ip_address, self.password)
            # use the ip.temp file to calculate a hash and then compare it with the hash of the last row in the database
            print("Calculating hash and compare it with the previous one")
            id = self.get_id(ip_address)
            self.calculate_hash_and_compare("TEMP/" + ip_address + ".temp", name_list[i], id)
            self.log("****** FINISHED BACKUPING " + ip_address + " ******")
            i = i + 1

        print("All the devices backup are fully up to date")
        # remove temp file

    # MANUAL MODE
    def backup_one_device(self, ip_address):
        name = self.get_name(ip_address)
        print("Connection to : " + ip_address)
        # save sh run to ip.temp
        self.connect_and_save_config(ip_address, self.password)
        # use the ip.temp file to calculate a hash and then compare it with the hash of the last row in the database
        print("Calculating hash and compare it with the previous one")
        id = self.get_id(ip_address)
        self.calculate_hash_and_compare("TEMP/" + ip_address + ".temp", name, id)








