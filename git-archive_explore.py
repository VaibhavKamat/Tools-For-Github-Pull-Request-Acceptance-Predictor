# -*- coding: utf-8 -*-
"""
Created on Thu May 17 12:34:58 2018

@author: vaibhav_kamat
"""
import os
import requests
import pickle 
import urllib
from urllib import request
import json
import base64
import re
import time
import datetime

import numpy as np

USERNAME = ''
PASSWORD = ''
username = ''
password = ''




def set_proxy(username=username,password=password,port='8080',proxy_server='goa'):
    """set proxy settings"""
    os.environ['http_proxy'] = 'http://'+username+':'+password+'@'+proxy_server+'proxy.persistent.co.in:'+port
    os.environ['https_proxy'] = 'http://'+username+':'+password+'@'+proxy_server+'proxy.persistent.co.in:'+port
    os.environ['HTTP_PROXY'] = 'http://'+username+':'+password+'@'+proxy_server+'proxy.persistent.co.in:'+port
    os.environ['HTTPS_PROXY'] = 'http://'+username+':'+password+'@'+proxy_server+'proxy.persistent.co.in:'+port

def api_hit_authentication(request,username=USERNAME,password=PASSWORD):
    """Use authentication method for urllib.requests method"""
    base64string = ('%s:%s' % (username, password))
    encoded_base64string = base64.b64encode(base64string.encode('ascii'))
    request.add_header("Authorization", "Basic %s" % encoded_base64string.decode('ascii'))
    return request


def download_git_archive_resources(year='2018',month='01',day='01',upto_hour='12'):
    """Download git archive files on a specific day at a particular hour"""
    import subprocess
    for i in range(int(upto_hour)):
        file_name = year+'-'+month+'-'+day+'-'+str(i)+'.json.gz'
        subprocess.run("powershell Invoke-WebRequest {} -OutFile {}".format('http://data.gharchive.org/'+file_name,file_name), shell=True)

def remove_lines_from_files(line_number,file_name='2018-01-01-12.json'):
    """Remove lines which contain those apis which do not hit, and give error"""
    f = open(file_name,"r+")
    d = f.readlines()
    f.seek(0)
    for i in d:
        if i != line_number:
            f.write(i)
    f.truncate()
    f.close()

def generate_repo_list(file_name):
    """Generate repository list with repo api links, using a particular git archive file"""
    i=0
    repo_list = []
    data = open(file_name,encoding='UTF-8')
    for lines in data:
        repo_data = json.loads(lines)
        i+=1
        if (i>5000):
            break
        try:
            #req = requests.get(repo_data['repo']['url'],auth=(USERNAME,PASSWORD)).json()
            repo_list.append(repo_data['repo']['url'])
        except:
            print(repo_data['repo']['url']+" not reachable")
            continue
    return repo_list[91:92]


def get_watchers_count(repo_link):
    """Get watchers count for a particular repository"""
    try:
        data = requests.get(repo_link,auth=(USERNAME,PASSWORD)).json()
    except:
        return 0
    return data["watchers"]
 
def get_open_issues_count(repo_link):
    """Get open issues for a particular repository"""
    try:
        data = requests.get(repo_link,auth=(USERNAME,PASSWORD)).json()
    except:
        return 0
    return data['open_issues']
    
def get_forks_count(repo_link):   
    """Get forks count for a particular repository"""
    try:
        data = requests.get(repo_link,auth=(USERNAME,PASSWORD)).json()
    except:
        return 0
    return data['forks']

def get_number_of_commits_for_repo(repo_link):
    """Get number of commits for a particular repository"""
    try:
        data = requests.get(repo_link+'/commits',auth=(USERNAME,PASSWORD)).json()
    except:
        return 0
    return len(data)
    
def get_number_of_commits_for_pullrequest(repo_link,pull_request_number):
    """Get number of commits in a particular pull request of a repository"""
    pull_link = repo_link+'/pulls/'+str(pull_request_number)+'/commits'
    try:
        data = requests.get(pull_link,auth=(USERNAME,PASSWORD)).json()
    except:
        return 0    
    return len(data)

def pull_acceptance_probability(pulls_url):
    """Returns the pull request acceptance probability of a particular repository"""
    pulls_data = requests.get(url=pulls_url,auth=(USERNAME,PASSWORD)).json()
    pulls_closed = 0 
    total_merged = 0
    
    for i in range(len(pulls_data)):
        if(pulls_data[i]['state']=='closed'):
            pulls_closed+=1
        if(pulls_data[i]['merged_at']!=None):                
            total_merged+=1
    if(pulls_closed!=0):
        pulls_prob = total_merged/pulls_closed
        
    return pulls_prob

def generate_timedelta(repo_link):
    """Returns time between the last push in the repo and current time"""
    data = requests.get(repo_link,auth=(USERNAME,PASSWORD)).json()
    currenttime = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.localtime())
    a = datetime.datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
    b = datetime.datetime.strptime(currenttime, "%Y-%m-%dT%H:%M:%SZ")
    # Time in seconds since last push 
    seconds_last_push = (b-a).total_seconds()
    return seconds_last_push

def generate_repo_data(repo_link):
    """Generate repo data, which includes watchers, forks, open issues and commits for a particular repository"""
    repo_data = {}
    repo_data['watchers'] = get_watchers_count(repo_link)
    repo_data['open_issues'] = get_open_issues_count(repo_link)
    repo_data['forks'] = get_forks_count(repo_link)
    repo_data['commits'] = get_number_of_commits_for_repo(repo_link)
    repo_data['time_delta'] = generate_timedelta(repo_link)
    repo_data['pulls_prob'] = pull_acceptance_probability(repo_link+'/pulls?state=all')
    
    return repo_data

