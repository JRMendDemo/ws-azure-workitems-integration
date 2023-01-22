import os
from configparser import ConfigParser
import argparse

conf_file = "./local-params.config" if os.path.exists("./local-params.config") else "./params.config"


def parse_args():
    parser = argparse.ArgumentParser(description='Utility to create params file for Azure WI integration')
    parser.add_argument('-u', '--userKey', help="WS User Key", dest='ws_user_key', default=os.environ.get("WS_USERKEY"), required=True if not os.environ.get("WS_USERKEY") else False)
    parser.add_argument('-o', '--apiKey', help="WS Org Key", dest='ws_org_token', default=os.environ.get("WS_TOKEN"), required=True if not os.environ.get("WS_TOKEN") else False)
    parser.add_argument('-l', '--wsurl', help="WS Url", dest='ws_url', default=os.environ.get("WS_URL"),required=True if not os.environ.get("WS_URL") else False)
    parser.add_argument('-a', '--azureUrl', help="Azure URL", dest='azure_url', default=os.environ.get("azure_URL", 'https://dev.azure.com/'))
    parser.add_argument('-ao', '--azureorg', help="Azure Org", dest='azure_org', default=os.environ.get("azure_org"),required=True)
    parser.add_argument('-ap', '--azurepat', help="Azure PAT", dest='azure_pat', required=True)
    parser.add_argument('-m', '--type', help="Modification Type", dest='m_type', default=os.environ.get("m_type", 'POLICY_MATCH'))
    parser.add_argument('-utc', '--utcdelta', help="UTC delta", dest='utc_delta', required=True)
    parser.add_argument('-apj', '--azureproject', help="Azure Prj", dest='azure_prj', required=True)
    parser.add_argument('-aa', '--azurearea', help="Azure Area", dest='azure_area', default="")
    parser.add_argument('-wp', '--wsproducttoken', help="WS Prd", dest='ws_prd', default="")
    parser.add_argument('-wpj', '--wsprojecttoken', help="WS Prj", dest='ws_prj',default="")
    parser.add_argument('-at', '--azuretype', help="Azure Type (WI or Bug)", dest='azure_type',default="wi")
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

        config.set(section="links", option="azureproject", value=args.azure_prj)
        config.set(section="links", option="wsproducts", value=args.ws_prd)
        config.set(section="links", option="wsprojects", value=args.ws_prj)

        with open(conf_file, 'w') as configfile:
            config.write(configfile)
    else:
        print("Configuration file (local-params.config) not found")

if __name__ == '__main__':
    main()
