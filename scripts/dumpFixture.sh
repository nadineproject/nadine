#!/bin/bash
export PYTHONPATH=.
echo ""
echo "THIS DUMPS ALL THE USER DATA (INCLUDING USERNAMES AND PASSWORDS) INTO A FIXTURE WHICH IS PART OF THE CHECKED IN CODE."
echo ""
echo "RUN THE PSEUDONOMIZER FIRST!"
echo ""
./manage.py dumpdata auth.User auth.Group --indent 1 > staff/fixtures/base.json
./manage.py dumpdata staff.Member staff.HowHeard staff.Industry staff.Neighborhood staff.DailyLog staff.Membership --indent 1 > staff/fixtures/staff.json
