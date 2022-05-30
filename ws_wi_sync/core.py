import json
import os
import logging
import sys

from msrest.authentication import BasicAuthentication
from vsts.vss_connection import VssConnection

from vsts.work_item_tracking.v4_1.models.wiql import Wiql
import requests
from configparser import ConfigParser
from _version import __description__, __tool_name__, __version__
from ws_wi_sync.config import *
from ws_sdk import WS

logging.basicConfig(level=logging.DEBUG if bool(os.environ.get("DEBUG", "false")) is True else logging.INFO,
                    handlers=[logging.StreamHandler(stream=sys.stdout)],
                    format='%(levelname)s %(asctime)s %(thread)d %(name)s: %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S')
logger = logging.getLogger(__tool_name__)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger_vsts = logging.getLogger('vsts')
logger_vsts.setLevel(logging.INFO)
logger_msrest = logging.getLogger('msrest')
logger_msrest.setLevel(logging.INFO)
logger_wssdk = logging.getLogger('ws_sdk')
logger_wssdk.setLevel(logging.INFO)

conf = None


def fetch_prj_policy(prj_token: str, sdate: str, edate: str):
    global conf
    if conf is None:
        startup()
    try:
        rt = WS.call_ws_api(self=conf.ws_conn, request_type="fetchProjectPolicyIssues",
                            kv_dict={"projectToken": prj_token, "policyActionType": "CREATE_ISSUE"})
        rt_res = [rt['product']['productName'], rt['project']['projectName']]
        for rt_el_val in rt['issues']:
            try:
                enb = rt_el_val['policy']['enabled']
            except:
                enb = False

            if (rt_el_val['policyViolations'][0]['lastModified'] >= sdate) and (
                    rt_el_val['policyViolations'][0]['lastModified'] <= edate) and enb:
                rt_res.append(rt_el_val)
    except Exception as err:
        rt_res = ["Internal error", f"{err}"]

    return rt_res


def get_prj_list_modified(fromdate: str, todate: str):
    global conf
    if conf is None:
        startup()
    try:
        mdf_types = conf.modification_types.split(',')
        rt = WS.call_ws_api(self=conf.ws_conn, request_type="getOrganizationLastModifiedProjects",
                            kv_dict={"fromDateTime": fromdate, "toDateTime": todate,
                                     "modificationTypes": mdf_types, "includeRequestToken": False})
        return rt
    except Exception as err:
        logger.error(f"Internal error: {err}")
        exit(-1)


def run_azure_api(api_type: str, api: str, data={}, version: str = "6.0", project: str = "", cmd_type: str ="?"):
    global conf
    if conf is None:
        startup()
    try:
        personal_access_token = conf.azure_pat
        if project == "":
            url = conf.azure_url + conf.azure_org + '/_apis/' + api + f'{cmd_type}api-version=' + version
        else:
            url = conf.azure_url + conf.azure_org + f'/{project}/_apis/' + api + f'{cmd_type}api-version=' + version

        if api_type == "GET":
            r = requests.get(url, json=data,
                             headers={'Content-Type': 'application/json-patch+json'},
                             auth=('', personal_access_token))
        else:
            r = requests.post(url, json=data,
                              headers={'Content-Type': 'application/json-patch+json'},
                              auth=('', personal_access_token))
        res = json.loads(r.text)
    except Exception as err:
        res = {"Internal error": f"{err}"}

    return res


def check_wi_id(id: str):
    global conf
    if conf is None:
        startup()
    try:
        personal_access_token = conf.azure_pat
        url = conf.azure_url + conf.azure_org
        credentials = BasicAuthentication('', personal_access_token)
        connection = VssConnection(base_url=url, creds=credentials)
        wiql = Wiql(
            query=f'select [System.Id],[System.State] From WorkItems Where [System.Title]="WS Issue_{id}"'
        )
        wit_client = connection.get_client(
            'vsts.work_item_tracking.v4_1.work_item_tracking_client.WorkItemTrackingClient')
        wiql_results = wit_client.query_by_wiql(wiql).work_items
        return wiql_results[0].id
    except:
        return 0


