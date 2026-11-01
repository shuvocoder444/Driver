import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('195.250.26.201', username='webkoders', key_filename=r'C:\Users\shuvo\.ssh\id_rsa')
sftp = ssh.open_sftp()

files_to_upload = [
    'templates/dashboard/base_dashboard.html',
    'apps/site_settings/context_processors.py',
    'apps/dashboard/views.py',
    'apps/accounts/views.py',
    'apps/accounts/urls.py',
    'templates/users/list.html',
    'apps/site_settings/views.py',
    'apps/billing/views.py',
]

print("Uploading updated files to remote server...")
for rel in files_to_upload:
    local_p = f'D:\\new\\{rel.replace("/", "\\")}'
    remote_p = f'/home/webkoders/rus.velohoster.com/{rel}'
    sftp.put(local_p, remote_p)
    print(f" -> Uploaded {rel}")

sftp.close()

print("Purging cache and restarting LiteSpeed WSGI...")
ssh.exec_command('pkill -9 -f "rus.velohoster.com/passenger_wsgi.py"')
ssh.exec_command('find /home/webkoders/rus.velohoster.com -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null')
ssh.exec_command('touch /home/webkoders/rus.velohoster.com/tmp/restart.txt')

ssh.close()
print("All files deployed and server restarted!")

