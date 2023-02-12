import datetime
import json
import logging
import os
import sys
import uuid

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from configparser import ConfigParser

from _version import __tool_name__, __version__, __description__
from config import *
from core import run_sync, update_wi_in_thread, get_all_prj_prd, get_keys_by_value, startup, run_azure_api, get_lastrun, set_lastrun

logger = logging.getLogger("Sync Run")
logging.getLogger('urllib3').setLevel(logging.INFO)
conf = None


def main():
    global conf
    global wi_fields, wi_type

    logger.info(f"Start running {__description__} Version {__version__}.")
    if conf is None:
        conf = startup()
    config = ConfigParser()
    if os.path.exists(conf_file):
        logger.info("Sync process is started")
        prepare_json_links()
        config.read(conf_file)
        time_delta = config['DEFAULT'].getint("utcdelta",0)
        #now = datetime.datetime.now() + datetime.timedelta(hours=-2)
        #set_lastrun(now.strftime("%Y-%m-%d %H:%M:%S"))
        last_run = get_lastrun() if conf.first_run == "No" else ((datetime.datetime.now() + datetime.timedelta(hours=time_delta)-datetime.timedelta(hours=8760)).strftime("%Y-%m-%d %H:%M:%S"))
        set_lastrun(lastrun=last_run)
        #last_run = get_conf_value(config['DEFAULT'].get("LastRun"), os.environ.get("Last_Run"))
        if not os.path.exists(wi_types):
            create_wi_json(wi_types)
        wi_type, wi_fields = load_wi_json(wi_types)

        #last_run = "2022-01-01 00:00:01" if not last_run else last_run # Just for first run, in case was not set in params.config
        now = datetime.datetime.now() + datetime.timedelta(hours=time_delta)
        todate = now.strftime("%Y-%m-%d %H:%M:%S")
        time_sync = (now-datetime.datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")).total_seconds()/3600 #in hours
        time_sync = time_sync if time_sync > 1 else 1
        logger.info(run_sync((now - datetime.timedelta(hours=time_sync)).strftime("%Y-%m-%d %H:%M:%S"),todate, wi_fields, wi_type, True))
        logger.info(update_wi_in_thread())
        now = datetime.datetime.now() + datetime.timedelta(hours=time_delta)
        set_lastrun(now.strftime("%Y-%m-%d %H:%M:%S"))
        #config.set(section="DEFAULT", option="LastRun", value=todate)
        with open(conf_file, 'w') as configfile:
            config.write(configfile)
    else:
        logger.error("Config file was not found")
        exit(-1)
    logger.info("Synchronization was finished successfully")


def load_wi_json(file : str):
    try:
        f = open(file)
        res = json.load(f)
        f.close()
    except:
        return {}
    load_el = conf.azure_type if conf.azure_type else "Task"
    for res_ in res:
        if res_["name"] == load_el:
            return load_el, res_["fields"]
    return load_el, []


def create_wi_json(file : str):
    r, errcode = run_azure_api(api_type="GET", api="wit/workitemtypes/", project=conf.azure_project, data={},
                               version="7.0")
    res_conf = []
    if errcode == 0:
        for el_ in r["value"]:
            fields = []
            for el_fld_ in el_["fields"]:
                if "Custom." in el_fld_["referenceName"] or el_fld_["alwaysRequired"]:
                    fields.append(
                        {"referenceName": el_fld_["referenceName"],
                         "name": el_fld_["name"],
                         "defaultValue": el_fld_["defaultValue"],
                         }
                    )
            el_dict = {
                "name": el_["name"],
                "referenceName": el_["referenceName"],
                "fields": fields
            }
            res_conf.append(el_dict)
    if res_conf:
        with open(file, 'w') as outfile:
            json.dump(res_conf, outfile, indent=4)
    else:
        logger.warning(f"The config file {file} is not created. No available Work Items Types in the {conf.azure_project} project")


def prepare_json_links():
    global conf
    try:
        prd_lst = conf.wsproducttoken.split(',')
    except:
        prd_lst =[]
    prj_lst = []
    res_json = {}

    if prd_lst:
        for el_prd in prd_lst:
            pr_el = get_all_prj_prd(el_prd)
            for prj_one in pr_el[1:]:
                prj_lst.append(prj_one)

    conf_prj = "" if conf.wsprojecttoken is None else conf.wsprojecttoken.split(',')

    for el_prj in conf_prj:
        rt = WS.call_ws_api(self=conf.ws_conn, request_type="getProjectTags", kv_dict={"projectToken": el_prj})
        el_json = {
            el_prj : rt['projectTags'][0]['name'],
            conf.azure_project : conf.azure_project,
            "sync": 1
        }
        new_ind = get_keys_by_value(res_json, el_prj)
        if new_ind == "":
            new_ind = uuid.uuid4().hex

        res_json[f"{new_ind}"] = el_json

    for el_prj in prj_lst:
        el_json = {
            el_prj[0] : el_prj[1],
            conf.azure_project : conf.azure_project,
            "sync": 1
        }
        new_ind = get_keys_by_value(res_json, el_prj[0])
        new_ind = uuid.uuid4().hex if new_ind == "" else new_ind

        res_json[f"{new_ind}"] = el_json

    with open('./links.json', 'w') as outfile:
        json.dump(res_json, outfile)

    return res_json


if __name__ == '__main__':
    main()