def update_wi_in_thread():
    global conf
    startup()
    try:
        personal_access_token = conf.azure_pat
        url = conf.azure_url + conf.azure_org
        credentials = BasicAuthentication('', personal_access_token)
        connection = VssConnection(base_url=url, creds=credentials)
        wiql = Wiql(
            query=f'select [System.Id] From WorkItems Where [System.ChangedDate] > "{conf.last_run}"'
        )
        wit_client = connection.get_client(
            'vsts.work_item_tracking.v4_1.work_item_tracking_client.WorkItemTrackingClient')
        wiql_results = wit_client.query_by_wiql(wiql=wiql, time_precision=True).work_items
        id_str = ""
        for wq_el in wiql_results:
            id_str += str(wq_el.id)+","

        id_str = id_str[:-1] if len(wiql_results) > 0 else ""
        if id_str != "":
            wi = run_azure_api(api_type="GET", api=f"wit/workitems?ids={id_str}&$expand=Relations", data={}, project=conf.azure_project,cmd_type="&")
            for wq_el in wi['value']:
                issue_id = wq_el['id']
                comment = wq_el['relations'][0]['attributes']['comment']
                prj_token = comment[0:wq_el['relations'][0]['attributes']['comment'].find(",")]
                uuid = comment[wq_el['relations'][0]['attributes']['comment'].find(",")+1:]
                wq_el_url = wq_el['url'][0:wq_el['url'].find("apis")] + f"workitems/edit/{issue_id}"

                ext_issues = [{"identifier": f"WS Issue_{issue_id}",
                               "url": wq_el_url,
                               "status": wq_el["fields"]['System.State'],
                               "lastModified": wq_el["fields"]['System.ChangedDate'],
                               "created": wq_el["fields"]['System.CreatedDate']
                               }]
                WS.call_ws_api(self=conf.ws_conn, request_type="updateExternalIntegrationIssues",
                               kv_dict={"projectToken": prj_token, "wsPolicyIssueItemUuid": uuid,
                                        "externalIssues": ext_issues})

            return f"Updated {len(wi['value'])} Work Items"
        else:
            return "Nothing to update"

    except Exception as err:
        return f"Internal error. Details: {err}"


def get_azure_prj_lst():
    try:
        azure_prj_list = run_azure_api(api_type="GET", api="projects")
        res = []
        for prj in azure_prj_list['value']:
            res.append((prj['id'], prj['name']))
    except Exception as err:
        res = [("Internal error", f"{err}")]

    return res


def get_all_prd_lst():
    global conf
    if conf is None:
        startup()
    try:
        rt = WS.call_ws_api(self=conf.ws_conn, request_type="getAllProducts")
        res = []
        for prd in rt['products']:
            res.append((prd['productToken'], prd['productName']))

    except:
        res = [("", "")]

    return res


def get_all_prj_prd(token: str):
    global conf
    if conf is None:
        startup()
    try:
        rt = WS.call_ws_api(self=conf.ws_conn, request_type="getAllProjects", kv_dict={"productToken": token})
        res = [("0", "All Projects")]
        for prd in rt['projects']:
            res.append((prd['projectToken'], prd['projectName']))

    except:
        res = [("0", "All Projects")]

    return res


def update_ws_issue(issueid: str, prj_token: str, exist_id: int):
    global conf
    if conf is None:
        startup()
    try:
        wi = run_azure_api(api_type="GET", api=f"wit/workitems/{exist_id}", data={}, project=conf.azure_project)
        url = wi['url'][0:wi['url'].find("apis")] + f"workitems/edit/{wi['id']}"
        ext_issues = [{"identifier": f"WS Issue_{exist_id}",
                       "url": url,
                       "status": wi["fields"]['System.State'],
                       "lastModified": wi["fields"]['System.ChangedDate'],
                       "created": wi["fields"]['System.CreatedDate']
                       }]
        WS.call_ws_api(self=conf.ws_conn, request_type="updateExternalIntegrationIssues",
                       kv_dict={"projectToken": prj_token, "wsPolicyIssueItemUuid": issueid,
                                "externalIssues": ext_issues})
    except Exception as err:
        logger.error(f"Internal error was proceeded. Details : {err}")


def create_wi(prj_token: str, azure_prj: str, sdate: str, edate: str):
    try:
        ws_prj = fetch_prj_policy(prj_token, sdate, edate)
        prd_name = ws_prj[0]
        prj_name = ws_prj[1]

        count_item = 1
        for prj_el in ws_prj[2:]:
            lib_id = prj_el['library']['keyId']
            # lib_uuid= prj_el['library']['keyUuid']
            lib_url = prj_el['library']['url']
            lib_name = prj_el['library']['name']
            lib_ver = prj_el['library']['version']
            for i, policy_el in enumerate(prj_el['policyViolations']):
                issue_id = policy_el['issueUuid']
                viol_type = policy_el['violationType']
                viol_status = policy_el['status']
                try:
                    vul_name = policy_el["vulnerability"]['name']
                except:
                    vul_name = ""
                try:
                    vul_severity = policy_el['vulnerability']['severity']
                except:
                    vul_severity = ""
                try:
                    vul_score = policy_el['vulnerability']['score']
                except:
                    vul_score = ""
                try:
                    vul_desc = policy_el['vulnerability']['description']
                except:
                    vul_desc = ""

                exist_id = check_wi_id(f"{lib_id}_{str(i + 1)}")
                if exist_id == 0:
                    data = [
                        {
                            "op": "add",
                            "path": "/fields/System.Title",
                            "value": f"WS Issue_{lib_id}_{str(i + 1)}"
                        },
                        {
                            "op": "add",
                            "path": "/fields/System.Description",
                            "value": "<b>Product: </b>" + prd_name + "<br>" + "<b>Project: </b>" + prj_name + "<br>" + "<b>Library: </b>" + lib_name + "<br><b> Library version:</b> " + str(
                                lib_ver) + "<br><b>Violation Type: </b>" + viol_type +
                                     "<br><b>Violation Status: </b>" + viol_status + "<br><b>Vulnerability: </b>" + vul_name + "<br><b>Severity: </b>" + vul_severity + "<br><b>Score: </b>" + str(
                                vul_score) + "<br><b>Description:</b> " + vul_desc
                        },
                        {
                            "op": "add",
                            "path": "/relations/-",
                            "value": {
                                "rel": "Hyperlink",
                                "url": lib_url,
                                "attributes": {"comment": prj_token + "," + policy_el['issueUuid']}
                            }
                        }
                    ]
                    run_azure_api(api_type="POST", api="wit/workitems/$task", data=data, project=azure_prj)
                    logger.info(f"Work Item {count_item} created")
                else:
                    update_ws_issue(issue_id, prj_token, exist_id)
                count_item += 1

        return "Work Items were created and updated successfully"
    except Exception as err:
        return f"Internal error was proceeded. Details : {err}"


