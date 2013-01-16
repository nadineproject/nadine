#!/bin/bash

celery inspect active -q > /dev/null 2> /dev/null
if [ $? -ne 0 ] ; then
        echo "Celery Not Running!" | mail jacob@officenomads.com -s "Celery Error"
fi
