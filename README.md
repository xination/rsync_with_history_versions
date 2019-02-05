# rsync_with_history_versions
 
It is a rsync application to backup files and directories with the functionality to review/recover the modified or deleted files from the history.

# 1. How to backup
<pre>git clone https://github.com/xination/rsync_with_history_versions </pre>
 
Basically, I use a python script to control the flow and invoke subprocess to call bash commands.


to use this script you need:
+ Python 2.7 ( for python3, you can just change the print function )
+ docopt (https://github.com/docopt/docopt)
+ a backup_plan.txt (included in this repo )

to run backup simply, -r or --read means to read a backup plan:
<pre>./rsync_backup.py -r backup_plan.txt </pre>

the backup instructions are listed in backup_plan.txt (of course, you can freely name your backup plan file, ex my_plan.dat )
for example
<pre> 
do_local_backup: true
local_backup_folder: ./backup

do_remote_backup: true
remote_backup_folder: YourID@server:/home/youID/backup/
ssh_port: 21
# adding sources (use relative or abs path)
add_source: ../file1
add_source: /home/yourID/dir
# keep the versions from today    
keep_version: 60
</pre>

# 2. Preview/recover modified and deleted files

We use the interactive mode by (-i option):
<pre>/rsync_backup.py -ir backup_plan.txt</pre>
It will be a menu-driven fashion.
<img src="./doc/menu.png">


