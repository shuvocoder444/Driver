import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('195.250.26.201', username='webkoders', key_filename=r'C:\Users\shuvo\.ssh\id_rsa')
sftp = ssh.open_sftp()

print("Uploading updated translations.py...")
sftp.put(r'D:\new\apps\site_settings\translations.py', '/home/webkoders/rus.velohoster.com/apps/site_settings/translations.py')
sftp.close()

print("Restarting WSGI on server...")
ssh.exec_command('pkill -9 -f "rus.velohoster.com/passenger_wsgi.py"')
ssh.exec_command('find /home/webkoders/rus.velohoster.com -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null')
ssh.exec_command('touch /home/webkoders/rus.velohoster.com/tmp/restart.txt')

ssh.close()
print("Deployment and LiteSpeed restart complete!")

