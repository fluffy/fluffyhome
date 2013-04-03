
Get ssh going 

change password 

Set up NTP 
set the timezone to be correct (copy right timezone file)

install emacs
install git 

clone the fluffyhome git repo 
copy espresso.py to home 

Set up a crontab for root with 

sudo crontab -e 

to look like


30  6  *   *   *     /home/pi/espresso.py --on 
30  16 *   *   *     /home/pi/espresso.py --off
36  19 *   *   *     /home/pi/espresso.py --off
