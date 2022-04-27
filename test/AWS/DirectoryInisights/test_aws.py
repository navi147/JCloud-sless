import os
import glob
import os.path
import gzip
import json
import subprocess
import urllib.request
import requests
import re
from re import search
from pathlib import Path


def run_subproc(cmd):
    sp = subprocess.run(['python3', cmd], stdout=subprocess.PIPE, text=True)
    return sp.stdout

def generate_data():
    # Add a system group
    url = "https://console.jumpcloud.com/api/v2/systemgroups"
    payload = {"name": "aws_di_app"}
    headers = {
        "x-api-key": os.environ['JC_API_KEY'],
        "content-type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    jr = json.loads(response.text)
    # Remove a system group
    url = "https://console.jumpcloud.com/api/v2/systemgroups/" + jr['id']
    response = requests.request("DELETE", url, headers=headers)
    # Add a system group
    url = "https://console.jumpcloud.com/api/v2/systemgroups"
    payload = {"name": "aws_di_app"}
    headers = {
        "x-api-key": os.environ['JC_API_KEY'],
        "content-type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    jr = json.loads(response.text)
    # Remove a system group
    url = "https://console.jumpcloud.com/api/v2/systemgroups/" + jr['id']
    response = requests.request("DELETE", url, headers=headers)

def test_script_produces_output_with_all_services():
    generate_data()
    pwd = os.path.dirname(os.path.realpath(__file__))

    print("running file...")
    print(pwd + "/temp_get-jcdirectoryinsights.py")
    # Set Variables:
    os.environ['incrementType'] = "day"
    os.environ['incrementAmount'] = "1"
    os.environ['service'] = 'all'
    os.environ['OrgId'] = '5ebeb8c7de6f1e713e19cfba'
    # End Variables
    run_subproc(pwd + "/temp_get-jcdirectoryinsights.py")
    files = glob.glob(pwd + "/jc_directoryinsights*.json.gz")
    for file in files:
        print("found File: " + file)
        assert os.path.exists(file)


def test_json_contents_for_all_services():
    pwd = os.path.dirname(os.path.realpath(__file__))
    files = glob.glob(pwd + "/jc_directoryinsights*.json.gz")
    with gzip.open(files[0], 'r') as f:
        data = f.read()
        j = json.loads (data.decode('utf-8'))
    # non empty json
    assert len(j) != 0
    # service can include all types
    for i in j:
        assert i['service'] == 'directory' or i['service'] == 'radius' or i['service'] == 'systems' or i['service'] == 'sso' or i['service'] == 'ldap' or i['service'] == 'mdm'
    j.sort(key = lambda x:x['timestamp'], reverse=True)
    # data should be sorted correctly
    assert j[0]['timestamp'] > j[len(j)-1]['timestamp']
    for file in files:
        # remove file for next test
        os.remove(file)

def test_json_again():
    os.environ['incrementType'] = "day"
    os.environ['incrementAmount'] = "1"
    os.environ['service'] = 'directory'
    os.environ['OrgId'] = '5ebeb8c7de6f1e713e19cfba'
    pwd = os.path.dirname(os.path.realpath(__file__))
    print("running file...")
    print(pwd + "/get-jcdirectoryinsights.py")
    run_subproc(pwd + "/temp_get-jcdirectoryinsights.py")
    files = glob.glob(pwd + "/jc_directoryinsights*.json.gz")
    with gzip.open(files[0], 'r') as f:
        data = f.read()
        j = json.loads (data.decode('utf-8'))
    for i in j:
        assert i['service'] == 'directory'
    for file in files:
        assert os.path.exists(file)
        # remove file for next test
        os.remove(file)

def test_changelog_version():
    pwd = os.path.dirname(os.path.realpath(__file__))
    path = Path(pwd)
    print(str(path.parent.parent.parent.absolute()) + '/AWS/DirectoryInsights/CHANGELOG.md')
    # get latest version from GitHub
    URL = "https://raw.githubusercontent.com/TheJumpCloud/JumpCloud-Serverless/master/AWS/DirectoryInsights/CHANGELOG.md"
    file = urllib.request.urlopen(URL)
    # get first version on changelog - this is the latest version
    for line in file:
        decoded_line = line.decode("utf-8")
        if decoded_line.startswith('##'):
            latestVersionText = decoded_line
            latestVersion = (latestVersionText[latestVersionText.find("[")+1:latestVersionText.find("]")])
            break
    # get the version from this branch
    with open(str(path.parent.parent.parent.absolute()) + '/AWS/DirectoryInsights/CHANGELOG.md') as f: 
        lines = f.readlines()
    for line in lines:
        # print(line)
        if line.startswith('##'):
            latestVersionBranchText = line
            latestVersionBranch = (latestVersionBranchText[latestVersionBranchText.find("[")+1:latestVersionBranchText.find("]")])
            break
    # get the user agent version from this branch:
    with open(str(path.parent.parent.parent.absolute()) + '/AWS/DirectoryInsights/get-jcdirectoryinsights.py') as u:
        scriptLines = u.readlines()
    for scriptLine in scriptLines:
        # print(scriptLine)
        if search('user-agent', scriptLine):
            useragent = scriptLine
            latestUserAgentFromBranch = re.search(r'DirectoryInsights/([\d.]+)', useragent).group(1)
            break
    print('latest version from GitHub: ' + latestVersion)
    print('latest version from this Branch: ' + latestVersionBranch)
    print('useragent version from this Branch: ' + latestUserAgentFromBranch)
    # Latest version should not be the same as the latest version from Branch
    assert latestVersion != latestVersionBranch
    # Latest version from branch should be updated in all places
    assert latestUserAgentFromBranch == latestVersionBranch