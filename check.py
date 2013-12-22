#!/usr/bin/env python
# 
# Check new-innov.com evals
# Vivek Sant <vsant@hcs.harvard.edu>
# 2013-06-30
# 

import os
import re
import difflib
import smtplib
import urllib, urllib2, cookielib

from settings import *

fn  = os.path.dirname(os.path.realpath(__file__)) + '/num.txt'
fn_evals = os.path.dirname(os.path.realpath(__file__)) + '/evals.html'
total_num = 0
grades_arr = ["Fail", "Low Pass", "Pass", "High Pass", "Honors", "Unknown"]


def mail(fr, to, msg, serverURL='', un='', pw=''):
  s = smtplib.SMTP(serverURL)
  if un != '' and pw != '':
    s.starttls()
    s.login(un, pw)
  s.sendmail(fr, to, msg)
  s.quit()

def email(data):
  if DRY_RUN:
    print "DRY RUN: ", data
    return
  for i in TO:
    mail(FR, i, MSG % { 'fr':FR, 'to':i, 'msg':data}, MAIL_SERVER, MAIL_UN, MAIL_PW)

def extract_grade(resp2):
  grade = 5
  if 'bold">honors' in resp2.lower():
    grade = 4
  elif 'bold">high pass' in resp2.lower():
    grade = 3
  elif 'bold">pass' in resp2.lower():
    grade = 2
  elif 'bold">low pass' in resp2.lower():
    grade = 1
  elif 'bold">fail' in resp2.lower():
    grade = 0
  return grades_arr[grade]

