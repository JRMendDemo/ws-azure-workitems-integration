from dataclasses import dataclass
import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from ws_sdk import WS

conf_file = "./local-params.config" if os.path.exists("./local-params.config") else "./params.config"
wi_types = "./local-workitem_types.json" if os.path.exists("./local-workitem_types.json") else "./workitem_types.json"

@dataclass
class Config:
    ws_user_key: str
    ws_org_token: str
    ws_url: str
    azure_url: str
    azure_org: str
    azure_project: str
    azure_pat: str
    modification_types: list
    ws_conn: WS
    utc_delta : int
    first_run : str
    wsproducttoken : str
    wsprojecttoken : str
    azure_area : str
    azure_type : str

    def conf_json(self):
        res = {
            "ws_user_key" : self.ws_user_key,
            "ws_org_token" : self.ws_org_token,
            "ws_url" : self.ws_url,
            "azure_url" : self.azure_url,
            "azure_org" : self.azure_org,
            "azure_project" : self.azure_project,
            "azure_pat" : self.azure_pat,
            "azure_area" : self.azure_area,
            "modification_types" : self.modification_types,
            "utc_delta" : self.utc_delta,
            "first_run" : self.last_run,
            "azure_type" : self.azure_type
        }
        return res


def get_conf_value(c_p_val, alt_val):
    return c_p_val if c_p_val else alt_val
