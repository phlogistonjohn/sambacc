"""A more pythonic wrapper for samba's smbconf
"""

from itertools import groupby
import os
import typing

import samba.samba3.param  # type: ignore
import samba.samba3.smbconf  # type: ignore
import samba.smbconf  # type: ignore


S = typing.TypeVar("S", bound="SMBConf")
ST = typing.Type[S]
optlist = list[tuple[str, str]]
opts = typing.Union[
    typing.Iterable[tuple[str, str]],
    dict[str, str],
]


def _options(v: opts) -> optlist:
    if isinstance(v, dict):
        return list(v.items())
    return list(v)


class SMBConf:
    def __init__(self, smbconf) -> None:
        self._smbconf = smbconf

    @classmethod
    def from_file(cls: ST, path: str) -> S:
        return cls(samba.smbconf.init_txt(path))

    @classmethod
    def from_registry(
        cls: ST,
        key: typing.Optional[str] = None,
        configfile: typing.Optional[str] = None,
    ) -> S:
        # TODO: is initializing the s3 configuration here the right
        # place to do it??
        if configfile is None:
            configfile = os.environ.get("SMB_CONF", "/etc/samba/smb.conf")
        s3_lp = samba.samba3.param.get_context()
        s3_lp.load(configfile)

        return cls(samba.samba3.smbconf.init_reg(key))

    @classmethod
    def from_prefix(cls: ST, path: str) -> S:
        return cls(samba.samba3.smbconf.init(path))

    def __enter__(self) -> None:
        """Start a transaction."""
        self._smbconf.transaction_start()

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            self._smbconf.transaction_commit()
            return
        self._smbconf.transaction_cancel()

    def get_share(self, name: str) -> tuple[str, optlist]:
        return self._smbconf.get_share(name)

    def share_names(self) -> list[str]:
        return self._smbconf.share_names()

    def all_shares(self) -> list[tuple[str, optlist]]:
        return self._smbconf.get_config()

    def delete_share(self, name: str) -> None:
        return self._smbconf.delete_share(name)

    def create_share(
        self,
        name: str,
        params: typing.Optional[opts] = None,
    ) -> None:
        if params is None:
            self._smbconf.create_share(name)
        else:
            self._smbconf.create_set_share(name, _options(params))

    # support some basic dict-like methods

    def __getitem__(self, name: str) -> optlist:
        return self.get_share(name)[1]

    def __setitem__(self, name: str, value: opts) -> None:
        try:
            self.delete_share(name)
        except samba.smbconf.SMBConfError as err:
            if err.error_code != samba.smbconf.SBC_ERR_NO_SUCH_SERVICE:
                raise
        self.create_share(name, value)

    def __iter__(self) -> typing.Iterable[str]:
        return iter(self.share_names())

    # configuration import funcs

    def import_smbconf_all(self, src: S) -> None:
        with self:
            for sname, params in src.all_shares():
                self[sname] = params

    def import_smbconf_batched(self, src: S, batch_size: int) -> None:
        # based on a comment in samba's source code for the net command
        # only import N items at a time so that the transaction does
        # not exceed talloc memory limits
        def _batchkf(item):
            return item[0] // batch_size

        for _, services in groupby(enumerate(src.all_shares()), _batchkf):
            with self:
                for _, (sname, params) in services:
                    self[sname] = params

    def import_smbconf(self, src: S, batch_size: int = 100) -> None:
        if batch_size is None:
            return self.import_smbconf_all(src)
        return self.import_smbconf_batched(src, batch_size)


def import_smb_conf(smb_conf_src: str) -> None:
    """Behaves much like `net conf import`."""
    conf_source: SMBConf = SMBConf.from_file(smb_conf_src)
    conf_sink: SMBConf = SMBConf.from_registry()
    conf_sink.import_smbconf(conf_source)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("SOURCE")
    cli = parser.parse_args()

    import_smb_conf(cli.SOURCE)


if __name__ == "__main__":
    main()
