import os
from configparser import ConfigParser
import argparse

conf_file = "./params.config"


def parse_args():
    parser = argparse.ArgumentParser(description='Utility to create params file for Azure WI integration')
    parser.add_argument('-u', '--userKey', help="WS User Key", dest='ws_user_key', default=os.environ.get("WS_USER_KEY"), required=True if not os.environ.get("WS_USER_KEY") else False)
    parser.add_argument('-o', '--token', help="WS Org Key", dest='ws_org_token', default=os.environ.get("WS_ORG_TOKEN"), required=True if not os.environ.get("WS_TOKEN") else False)
    parser.add_argument('-l', '--wsurl', help="WS Url", dest='ws_url', default=os.environ.get("WS_URL", 'https://saas.whitesourcesoftware.com'))
    parser.add_argument('-a', '--azureUrl', help="Azure URL", dest='azure_url', default=os.environ.get("azure_URL", 'https://dev.azure.com/'))
    parser.add_argument('-ao', '--azureorg', help="Azure Org", dest='azure_org', default=os.environ.get("azure_org"),required=True)
    parser.add_argument('-ap', '--azurepart', help="Azure PAT", dest='azure_pat', required=True)
    parser.add_argument('-m', '--type', help="Modification Type", dest='m_type', default=os.environ.get("m_type", 'POLICY_MATCH'))
    parser.add_argument('-utc', '--utcdelta', help="UTC delta", dest='utc_delta', required=True)
    parser.add_argument('-st', '--synctime', help="Sync Tyme", dest='sync_time', required=True)
    parser.add_argument('-sr', '--syncrun', help="Sync Run", dest='sync_run', default=True)
    parser.add_argument('-is', '--initialsync', help="Initial Sync", dest='initial_sync', default=False)
    parser.add_argument('-id', '--initialstartdate', help="Initial Start Date", dest='initial_start_date', required=True)
    parser.add_argument('-apj', '--azureproject', help="Azure Prj", dest='azure_prj', required=True)
    parser.add_argument('-wp', '--wsproducts', help="WS Prd", dest='ws_prd', default="")
    parser.add_argument('-wpj', '--wsprojects', help="WS Prj", dest='ws_prj',default="")
    arguments = parser.parse_args()

    return arguments


def main():
    args = parse_args()
    if os.path.exists(conf_file):
        config = ConfigParser()
        config.read(conf_file)
        config.set(section="DEFAULT", option="wsuserkey", value=args.ws_user_key)
        config.set(section="DEFAULT", option="wsorgtoken", value=args.ws_org_token)
        config.set(section="DEFAULT", option="wsurl", value=args.ws_url)
        config.set(section="DEFAULT", option="azureurl", value=args.azure_url)
        config.set(section="DEFAULT", option="azureorg", value=args.azure_org)
        config.set(section="DEFAULT", option="azurepat", value=args.azure_pat)
        config.set(section="DEFAULT", option="modificationtypes", value=args.m_type)
        config.set(section="DEFAULT", option="utcdelta", value=args.utc_delta)
        config.set(section="DEFAULT", option="synctime", value=args.sync_time)
        config.set(section="DEFAULT", option="syncrun", value=args.sync_run)
        config.set(section="DEFAULT", option="initialsync", value=args.initial_sync)
        config.set(section="DEFAULT", option="initialstartdate", value=args.initial_start_date)

        config.set(section="links", option="azureproject", value=args.azure_prj)
        config.set(section="links", option="wsproducts", value=args.ws_prd)
        config.set(section="links", option="wsprojects", value=args.ws_prj)

        with open(conf_file, 'w') as configfile:
            config.write(configfile)

if __name__ == '__main__':
    main()
