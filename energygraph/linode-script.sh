#!/bin/bash


# <UDF name="notify_email" Label="Send email notification to" default="fluffy@iii.ca" example="Email address to send notification" />

# <UDF name="user_name" label="Unprivileged user account name" default="fluffy" example="This is the account that you will be using to log in." />
# <UDF name="user_password" label="Unprivileged user password" />
# <UDF name="user_sshkey" label="Public Key for user" default="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAIEArnAyN+d/Bsx89sV5Xgh5gsvlxIV/8q598s+sAuR5V7n56z56cKpLGdmPdsha1E6D0PEEY1DcVY0VqXa5bML++6+Glie9TAoBR3TLXSfea4gK3EFvwZI5purl+Kw3blFRLpr9p8k2w/Bv9ACYcaxj09Zio/XrX0yWGa44rbnhGd0= fluffy@dhcp-128-107-142-125.cisco.com"  />

# <UDF name="sys_hostname" label="System hostname" default="fluffyhome" example="Name of your server, i.e. linode1." />

#set -x
set -e
set -u

exec &> /root/stackscript.log

source <ssinclude StackScriptID="1"> # StackScript Bash Library
system_update

source <ssinclude StackScriptID="124"> # lib-system



# Configure system
source <ssinclude StackScriptID="123"> # lib-system-ubuntu
system_update_hostname "$SYS_HOSTNAME"


# Create user account
system_add_user "$USER_NAME" "$USER_PASSWORD" "sudo" "/bin/bash"
if [ "$USER_SSHKEY" ]; then
    system_user_add_ssh_key "$USER_NAME" \" "$USER_SSHKEY" \" 
fi



# Configure sshd
system_sshd_permitrootlogin "No"
system_sshd_passwordauthentication "Yes"
touch /tmp/restart-ssh



# Lock user account if not used for login
passwd -l root


# Install Postfix
postfix_install_loopback_only # SS1


# Setup logcheck
system_security_logcheck


# Setup fail2ban
system_security_fail2ban


# Setup firewall
system_security_ufw_configure_basic


source <ssinclude StackScriptID="126"> # lib-python
python_install


# lib-system - SS124
system_install_utils
system_install_build
system_install_git


# Install and configure apache and mod_wsgi
    source <ssinclude StackScriptID="122"> # lib-apache
    apache_worker_install
    apache_mod_wsgi_install
    apache_cleanup



# Install PostgreSQL and setup database
    source <ssinclude StackScriptID="125"> # lib-postgresql
    postgresql_install
    #postgresql_create_user "$POSTGRESQL_USER" "$POSTGRESQL_PASSWORD"



# Install MongoDB
    source <ssinclude StackScriptID="128"> # lib-mongodb
    mongodb_install


#install emacs 
apt-get -y install emacs23-nox 


restart_services
restart_initd_services



# Send info message
cat > ~/setup_message <<EOD
The Linode VPS configuration is completed.
EOD
mail -s "Your Linode VPS is ready" fluffy@iii.ca < ~/setup_message
