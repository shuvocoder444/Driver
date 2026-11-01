import hashlib
import os

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('195.250.26.201', username='webkoders', key_filename=r'C:\Users\shuvo\.ssh\id_rsa')
sftp = ssh.open_sftp()

def get_local_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

files_to_check = [
    'templates/dashboard/base_dashboard.html',
    'templates/dashboard/admin.html',
    'templates/dashboard/superadmin.html',
    'templates/dashboard/driver.html',
    'templates/landing/base_frontend.html',
    'templates/billing/purchase.html',
    'apps/dashboard/views.py',
    'apps/accounts/views.py',
    'apps/site_settings/context_processors.py',
    'apps/site_settings/translations.py',
]

print("Comparing files with remote server...")
for rel in files_to_check:
    local_p = os.path.join(r'D:\new', rel.replace('/', os.sep))
    remote_p = f'/home/webkoders/rus.velohoster.com/{rel}'
    local_md5 = get_local_md5(local_p)
    try:
        remote_data = sftp.file(remote_p, 'rb').read()
        remote_md5 = hashlib.md5(remote_data).hexdigest()
        if local_md5 == remote_md5:
            print(f" MATCH: {rel}")
        else:
            print(f"❌ MISMATCH: {rel} (Local: {local_md5[:8]}, Remote: {remote_md5[:8]})")
    except Exception as e:
        print(f"⚠️ REMOTE ERROR for {rel}: {e}")

sftp.close()
ssh.close()
