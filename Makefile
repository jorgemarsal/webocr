MYSQL_HOSTNAME=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_ROOT_PASSWORD=123
MYSQL_DBNAME=webocr
MYSQL_DATADIR=/var/lib/mysql/webocr
MYSQL_DOCKER_VERSION=mysql:latest
MYSQL_DOCKER_NAME=mysql
MYSQL_INIT_FILE=sql/webocr.sql

#
# DB
#

mysql:
	sudo mkdir -p $(MYSQL_DATADIR)
	sudo docker run --name $(MYSQL_DOCKER_NAME) -e MYSQL_ROOT_PASSWORD=$(MYSQL_ROOT_PASSWORD) \
            -v $(MYSQL_DATADIR):/var/lib/mysql --net=host -d $(MYSQL_DOCKER_VERSION)
init-mysql:
	        mysql -h $(MYSQL_HOSTNAME) -u $(MYSQL_USER) -P$(MYSQL_PORT) -p$(MYSQL_ROOT_PASSWORD) < $(MYSQL_INIT_FILE)
connect-mysql:
	mysql -h $(MYSQL_HOSTNAME) -u $(MYSQL_USER) -P$(MYSQL_PORT) -p$(MYSQL_ROOT_PASSWORD) -D$(MYSQL_DBNAME)
delete-mysql:
	sudo docker rm -f $(MYSQL_DOCKER_NAME) 
logs-mysql:
	sudo docker logs -f $(MYSQL_DOCKER_NAME) 

#
# Docker
#

IMAGE := jorgemarsal/webocr_worker:0.0.1
DOCKER_REPO := 172.17.0.1:5000/

build:
	cp webocr/webocr/tasks.py .
	docker build  -t $(DOCKER_REPO)$(IMAGE) .

push:
	docker push $(DOCKER_REPO)$(IMAGE)

worker:
	docker run --name=worker -d --net=host $(DOCKER_REPO)$(IMAGE)
worker-i:
	
	docker run -it --net=host $(DOCKER_REPO)$(IMAGE) /bin/bash

task-server:
	cd webocr; python -m tcelery --port=8888 --app=webocr.tasks --address=0.0.0 > /tmp/taskserver.log 2>&1 &
