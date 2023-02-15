import json
import os
import logging
import sys
import uuid

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

import requests
from configparser import ConfigParser
from _version import __tool_name__, __version__
from config import *
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


def get_lastrun():
    azure_prj_id = get_azureprj_id(conf.azure_project)
    if azure_prj_id:
        r, errorcode = run_azure_api(api_type="GET", api=f"projects/{azure_prj_id}/properties", data={},
                                     version="7.0-preview", cmd_type="?keys=Lastrun&", header="application/json")

    return try_or_error(lambda: r["value"][0]["value"], "")


def set_lastrun(lastrun: str):
    azure_prj_id = get_azureprj_id(conf.azure_project)
    if azure_prj_id:
        data = [{
            "op": "add",
            "path": "/Lastrun",
            "value": f"{lastrun}"
        }]
        r, errorcode = run_azure_api(api_type="PATCH", api=f"projects/{azure_prj_id}/properties", data=data,
                                     version="7.0-preview")


def get_azureprj_id(prj_name : str) :
    res = ""
    r, errorcode = run_azure_api(api_type="GET",api=f"projects", data={},
                           version="7.0",header="application/json")
    if errorcode == 0:
        for prj_ in r["value"]:
            if prj_["name"] == prj_name:
                res = prj_["id"]
                break
    return res


def try_or_error(supplier, msg):
    try:
        return supplier()
    except:
        return msg


def fetch_prj_policy(prj_token: str, sdate: str, edate: str):
    global conf
    if conf is None:
        startup()
    try:
        rt = WS.call_ws_api(self=conf.ws_conn, request_type="fetchProjectPolicyIssues",
                            kv_dict={"projectToken": prj_token, "policyActionType": "CREATE_ISSUE", "fromDateTime" : sdate, "toDateTime" : edate})
        rt_res = [rt['product']['productName'], rt['project']['projectName']]
        for rt_el_val in rt['issues']:
            if try_or_error(lambda :rt_el_val['policy']['enabled'],False):
                rt_res.append(rt_el_val)
    except Exception as err:
        rt_res = ["Internal error", f"{err}"]

    return rt_res


def get_prj_list_modified(fromdate: str, todate: str):
    global conf
    if conf is None:
        startup()
    try:
        try:
            mdf_types = conf.modification_types.split(',')
            rt = WS.call_ws_api(self=conf.ws_conn, request_type="getOrganizationLastModifiedProjects",
                                kv_dict={"fromDateTime": fromdate, "modificationTypes": mdf_types, "toDateTime": todate,
                                         "includeRequestToken": False})
        except:
            rt = WS.call_ws_api(self=conf.ws_conn, request_type="getOrganizationLastModifiedProjects",
                                kv_dict={"fromDateTime": fromdate, "toDateTime": todate,
                                         "includeRequestToken": False})

        return rt
    except Exception as err:
        logger.error(f"Internal error: {err}")
        exit(-1)


def run_azure_api(api_type: str, api: str, data={}, version: str = "6.0", project: str = "", cmd_type: str ="?", header: str = "application/json-patch+json"):
    global conf
    errorcode = 0
    if conf is None:
        startup()
    try:
        url = f"{conf.azure_url}{conf.azure_org}/_apis/{api}{cmd_type}api-version={version}" if project == "" else f"{conf.azure_url}{conf.azure_org}/{project}/_apis/{api}{cmd_type}api-version={version}"

        if api_type == "GET":
            r = requests.get(url, json=data,
                             headers={'Content-Type': f'{header}'},
                             auth=('', conf.azure_pat))
        elif api_type == "POST":
            r = requests.post(url, json=data,
                          headers={'Content-Type': f'{header}'},
                          auth=('', conf.azure_pat))
        elif api_type == "PATCH":
            r = requests.patch(url, json=data,
                          headers={'Content-Type': f'{header}'},
                          auth=('', conf.azure_pat))

        res = json.loads(r.text)
        try:
            msg = res['message']
            logger.error(f"Error was raised. The reason: {msg}")
            errorcode = 1
        except:
            pass
    except Exception as err:
        errorcode = 1
        res = {"Internal error": f"{err}"}

    return res, errorcode


