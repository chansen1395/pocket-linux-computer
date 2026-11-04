@echo off
title Pocket - step 1: USB mode
echo Pocket step 1: waiting for the Pi 5 in USB mode.
echo.
echo   Pi fully unplugged  ^>  HOLD power button  ^>  plug USB-C into a REAR PC port  ^>  release after 1 s
echo.
cd /d "C:\Program Files (x86)\Raspberry Pi"
rpiboot.exe -d mass-storage-gadget64
echo.
echo If you saw "Second stage boot server done", the card is now a USB disk on this PC.
echo Cancel any "format disk" popup, then run 2-flash.cmd. Keep this window open.
pause
