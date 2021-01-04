# Do the samba python bindings not export any useful constants?
ACB_DISABLED = 0x00000001
ACB_NORMAL = 0x00000010
ACB_PWNOEXP = 0x00000200


def _samba_modules():
    from samba.samba3 import param
    from samba.samba3 import passdb

    return param, passdb


class PassDBLoader:
    def __init__(self, smbconf=None):
        param, passdb = _samba_modules()
        lp = param.get_context()
        if smbconf is None:
            lp.load_default()
        else:
            lp.load(smbconf)
        passdb.set_secrets_dir(lp.get("private dir"))
        self._pdb = passdb.PDB(lp.get("passdb backend"))
        self._passdb = passdb

    def add_user(self, user_entry):
        if not (user_entry.nt_passwd or user_entry.plaintext_passwd):
            raise ValueError(
                f"user entry {user_entry.username} lacks password value"
            )
        # probe for an existing user, by name
        try:
            samu = self._pdb.getsampwnam(user_entry.username)
        except self._passdb.error:
            samu = None
        # if it doesn't exist, create it
        if samu is None:
            # FIXME, research if there are better flag values to use
            acb = ACB_NORMAL | ACB_PWNOEXP
            self._pdb.create_user(user_entry.username, acb)
            samu = self._pdb.getsampwnam(user_entry.username)
        acb = samu.acct_ctrl
        # update password/metadata
        if user_entry.nt_passwd:
            samu.nt_passwd = user_entry.nt_passwd
        elif user_entry.plaintext_passwd:
            samu.plaintext_passwd = user_entry.plaintext_passwd
        # Try to mimic the behavior of smbpasswd and clear the account disabled
        # flag when adding or updating the user.
        # We don't expect granular, on the fly, user management in the
        # container, so it seems pointless to have a user that can't log in.
        if acb & ACB_DISABLED:
            samu.acct_ctrl = acb & ~ACB_DISABLED
        # update the db
        self._pdb.update_sam_account(samu)
