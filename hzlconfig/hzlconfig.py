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

"""Compiles the Hazelnet configuration from a JSON file into binary files
for each Client and the Server that could be parsed easily by the DLLs."""

import os
from dataclasses import dataclass, field
from typing import List

from . import structs, jsonparser

MAGIC_NUMBER_CLIENT = b'HZLc\0'
MAGIC_NUMBER_SERVER = b'HZLs\0'


@dataclass
class Config:
    server: structs.Server
    clients: List[structs.Client] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, input_file_name: str) -> 'Config':
        dictionaries = jsonparser.JsonConfigParser(input_file_name)
        clients = []
        for client in dictionaries.clients:
            groups_this_client_is_in = [
                group for group in dictionaries.groups
                if client['sid'] in group['clients']
            ]
            client_config = structs.ClientConfig(
                timeout_req_to_res_millis=client[
                    'timeoutReqToResMillis'],
                ltk=client['ltk'],
                sid=client['sid'],
                header_type=dictionaries.bus['headerType'],
                amount_of_groups=len(groups_this_client_is_in),
            )
            client_group_configs = [
                structs.ClientGroupConfig(
                    max_ctrnonce_delay=group['maxCtrnonceDelayMsgs'],
                    max_silence_interval_millis=group[
                        'maxSilenceIntervalMillis'],
                    session_renewal_duration_millis=group[
                        'sessionRenewalDurationMillis'],
                    gid=group['gid'],
                )
                for group in groups_this_client_is_in
            ]
            new_client = structs.Client(
                nickname=client['nickname'],
                config=client_config,
                groups=client_group_configs,
            )
            clients.append(new_client)
        server_config = structs.ServerConfig(
            header_type=dictionaries.bus['headerType'],
            amount_of_groups=len(dictionaries.groups),
            amount_of_clients=len(dictionaries.clients),
        )
        server_side_client_configs = [
            structs.ServerSideClientConfig(
                sid=client['sid'],
                ltk=client['ltk'],
            )
            for client in dictionaries.clients
        ]
        server_group_configs = [
            structs.ServerGroupConfig(
                max_ctrnonce_delay=group['maxCtrnonceDelayMsgs'],
                ctrnonce_upper_limit=group['ctrNonceUpperLimit'],
                session_duration_millis=group['sessionDurationMillis'],
                delay_between_ren_notifications_millis=group[
                    'delayBetweenRenNotificationsMillis'],
                client_sids_in_group_bitmap=group['clientSidsInGroupBitmap'],
                max_silence_interval_millis=group['maxSilenceIntervalMillis'],
                gid=group['gid'],
            )
            for group in dictionaries.groups
        ]
        server = structs.Server(
            config=server_config,
            clients=server_side_client_configs,
            groups=server_group_configs,
        )
        return Config(
            server=server,
            clients=clients,
        )

    def to_binary_files(self, output_dir_name: str,
                        endianness: str,
                        padding_value: int) -> None:
        os.makedirs(output_dir_name, exist_ok=True)
        self._clients_to_binary_file(output_dir_name, endianness,
                                     padding_value)
        self._server_to_binary_file(output_dir_name, endianness, padding_value)

    def _clients_to_binary_file(self, output_dir_name: str,
                                endianness: str,
                                padding_value: int) -> None:
        for client in self.clients:
            out_file_name = os.path.join(
                output_dir_name,
                f'hzl_HardcodedConfig{client.nickname}.hzl'
            )
            with open(out_file_name, 'bw+') as client_bin_file:
                client_bin_file.write(MAGIC_NUMBER_CLIENT)
                client_bin_file.write(client.config.to_bytes(endianness,
                                                             padding_value))
                for group in client.groups:
                    client_bin_file.write(group.to_bytes(endianness,
                                                         padding_value))

    def _server_to_binary_file(self, output_dir_name: str,
                               endianness: str,
                               padding_value: int) -> None:
        out_file_name = os.path.join(
            output_dir_name,
            f'hzl_HardcodedConfig{self.server.nickname}.hzl'
        )
        with open(out_file_name, 'bw+') as server_bin_file:
            server_bin_file.write(MAGIC_NUMBER_SERVER)
            server_bin_file.write(self.server.config.to_bytes(endianness,
                                                              padding_value))
            for client in self.server.clients:
                server_bin_file.write(client.to_bytes(endianness,
                                                      padding_value))
            for group in self.server.groups:
                server_bin_file.write(group.to_bytes(endianness,
                                                     padding_value))

    def to_c_source_files(self, output_dir_name: str,
                          padding_value: int) -> None:
        os.makedirs(output_dir_name, exist_ok=True)
        self._write_server_to_c_source_file(output_dir_name, padding_value)
        self._write_clients_to_c_source_files(output_dir_name, padding_value)
        self._write_server_header_file(output_dir_name)
        self._write_client_c_header_file(output_dir_name)

    def _write_server_to_c_source_file(self, output_dir_name: str,
                                       padding_value: int):
        out_file_name = os.path.join(
            output_dir_name,
            f'hzl_HardcodedConfig{self.server.nickname}.c'
        )
        with open(out_file_name, 'w', encoding='UTF-8') as server_c_file:
            server_c_file.write(self.server.to_c_source(padding_value))

    def _write_clients_to_c_source_files(self, output_dir_name: str,
                                         padding_value: int):
        for client in self.clients:
            out_file_name = os.path.join(
                output_dir_name,
                f'hzl_HardcodedConfig{client.nickname}.c'
            )
            with open(out_file_name, 'w', encoding='UTF-8') as client_c_file:
                client_c_file.write(client.to_c_source(padding_value))

    def _write_server_header_file(self, output_dir_name):
        out_file_name = os.path.join(
            output_dir_name,
            f'hzl_HardcodedConfigServer.h'
        )
        template_file_name = os.path.join(
            os.path.dirname(__file__),
            'server_h_template.h',
        )
        with open(out_file_name, 'w', encoding='UTF-8') as client_h_file, \
            open(template_file_name, encoding='UTF-8') as template:
            formatted = template.read().format(
                year=structs.current_year(),
                timestamp=structs.iso_timestamp_with_utc_tz())
            client_h_file.write(formatted)

    def _write_client_c_header_file(self, output_dir_name):
        out_file_name = os.path.join(
            output_dir_name,
            f'hzl_HardcodedConfigClient.h'
        )
        template_file_name = os.path.join(
            os.path.dirname(__file__),
            'client_h_template.h',
        )
        with open(out_file_name, 'w', encoding='UTF-8') as client_h_file, \
            open(template_file_name, encoding='UTF-8') as template:
            formatted = template.read().format(
                year=structs.current_year(),
                timestamp=structs.iso_timestamp_with_utc_tz())
            client_h_file.write(formatted)


def compile_json_file(json_file_name: str,
                      output_dir_name: str = 'generated',
                      endianness: str = '<',
                      padding_value: int = 0xAA):
    hzl_config = Config.from_json_file(json_file_name)
    output_dir_name = os.path.join(
        os.path.dirname(os.path.abspath(json_file_name)),
        output_dir_name)
    hzl_config.to_binary_files(output_dir_name, endianness, padding_value)
    hzl_config.to_c_source_files(output_dir_name, padding_value)
    print(f'Compiled into {output_dir_name}')
