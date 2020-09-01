# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright 2019, GeoSolutions Sas.
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
#
#########################################################################

from six import string_types
from geoserver.support import ResourceInfo, build_url, xml_property

try:
    from past.builtins import basestring
except ImportError:
    pass


class Style(ResourceInfo):
    supported_formats = ["sld10", "sld11", "zip10", "css10"]
    content_types = {
        "sld10": "application/vnd.ogc.sld+xml",
        "sld11": "application/vnd.ogc.se+xml",
        "zip10": "application/zip",
        "css10": "application/vnd.geoserver.geocss+css",

    }

    def __init__(self, catalog, name, workspace=None, style_format="sld10"):
        super(Style, self).__init__()
        assert isinstance(name, string_types)
        assert style_format in Style.supported_formats

        self.catalog = catalog
        self.workspace = workspace
        self.name = name
        self.style_format = style_format
        self._sld_dom = None

    @property
    def fqn(self):
        if not self.workspace:
            return self.name
        return '{}:{}'.format(self.workspace, self.name)

    @property
    def href(self):
        return self._build_href('.xml')

    @property
    def body_href(self):
        return self._build_href('.sld')

    @property
    def create_href(self):
        return self._build_href('.xml', True)

    @property
    def content_type(self):
        return Style.content_types[self.style_format]

    def _build_href(self, extension, create=False):
        path_parts = ["styles"]
        query = {}
        if not create:
            path_parts.append(self.name + extension)
        else:
            query['name'] = self.name
        if self.workspace is not None:
            path_parts = ["workspaces", getattr(self.workspace, 'name', self.workspace)] + path_parts
        return build_url(self.catalog.service_url, path_parts, query)

    filename = xml_property("filename")

    def _get_sld_dom(self):
        if self._sld_dom is None:
            self._sld_dom = self.catalog.get_xml(self.body_href)
        return self._sld_dom

    @property
    def sld_title(self):
        user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}NamedLayer/{http://www.opengis.net/sld}UserStyle")
        if not user_style:
            user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}UserLayer/{http://www.opengis.net/sld}UserStyle")

        title_node = None
        if user_style:
            try:
                # it is not mandatory
                title_node = user_style.find("{http://www.opengis.net/sld}Title")
            except AttributeError:
                title_node = None

        return title_node.text if title_node is not None else None

    @property
    def sld_name(self):
        user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}NamedLayer/{http://www.opengis.net/sld}UserStyle")
        if not user_style:
            user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}UserLayer/{http://www.opengis.net/sld}UserStyle")

        name_node = None
        if user_style:
            try:
                # it is not mandatory
                name_node = user_style.find("{http://www.opengis.net/sld}Name")
            except AttributeError:
                name_node = None

        return name_node.text if name_node is not None else None

    @property
    def sld_body(self):
        resp = self.catalog.http_request(self.body_href)
        return resp.content

    @property
    def body(self):
        # [:-2] remove version tag from type. GeoServer does not accept it
        resp = self.catalog.http_request(self._build_href('.{}'.format(self.style_format[:-2])))
        return resp.content

    def update_body(self, body):
        headers = {"Content-Type": self.content_type}
        self.catalog.http_request(
            self.body_href, data=body, method='put', headers=headers)
