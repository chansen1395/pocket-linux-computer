@echo off
title Pocket - step 2: flash
echo Pocket step 2: flashing the card (an administrator prompt will appear).
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','%~dp0flash.ps1'"
