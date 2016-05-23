ftptool
==========

FTP wrapper implementing a slightly more usable API.

### Setup ###

This package was built using `setuptools` in Python > 3.4 and is not entirely backwards compatible with Python 2.7. Setup of the package for development or for production use is relatively straightforward.

Everything below is written for Ubuntu 14.04.

#### Python 3 ####

Get the latest version of Python 3 provided by Ubuntu 14.04.

```
# System dependencies
sudo apt-get install build-essential libssl-dev libffi-dev

# Get or update system provided Python 3
sudo apt-get update
sudo apt-get install python python-dev python3 python3-dev
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
rm get-pip.py

# Setup pip, virtualenv, and virtualenvwrapper
sudo pip install --upgrade pip
sudo pip install https://github.com/pypa/virtualenv/tarball/develop
sudo pip install virtualenvwrapper
echo -e "\n# virtualenv config\nexport WORKON_HOME=$HOME/.virtualenvs\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc

# Setup a new virtual environment for Python 3
mkvirtualenv -p python3 dev
deactivate
workon dev
```

#### Package ####

Clone the repository into a convenient directory.
```
git clone git@code.espn.com:ATG/ftpwrapper.git ftptool
cd ftptool
```

Setup and expose the package with `python setup.py develop`.

```
python setup.py develop
```

