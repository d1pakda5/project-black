from functools import reduce
from sqlalchemy import func

from black.db import Sessions, DictDatabase


class DictManager(object):
    def __init__(self):
        self.sessions = Sessions()
        self.dicts = []

        self.fetch_dicts()

    def fetch_dicts(self):
        get_result = DictDatabase.get()

        if get_result["status"] == "success":
            self.dicts = list(map(lambda x: x.dict(), get_result["dicts"]))
        else:
            raise Exception(get_result)

    def count(self, project_uuid):
        return DictDatabase.count(project_uuid)

    def create(self, name, content, project_uuid):
        create_result = DictDatabase.create(name, content, project_uuid)

        if create_result["status"] == "success":
            self.dicts.append(create_result["dictionary"].dict())

        return create_result

    def get(self, project_uuid=None):
        return {
            "status": "success",
            "dicts": list(filter(
                lambda a: a["project_uuid"] == project_uuid,
                self.dicts
            ))
        }

    def delete(self, project_uuid, dict_id=None, name=None):
        return DictDatabase.delete(project_uuid, dict_id, name)