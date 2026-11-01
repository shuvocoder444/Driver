import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('195.250.26.201', username='webkoders', key_filename=r'C:\Users\shuvo\.ssh\id_rsa')
cmd = '/home/webkoders/virtualenv/rus.velohoster.com/3.12/bin/python /home/webkoders/rus.velohoster.com/manage.py shell -c "from apps.accounts.models import CustomUser; u = CustomUser.objects.get(email=\'admin@topd.kg\'); print(\'role:\', u.role, \'is_superuser:\', u.is_superuser, \'is_staff:\', u.is_staff, \'is_superadmin:\', u.is_superadmin)"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
ssh.close()
