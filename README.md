[![Logo](https://whitesource-resources.s3.amazonaws.com/ws-sig-images/Whitesource_Logo_178x44.png)](https://www.whitesourcesoftware.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellowgreen.svg)](https://opensource.org/licenses/Apache-2.0)
[![WS projects cleanup](https://github.com/whitesource-ps/ws-cleanup-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/whitesource-ps/ws-cleanup-tool/actions/workflows/ci.yml)
[![Python 3.7](https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Blue_Python_3.7%2B_Shield_Badge.svg/86px-Blue_Python_3.7%2B_Shield_Badge.svg.png)](https://www.python.org/downloads/release/python-370/)
[![PyPI](https://img.shields.io/pypi/v/ws-cleanup-tool?style=plastic)](https://pypi.org/project/ws-cleanup-tool/)

# WhiteSource Integration for Azure Work Items cloud platform - UNDER MAINTENANCE
### Tool to proceed 2-ways integrations between WS entities and Azure Work Items 
* The tool creates and updates Workitems tasks for product\project in **WhiteSource** Organization. 
* Full parameters list is available below
* The tool can be configured :
  * By configuring params.config on the executed dir or passing a path to file in the same format.
  
## Supported Operating Systems
- **Linux (Bash):**	CentOS, Debian, Ubuntu, RedHat
- **Windows (PowerShell):**	10, 2012, 2016

## Pre-requisites
* Python 3.7+

## Permissions
* The user used to execute the tool has to have "Organization Administrator" or "Product Administrator" on all the maintained products and "Organization Auditor" permissions.
* It is recommended to use a service user.
* The user has to have permissions for creating and updating Work Items tasks in Azure DevOps organization. 

## Installation and Execution from PyPi (recommended):
1. Install by executing: `pip install ws-wi-integration`
2. Configure the appropriate parameters either by using in `params.config`.
3. Execute the tool (`wi_integration`). 

## Installation and Execution from GitHub:
1. Download and unzip **ws-wi-integration.zip** 
2. Install requirements: `pip install -r requirements.txt`
3. Configure the appropriate parameters either by in `params.config`.
4. Execute: `python ws_wi_integration.py` 

## Full Usage parameters in the params.config file.
###Structure of params.config file:

[DEFAULT]  
wsuserkey = **your WS user Key**  
wsorgtoken = **your WS Org Token**  
wsurl = https://saas.whitesourcesoftware.com  
azureurl = https://dev.azure.com/  
azureorg = **Your Azure Org**  
azurepat = **Your Azure PAT (Personal Access Token)**  
modificationtypes = POLICY_MATCH  
lastrun = **DateTime of last run** (Format YYY-MM-DD HH:MM:SS. Example: 2022-05-26 10:31:32)  
utcdelta = -3   
synctime = 5  
syncrun = True  
initialsync = False  
initialstartdate = **Start date** for initial synchronization process. (Format YYY-MM-DD. Example: 2022-05-26)

[links]  
azureproject = **Name of your Azure project**  
wsproducts = **List of your WS product's tokens.**  Separated by comma 
wsprojects = **List of your WS product's tokens.**  Separated by comma


**Short description:**  
1. Sync tool can be run just for one Azure project at this moment  
2. **azureurl** is URL of Azure DevOps cloud platform. The default value is https://dev.azure.com/  
3. **azurepat** is Personal Access Token for your Azure account.
   1. The instruction of getting PAT here: https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows  
4. **wsurl** is URL of WS cloud platform. The default value is https://saas.whitesourcesoftware.com
5. **modificationtypes** is a List of possible issue's types which can be used in sync process.  
   1. Possible values are : **INVENTORY,METADATA,SCAN,POLICY_MATCH,SCAN_COMMENT,SOURCE_FILE_MATCH**  
   2. Please, pay attention that values should be provided **without** spaces as described above
6. **utcdelta** is delta between local time of your server and UTC. For example, delta between local Israel time and UTS is **-3** hours
7. **wsproducts** is a List of all your product's tokens that should be INCLUDED into Sync process. List separated by comma.      
8. **wsprojects** is a List of all your project's tokens that should be INCLUDED into Sync process. List separated by comma.
   1. Example
```mermaid
graph TD
Product_1 --> Project_1
Product_1 --> Project_2
Product_1 --> Project_3
Product_2 --> Project_4
Product_2 --> Project_5
Product_2 --> Project_6
```  
If you want to include to sync process all projects of Product_1 and Project_5 and Project_6 from Product_2 then you parameters should be  
wsproducts = Product_1  
wsprojects = Project_5, Project_6  
**This configuration is equal of the such scheme:**  
wsproducts =   
wsprojects = Project_1, Project_2, Project_3, Project_5, Project_6  

5. **synctime** is time period in **MINUTES** for running sync process in **synctime** minutes
   1. Not recommended setting the value less than 20 minutes
6. **syncrun** is True or False. **True** means run synchronization in **synctime** minutes
7. **initialsync**  is True or False. **True** means run initial synchronization for all WS issues  
8. **initialstartdate** is start date of synchronization process 
