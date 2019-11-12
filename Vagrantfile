# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # From https://gist.github.com/millisami/3798773
  def local_cache(box_name)
    cache_dir = File.join(File.expand_path('~/.vagrant.d'), 'cache', 'apt', box_name)
    partial_dir = File.join(cache_dir, 'partial')
    FileUtils.mkdir_p(partial_dir) unless File.exists? partial_dir
    cache_dir
  end


  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "generic/debian9"
  cache_dir = local_cache(config.vm.box)
  config.vm.synced_folder cache_dir, "/var/cache/apt/archives/"

  # accessing "localhost:31337" will access port 3133 on the guest machine.
  config.vm.network :forwarded_port, guest: 8989, host: 8989

  # If true, then any SSH connections made will enable agent forwarding.
  # Default value: false
  config.ssh.forward_agent = true

$rootScript = <<SCRIPT
  set -x
  apt-get update -y
  apt-get install git vim screen -y
  apt-get install python3-pip python3-dev virtualenv -y
  apt-get install postgresql postgresql-server-dev-all python-psycopg2 -y
  apt-get install libffi-dev libghc-cairo-dev libghc-pango-dev libxml2-dev libxslt1-dev libjpeg62-turbo-dev -y
  apt-get autoremove -y
  apt-get clean

  sudo -u postgres createuser --createdb --no-superuser --no-createrole nadine
  sudo -u postgres createdb --owner=nadine nadinedb
  sudo -u postgres psql -d postgres -c "ALTER USER nadine WITH PASSWORD 'password'"
  sed -i.bak 's/peer$/trust/' /etc/postgresql/9.6/main/pg_hba.conf
  service postgresql restart

  if [ -f /etc/init.d/nginx ]; then
    apt-get remove nginx
    killall nginx
  fi

SCRIPT

$userScript = <<SCRIPT
  if [ ! -f webapp ]; then
    virtualenv -p /usr/bin/python3 webapp
    cd webapp
    source bin/activate
    pip install pip --upgrade
    git clone https://github.com/nadineproject/nadine.git
    cd nadine
    pip install -r requirements.txt

    #SECURE_RANDOM=$(dd if=/dev/urandom count=1 bs=28 2>/dev/null | od -t x1 -A n)
    #SECRET_KEY="${SECURE_RANDOM//[[:space:]]/}"
    #sed "s/^SECRET_KEY.*$/SECRET_KEY = '$SECRET_KEY'/" nadine/settings/local_settings.example >> nadine/local_settings.py

    cd nadine
    ./manage.py migrate
    ./manage.py create_admin
  fi

  cd /home/vagrant/webapp
  source bin/activate
  cd nadine
  screen -dmS django ./manage.py runserver 0.0.0.0:8989
SCRIPT


  config.vm.provision "shell",
    privileged: true,
    inline: $rootScript

  config.vm.provision "shell",
    privileged: false,
    inline: $userScript

end
