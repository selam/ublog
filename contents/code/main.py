# -*- coding: utf-8 -*-
# Copyright stuff
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
from PyKDE4 import plasmascript
from PyKDE4.kdeui import KIcon
from PyKDE4.kdeui import KColorScheme
from PyKDE4.kdeui import KTextEdit
from PyKDE4.kdeui import KInputDialog, KTabBar
from PyKDE4.kdecore import KToolInvocation

from PyKDE4.plasma import Plasma
from PyQt4 import uic
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import Qt, SIGNAL, QEvent
from PyQt4.QtGui import QGraphicsLinearLayout
from PyQt4.QtGui import QGraphicsAnchorLayout
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QFontMetrics
from PyQt4.QtGui import QSizePolicy
from PyQt4.QtGui import QPalette
from PyQt4.QtGui import QGraphicsWidget
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QKeyEvent
import oauth2 as oauth
import urlparse
import json
from passwordmanager import PasswordManager
from tweet_widget import TweetWidget

CONSUMER_KEY = "dzwpeW3qkQt4pK0ZhIsEg"
CONSUMER_SECRET = "WOz5d71KyyBsByqUn4om5bEyrrEFI0mBVdqJaMOUJg8"


class UBlogApplet(plasmascript.Applet):

    def __init__(self, parent, **kwargs):
        plasmascript.Applet.__init__(self, parent)
        self._layout = None
        self.flash = None
        self.tab_bar = None
        self.ui = None
        self.status_edit = None
        self.scroll_widget = None
        self.tweets_layout = None
        self.main_frame = None
        self.pm = PasswordManager()
        self.consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
        self.client = oauth.Client(self.consumer)
        self.icon = None
        self.oauth_secret = None
        self.oauth_key = None
        self.history_size = 10
        self.timer = QTimer(self)
        self.history_refresh = 1
        self.tweets_widget = None
        self.message_id = None

    def init(self):
        """
        create interface, this method invoked by plasma it self
        """
        self.setHasConfigurationInterface(True)
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.setBackgroundHints(Plasma.Applet.DefaultBackground)

        #
        self.flash = Plasma.FlashingLabel(self.applet)
        self.flash.setAutohide(True)
        self.flash.setMinimumSize(0, 20)
        self.flash.setDuration(2000)
        self.tab_bar = Plasma.TabBar()

        self._layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self._layout.setSpacing(3)

        flash_layout = QGraphicsLinearLayout(Qt.Horizontal)
        flash_layout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        fnt = Plasma.Theme.defaultTheme().font(Plasma.Theme.DefaultFont)
        fnt.setBold(True)
        fm = QFontMetrics(fnt)

        self.flash.setFont(fnt)
        self.flash.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        title_layout = QGraphicsLinearLayout(Qt.Vertical)

        flash_layout.addItem(self.flash)
        flash_layout.addItem(title_layout)

        self.main_frame = Plasma.Frame(self.applet)
        m_header_layout = QGraphicsAnchorLayout(self.main_frame)
        m_header_layout.setSpacing(5)

        self.icon = Plasma.IconWidget(self.main_frame)
        self.icon.setIcon(KIcon("user-identity"))
        self.icon.setTextBackgroundColor(QColor())
        icon_size = self.icon.sizeFromIconSize(48)
        self.icon.setMinimumSize(icon_size)
        self.icon.setMaximumSize(icon_size)

        m_header_layout.addAnchor(self.icon, Qt.AnchorVerticalCenter, m_header_layout, Qt.AnchorVerticalCenter)
        m_header_layout.addAnchor(self.icon, Qt.AnchorLeft, m_header_layout, Qt.AnchorLeft)

        status_edit_frame = Plasma.Frame(self.main_frame)
        status_edit_frame.setFrameShadow(Plasma.Frame.Sunken)
        status_edit_layout = QGraphicsLinearLayout(status_edit_frame)
        self.status_edit = Plasma.TextEdit()
        self.status_edit.setPreferredHeight(fm.height() * 4)
        self.status_edit.setEnabled(False)
        status_edit_layout.addItem(self.status_edit)

        edit_pal = self.status_edit.palette()
        m_color_scheme = KColorScheme(QPalette.Active, KColorScheme.View, Plasma.Theme.defaultTheme().colorScheme())
        edit_pal.setColor(QPalette.Text, m_color_scheme.foreground().color())
        self.status_edit.nativeWidget().setPalette(edit_pal)
        self.status_edit.nativeWidget().installEventFilter(self)
        m_header_layout.addAnchor(self.icon, Qt.AnchorRight, status_edit_frame, Qt.AnchorLeft)
        m_header_layout.addAnchors(status_edit_frame, m_header_layout, Qt.Vertical)
        m_header_layout.addAnchor(status_edit_frame, Qt.AnchorRight, m_header_layout, Qt.AnchorRight)
        m_header_layout.activate()
        m_header_layout.setMaximumHeight(m_header_layout.effectiveSizeHint(Qt.PreferredSize).height())

        self.scroll_widget = Plasma.ScrollWidget(self.applet)
        self.tweets_widget = QGraphicsWidget(self.scroll_widget)
        self.scroll_widget.setWidget(self.tweets_widget)
        self.tweets_layout = QGraphicsLinearLayout(Qt.Vertical, self.tweets_widget)
        self.tweets_layout.setSpacing(3)
        self.tweets_layout.addItem(self.main_frame)

        self.tab_bar.addTab(self.trUtf8("Timeline"))
        self.tab_bar.addTab(self.trUtf8("Replies"))
        self.tab_bar.addTab(self.trUtf8("Messages"))

        self._layout.addItem(flash_layout)
        self._layout.addItem(self.tab_bar)
        self._layout.addItem(self.scroll_widget)

        self.applet.setLayout(self._layout)
        self.connect(self.tab_bar, SIGNAL('currentChanged(int)'), self.mode_changed)
        self.connect(self.status_edit, SIGNAL('textChanged()'), self.edit_text_changed)
        self.check_config()

    def check_config(self):
        self.oauth_secret = unicode(self.pm.readPassword("twitter_secret")[1])
        self.oauth_key = unicode(self.pm.readPassword("twitter_token")[1])
        self.history_size = int(self.pm.readEntry("historySize")[1])
        self.history_refresh = int(self.pm.readEntry("historyRefresh")[1])

        if self.history_size == '':
            self.history_size = 10

        if self.history_refresh is None or self.history_refresh == '':
            self.history_refresh = 5

        if self.oauth_key == '' or self.oauth_secret == '':
            self.authenticate()
        else:
            self.status_edit.setEnabled(True)
            self.connect(self.timer, SIGNAL('timeout()'), self.update)
            self.update()
            self.timer.start(self.history_refresh * 60 * 1000)

    def edit_text_changed(self):
        remaining_char = 140 - self.status_edit.nativeWidget().toPlainText().length()
        self.flash.flash(unicode(self.trUtf8("%s character left", "%s character left")) % remaining_char, 2000)

    def createConfigurationInterface(self, dialog):
        """
            create configuration settings for user parameters
        """
        self.connect(dialog, SIGNAL('applyClicked()'), self.config_accepted)
        self.connect(dialog, SIGNAL('okClicked()'), self.config_accepted)
        widget = QWidget(dialog)
        self.ui = uic.loadUi(self.package().filePath('ui', 'configuration.ui'), widget)
        history_size = self.pm.readEntry("historySize")[1]
        history_refresh = self.pm.readEntry("historyRefresh")[1]
        if history_size:
            self.ui.historySizeSpinBox.setValue(int(str(history_size)))
        if history_refresh:
            self.ui.historyRefreshSpinBox.setValue(int(str(history_refresh)))
        dialog.addPage(widget, self.trUtf8("General"), "view-pim-journal")

    def config_accepted(self):
        """
            we must update timer object after these settings changed
        """
        self.pm.writeEntry("historyRefresh", str(self.ui.historyRefreshSpinBox.value()))
        self.pm.writeEntry("historySize", str(self.ui.historySizeSpinBox.value()))
        self.history_size = str(self.ui.historyRefreshSpinBox.value())
        self.history_refresh = int(self.ui.historySizeSpinBox.value())

        self.status_edit.setEnabled(True)
        self.timer.stop()
        self.timer.start(self.history_refresh * 60 * 1000)
        self.update()

    def mode_changed(self):
        self.flash.flash(self.trUtf8("Refreshing timeline..."))
        self.timer.stop()
        self.update()
        self.timer.start(int(self.history_refresh) * 60 * 1000)

    def update(self):
        self.flash.flash(self.trUtf8("Refreshing timeline..."))
        current_idx = self.tab_bar.currentIndex()
        if current_idx == 0:
            self.__update_timeline()
        elif current_idx == 1:
            self.__update_replies()
        else:
            self.__update_messages()

    def __make_rest_calls(self, url, user=True):
        token = oauth.Token(self.oauth_key, self.oauth_secret)
        client = oauth.Client(self.consumer, token=token)
        resp, content = client.request(url+"?count="+str(self.history_size))
        self.tweets_widget.prepareGeometryChange()
        if resp['status'] == '200':
            # we must clear all tweets widgets before
            for i in xrange(0, self.tweets_layout.count()-1):
                widget = self.tweets_layout.itemAt(1)
                if isinstance(widget, TweetWidget):
                    widget.deleteLater()
                    self.tweets_layout.removeAt(1)
            tweets = json.loads(content)
            for tweet in tweets:
                widget = TweetWidget(self.tweets_widget)
                widget.set_data(tweet, user=user)
                self.connect(widget, SIGNAL('reply(QString, QString)'), self.reply)
                self.connect(widget, SIGNAL('profile(QString)'), self.profile)
                self.connect(widget, SIGNAL('retweet(QString)'), self.retweet)
                self.connect(widget, SIGNAL('favorite(QString, bool)'), self.favorite)
                self.tweets_layout.addItem(widget)
            self.layout()

    def __update_timeline(self):
        self.__make_rest_calls("https://api.twitter.com/1.1/statuses/home_timeline.json")

    def __update_messages(self):
        self.__make_rest_calls("https://api.twitter.com/1.1/direct_messages.json", user=False)

    def __update_replies(self):
        self.__make_rest_calls("https://api.twitter.com/1.1/statuses/mentions_timeline.json")

    def reply(self, message_id, authorname):
        self.status_edit.setText(authorname + ' ')
        self.message_id = message_id

    def profile(self, user):
        KToolInvocation.invokeBrowser("https://twitter.com/%s" % (user,))

    def __make_post_calls(self, url, body):
        self.setBusy(True)
        self.timer.stop()
        token = oauth.Token(self.oauth_key, self.oauth_secret)
        client = oauth.Client(self.consumer, token=token)
        resp, content = client.request(url,
                                       method='POST', body=body)
        if resp['status'] == '200':
            self.update()
        self.timer.start()

    def retweet(self, message_id):
        self.flash.flash(self.trUtf8("Retweetting..."))
        self.__make_post_calls("https://api.twitter.com/1.1/statuses/retweet/"+str(message_id)+".json",
                               body='id='+str(message_id))

    def favorite(self, message_id, add):
        if add:            
            self.flash.flash(self.trUtf8("Adding favorites..."))
        else:
            self.flash.flash(self.trUtf8("Removing from favorites..."))
        self.__make_post_calls("https://api.twitter.com/1.1/favorites/"+("create" if add else "destroy")+".json",
                               body='id='+str(message_id))

    def update_status(self):
        tweet = str(self.status_edit.nativeWidget().toPlainText())
        self.flash.flash(self.trUtf8("Tweet sending..."))
        self.setBusy(True)
        body = 'status='+tweet
        if tweet.startswith('@') and self.message_id is not None:
            body += '&in_reply_to_status_id='+str(self.message_id)
        self.message_id = None
        self.__make_post_calls("https://api.twitter.com/1.1/statuses/update.json",
                               body=body)
        self.status_edit.setText(' ')

    def eventFilter(self, obj, event):
        if isinstance(obj, KTextEdit):
            if event.type() == QEvent.KeyPress:
                key_event = QKeyEvent(event)
                key = key_event.key()
                if (key_event.modifiers() == Qt.ControlModifier) and (key == Qt.Key_Enter or key == Qt.Key_Return):
                    self.update_status()
                    return True

                safe_keys = [Qt.Key_Delete, Qt.Key_Backspace,
                             Qt.Key_Up, Qt.Key_Down,
                             Qt.Key_Right, Qt.Key_Left,
                             Qt.Key_Home, Qt.Key_End]

                if key not in safe_keys:
                    if self.status_edit.nativeWidget().toPlainText().length() >= 140:
                        return True
            return False

        elif isinstance(obj, KTabBar) and event.type() == QEvent.MouseButtonPress:
            self.scroll_widget.ensureItemVisible(self.main_frame)
            self.status_edit.setFocus()
            return False
        else:
            return self.applet.eventFilter(obj, event)

    def authenticate(self, loop_count):
        if loop_count >= 5:
            return self.quit()
        loop_count += 1
        resp, content = self.client.request("https://twitter.com/oauth/request_token", "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        request_token = dict(urlparse.parse_qsl(content))

        KToolInvocation.invokeBrowser("https://twitter.com/oauth/authorize?oauth_token=%s&oauth_callback=oob" % (
                                                                                request_token['oauth_token']))

        dialog = KInputDialog.getText(self.trUtf8("PIN"), self.trUtf8("Enter the PIN received from Twitter:"))
        if dialog[1] is True and not dialog[0].isEmpty():
            token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
            token.set_verifier(str(dialog[0]))
            client = oauth.Client(self.consumer, token)
            resp, content = client.request("https://twitter.com/oauth/access_token", "POST")
            if resp['status'] == '200':
                access_token = dict(urlparse.parse_qsl(content))
                self.oauth_secret = access_token['oauth_token_secret']
                self.oauth_key = access_token['oauth_token']
                self.pm.writePassword("twitter_secret", self.oauth_secret)
                self.pm.writePassword("twitter_token", self.oauth_key)
            else:
                self.authenticate(loop_count)
        else:
            self.quit()

    def quit(self):
        self.close()

def CreateApplet(parent):
    return UBlogApplet(parent)