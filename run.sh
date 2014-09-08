if [ ! -d "log" ]; then
    mkdir log
fi
killall -s INT uwsgi
uwsgi --ini uwsgi.ini
