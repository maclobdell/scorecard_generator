#!/usr/bin/env python
import argparse
import os.path
import subprocess
import datetime
from datetime import datetime
import sys
import json
from os.path import join, abspath, dirname
from json import load, dump
import re
import logging

parser = argparse.ArgumentParser(description='Generate Scorecards')
parser.add_argument("-d", "--dontrun", default=0, action='count', help="print commands, don't run them")  #just check if present
parser.add_argument("-f", "--folder", default="test_output", action='store', help="Folder to find test results")  #default is string

def main():
#  1. check that all three log files are present, if so, generate the scorecard_data
#        Read each test log file and add data to the scorecard
#  2.  validate scorecard and report any errors
    
    args = parser.parse_args()
    folder = args.folder

    #files are in folder structure /<test_output>/<mbed_version>/<platform>

    #change to the test results directory
    try:
        os.chdir(folder)
    except:
        print "expected test results folder does not exist"

    mo = datetime.now().month
    day = datetime.now().day
    hr = datetime.now().hour
    min = datetime.now().minute
    timestamp =  str(mo) + str(day) + str(hr) + str(min)
    print("TIMESTAMP : " + timestamp)

    log_file_path = "scg_log_" + timestamp + ".txt"
    logging.basicConfig(filename=log_file_path, level=logging.DEBUG)
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)     


    #identify sub directories that hold results for various mbed os versions
    for v in os.listdir("."):
        if os.path.isdir(v):    #a directory here must be the mbed-os version 
            mbed_ver = v
            print "mbed os ver:", v
            os.chdir(v)
                #identify sub directores that hold results for various platforms
            for t in os.listdir("."):   #a directory here must be a target
                if os.path.isdir(t):
                    target = t
                    print "target:", t
                    os.chdir(t)         #change to the directory
                        
                        #Check that at least one results file exists here, or maybe check that all necessary files exist?
                        # can we make a scorecard without full toolchain results?

                    if args.dontrun == 0:
                        generate_scorecard("./", target, mbed_ver, log)    
                    os.chdir("../")        

def generate_scorecard(folder_path, target, mbed_ver, log) :

    score_card_file = target + mbed_ver + "_scorecard.json"    #give it a name
    scorecard_data = {}
        
    scorecard_data["date"] = datetime.now().day
    scorecard_data["ver"] = mbed_ver

    gcc_arm_filecount = 0
    arm_filecount = 0
    iar_filecount = 0
    
    for file in os.listdir(folder_path):
        if file.startswith(target + "_gcc"):
            gcc_arm_filecount = gcc_arm_filecount + 1
        if file.startswith(target + "_arm"):
            arm_filecount = arm_filecount + 1
        if file.startswith(target + "iar"):                        
            iar_filecount = iar_filecount + 1

    if gcc_arm_filecount == 0:
        log.error("Test results file not found: " + mbed_ver + " " + target + " gcc_arm")
    if arm_filecount == 0:
        log.error("Test results file not found: " + mbed_ver + " " + target + " _arm")
    if iar_filecount == 0:
        log.error("Test results file not found: " + mbed_ver + " " + target + " _iar")                        
    if gcc_arm_filecount > 1:
        log.error("Too many test results files found: " + mbed_ver + " " + target + " gcc_arm")
    if arm_filecount > 1:
        log.error("Too many test results files found: " + mbed_ver + " " + target + " _arm")
    if iar_filecount > 1:
        log.error("Too many test results files found: " + mbed_ver + " " + target + " _iar")                        

    
