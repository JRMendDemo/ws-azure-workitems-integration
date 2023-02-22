import os
from configparser import ConfigParser
import argparse
import json
import requests

conf_file = "./local-params.config" if os.path.exists("./local-params.config") else "./params.config"
wi_types = "./local-workitem_types.json" if os.path.exists("./local-workitem_types.json") else "./workitem_types.json"


def parse_args():
    parser = argparse.ArgumentParser(description='Utility to create params file for Azure WI integration')
    parser.add_argument('-u', '--user-key', help="WS User Key", dest='ws_user_key', default=os.environ.get("WS_USERKEY"), required=True if not os.environ.get("WS_USERKEY") else False)
    parser.add_argument('-o', '--api-key', help="WS Org Key", dest='ws_org_token', default=os.environ.get("WS_TOKEN"), required=True if not os.environ.get("WS_TOKEN") else False)
    parser.add_argument('-l', '--url', help="WS Url", dest='ws_url', default=os.environ.get("WS_URL"),required=True if not os.environ.get("WS_URL") else False)
    parser.add_argument('-a', '--azureurl', help="Azure URL", dest='azure_url', default=os.environ.get("azure_URL", 'https://dev.azure.com/'))
    parser.add_argument('-ao', '--azureorg', help="Azure Org", dest='azure_org', default=os.environ.get("azure_org"),required=True)
    parser.add_argument('-ap', '--azurepat', help="Azure PAT", dest='azure_pat', required=True)
    parser.add_argument('-m', '--type', help="Modification Type", dest='m_type', default=os.environ.get("m_type", 'POLICY_MATCH'))
    parser.add_argument('-utc', '--utcdelta', help="UTC delta", dest='utc_delta', required=True)
    parser.add_argument('-apj', '--azureproject', help="Azure Prj", dest='azure_prj', required=True)
    parser.add_argument('-aa', '--azurearea', help="Azure Area", dest='azure_area', default="")
    parser.add_argument('-wp', '--wsproducttoken', help="WS Prd", dest='ws_prd', default="")
    parser.add_argument('-wpj', '--wsprojecttoken', help="WS Prj", dest='ws_prj',default="")
    parser.add_argument('-at', '--azuretype', help="Azure Type", dest='azure_type',default="Task")
    parser.add_argument('-cf', '--customfields', help="Custom Fields", dest='azure_custom',default="")
    parser.add_argument('-fr', '--reset', help="Get all data", dest='reset',default="No")
    arguments = parser.parse_args()

    return arguments


def main():
    args = parse_args()
    if os.path.exists(conf_file):
        config = ConfigParser()
        config.read(conf_file)
        config.set(section="DEFAULT", option="wsuserkey", value=args.ws_user_key)
        config.set(section="DEFAULT", option="apikey", value=args.ws_org_token)
        config.set(section="DEFAULT", option="wsurl", value=args.ws_url)
        config.set(section="DEFAULT", option="azureurl", value=args.azure_url)
        config.set(section="DEFAULT", option="azureorg", value=args.azure_org)
        config.set(section="DEFAULT", option="azurepat", value=args.azure_pat)
        mod_type = "" if args.m_type.lower() == "all" else args.m_type
        config.set(section="DEFAULT", option="modificationtypes", value=mod_type)
        config.set(section="DEFAULT", option="utcdelta", value=args.utc_delta)
        config.set(section="DEFAULT", option="azurearea", value=args.azure_area)
        config.set(section="DEFAULT", option="azuretype", value=args.azure_type)
        config.set(section="DEFAULT", option="reset", value=args.reset)

        config.set(section="links", option="azureproject", value=args.azure_prj)
        config.set(section="links", option="wsproducttoken", value=args.ws_prd)
        config.set(section="links", option="wsprojecttoken", value=args.ws_prj)

        with open(conf_file, 'w') as configfile:
            config.write(configfile)
    else:
        print(f"Configuration file ({conf_file}) not found")
    create_wi_json(wi_types,args)


def create_wi_json(file : str, args):
    def get_defval_from_custom(field_name : str):
        cstm_flds = args.azure_custom.split(";")
        res = ""
        for cstm_ in cstm_flds:
            key_val = cstm_.split("::")
            if key_val[0] == field_name:
                res = key_val[1]
                break
        return res

    def run_azure_api(api_type: str, api: str, data={}, version: str = "6.0", project: str = "", cmd_type: str = "?",
                      header: str = "application/json-patch+json"):
        errorcode = 0
        try:
            url = f"{args.azure_url}{args.azure_org}/_apis/{api}{cmd_type}api-version={version}" if project == "" else f"{args.azure_url}{args.azure_org}/{project}/_apis/{api}{cmd_type}api-version={version}"

            r = requests.get(url, json=data,
                             headers={'Content-Type': f'{header}'},
                             auth=('', args.azure_pat)) if api_type == "GET" else \
                requests.post(url, json=data,
                              headers={'Content-Type': f'{header}'},
                              auth=('', args.azure_pat))
            res = json.loads(r.text)
        except Exception as err:
            errorcode = 1
            res = {"Internal error": f"{err}"}

        return res, errorcode

    r, errcode = run_azure_api(api_type="GET", api="wit/workitemtypes/", project=args.azure_prj, data={},
                               version="7.0")
    res_conf = []
    if errcode == 0:
        for el_ in r["value"]:
            fields = []
            for el_fld_ in el_["fields"]:
                if "Custom." in el_fld_["referenceName"] or el_fld_["alwaysRequired"]:
                    def_val = get_defval_from_custom(el_fld_["referenceName"][7:]) if "Custom." in el_fld_["referenceName"] else el_fld_["defaultValue"]
                    fields.append(
                        {"referenceName": el_fld_["referenceName"],
                         "name": el_fld_["name"],
                         "defaultValue": def_val,
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


if __name__ == '__main__':
    main()
