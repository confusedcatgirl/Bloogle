@echo off

python -m venv ../venv
call ../venv/Scripts/activate.bat
pip install -r ../requirements.txt

curl https://nginx.org/download/nginx-1.29.0.zip --output nginx.zip -C -
curl https://archive.mariadb.org//mariadb-11.8.2/winx64-packages/mariadb-11.8.2-winx64.zip --output mariadb.zip -C -
tar -xf nginx.zip
tar -xf mariadb.zip

rmdir /s /q ..\mariadb
rmdir /s /q ..\nginx
move mariadb-11.8.2-winx64 ..\mariadb
move nginx-1.29.0 ..\nginx