def main(args):
  try:
    page_data = urllib2.urlopen(url_login).read()
  except:
    return -1
  m = re.search('id="__EVENTVALIDATION" value="(.*?)" />', page_data)
  if m:
    event_val = m.group(1)
  m = re.search('id="__VIEWSTATE" value="(.*?)" />', page_data)
  if m:
    view_state = m.group(1)

  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  login_data = urllib.urlencode({
    '__EVENTTARGET'     : '',
    '__EVENTARGUMENT'   : '',
    '__VIEWSTATE'       : view_state,
    '__EVENTVALIDATION' : event_val,
    'txtClientName'     : inst,
    'txtClientName_ClientState' : '{"enabled":true,"emptyMessage":"Institution","validationText":"' + inst + '","valueAsString":"' + inst + '"}',
    'txtUsername'       : un,
    'txtUsername_ClientState' : '{"enabled":true,"emptyMessage":"Username","validationText":"' + un + '","valueAsString":"' + un + '"}',
    'txtPassword'       : pw,
    'btnLoginNew'       : 'Log In',
    'btnLogin_ClientState' : '',
    'btnCancel_ClientState' : '',
    'scrWidth' : '1920',
    'scrHeight' : '1080'
  })
  opener.open(url_login, login_data)
  resp = opener.open(url_evals).read()
  resp = resp.replace('datagridalternatingitemstyle', 'X')
  resp = resp.replace('datagriditemstyle', 'X')
  resp = resp.replace('<font color="red">Q</font>', '')
  resp = re.sub('<input id=".*?" type="checkbox" name=".*?"', '<input id="" type="checkbox" name=""', resp)

  m = re.findall('<div class="subtextblue">Count: (.*?)</div>', resp)
  if m:
    total_num = str(reduce(lambda x,y:int(x)+int(y), m))
  else:
    return -1

  if os.path.exists(fn):
    f = open(fn, "r+")
    cache = f.read().strip()
    # Check if dl == cache, if not, save new version and email alert
    if cache != total_num:
      f.close()
      if not DRY_RUN:
        f = open(fn, "w+")
        f.write(total_num)
      #email(str(cache)+"->"+str(total_num))
      # Diff the evals page, analyze each new eval
      if os.path.exists(fn_evals):
        f2 = open(fn_evals, "r+")
        f2_data = f2.read().strip()
        f2_data = f2_data.replace('datagridalternatingitemstyle', 'X')
        f2_data = f2_data.replace('datagriditemstyle', 'X')
        f2_data = f2_data.replace('<font color="red">Q</font>', '')
        f2_data = re.sub('<input id=".*?" type="checkbox" name=".*?"', '<input id="" type="checkbox" name=""', f2_data)
        if f2_data != resp:
          f2.close()
          if not DRY_RUN:
            f2 = open(fn_evals, "w+")
            f2.write(resp)

          diff = difflib.ndiff(f2_data.splitlines(), resp.splitlines())
          adds = filter(lambda x: x[0] == '+', list(diff))
          adds_view = filter(lambda x:'>View</a>' in x, adds)
          adds_check = filter(lambda x:'checkbox' in x, adds)

          adds_check_parsed = []
          for i in adds_check:
            m = re.search('type="checkbox" name="(.*?)".*?</td><td></td><td>.*?</td><td>.*?</td><td>.*?\((\D*?)\)</td>', i)
            if m:
              adds_check_parsed.append((m.group(1), m.group(2)))

          adds_view_parsed = []
          for i in adds_view:
            m = re.search('__doPostBack\(&#39;(.*?)&#39;.*?</td><td>.*?</td><td>.*</td><td>.*?</td><td>.*?\((\D*?)\)</td>', i)
            if m:
              adds_view_parsed.append((m.group(1), m.group(2)))
          # Iterate thru adds_check_parsed and adds_view_parsed, analyzing each new eval
          m = re.search('id="__EVENTVALIDATION" value="(.*?)" />', resp)
          if m:
            event_val = m.group(1)
          m = re.search('id="__VIEWSTATE" value="(.*?)" />', resp)
          if m:
            view_state = m.group(1)
          m = re.search("hf.value += '(.*?)';", resp)
          if m:
            rsm1 = m.group(1)
          for i in adds_view_parsed:
            post_data = urllib.urlencode({
              'RSM1_TSSM'         : rsm1,
              'RadScriptManager1_TSM' : '',
              '__EVENTTARGET'     : i[0],
              '__EVENTARGUMENT'   : '',
              '__LASTFOCUS'       : '',
              '__VIEWSTATE'       : view_state,
              '__EVENTVALIDATION' : event_val,
              'ctl03$ddlClassDefinitions' : '16',
              'ctl02_ScrollX' : '0',
              'ctl02_ScrollY' : '0'
            })
            resp2 = opener.open(url_evals, post_data).read()
            email(i[1] + ": " + extract_grade(resp2))
          for i in adds_check_parsed:
            post_data = urllib.urlencode({
              'RSM1_TSSM'         : rsm1,
              'RadScriptManager1_TSM' : '',
              '__EVENTTARGET'     : 'ctl03$lnkPrintEvaluations2$DisabledLinkButton1',
              '__EVENTARGUMENT'   : '',
              '__LASTFOCUS'       : '',
              '__VIEWSTATE'       : view_state,
              '__EVENTVALIDATION' : event_val,
              'ctl03$ddlClassDefinitions' : '16',
              'ctl02_ScrollX' : '0',
              'ctl02_ScrollY' : '0',
              i[0]            : 'on'
            })
            resp2 = opener.open(url_evals, post_data).read()
            if extract_grade(resp2) != "Unknown":
              email(i[1] + ": " + extract_grade(resp2))
      else:
        f2 = open(fn_evals, "w+")
        f2.write(resp)
  elif not DRY_RUN:
    f = open(fn, "w+")
    f.write(total_num)
    if not os.path.exists(fn_evals):
      f2 = open(fn_evals, "w+")
      f2.write(resp)
  # Access this URL to 'show' that the script has been run
  try:
    if URL_MONITORING and not DRY_RUN:
      urllib2.urlopen(URL_MONITORING).read()
  except:
    pass
  return 0

if __name__ == "__main__":
  import sys 
  sys.exit(main(sys.argv))
