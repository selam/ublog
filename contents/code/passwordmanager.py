#-*- coding: utf-8 -*-
"""
This file is part of UBlog.

UBlog is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

UBlog is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with UBlog.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyKDE4.kdeui import KWallet


class PasswordManager(object):

    FOLDER_NAME = "ublog"

    def __init__(self, window_id=0):
        self.wallet = None
	self.window_id = window_id

    def __open_wallet(self):
        if self.wallet is not None:
            return True

        self.wallet = KWallet.Wallet.openWallet(KWallet.Wallet.NetworkWallet(), self.window_id)

        if self.wallet:
            if not self.wallet.setFolder(PasswordManager.FOLDER_NAME):
                self.wallet.createFolder(PasswordManager.FOLDER_NAME)
                self.wallet.setFolder(PasswordManager.FOLDER_NAME)
            return True
        return False

    def __getattr__(self, item, *args):
        if self.__open_wallet():
            return getattr(self.wallet, item, *args)
