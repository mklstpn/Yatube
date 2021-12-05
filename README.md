# Yatube

## Описание

#### Yatube  - учебный проект социальной сети с подписками, комментариями и постами. 

## Как запустить проект:

Создать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source env/Scripts/activate
```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

#### Адрес сервера

http://127.0.0.1:8000/
