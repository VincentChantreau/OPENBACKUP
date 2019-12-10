import hashlib
import secrets
import mysql
import mysql.connector as mariadb
from mysqlx import errorcode
from netmiko import ConnectHandler


# SSH CONNECTION
def connect_and_save_config(ip, password):
    device = ConnectHandler(device_type='cisco_ios', ip=ip, username='network', password=password)
    output = device.send_command("show run")
    print("Running-configuration retrieved, closing connection to device")
    device.disconnect()
    print("Writing configuration to a temporary file")

    # write output to a temporary file
    path_to_temp_file = ip + ".temp"
    temp_config_file = open(path_to_temp_file, "w+")
    temp_config_file.write(output)
    temp_config_file.close()


def calculate_hash_and_compare(temp_config_path, device_name, device_id):
    # First we check if there is an existing table in the DB for our device. If not, we create one

    try:
        cursor.execute("SELECT * FROM {}".format(device_name))

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_NO_SUCH_TABLE:
            print("Table not found, creating a new one")
            cursor.execute(
                "CREATE TABLE {} (`device_id` int(32) unsigned NOT NULL,`backup_id` int(32) NOT NULL,`hash` text NOT NULL,`date` date NOT NULL,`config` longtext NOT NULL,`device_type` varchar(50) NOT NULL,`location` text,KEY `device_id` (`device_id`),CONSTRAINT `{}_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `device_list` (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;".format(
                device_name, device_name))
            mariadb_connection.commit()
            request_insert ="INSERT INTO {} (device_id,backup_id,hash) VALUES ('{}','0','0')".format(device_name,device_id)
            print(request_insert)
            cursor.execute(request_insert)
            print("Table successfully created, continuing")
        else:
            print("Existing table found, continuing")

    file = open(temp_config_path, "r")
    print("Successfully opened " + temp_config_path)
    temp_config = file.read()
    print("Reading done, converting into hash")

    config = bytes(temp_config, encoding='utf-8')
    hash_object = hashlib.sha1(config)
    new_hash = hash_object.hexdigest()
    print("New hash : " + new_hash)
    # Retrieve previous hash from DB
    previous_hash = ""
    request_prv_hash="SELECT hash FROM {} WHERE backup_id=(SELECT MAX(backup_id) FROM {})".format(device_name, device_name)
    cursor.execute(request_prv_hash)
    result = cursor.fetchall()

    for row in result:
        previous_hash = "".join(row)
        print("Previous hash : " + previous_hash)
    # Compare both hash

    if not secrets.compare_digest(previous_hash, new_hash):
        # If True, no changes will be made.
        # If the new is != from the previous, push the new config file into the DB as a new row
        cursor.execute("SELECT MAX(backup_id) FROM %s" % (device_name))
        result = cursor.fetchall()
        for row in result:
            old_backup_id = ','.join(str(v) for v in row)

        new_backup_id = int(old_backup_id) + 1
        config = open(temp_config_path, "r")
        new_config = config.read()

        add_new_config = ("INSERT INTO {} (device_id, backup_id, hash, config) VALUES ('{}','{}','{}','{}')").format(
            device_name, device_id, new_backup_id, new_hash, new_config)
        cursor.execute(add_new_config)
        mariadb_connection.commit()  # without commiting the data are not pushed/saved in the DB, dkw.
        mariadb_connection.close()
        print("Successfully pushed new configuration into the Database !")
    else:
        print("No changes were made, configuration still the same")




def get_ip_list():
    cursor.execute("SELECT ip_address FROM device_list")
    result_ip = cursor.fetchall()
    ip_list = []  # Creating a list to contain all IP address.
    for row in result_ip:
        ip_list.append("".join(row))
    return ip_list


def get_name_list():
    cursor.execute("SELECT device_name FROM device_list")
    result_name = cursor.fetchall()
    name_list = []  # Creating a list to contain all names ( lining up with ip_list )
    for row in result_name:
        name_list.append("".join(row))
    return name_list

def get_id(ip_address):
    cursor.execute("SELECT id FROM device_list WHERE ip_address = '{}'".format(ip_address))
    result_id = cursor.fetchall()
    for row in result_id:
        id=','.join(str(v) for v in row)
    return id

mode = "standalone"
# password = input("Password : ")
mariadb_connection = mariadb.connect(user='root', password='azerty', database='OPENBACKUP', host="10.2.2.105")
cursor = mariadb_connection.cursor(buffered=True)

# STANDALONE MODE
if mode == "standalone":
    i = 0
    name_list = get_name_list()
    ip_list = get_ip_list()
    for ip_address in ip_list:
        print("Connection to : " + ip_address)
        # save sh run to ip.temp
        connect_and_save_config(ip_address, password)
        # use the ip.temp file to calculate a hash and then compare it with the hash of the last row in the database
        print("Calculating hash and compare it with the previous one")
        id = get_id(ip_address)
        calculate_hash_and_compare(ip_address + ".temp", name_list[i], id)
        i = +1

    mariadb_connection.close()