#Get test data            
    for file in os.listdir(folder_path):
        if file.endswith("_results.json"):

            #TODO Need error condition checking such as missing input file, mismatch in target or toolchain, duplicate data, etc.    

            test_data_json_file = os.path.join(folder_path, file)    
             
            with open (test_data_json_file, "r") as f:
                test_data = json.loads(f.read()) 
                f.close()
            
                for target_toolchain in test_data:                
                    test_results = {}
                    platform, toolchain = target_toolchain.split("-")
                    #print platform,toolchain
                    scorecard_data["name"] = platform
                                    
                    target_test_data = test_data[target_toolchain]
                    for test_suite in target_test_data:
                        test_suite_data = target_test_data[test_suite]  
                        test_results[test_suite] =  test_suite_data.get("single_test_result", "none")
                        
            scorecard_data[toolchain] = test_results    
        
        if file.endswith("_target_data.json"): 
    
            target_data_json_file = os.path.join(folder_path, file)         
            
            with open (target_data_json_file, "r") as f:
                target_data = json.loads(f.read()) 
                f.close()

            scorecard_data["device_has"] = target_data["device_has"]


    test_dictionary = {"ethernet": [], "wifi": [" tests-network-wifi\n"], "rtc": [" tests-mbed_drivers-rtc\n", " tests-mbed_hal-rtc\n", " tests-mbed_hal-rtc_reset\n", " tests-mbed_hal-rtc_time\n", " tests-mbed_hal-rtc_time_conv\n"], "uart": [], "flash": [" features-tests-filesystem-flashsim_block_device\n", " tests-mbed_drivers-flashiap\n", " tests-mbed_hal-flash\n"], "rtos": [" tests-mbedmicro-rtos-mbed-basic\n", " tests-mbedmicro-rtos-mbed-circularbuffer\n",   "tests-mbedmicro-rtos-mbed-condition_variable\n", " tests-mbedmicro-rtos-mbed-event_flags\n", " tests-mbedmicro-rtos-mbed-heap_and_stack\n", " tests-mbedmicro-rtos-mbed-kernel_tick_count\n", " tests-mbedmicro-rtos-mbed-mail\n", " tests-mbedmicro-rtos-mbed-malloc\n", " tests-mbedmicro-rtos-mbed-memorypool\n", " tests-mbedmicro-rtos-mbed-mutex\n", " tests-mbedmicro-rtos-mbed-queue\n", " tests-mbedmicro-rtos-mbed-rtostimer\n", " tests-mbedmicro-rtos-mbed-semaphore\n", " tests-mbedmicro-rtos-mbed-signals\n", " tests-mbedmicro-rtos-mbed-systimer\n", " tests-mbedmicro-rtos-mbed-threads\n"], "6lowpan": [], "timer": [" tests-mbed_drivers-lp_timer\n", " tests-mbed_drivers-timer\n", " tests-mbed_drivers-timerevent\n", " tests-mbedmicro-rtos-mbed-rtostimer\n", " tests-mbedmicro-rtos-mbed-systimer\n"], "trng": [], "spi": [], "emac": [" tests-network-emac\n"], "sleep": [" tests-mbed_drivers-sleep_lock\n", " tests-mbed_hal-sleep\n", " tests-mbed_hal-sleep_manager\n", " tests-mbed_hal-sleep_manager_racecondition\n"], "cellular": [" features-cellular-tests-api-cellular_device\n", " features-cellular-tests-api-cellular_information\n", " features-cellular-tests-api-cellular_network\n", " features-cellular-tests-api-cellular_power\n", " features-cellular-tests-api-cellular_sim\n", " features-cellular-tests-socket-udp\n", " features-netsocket-cellular-generic_modem_driver-tests-unit_tests-default\n"], "digital": [], "ble": [" tests-mbedmicro-rtos-mbed-condition_variable\n"], "watchdog": [], "i2c": [], "ticker": [" tests-mbed_drivers-lp_ticker\n", " tests-mbed_drivers-ticker\n", " tests-mbed_hal-common_tickers\n", " tests-mbed_hal-common_tickers_freq\n", " tests-mbed_hal-lp_ticker\n", " tests-mbed_hal-ticker\n", " tests-mbed_hal-us_ticker\n"], "lorawan": [" tests-lorawan-loraradio\n"], "analog": []}

    requirement_results = {}
    for keyword in test_dictionary:  #keyword is like the requirement category
        for required_test in test_dictionary[keyword]:  #for each test that supports a category
            #print keyword + " " + tests
                #check the test results for the three compilers
    
    
            for toolchain in ["ARM", "GCC_ARM", "IAR"]:      
                test_results = scorecard_data[toolchain]
                for test_suite_name in test_results:  #get test name
                    test_suite_result = test_results[test_suite_name]  #get test result

                    if test_suite_name == required_test:
                        #check result
                        if test_suite_result == 'OK':              #add this result to the tally          
                            requirement_results[keyword] = 'OK'
                        else:
                            requirement_results[keyword] = 'FAIL'  
                        
    print requirement_results
    scorecard_data['Mbed_Enabled_Requirements'] = requirement_results

    #TODO - put all scorecard files in the same folder, not down in the numerous folders
        
    s = json.dumps(scorecard_data)    
    with open (folder_path + "//" + target + "_" + mbed_ver + "_scorecard.json", "w") as f:
        f.write(s)
        f.close()


if __name__ == '__main__':
    main()