def check_wi_id(id: str):
    global conf
    if conf is None:
        startup()
    try:
        data = {"query" : f'select [System.Id],[System.State] From WorkItems Where [System.Title]="{id}" And [System.TeamProject] = "{conf.azure_project}" '}
        r, errocode = run_azure_api(api_type="POST",api="wit/wiql", version="7.0", project=conf.azure_project,data=data, header="application/json")
        return r["workItems"][0]["id"] if errocode == 0 else 0
    except:
        return 0


def update_wi_in_thread():
    global conf
    startup()
    try:
        data = {"query" : f'select [System.Id] From WorkItems Where [System.ChangedDate] > "{get_lastrun()}" And [System.TeamProject] = "{conf.azure_project}"'}
        r, errocode = run_azure_api(api_type="POST",api="wit/wiql", version="7.0", project=conf.azure_project,data=data, header="application/json",cmd_type="?timePrecision=True&")

        id_str = ""
        if errocode == 0:
            for wi_ in r["workItems"]:
                id_str += str(wi_["id"]) + ","
            id_str = id_str[:-1] if len(r["workItems"]) > 0 else ""

        if id_str:
            wi, errcode = run_azure_api(api_type="GET", api=f"wit/workitems?ids={id_str}&$expand=Relations", data={}, project=conf.azure_project,cmd_type="&")
            if errcode == 0:
                for wq_el in wi['value']:
                    issue_id = wq_el['id']
                    issue_wi_title = wq_el['fields']['System.Title']
                    comment = wq_el['relations'][0]['attributes']['comment']
                    prj_token = comment[0:wq_el['relations'][0]['attributes']['comment'].find(",")]
                    uuid = comment[wq_el['relations'][0]['attributes']['comment'].find(",")+1:]
                    wq_el_url = wq_el['url'][0:wq_el['url'].find("apis")] + f"workitems/edit/{issue_id}"

                    ext_issues = [{"identifier": f"{issue_wi_title}",
                                   "url": wq_el_url,
                                   "status": wq_el["fields"]['System.State'],
                                   "lastModified": wq_el["fields"]['System.ChangedDate'],
                                   "created": wq_el["fields"]['System.CreatedDate']
                                   }]
                    rt = WS.call_ws_api(self=conf.ws_conn, request_type="updateExternalIntegrationIssues",
                                   kv_dict={"projectToken": prj_token, "wsPolicyIssueItemUuid": uuid,
                                            "externalIssues": ext_issues})

                return f"Updated {len(wi['value'])} {conf.azure_type}s"
        else:
            return "Nothing to update"

    except Exception as err:
        return f"Internal error. Details: {err}"