def run_sync(st_date: str, end_date: str, in_script : bool = False):
    try:
        f = open("../links.json")
        sync_data = json.load(f)
        f.close()
    except Exception as err:
        return f"Error during open config file: {err}"

    res = []
    modified_projects = get_prj_list_modified(st_date, end_date)
    fnd = False
    for sync_el in sync_data:
        if int(sync_data[sync_el]['sync']) == 1:
            fnd = False
            for i, key_el in enumerate(sync_data[sync_el].keys()):
                if i == 0:
                    a = key_el
                    for mod_pj_el in modified_projects['lastModifiedProjects']:
                        if a in mod_pj_el.values():
                            fnd = True
                            break
                elif i == 1:
                    b = key_el
        if fnd:
            res.append((a, b))

    for prj_el in res:
        create_wi(prj_el[0], prj_el[1], st_date, end_date)

    if len(res) > 0:
        return f"Created/updated {len(res)} projects"
    else:
        return "Nothing to create now"

    '''
    if in_script:
        if res is None:
            return "Nothing to create now"
        else:
            return "Work Items were created successfully"
    else:
        return "Work Items were created successfully"
    '''

def get_keys_by_value(dictOfElements, valueToFind):
    list_of_items = dictOfElements.items()
    res = ""
    for item in list_of_items:
        for it in item[1]:
            if it == valueToFind:
                return item[0]
    return res


def startup():
    global conf
    if os.path.exists(conf_file):
        config = ConfigParser()
        config.read(conf_file)

        conf = Config(
            ws_user_key=get_conf_value(config['DEFAULT'].get("WsUserKey"), os.environ.get("WS_USER_KEY")),
            ws_org_token=get_conf_value(config['DEFAULT'].get("WsOrgToken"), os.environ.get("WS_ORG_TOKEN")),
            ws_url=get_conf_value(config['DEFAULT'].get("WsUrl"), os.environ.get("WS_URL")),
            azure_project=get_conf_value(config['links'].get("azureproject"), os.environ.get("AZURE_PROJECT")),
            wsproducts=get_conf_value(config['links'].get("wsproducts"), os.environ.get("WS_PRODUCTS")),
            wsprojects=get_conf_value(config['links'].get("wsprojects"), os.environ.get("WS_PROJECTS")),
            azure_url=get_conf_value(config['DEFAULT'].get('AzureUrl'), os.environ.get("Azure_Url")),
            azure_org=get_conf_value(config['DEFAULT'].get('AzureOrg'), os.environ.get("Azure_Org")),
            #azure_project=get_conf_value(config['DEFAULT'].get('AzureProject'), os.environ.get("Azure_Project")),
            azure_pat=get_conf_value(config['DEFAULT'].get('AzurePat'), os.environ.get("Azure_Pat")),
            modification_types=get_conf_value(config['DEFAULT'].get('modificationTypes'),
                                              os.environ.get("modification_Types")),
            dry_run=config['DEFAULT'].getboolean("DryRun", False),
            sync_run=config['DEFAULT'].getboolean("SyncRun", False),
            sync_time=config['DEFAULT'].getint("SyncTime", 10),
            last_run=get_conf_value(config['DEFAULT'].get("LastRun"), os.environ.get("Last_Run")),
            utc_delta = config['DEFAULT'].getint("utcdelta", 0),
            initial_sync = config['DEFAULT'].getboolean("initialsync", False),
            initial_startdate = get_conf_value(config['DEFAULT'].get("InitialStartdate"), os.environ.get("Initial_Start")),
            ws_conn=None
        )
        try:
            conf.ws_conn = WS(url=conf.ws_url,
                              user_key=conf.ws_user_key,
                              token=conf.ws_org_token,
                              skip_ua_download=True,
                              tool_details=(f"ps-{__tool_name__.replace('_', '-')}", __version__))

            return conf
        except Exception as err:
            logger.error(f"Internal error was proceeded. Details : {err}")
            exit(-1)
    else:
        logger.error(f"No configuration file found at: {conf_file}")
        raise FileNotFoundError
