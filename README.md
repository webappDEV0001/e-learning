# 4actuaries

E-learning application


## Prerequisities

In order to run this containers you'll need docker and docker-compose installed.

* [Install Docker](https://docs.docker.com/install)
* [Install Docker-compose](https://docs.docker.com/compose/install/)
* [Install wkhtmltopdf](https://pypi.org/project/pdfkit/)


## Getting Started

#### Clone and enter git repository
```shell
$ git clone https://git.krypta.it/owner/4actuaries && cd 4actuaries
```

#### Create .env file from template

```shell
$ cp .env.example .env
```

#### Run docker-compose up

```shell
$ docker-compose -f utils/docker/docker-compose.yml up --build
```

After couple of minutes app should start and you will have access to http://localhost:8000/


#### (Optionally) You can create superuser (admin)

```shell
$ docker-compose exec web python manage.py createsuperuser
```

