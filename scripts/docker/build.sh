#!/usr/bin/env bash
set -x
echo "please use: sh build.sh d 1.0.0 or sh build.sh p 1.0.1"

APP_NAME=app
BASE_URL=openanolis-registry.cn-zhangjiakou.cr.aliyuncs.com
SPACE=augur
NAME=augur

if [ $1 == d ]
then
  env=daily
  tag=${env}-v$2
fi
if [ $1 == p ]
then
  env=prod
  tag=v$2
fi

if [ -z ${env} ] or [ -z ${tag} ]
then
    echo "env or tag is empty, please use like sh build.sh d 1.0.0 or sh build.sh p 1.0.1"
    exit 1
fi

echo ${BASE_URL}/${SPACE}/${NAME}:${tag}

sudo docker build -t augur-docker -f docker/backend/Dockerfile .
# sudo docker push ${BASE_URL}/${SPACE}/${NAME}:${tag}

sudo docker rm $(docker ps -a -q --filter status='exited')
sudo docker rmi $(docker images -q --filter dangling=true)