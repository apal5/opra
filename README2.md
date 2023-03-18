### Steps to set-up
1. Git clone this repository
2. copied [OPRA Dependencies](https://github.com/tomjmwang/opra_dependencies/tree/master/python_packages) to local machine's python libraries
Note: Has to use sudo privilege to perform the change
```
sudo cp -R prefpy/ /usr/lib/python3/dist-packages/
sudo cp -R django_mobile/ /usr/lib/python3/dist-packages/
```

Conda Environment
Exporting
```
conda env export > environment.yml
```

Importing
```
conda env create -f environment.yml
```

Installing dependencies
```
pip3 install django==2.2
pip3 install django-mathfilters
pip3 install django-cors-headers
pip3 install django-qr-code
pip3 install django-mobile
pip3 install prefpy
pip install whitenoise==4.1.2