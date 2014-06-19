#!/bin/bash
# http://wiki.nginx.org/InstallOptions
MY=nginx
curl http://nginx.org/download/nginx-1.5.13.tar.gz -o $MY.tar.gz
mkdir $MY && tar -zxvf $MY.tar.gz -C $MY --strip-components 1  
cd $MY
./configure \
--with-cc-opt="-Wno-deprecated-declarations" \
--with-http_ssl_module \
--prefix={{nginx_dir}}
make -j2

if [ "$(uname)" == "Darwin" ]; then
    make install
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    checkinstall --fstrans=no --default
fi

