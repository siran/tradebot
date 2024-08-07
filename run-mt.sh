#!/bin/bash

DATE=$(date +%Y%m%d)

echo "starting shell loop..."
while python morning_trader.py | tee -a "mt-${DATE}.log"; do
	echo "loop exited"
	# if [ "$?" -eq 0 ]; then
	# 	exit 0
	# fi
	echo "exit_code = $?, restarting in 5..."
	sleep 5
done
