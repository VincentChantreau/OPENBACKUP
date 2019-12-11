from cmd import Cmd
# import readline
from interaction import interaction

change_options = ["name", "ip"]
command = interaction()
list_options=["switch","router","firewall","all"] # USE A DB CALL TO RETRIEVE VALUE IN DEVICE TYPE TABLE TO BE DYNAMIC
# list_options = command.allowed_type


class Prompt(Cmd):
    prompt = "OPENBACKUP>"

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

    def do_add_device(self, arg):
        command.add_device_to_db()

    def do_add_csv(self, arg):
        command.add_device_csv_list()

    def do_change(self, arg):

        if arg and arg in change_options:

            if arg == "name":
                command.change_device_name()

            if arg == "ip":
                command.change_device_ip()

    def complete_change(self, text, line, begidx, endidx):
        if not text:
            completion = change_options
        else:
            completion = [f
                          for f in change_options
                          if f.startswith(text)
                          ]
        return completion

    def do_get_config(self,arg):
        command.call_back_conf()

    def do_exit(self, arg):
        exit()

    # HELP SECTION

    def help_list(self):
        print("This command allow you to list all devices that are registered in the Database")
        print("You can use the parameters all, switch, router,firewall to be more or less precise")
        # Should add a parameter to select device category like '--switch' or '--firewall'

    def help_add_device(self):
        print("This command allow you to add a new device to the Database, by setting his IP address, name, type and location (optionnal)")

    def help_change(self):
        print("This command allow you to change the name or the IP address of a device in the Database")
        print("Parameters are : ip / name ")

    def help_add_csv(self):
        print("This command allow you to add multiple device at the same time with a single csv file")
        print("The CSV syntax must be the following one : ip_address,device_name,device_type,device_location(optional)")

    def help_get_config(self):
        print("This command allow you to get back a configuration file from a device that you will be prompted to specify")
        print("You can choose between showing the configuration on screen or save it in the DOWNLOADED CONFIGURATION folder")


    do_EOF = do_exit
    # Create a def for basic action like add, show, del etc, and the precise completion with another def. Can be cool


Prompt().cmdloop()
