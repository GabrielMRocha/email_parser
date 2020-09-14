#!/usr/bin/env python
# coding: utf-8


import re
import json
from bs4 import BeautifulSoup as BS
import os
import datetime

                    
#Functions for each airline. In real life they would be all stored separatedly in another file(s)       

def parser_latam(html_file):

    
    with open (html_file, encoding="UTF-8") as fp:
        soup = BS(fp, "lxml",from_encoding="UTF-8")
        
    res_number="" #there's no info about the reservation number in Latam emails
        
    # defines two important objects: the whole html file in str format, and a list with all <strong> tags, which cointain useful flight info
    soup_string = str(soup)
    info=soup.findAll("strong")

    # find the iata codes
    iataRegex = re.compile(r'(\s|>)([A-Z]{3})(\s|<)')

    iataCodes = [item[1] for item in iataRegex.findall(soup_string)]

    # find the airport/city names
    airports = [info[1].string.lstrip(), info[2].string.lstrip()]

#finds the dates and times of the flights

    # get the dates and removes the suffixes
    dateRegex = re.compile(r'([A-Z]{1}\w{2,8} \d\d)\w\w (\d{4})')
    dates = [" ".join(item) for item in dateRegex.findall(soup_string)]

    #gets the time of the flights
    timeRegex = re.compile(r'\d\d:\d\d')
    times = timeRegex.findall(soup_string)

    # puts date and time in one string
    if len(times) == 2: #when there's no arrival time
        completeTime = [" ".join(item) for item in list(zip(dates,times))]
    else:
        completeTime = [" ".join(item) for item in [(dates[0],times[0]),(dates[0],times[1]),(dates[1],times[2]),(dates[1],times[3])]]


    # creates the date time objects
    date_time_objs = [datetime.datetime.strptime(item, "%B %d %Y %H:%M") for item in completeTime]
    
    if len(date_time_objs) == 2: #when there's no arrival time
        date_time_objs.append("")
        date_time_objs.append("")
        date_time_objs[2] = date_time_objs[1]
        date_time_objs[1] = ""

    #check if arrival time is on the next day
    for index in range(len(date_time_objs)):
        try:
            if index%2==0 and date_time_objs[index] > date_time_objs[index +1]:
                date_time_objs[index+1] = date_time_objs[index+1]+ datetime.timedelta(days=1)
        except TypeError: #when there's no arrival time
            pass


    #find the flight codes

    flightCodeRegex = re.compile(r'[A-Z0-9]{5,6}')
    flightCodes=[]
    for item in info:
        try:
            code = flightCodeRegex.findall(item.string)
        except TypeError: # jumps the cases where there's styling within the tag, like the superscript '+1'

            pass
        if code:
            flightCodes.append(code[0]) 

    # creates the dictionaries to be returned by the function
    old_flight={"carrier": flightCodes[0][:2], "carrier_number": flightCodes[0][2:], "departure": {"airport":airports[0], "airport_iata": iataCodes[0], "datetime": date_time_objs[0]}, "arrival": {"airport":airports[1], "airport_iata": iataCodes[1], "datetime": date_time_objs[1]}}
    new_flight={"carrier": flightCodes[1][:2], "carrier_number": flightCodes[1][2:], "departure": {"airport":airports[0], "airport_iata": iataCodes[0], "datetime": date_time_objs[2]}, "arrival": {"airport":airports[1], "airport_iata": iataCodes[1], "datetime": date_time_objs[3]}}

    return  {"reservation_number":res_number, "old_flights": old_flight, "new_flights": new_flight}

    

def parser_norwegian(html_file):
    
    with open (html_file, encoding="UTF-8") as fp:
        soup = BS(fp, "lxml",from_encoding="UTF-8")

    #get reservation number
    res_number= soup.find("div", {"class": "next-trip-heading"}).contents[3].strip()[-6:]

    def flight_parser(new_old):

        #get the flights table
        flightsTable = soup.find("table", {"id": "{}_flight_details".format(new_old)}).findChildren("tr", recursive=False)[1:]

        #get all the span tags containning the flight info
        flightsSpan=[]
        for item in flightsTable:
             flightsSpan.append(item.findAll("span"))

        #creating a list with one dict for each flight
        flightLst=[]
        for flight in flightsSpan:
            dct = {"carrier": flight[6].getText()[:2], "carrier_number": flight[6].getText()[2:], "departure": {"airport":flight[2].getText(), "airport_iata": flight[3].getText().replace(u'\xa0', u'').replace('(','').replace(')',''), "datetime": datetime.datetime.strptime(flight[7].getText().strip().replace(u'\xa0', u''), "%d%b%Y%H:%M")}, "arrival": {"airport":flight[4].getText(), "airport_iata": flight[5].getText().replace(u'\xa0', u'').replace('(','').replace(')',''), "datetime": datetime.datetime.strptime(flight[8].getText().strip().replace(u'\xa0', u''), "%d%b%Y%H:%M")}}
            flightLst.append(dct)

        return flightLst

    #creating the objects with the old and the new flights
    old_flights = flight_parser("old")
    new_flights = flight_parser("new")

    return {"reservation_number":res_number, "old_flights": old_flights, "new_flights": new_flights}
                

#### end of functions


# runner to identify which airline is sending the email and call up its respective parser. In the task this is done via folder name, in real life would be done via email address from the sender.

path = "./data" #for windows, change the '/' to '\\'

#dict with airlines and its respective parsers. 
parser_dict = {"latam":parser_latam, "norwegian":parser_norwegian}

#Looping through the files and generating the .json outputs. 
for subdir, dirs, files in os.walk(path):
    for file in files:
        if file.lower().endswith(".html"):
            airline = subdir.rsplit("/")[-1] #for windows, change the '/' to '\\'
            if airline in parser_dict:
                output = parser_dict[airline](path+"/"+airline+"/"+file) #runs the parser for the file
                with open(path+"/"+airline+"/"+file[:-4]+"json", "w") as outfile: #creates the outputs in the same folder as the html files
                    json.dump(output, outfile, indent=4, sort_keys=False, ensure_ascii=False, default=str)





