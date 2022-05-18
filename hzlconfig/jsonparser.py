#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2020-2022, Matjaž Guštin <dev@matjaz.it>
# <https://matjaz.it>. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of nor the names of its contributors may be used to
#    endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
from typing import Dict, List, Union

TypeJsonDict = Dict[
    str, Union[bool, int, bytes, List, None, str, 'TypeJsonDict']]


class JsonConfigParser:
    def __init__(self, input_file_name: str):
        with open(input_file_name, encoding='UTF-8') as json_file:
            config = json.loads(json_file.read())
        self.clients: List[TypeJsonDict] = config['clients']
        self.groups: List[TypeJsonDict] = config['groups']
        self.bus: TypeJsonDict = config['bus']
        self.defaults: TypeJsonDict = config['defaults']

        # Initialisation
        self._check_clients()
        self._check_groups()
        self._inject_defaults_into_clients()
        self._inject_defaults_into_groups()
        self._sort_clients_by_sid()
        self._sort_groups_by_gid()
        self._add_clients_bitmap_to_groups()
        self._convert_ltks_to_bytes()

    def _check_clients(self):
        assert len(self.clients) > 0
        assert (self.clients[0]['sid'] == 1)
        assert (self.clients[-1]['sid'] == len(self.clients))
        # Check that each client has a unique nickname, case insensitive.
        nicknames = [client['nickname'].lower() for client in self.clients]
        unique_nicknames = set(nicknames)
        assert len(nicknames) == len(unique_nicknames)

    def _check_groups(self):
        assert len(self.groups) > 0
        assert (self.groups[0]['gid'] == 0)
        assert (self.groups[-1]['gid'] == len(self.groups) - 1)
        for group in self.groups[1:]:
            bitmap = 0
            for sid in group['clients']:
                bitmap |= 1 << (sid - 1)
            group['clientSidsInGroupBitmap'] = bitmap

    def _inject_defaults_into_clients(self):
        for client in self.clients:
            self._extend_dict_no_overwrite(client, self.bus)
            self._extend_dict_no_overwrite(client, self.defaults)

    def _inject_defaults_into_groups(self):
        for group in self.groups:
            self._extend_dict_no_overwrite(group, self.defaults)

    def _sort_clients_by_sid(self):
        self.clients.sort(key=lambda client: client['sid'])

    def _sort_groups_by_gid(self):
        self.groups.sort(key=lambda groups: groups['gid'])

    def _add_clients_bitmap_to_groups(self):
        self.groups[0]['clientSidsInGroupBitmap'] = 0xFFFFFFFF  # Broadcast
        self.groups[0]['clients'] = list(
            client['sid'] for client in self.clients)
        for group in self.groups[1:]:
            bitmap = 0
            for sid in group['clients']:
                bitmap |= 1 << (sid - 1)
                assert (1 <= sid <= len(self.clients))
            group['clientSidsInGroupBitmap'] = bitmap

    def _convert_ltks_to_bytes(self):
        for client in self.clients:
            client['ltk'] = bytes.fromhex(client['ltk'])
            assert (len(client['ltk']) == 16)

    @staticmethod
    def _extend_dict_no_overwrite(original: TypeJsonDict,
                                  extension: TypeJsonDict):
        for k, v in extension.items():
            if k not in original:
                original[k] = v


def ltk_from_string(ltk: str) -> bytes:
    ltk = bytes.fromhex(ltk)
    assert len(ltk) == 16
    return ltk
