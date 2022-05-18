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

import abc
import datetime
import os.path
import struct
from dataclasses import dataclass, field
from typing import ByteString, Iterable, List


def c_source_array_bytes(binary: Iterable[int]) -> str:
    return (
        '\n'
        '    {\n'
        + ''.join(f'        0x{i:02X},\n' for i in binary)
        + '    }'
    )


class ConfigStruct(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def binformat(cls) -> str:
        pass

    @abc.abstractmethod
    def to_c_source(self, padding_value: int) -> str:
        pass

    @abc.abstractmethod
    def to_bytes(self, endianness: str, padding_value: int) -> bytes:
        pass

    @classmethod
    def from_bytes(cls, binary: ByteString) -> 'ConfigStruct':
        fields = struct.unpack(cls.binformat(), binary)
        return cls(*fields)

    @classmethod
    def from_bytes_many(cls,
                        binary: ByteString,
                        amount: int,
                        ) -> Iterable['ConfigStruct']:
        total_len = struct.calcsize(cls.binformat()) * amount
        return (cls(*fields) for fields
                in struct.iter_unpack(cls.binformat(), binary[:total_len]))


@dataclass
class ClientConfig(ConfigStruct):
    timeout_req_to_res_millis: int
    ltk: bytes
    sid: int
    header_type: int
    amount_of_groups: int

    @classmethod
    def binformat(cls) -> str:
        return 'H16sBBB1s'

    def to_bytes(self, endianness: str, padding_value: int) -> bytes:
        assert struct.calcsize(self.binformat()) == 22
        return struct.pack(
            endianness + self.binformat(),
            self.timeout_req_to_res_millis,
            self.ltk,
            self.sid,
            self.header_type,
            self.amount_of_groups,
            bytes([padding_value]),
        )

    def to_c_source(self, padding_value: int) -> str:
        return \
            f"""{{
    .timeoutReqToResMillis = {self.timeout_req_to_res_millis},
    .ltk = {c_source_array_bytes(self.ltk)},
    .sid = {self.sid},
    .headerType = {self.header_type},
    .amountOfGroups = {self.amount_of_groups},
    .unusedPadding = {c_source_array_bytes([padding_value])},
}}"""


@dataclass
class ClientGroupConfig(ConfigStruct):
    max_ctrnonce_delay: int
    max_silence_interval_millis: int
    session_renewal_duration_millis: int
    gid: int

    @classmethod
    def binformat(cls) -> str:
        return 'IHHB3s'

    def to_bytes(self, endianness: str, padding_value: int) -> bytes:
        assert struct.calcsize(self.binformat()) == 12
        return struct.pack(
            endianness + self.binformat(),
            self.max_ctrnonce_delay,
            self.max_silence_interval_millis,
            self.session_renewal_duration_millis,
            self.gid,
            bytes([padding_value] * 3),
        )

    def to_c_source(self, padding_value: int) -> str:
        return \
            f"""{{
    .maxCtrnonceDelayMsgs = {self.max_ctrnonce_delay},
    .maxSilenceIntervalMillis = {self.max_silence_interval_millis},
    .sessionRenewalDurationMillis = {self.session_renewal_duration_millis},
    .gid = {self.gid},
    .unusedPadding = {c_source_array_bytes([padding_value] * 3)},
}}"""


@dataclass
class Client:
    nickname: str
    config: ClientConfig
    groups: List[ClientGroupConfig] = field(default_factory=list)

    def to_c_source(self, padding_value: int) -> str:
        template_file_name = os.path.join(
            os.path.dirname(__file__),
            'client_c_template.c',
        )
        with open(template_file_name, encoding='UTF-8') as template:
            return template.read().format(
                year=current_year(),
                timestamp=iso_timestamp_with_utc_tz(),
                client_name=self.nickname,
                amount_of_groups=len(self.groups),
                client_config=self.config.to_c_source(padding_value),
                group_configs=',\n'.join(g.to_c_source(padding_value)
                                         for g in self.groups),
            )


@dataclass
class ServerSideClientConfig(ConfigStruct):
    sid: int
    ltk: bytes

    @classmethod
    def binformat(cls) -> str:
        return 'B16s'

    def to_bytes(self, endianness: str, padding_value: int) -> bytes:
        assert struct.calcsize(self.binformat()) == 17
        return struct.pack(
            endianness + self.binformat(),
            self.sid,
            self.ltk,
        )

    def to_c_source(self, padding_value: int) -> str:
        return \
            f"""{{
    .sid = {self.sid},
    .ltk = {c_source_array_bytes(self.ltk)},
}}"""


@dataclass
class ServerGroupConfig(ConfigStruct):
    max_ctrnonce_delay: int
    ctrnonce_upper_limit: int
    session_duration_millis: int
    delay_between_ren_notifications_millis: int
    client_sids_in_group_bitmap: int
    max_silence_interval_millis: int
    gid: int

    @classmethod
    def binformat(cls) -> str:
        return 'IIIIIHB1s'

    def to_bytes(self, endianness: str, padding_value: int) -> bytes:
        assert struct.calcsize(self.binformat()) == 24
        return struct.pack(
            endianness + self.binformat(),
            self.max_ctrnonce_delay,
            self.ctrnonce_upper_limit,
            self.session_duration_millis,
            self.delay_between_ren_notifications_millis,
            self.client_sids_in_group_bitmap,
            self.max_silence_interval_millis,
            self.gid,
            bytes([padding_value]),
        )

    def to_c_source(self, padding_value: int) -> str:
        return \
            f"""{{
    .maxCtrnonceDelayMsgs = {self.max_ctrnonce_delay},
    .ctrNonceUpperLimit = 0x{self.ctrnonce_upper_limit:06X},
    .sessionDurationMillis = {self.session_duration_millis},
    .delayBetweenRenNotificationsMillis = {
            self.delay_between_ren_notifications_millis},
    .clientSidsInGroupBitmap = 0x{self.client_sids_in_group_bitmap:08X},
    .maxSilenceIntervalMillis = {self.max_silence_interval_millis},
    .gid = {self.gid},
    .unusedPadding = {c_source_array_bytes([padding_value])},
}}"""


@dataclass
class ServerConfig(ConfigStruct):
    header_type: int
    amount_of_groups: int
    amount_of_clients: int

    @classmethod
    def binformat(cls) -> str:
        return 'BBB'

    def to_bytes(self, endianness: str, padding_value: int) -> bytes:
        assert struct.calcsize(self.binformat()) == 3
        return struct.pack(
            endianness + self.binformat(),
            self.amount_of_groups,
            self.amount_of_clients,
            self.header_type,
        )

    def to_c_source(self, padding_value: int) -> str:
        return \
            f"""{{
    .amountOfGroups = {self.amount_of_groups},
    .amountOfClients = {self.amount_of_clients},
    .headerType = {self.header_type},
}}"""


@dataclass
class Server:
    config: ServerConfig
    clients: List[ServerSideClientConfig] = field(default_factory=list)
    groups: List[ServerGroupConfig] = field(default_factory=list)
    nickname: str = 'Server'

    def to_c_source(self, padding_value: int) -> str:
        template_file_name = os.path.join(
            os.path.dirname(__file__),
            'server_c_template.c',
        )
        with open(template_file_name, encoding='UTF-8') as template:
            return template.read().format(
                year=current_year(),
                timestamp=iso_timestamp_with_utc_tz(),
                client_name=self.nickname,
                amount_of_clients=len(self.clients),
                amount_of_groups=len(self.groups),
                server_config=self.config.to_c_source(padding_value),
                client_configs=',\n'.join(c.to_c_source(padding_value)
                                          for c in self.clients),
                group_configs=',\n'.join(g.to_c_source(padding_value)
                                         for g in self.groups),
            )


def iso_timestamp_with_utc_tz() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def current_year() -> int:
    return datetime.datetime.now(datetime.timezone.utc).year
