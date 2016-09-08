#!/bin/bash 

function run {
	hostname > .hpcservicehost
	rm -f couchdb.std*
	couchdb -b >/dev/null 
}


if [ ! -f .hpcservicehost ]; then
	run 
fi
couchhost=$(cat .hpcservicehost)
error=$(curl -Ss http://$couchhost:5984  2>&1 >/dev/null)
if [ -n "$error" ]; then
	run
fi
cat .hpcservicehost

