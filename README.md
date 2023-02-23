[![Logo](https://resources.mend.io/mend-sig/logo/mend-dark-logo-horizontal.png)](https://www.mend.io/)  

[![License](https://img.shields.io/badge/License-Apache%202.0-yellowgreen.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/whitesource-ps/ws-azure-workitems-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/whitesource-ps/ws-azure-workitems-integration/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/whitesource-ps/ws-azure-workitems-integration)](https://github.com/whitesource-ps/ws-azure-workitems-integration/releases/latest)  

# Mend Integration for Azure Work Items cloud platform
### Self-hosted tool to proceed with integrations between Mend entities and Azure Work Items 
* The tool creates and updates Workitems tasks for a product\project in **Mend** Organization
* Full parameters (Azure variables) list is available below
* The tool can be configured by Azure DevOps variables
    
## Supported Operating Systems
- **Linux (Bash):**	CentOS, Debian, Ubuntu
- **Windows (PowerShell):**	10, 2012, 2016

## Pre-requisites
* Python 3.9+

## Permissions
* The user used to execute the tool has to have "Organization Administrator" or "Product Administrator" on all the maintained products and "Organization Auditor" permissions
* It is recommended to use a service user
* A user must have permission to create and update Work Items tasks in the Azure DevOps organization 

## Installation on the Azure side:
1. Create a **pipeline** in your Azure organization and config it using the [azure-pipelines.yml](https://github.com/whitesource-ps/ws-azure-workitems-integration/blob/master/azure-pipelines.yml)
2. Configure the appropriate variables (secrets) in the Azure pipeline

### Command-Line Arguments and linked Azure variables
| Parameter                          |  Type  | Azure variable       | Required | Description                                                                                                                                                                                                     |
|:-----------------------------------|:------:|----------------------|:--------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **&#x2011;&#x2011;help**           | switch |                      |    No    | Show help and exit                                                                                                                                                                                              |
| **&#x2011;&#x2011;url**            | string | WS_URL               |   Yes    | Mend server URL                                                                                                                                                                                                 |
| **&#x2011;&#x2011;user-key**       | string | WS_USERKEY           |   Yes    | Mend User Key (Secret variable in Azure)                                                                                                                                                                        |
| **&#x2011;&#x2011;api-key**        | string | WS_APIKEY            |   Yes    | Mend API Key  (Secret variable in Azure)                                                                                                                                                                        |
| **&#x2011;&#x2011;azureurl**       | string | WS_AZUREURL          |    No    | Azure Server URL (default: `https://dev.azure.com/` )                                                                                                                                                           | 
| **&#x2011;&#x2011;azureorg**       | string | WS_AZUREORG          |   Yes    | Azure Organization Name                                                                                                                                                                                         | 
| **&#x2011;&#x2011;azurearea**      | string | WS_AZUREAREA         |    No    | **FULL** path of Azure Area (default: Azure Project root)*                                                                                                                                                      | 
| **&#x2011;&#x2011;azurepat**       | string | WS_AZUREPAT          |   Yes    | Azure PAT ([Personal Access Token](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)) (Secret variable in Azure)  |
| **&#x2011;&#x2011;azureproject**   | string | WS_AZUREPROJECT      |   Yes    | Azure project name                                                                                                                                                                                              |
| **&#x2011;&#x2011;azuretype**      | string | WS_AZURETYPE         |    No    | Type of created Azure object (default: `Task`)***.                                                                                                                                                              |
| **&#x2011;&#x2011;wsprojecttoken** | string | WS_PROJECTTOKEN      |    No    | List of all your project's tokens that should be INCLUDED in the Sync process (separated by a comma)                                                                                                            |
| **&#x2011;&#x2011;wsproducttoken** | string | WS_PRODUCTTOKEN      |    No    | List of all your product's tokens that should be INCLUDED in the Sync process (separated by a comma)                                                                                                            |
| **&#x2011;&#x2011;type**           | string | WS_MODIFICATIONTYPES |    No    | [List of modification types](https://whitesource.atlassian.net/wiki/spaces/PROD/pages/2429681685/Issue+Tracker+Integration+-+API+Documentation#getOrganizationLastModifiedProjects) (default: `POLICY_MATCH`)** |
| **&#x2011;&#x2011;utcdelta**       | string | WS_UTCDELTA          |    No    | The delta between the local time of your **computer where you run tool** and **MEND's environment** (default: 0)                                                                                                |
| **&#x2011;&#x2011;firstrun**       | string | WS_RESET             |    No    | The parameter should be set to `True` in case initial run (default: `False`)                                                                                                                                    |
| **&#x2011;&#x2011;customfields**   | string | WS_CUSTOMFIELDS      |    No    | The string defines names and values for custom fields of WorkItem ****                                                                                                                                          |

\* The area value could be like this **"SomeProject\\\SomeArea_1\\\SomeArea_2"**
      1. Please, pay attention that the **slash needs to be escaped as shown in the example**  
      2. if Area path contains **spaces** then the path must be enclosed in single quotes

\** 1. Possible values are : **INVENTORY,METADATA,SCAN,POLICY_MATCH,SCAN_COMMENT,SOURCE_FILE_MATCH** or **All** for all types   
   2. Please, pay attention that values should be provided **without** spaces as described above  

\***  There are several types of working item:
1. **Epic** (Basic, Agile, Scrum, and CMMI)
2. **Feature** (Agile, Scrum, and CMMI)
3. **User Story** (Agile), Product backlog item (Scrum), Requirement (CMMI)
4. **Task** (Basic, Agile, Scrum, and CMMI)
5. **Impediment** (Scrum), Issue (Agile and Basic)
6. **Bug** (Agile, Scrum, and CMMI)

\**** The syntax of ```customfields``` is  
**[Name of Custom Field1]::[Value of Custom Field1];[Name of Custom Field2]::[Value of Custom Field2]** where  
**Value of Custom Field** can be provided as combination of Mend object name and free text.
#### Example of customfields parameter
SomeCustomField1::MEND:library.localPaths&Some Free Text;SomeCustomField2::MEND:policy.owner.email
1. **SomeCustomField1** and **SomeCustomField2** are names of Custom Azure Fields 
2. **MEND:** This is a special operator that indicates that it is followed by the name of the Mend object.
3. **library.localPath** and **policy.owner.email** are names of Mend objects
4. **;** is a separator of different values for **SomeCustomField1** or **SomeCustomField2** field
5. Pairs [Some custom field]::[Custom value] separated by **&** 