def diff_status(patch_url):
    PATCH_DATA = requests.get(url=patch_url,auth=(USERNAME,PASSWORD)).text.split("\n")
    DATA=[]
    if len(PATCH_DATA) is 1:
        DATA.append(0)
        DATA.append(0)
        DATA.append(0)
    else:    
        for k in range(len(PATCH_DATA)):
            reg_match=re.match(r'^[ ]*[0-9]* file*[a-z] change*[a-z]',PATCH_DATA[k])
           
            if reg_match:
                    need_line=PATCH_DATA[k].split(",")
                    no_of_file_changed=need_line[0]
                    DATA.append(int(no_of_file_changed[1]))
                    
                    if len(need_line) == 2:
                        if 'insertion' in need_line[1]:
                            no_of_line_change=need_line[1].strip().split(" ") #previously variable name is data5
                            no_of_insertion=no_of_line_change[0]
                            DATA.insert(1,int(no_of_insertion))
                            DATA.insert(2,0)
                        else:
                            no_of_line_change = need_line[1].strip().split(" ")
                            no_of_deletion=no_of_line_change[0]
                            DATA.insert(2,int(no_of_deletion))
                            DATA.insert(1,0)
                    elif len(need_line) == 3:
                        no_of_insertion_line=need_line[1].strip().split(" ")
                        no_of_insertion=no_of_insertion_line[0]
                        no_of_deletion_line=need_line[2].strip().split(" ")
                        no_of_deletion=no_of_deletion_line[0]
                        DATA.append(int(no_of_insertion))
                        DATA.append(int(no_of_deletion))
                    else:
                        DATA.insert(1,0)
                        DATA.insert(2,0)
                    break    
    return DATA

def get_pullrequest_data(repo_links):  
    """Get Pull request data in a Dictionary"""
    features_dict = {}
    i=0
    for repo_link in repo_links:
        try:
            i+=1
            print(i)
            repo_data = generate_repo_data(repo_link)
            pulls_data = requests.get(repo_link+'/pulls?state=all',auth=(USERNAME,PASSWORD)).json()
            
            for pull_request in pulls_data:
                features_dict[pull_request['id']] = {}
                features_dict[pull_request['id']]['watchers'] = repo_data['watchers']
                features_dict[pull_request['id']]['forks'] = repo_data['forks']
                features_dict[pull_request['id']]['open_issues'] = repo_data['open_issues']
                features_dict[pull_request['id']]['repo_commits'] = repo_data['commits']
                features_dict[pull_request['id']]['commits'] = get_number_of_commits_for_pullrequest(repo_link,pull_request['number'])
                
                features_dict[pull_request['id']]['time_delta'] = repo_data['time_delta']
                features_dict[pull_request['id']]['pulls_prob'] = repo_data['pulls_prob']
                
                features_dict[pull_request['id']]['repo_link'] = repo_link
                features_dict[pull_request['id']]['number'] = pull_request['number']
                features_dict[pull_request['id']]['files_changed'] = diff_status(pull_request['patch_url'])[0]
                features_dict[pull_request['id']]['insertions'] = diff_status(pull_request['patch_url'])[1]
                features_dict[pull_request['id']]['deletions'] = diff_status(pull_request['patch_url'])[2]
                
                print("pull request URL",pull_request['url'])
                features_dict[pull_request['id']]['status'] = get_label(pull_request['url'])
        except urllib.error.HTTPError:
            print("Repository "+repo_link+' Not Reachable')
            continue
    return features_dict

def generate_features(features_dict):
    """Generate feature in the form of numpy array. This function will take feature dictionary as an input"""
    features = []
    for key,values in features_dict.items():
        watchers = values['watchers']
        forks = values['forks']
        open_issues = values['open_issues']
        repo_commits = values['repo_commits']
        commits = values['commits']
        time_delta = values['time_delta']
        pulls_prob = values['pulls_prob']
        files_changed = values['files_changed']
        insertions = values['insertions']
        deletions = values['deletions']
        status = values['status']
        features.append([watchers,forks,open_issues,repo_commits,commits,time_delta,pulls_prob,files_changed,insertions,deletions,status])
    features = np.array(features)
    
    return features

def get_label(pull_url):
    """Get pull request status for a particular pull request"""
    label_url = pull_url+r"/merge"
    label_status = requests.get(url=label_url,auth=(USERNAME,PASSWORD))
    print(type(label_status),label_status)

    pulls_data = requests.get(url=pull_url,auth=(USERNAME,PASSWORD)).json()
    if label_status.status_code == 204:
        return 1
    if label_status.status_code == 404:
        if pulls_data['state'] == 'closed':
            return 0
        elif pulls_data['state'] == 'open':
            return 2
    else:
        return -1 
    
    
    
#E:\TExT\ML Git Usecase\gitarchive \D:\ML\TExT\ML Git Use Case\gitarchive\
#https://api.github.com/repos/bitpay/bitcore/pulls/1544/merge 
#https://api.github.com/repos/getify/You-Dont-Know-JS/pulls?page=1&per_page=100&state=all

set_proxy()
repo_list = generate_repo_list(r'D:\ML\TExT\ML Git Use Case\gitarchive\2018-01-01-12.json')
features_dict = get_pullrequest_data(['https://api.github.com/repos/bitpay/bitcore'])
print(features_dict)
'''
print(features_dict)

features = generate_features(features_dict)
print(features)

with open('feature_dict_91-100.json', 'a') as outfile:
   json.dump(features_dict, outfile)
   
features_dict = get_pullrequest_data(['https://api.github.com/repos/torvalds/linux'])
print(generate(features_dict))

#with open('features_0-100.pickle', 'a') as outfile:  
    #pickle.dumps(features,outfile)

print(diff_status("https://github.com/bitpay/bitcore/pull/1556.patch"))
'''