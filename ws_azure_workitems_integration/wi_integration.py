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
from core import run_sync, update_wi_in_thread, get_all_prj_prd, get_keys_by_value, startup, run_azure_api

logger = logging.getLogger("Sync Run")
logging.getLogger('urllib3').setLevel(logging.INFO)
conf = None


def main():
    global conf
    logger.info(f"Start running {__description__} Version {__version__}.")
    if conf is None:
        conf = startup()
    config = ConfigParser()
    if os.path.exists(conf_file):
        logger.info("Sync process is started")
        #sync_run = True
        prepare_json_links()
        #while sync_run:
        config.read(conf_file)
        last_run = get_conf_value(config['DEFAULT'].get("LastRun"), os.environ.get("Last_Run"))
        #sync_time = config['DEFAULT'].getint("SyncTime", 10)
        #sync_run =  config['DEFAULT'].getboolean("SyncRun", False)
        #if sync_run:
        time_delta = config['DEFAULT'].getint("utcdelta",0)
        now = datetime.datetime.now() + datetime.timedelta(hours=time_delta)
        todate = now.strftime("%Y-%m-%d %H:%M:%S")
        time_sync = (now-datetime.datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")).total_seconds()/3600 #in hours
        time_sync = time_sync if time_sync > 1 else 1
        logger.info(run_sync((now - datetime.timedelta(hours=time_sync)).strftime("%Y-%m-%d %H:%M:%S"),todate, True))
        logger.info(update_wi_in_thread())
        config.set(section="DEFAULT", option="LastRun", value=todate)
        with open(conf_file, 'w') as configfile:
            config.write(configfile)
            #logger.info(f"Next run in {sync_time} minutes")
            #time.sleep(sync_time*60)
        #else:
        #    logger.info(f"Sync run is not on")
    else:
        logger.error("Config file was not found")
        exit(-1)
    logger.info("Synchronization was finished successfully")


def prepare_json_links():
    global conf
    try:
        prd_lst = conf.wsproducts.split(',')
    except:
        prd_lst =[]
    prj_lst = []
    #try:
    #    f = open("./links.json")
    #    res_json = json.load(f)
    #    f.close()
    #except:
    res_json = {}

    if prd_lst is not None:
        for el_prd in prd_lst:
            pr_el = get_all_prj_prd(el_prd)
            for prj_one in pr_el[1:]:
                prj_lst.append(prj_one)

    conf_prj = "" if conf.wsprojects is None else conf.wsprojects.split(',')

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
        if new_ind == "":
            new_ind = uuid.uuid4().hex

        res_json[f"{new_ind}"] = el_json

    with open('./links.json', 'w') as outfile:
        json.dump(res_json, outfile)

    return res_json


if __name__ == '__main__':
    main()
