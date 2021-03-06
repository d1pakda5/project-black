from sqlalchemy import Integer, or_, and_

from black.db import (
    HostDatabase, IPDatabase, ScanDatabase, FileDatabase
)


def get_filter_clause(column, plist):
    '''Return a filter clause under given table column

    Keyword arguments:
    column -- sql tables' column filter is applied to
    plist -- list of patterns, ilike ['*foo*', '!*foo1*']
    '''
    positive_clause = []
    negative_clause = []

    for pattern in plist:
        if pattern:
            if isinstance(column.type, Integer):
                if pattern.startswith('!'):
                    pattern = pattern[1:]
                    negative_clause.append(column != int(pattern))
                else:
                    if pattern == '%':
                        positive_clause.append(column > 0)
                    else:
                        positive_clause.append(column == int(pattern))
            else:
                if pattern.startswith('!'):
                    pattern = pattern[1:]
                    if '%' in pattern:
                        negative_clause.append(~column.ilike(pattern.replace('*', '%')))
                    else:
                        negative_clause.append(column != pattern)
                else:
                    if '%' in pattern:
                        positive_clause.append(column.ilike(pattern.replace('*', '%')))
                    else:
                        positive_clause.append(column == pattern)

    return and_(and_(*negative_clause), or_(*positive_clause))


class Filters(object):
    def __init__(self, raw_filters):
        self.ips = True
        self.hosts = True

        self._construct_from_dict(raw_filters)

    def _construct_from_dict(self, filters):
        for key in filters.keys():
            filter_value = filters[key]

            if key == 'ip':
                self.ips = get_filter_clause(
                    IPDatabase.target, filter_value
                )
            elif key == 'host':
                self.hosts = get_filter_clause(
                    HostDatabase.target, filter_value
                )

    @staticmethod
    def build_scans_filters(filters, alias):
        parsed_filters = {}

        ports = filters.get('port', [])
        protocols = filters.get('protocol', [])
        banners = filters.get('banner', [])

        parsed_filters['ports'] = get_filter_clause(alias.port_number, ports)
        parsed_filters['protocols'] = get_filter_clause(alias.protocol, protocols)
        parsed_filters['banners'] = get_filter_clause(alias.banner, banners)
    
        filters_exist = (
            ports or
            protocols or
            banners
        )

        scans_clause = True

        if filters_exist:
            scans_clause = and_(
                parsed_filters['ports'],
                parsed_filters['protocols'],
                parsed_filters['banners']
            )

        return scans_clause

    @staticmethod
    def build_files_filters(filters, alias, project_uuid=None):
        files_filters = True        

        # If there are no filters, return
        if filters.get('files', None):
            files_filters = get_filter_clause(alias.status_code, filters.get('files', []))

        # if project_uuid:
        #     files_filters = and_(
        #         files_filters,
        #         get_filter_clause(alias.project_uuid, [str(project_uuid)])
        #     )

        return files_filters
