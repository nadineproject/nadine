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
  config.vm.box = "trusty32"

  # custom baked ubuntu vm that hass updates applied and packages applied
  config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-i386-vagrant-disk1.box"

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
  apt-get install git vim tmux -y
  apt-get install python-dev python-pip python-software-properties -y
  apt-get install libffi-dev libxml2-dev libxslt1-dev libjpeg8-dev -y
  apt-get install python-psycopg2 libpq-dev postgresql -y
  apt-get autoremove -y
  apt-get clean

  sudo -u postgres createuser --createdb --no-superuser --no-createrole nadine
  sudo -u postgres createdb --owner=nadine nadinedb
  sudo -u postgres psql -d postgres -c "ALTER USER nadine WITH PASSWORD 'password'"
  sed -i.bak 's/peer$/trust/' /etc/postgresql/9.3/main/pg_hba.conf
  service postgresql restart

  if [ -f /etc/init.d/nginx ]; then
    apt-get remove nginx
    killall nginx
  fi

  pip install pip --upgrade
  pip install virtualenv
  pip install virtualenvwrapper
SCRIPT

$userScript = <<SCRIPT
  git config --global url."https://".insteadOf git://

  echo export WORKON_HOME="/home/vagrant/envs" >> /home/vagrant/.bashrc
  export WORKON_HOME="/home/vagrant/envs"
  echo source /usr/local/bin/virtualenvwrapper.sh >> /home/vagrant/.bashrc
  source /usr/local/bin/virtualenvwrapper.sh
  cd /vagrant

  mkvirtualenv nadine
  yes | pip install -r requirements.txt

  if [ ! -f nadine/local_settings.py ]; then
  	SECURE_RANDOM=$(dd if=/dev/urandom count=1 bs=28 2>/dev/null | od -t x1 -A n)
  	SECRET_KEY="${SECURE_RANDOM//[[:space:]]/}"
  	sed "s/^SECRET_KEY.*$/SECRET_KEY = '$SECRET_KEY'/" nadine/local_settings.example > nadine/local_settings.py
    #sed -i.bak "s/'postgres'/'modernomad'/" modernomad/local_settings.py
  fi

  echo workon nadine >> /home/vagrant/.bashrc
  workon nadine
  ./manage.py migrate
  ./manage.py create_admin
  tmux -c ./manage.py runserver 0.0.0.0:8989
SCRIPT


  config.vm.provision "shell",
    privileged: true,
    inline: $rootScript

  config.vm.provision "shell",
    privileged: false,
    inline: $userScript

end
