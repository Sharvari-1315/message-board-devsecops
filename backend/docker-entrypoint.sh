/usr/bin/wait-for-it.sh db:5432 --timeout=60 --strict -- echo "Database is up and running"

python -c "from app import init_db; init_db()"

exec gunicorn -w 4 -b 0.0.0.0:5000 app:app