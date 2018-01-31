
clear the cache

find . -name __pycache__ -type d |xargs rm {} \;

# make migrations

python manage.py makemigrations --emtpy autocd
python manage.py makemigrations --emtpy accounts

python manage.py makemigrations
python manage.py migrate

