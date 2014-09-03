if [ ! -d "log" ]; then
    mkdir log
fi
uwsgi --ini uwsgi.ini
