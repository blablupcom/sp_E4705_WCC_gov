# -*- coding: utf-8 -*-

#### IMPORTS 1.0

import os, json
import re
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup


#### FUNCTIONS 1.2

import requests       # import requests to validate URL

def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9QY][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9QY][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    now = datetime.now()
    year, month = date[:4], date[5:7]
    validYear = (2000 <= int(year) <= now.year)
    if 'Q' in date:
        validMonth = (month in ['Q0', 'Q1', 'Q2', 'Q3', 'Q4'])
    elif 'Y' in date:
        validMonth = (month in ['Y1'])
    else:
        try:
            validMonth = datetime.strptime(date, "%Y_%m") < now
        except:
            return False
    if all([validName, validYear, validMonth]):
        return True


def validateURL(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=20)
        count = 1
        while r.status_code == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = requests.get(url, allow_redirects=True, timeout=20)
        sourceFilename = r.headers.get('Content-Disposition')
        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        elif r.headers['Content-Type'] == 'text/csv':
            ext = '.csv'
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.status_code == 200
        validFiletype = ext.lower() in ['.csv', '.xls', '.xlsx']
        return validURL, validFiletype
    except:
        print ("Error validating URL.")
        return False, False


def validate(filename, file_url):
    validFilename = validateFilename(filename)
    validURL, validFiletype = validateURL(file_url)
    if not validFilename:
        print filename, "*Error: Invalid filename*"
        print file_url
        return False
    if not validURL:
        print filename, "*Error: Invalid URL*"
        print file_url
        return False
    if not validFiletype:
        print filename, "*Error: Invalid filetype*"
        print file_url
        return False
    return True


def convert_mth_strings ( mth_string ):
    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    for k, v in month_numbers.items():
        mth_string = mth_string.replace(k, v)
    return mth_string


#### VARIABLES 1.0

entity_id = "E4705_WCC_gov"
url = "https://datamillnorth.org/dataset/wakefield-council-spend-over-500-pounds"
errors = 0
data = []

#### READ HTML 1.0

html = requests.get(url)
soup = BeautifulSoup(html.text, "lxml")

#### SCRAPE DATA
files_dics = json.loads(html.text.split('__INITIAL_STATE__=')[-1].split('}</script>')[0]+'}')['dataset']['resources']
for files_dic in files_dics.items():
    if '.csv' in files_dic[1]['url'] or '.xls' in files_dic[1]['url']:
        csvfile = files_dic[1]['url']
        link_text = csvfile.split('/')[-1]
        if 'q1' in csvfile or 'Q1' in csvfile:
            csvMth = 'Q1'
            s_year = re.search('(\d{4})', link_text)
            if s_year:
                csvYr = s_year.groups()[0]
        if 'q2' in csvfile or 'Q2' in csvfile:
            csvMth = 'Q2'
            s_year = re.search('(\d{4})', link_text)
            if s_year:
                csvYr = s_year.groups()[0]
        if 'q3' in csvfile or 'Q3' in csvfile:
            csvMth = 'Q3'
            s_year = re.search('(\d{4})', link_text)
            if s_year:
                csvYr = s_year.groups()[0]
        if 'q4' in csvfile or 'Q4' in csvfile:
            csvMth = 'Q4'
            s_year = re.search('(\d{4})', link_text)
            if s_year:
                csvYr = s_year.groups()[0]
        if '3500' in csvYr:
            csvYr = files_dic[1]['url'].split('-')[-2][-4:]
        csvMth = convert_mth_strings(csvMth.upper())
        todays_date = str(datetime.now())
        data.append([csvYr, csvMth, csvfile])

#### STORE DATA 1.0

for row in data:
    csvYr, csvMth, url = row
    filename = entity_id + "_" + csvYr + "_" + csvMth
    todays_date = str(datetime.now())
    file_url = url.strip()

    valid = validate(filename, file_url)

    if valid == True:
        scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
        print filename
    else:
        errors += 1

if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)

#### EOF

