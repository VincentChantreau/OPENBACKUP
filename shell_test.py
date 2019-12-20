from cmd import Cmd
# import readline
import json

from interaction import interaction
from time import sleep

try:
    with open('openbackup_config.json') as config:
        config_file = json.load(config)
except FileNotFoundError or PermissionError:
    print("Error while reading/opening the configuration file, exiting")
    sleep(5)
    exit()

command = interaction(
    config_file)  # Create an interaction object to interact with the DB, passing the config file in parameters

change_options = ["name", "ip"]
list_options = ["switch", "router", "firewall",
                "all"]
add_options = ["csv", "device"]


# TODO USE A DB CALL TO RETRIEVE VALUE IN DEVICE TYPE TABLE TO BE DYNAMIC


class Prompt(Cmd):
    prompt = "OPENBACKUP>"

    def do_set_backup(self,arg):
        command.trigger_backup(arg)

    def do_set_backup_interval(self,arg):
        command.set_backup_interval(arg)

    def do_list(self, arg):
        command.list(arg)

    def complete_list(self, text, line, begidx, endidx):
        if not text:
            completion = list_options
        else:
            completion = [f
                          for f in list_options
                          if f.startswith(text)
                          ]
        return completion

    def do_add(self, arg):
        if arg == "csv":
            command.add_device_csv_list()
        elif arg == "device":
            command.add_device_to_db()
        else:
            print("Unknown option")

    def complete_add(self, text, line, begidx, endidx):
        if not text:
            completion = add_options
        else:
            completion = [f
                          for f in add_options
                          if f.startswith(text)
                          ]
        return completion

    def do_change(self, arg):

        if arg and arg in change_options:

            if arg == "name":
                command.change_device_name()

            if arg == "ip":
                command.change_device_ip()
        else:
            print("Unknown option")

    def complete_change(self, text, line, begidx, endidx):

        if not text:
            completion = change_options
        else:
            completion = [f
                          for f in change_options
                          if f.startswith(text)
                          ]
        return completion

    def do_get_config(self, arg):
        command.call_back_conf()

    def do_exit(self, arg):
        exit()

    # HELP SECTION

    def help_list(self):
        print("This command allow you to list all devices that are registered in the Database")
        print("You can use the parameters all, switch, router,firewall to be more or less specific")
        # Should add a parameter to select device category like '--switch' or '--firewall'

    def help_change(self):
        print("This command allow you to change the name or the IP address of a device in the Database")
        print("Parameters are : ip / name ")

    def help_add(self):
        print("This command takes one parameter : csv or device.")
        print(
            "the device option allow you to add a new device to the Database, by setting his IP address, name, type and location (optionnal)")
        print("csv add multiple device at the same time with a single csv file")
        print("The CSV syntax must be the following one : ip_address,device_name,device_type,device_location(optional)")

    def help_get_config(self):
        print(
            "This command allow you to get back a configuration file from a device that you will be prompted to specify")
        print(
            "You can choose between showing the configuration on screen or save it in the DOWNLOADED CONFIGURATION folder")

    def help_set_backup(self):
        print("Can take value on or off to activate the backup scheduler")

    def help_set_backup_interval(self):
        print("Set the backup interval, can't be defined under a second")
    # Create a def for basic action like add, show, del etc, and the precise completion with another def. Can be cool


Prompt().cmdloop()
