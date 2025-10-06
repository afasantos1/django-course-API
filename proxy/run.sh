#!/bin/sh

set -e

envsubst < /etc/nginx/default.conf.tpl > /tmp/default.conf
nginx -c /tmp/default.conf -g 'daemon off;'