def get_azure_prj_lst():
    try:
        azure_prj_list, errcode = run_azure_api(api_type="GET", api="projects")
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
        wi, errcode = run_azure_api(api_type="GET", api=f"wit/workitems/{exist_id}", data={}, project=conf.azure_project)
        url = wi['url'][0:wi['url'].find("apis")] + f"workitems/edit/{wi['id']}"
        ext_issues = [{"identifier": f"WS Issue_{issueid}",
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


def create_wi(prj_token: str, azure_prj: str, sdate: str, edate: str, del_ : list, cstm_flds : list, wi_type : str):
    def set_priority(value : float):
        score= [70,55,40]  # Mend gradation of SCC scores
        z = value*10
        for i, sc_ in enumerate(score):
            if z//sc_ == 1:
                break
        return i+1

    def analyze_fields(fld : dict, prj : list):
        val = ""
        if fld["defaultValue"]:
            step1 = fld["defaultValue"].split("&")
            for st_ in step1:
                t = f"{mend_val(st_[5:], prj)}" if "MEND:" in st_ else st_
                if t:
                    val += t
                elif "MEND:" in st_:
                    logger.warning(f"The value of field {fld['referenceName']} is empty. Check the syntax that was provided. It could be the reason.")
        return fld["referenceName"], val.strip()

    def mend_val(alert_val : str, prj_el : list):
        lst = alert_val.split(".")
        temp = None
        for lst_ in lst:
            try:
                temp = prj_el[lst_] if not temp else temp[lst_]
                if type(temp) is list:
                    rs = ""
                    for el_ in temp:
                        rs += el_ +","
                    return rs[:-1] if rs else ""
            except:
                return ""
        return temp

    global conf
    try:
        ws_prj = fetch_prj_policy(prj_token, sdate, edate)
        prd_name = ws_prj[0]
        prj_name = ws_prj[1]

        count_item = 1
        for prj_el in ws_prj[2:]:
            lib_id = prj_el["library"]["keyId"]
            # lib_uuid= prj_el['library']['keyUuid']
            lib_url = prj_el["library"]["url"]
            lib_name = prj_el["library"]["filename"]
            #lib_ver = prj_el["library"]["version"]
            lib_local_path = ""
            try:
                for loc_path_ in prj_el["library"]["localPaths"]:
                    lib_local_path += try_or_error(lambda: loc_path_,"")+"<br>"
            except:
                pass
            for i, policy_el in enumerate(prj_el["policyViolations"]):
                issue_id = policy_el["issueUuid"]
                #viol_type = policy_el["violationType"]
                #viol_status = policy_el["status"]
                vul_name = try_or_error(lambda:policy_el["vulnerability"]["name"],"")
                vul_severity = try_or_error(lambda:policy_el["vulnerability"]["cvss3_severity"],"")
                vul_title = f"{vul_name} ({vul_severity}) detected in {lib_name}"

                vul_score = try_or_error(lambda:policy_el["vulnerability"]["cvss3_score"],"")
                vul_desc = try_or_error(lambda:policy_el["vulnerability"]["description"],"")
                vul_url = try_or_error(lambda:policy_el["vulnerability"]["url"],"")
                vul_origin_url = try_or_error(lambda:policy_el["vulnerability"]["topFix"]["url"],"")
                vul_publish_date = try_or_error(lambda:policy_el["vulnerability"]["publishDate"],"")
                vul_fix_resolution = try_or_error(lambda:policy_el["vulnerability"]["topFix"]["fixResolution"],"")
                vul_fix_type = try_or_error(lambda:policy_el["vulnerability"]["topFix"]["type"],"")
                vul_fix_release_date = try_or_error(lambda:policy_el["vulnerability"]["topFix"]["date"],"")

                exist_id = check_wi_id(vul_title)
                if exist_id == 0:
                    priority = set_priority(float(vul_score))
                    desc = "<b>Vulnerable Library: </b>" + lib_name + "<br><b> Library home page:</b> " + lib_local_path + \
                           "<br><b>Vulnerability Details:</b> " + vul_desc + "<br><b>Publish Date:</b> " + vul_publish_date + \
                           f"<br><b>URL:</b> <a href='{vul_url}'>{vul_name}</a>" + \
                           "<br><b>CVSS 3 Score Details </b>(" + str(vul_score) + ")<br>Suggested Fix:<br><b>Type:</b> " + vul_fix_type + \
                           f"<br><b>Origin:</b> <a href='{vul_origin_url}'></a><br><b>Release Date:</b> " + vul_fix_release_date + \
                           "<br><b>Fix Resolution:</b> " + vul_fix_resolution
                    data = [
                        {
                            "op": "add",
                            "path": "/fields/System.Title",
                            "value" : vul_title
                        },
                        {
                            "op" : "add",
                            "path" : "/fields/Microsoft.VSTS.Common.Priority",
                            "value" : priority
                        },
                        {
                            "op": "add",
                            "path": "/fields/System.Description",
                            "value": desc
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
                    for custom_ in cstm_flds:
                        fld_name, fld_val = analyze_fields(custom_, prj_el)
                        if fld_val:
                            data.append({
                                "op" : "add",
                                "path" : f"/fields/{fld_name}", #azure_field_name(custom_[0])
                                "value" : fld_val
                            })

                    if not (conf.azure_area is None or conf.azure_area == ""):
                        data.append(
                            {
                                "op": "add",
                                "path": "/fields/System.AreaPath",
                                "value": f"{conf.azure_area}"
                            }
                        )
                    try:
                        r, errcode = run_azure_api(api_type="POST", api=f"wit/workitems/${wi_type}", data=data, project=azure_prj)
                        if errcode == 0:
                            logger.info(f"{conf.azure_type} {count_item} of Mend project {prj_name} created")
                        else:
                            logger.warning(f"{conf.azure_type} was not created. Details: {r['message']}")
                    except Exception as err:
                        logger.error(f"Error was proceeded during creation: {err}")
                    count_item += 1
                else:
                    if exist_id not in del_:
                        update_ws_issue(issue_id, prj_token, exist_id)
        if errcode == 0:
            return f"{count_item-1} {conf.azure_type}s were created or updated successfully"
    except Exception as err:
        return f"Internal error was proceeded. Details : {err}"


def run_sync(st_date: str, end_date: str, custom_flds : list, wi_type : str, in_script : bool = False):
    try:
        f = open("./links.json")
        sync_data = json.load(f)
        f.close()
    except:
        sync_data = {}

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
    deleted_items = get_deleted_items()
    for prj_el in res:
        create_wi(prj_el[0], prj_el[1], st_date, end_date, deleted_items, custom_flds, wi_type)

    if len(res) > 0:
        return f"Proceed {len(res)} project(s)"
    else:
        return "Nothing to create now"


def get_deleted_items():
    del_lst = []
    r, errcode = run_azure_api(api_type="GET", api=f"wit/recyclebin", data={}, project=conf.azure_project)
    if errcode == 0:
        for res_ in r["value"]:
            del_lst.append(res_["id"])
    return del_lst


def get_keys_by_value(dictOfElements, valueToFind):
    for item in dictOfElements.items():
        for it in item[1]:
            if it == valueToFind:
                return item[0]
    return uuid.uuid4().hex


def extract_url(url : str)-> str:
    url_ = url if url.startswith("https://") else f"https://{url}"
    url_ = url_.replace("http://","")
    pos = url_.find("/",8)
    return url_[0:pos] if pos>-1 else url_


def startup():
    global conf
    if os.path.exists(conf_file):
        config = ConfigParser()
        config.read(conf_file)

        conf = Config(
            ws_user_key=get_conf_value(config['DEFAULT'].get("WsUserKey"), os.environ.get("WS_USERKEY")),
            ws_org_token=get_conf_value(config['DEFAULT'].get("Apikey"), os.environ.get("WS_TOKEN")),
            ws_url=get_conf_value(config['DEFAULT'].get("WsUrl"), os.environ.get("WS_URL")),
            wsproducttoken=get_conf_value(config['links'].get("wsproducttoken"), os.environ.get("WS_PRODUCTTOKEN")),
            wsprojecttoken=get_conf_value(config['links'].get("wsprojecttoken"), os.environ.get("WS_PROJECTTOKEN")),
            azure_url=get_conf_value(config['DEFAULT'].get('AzureUrl'), os.environ.get("AZURE_URL")),
            azure_org=get_conf_value(config['DEFAULT'].get('AzureOrg'), os.environ.get("AZURE_ORG")),
            azure_pat=get_conf_value(config['DEFAULT'].get('AzurePat'), os.environ.get("AZURE_PAT")),
            azure_project=get_conf_value(config['links'].get("azureproject"), os.environ.get("AZURE_PROJECT")),
            modification_types=get_conf_value(config['DEFAULT'].get('modificationTypes'),
                                              os.environ.get("modification_Types")),
            first_run=get_conf_value(config['DEFAULT'].get("FirstRun"), "No"),
            utc_delta = config['DEFAULT'].getint("utcdelta", 0),
            azure_area = get_conf_value(config['DEFAULT'].get('AzureArea'), os.environ.get("AZURE_AREA")),
            azure_type = get_conf_value(config['DEFAULT'].get('azuretype'), "Task"),
            ws_conn=None
        )

        try:
            conf.ws_conn = WS(url=extract_url(conf.ws_url),
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
