from dataclasses import dataclass

from ws_sdk import WS

conf_file = "./params.config"
__tool_name__ = "WI plugin"

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
    dry_run: bool
    ws_conn: WS
    sync_time : int
    utc_delta : int
    sync_run : bool
    last_run : str
    wsproducts : str
    wsprojects : str
    initial_sync : bool
    initialstartdate : str

    def conf_json(self):
        res = {
            "ws_user_key" : self.ws_user_key,
            "ws_org_token" : self.ws_org_token,
            "ws_url" : self.ws_url,
            "azure_url" : self.azure_url,
            "azure_org" : self.azure_org,
            "azure_project" : self.azure_project,
            "azure_pat" : self.azure_pat,
            "modification_types" : self.modification_types,
            "dry_run" : self.dry_run,
            "sync_time" : self.sync_time,
            "sync_run" : self.sync_run,
            "utc_delta" : self.utc_delta,
            "last_run" : self.last_run,
        }
        return res


def get_conf_value(c_p_val, alt_val):
    return c_p_val if c_p_val else alt_val
