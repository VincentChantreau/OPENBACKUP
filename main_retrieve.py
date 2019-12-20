import datetime
from retrieve import Retrieve
from time import sleep


backup=Retrieve("password")


scheduler_state = ""
# backup_state = ""
scheduler_state = backup.get_scheduler_state()


while scheduler_state != "off":

    # get the interval time to apply changes at each loop, if there's one.
    interval = int(backup.get_interval())

    # get the scheduler_state in state variable, to be check by the while loop
    scheduler_state = backup.get_scheduler_state()

    # if the backup_state is on, proceed to the backup of all devices, else do nothing
    if backup.get_backup_state() == "on":

        date_start = datetime.datetime.now()
        print("Backuping now at " + str(date_start))
        backup.backup_all_device()

        date_stop = datetime.datetime.now()
        print("End of the backup at "+ str(date_stop))

        next_date = date_stop + datetime.timedelta(0, int(interval))
        print("Next scheduled backup at " + str(next_date))

    else:
        print("Not backuping")

    sleep(interval)


print("End of the backup loop")
backup.mariadb_connection.close()
