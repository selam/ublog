# -*- coding: utf-8 -*-
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

from PyKDE4.plasma import Plasma
from PyQt4.QtCore import SIGNAL, Qt, QChar, QUrl
from PyQt4.QtGui import QSizePolicy, QImage, QPixmap, QIcon
from PyQt4.QtGui import QGraphicsAnchorLayout, QGraphicsWidget
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from datetime import datetime
from dateutil import parser
import pytz
import re

r = re.compile(r"((http|https)://[^\s<>'\"]+[^!,\.\s<>'\"\]])")

class TweetWidget(Plasma.Frame):

    def __init__(self, parent):
        Plasma.Frame.__init__(self, parent)
        self.author = Plasma.Label(self)
        self.author.nativeWidget().setWordWrap(False)
        self.picture = Plasma.IconWidget(self)
        self.picture.setMinimumSize(self.picture.sizeFromIconSize(32))
        self.picture.setMaximumSize(self.picture.sizeFromIconSize(32))
        self.connect(self.picture, SIGNAL('clicked()'),
                     lambda: self.emit(SIGNAL('profile(QString)'), self.author.text()))

        self._from = Plasma.Label(self)
        self._from.nativeWidget().setWordWrap(False)

        self.text = Plasma.TextBrowser(self)
        self.text.nativeWidget().setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.text.nativeWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text.nativeWidget().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text.nativeWidget().setCursor(Qt.ArrowCursor)

        self.favorite_button = Plasma.ToolButton(self)
        self.favorite_button.setText(QChar(0x2665))
        self.connect(self.favorite_button, SIGNAL('clicked()'),
                     lambda: self.emit(SIGNAL('favorite(QString, bool)'),
                                       str(self.message_id), False if self.is_favorite else True))

        self.reply_button = Plasma.ToolButton(self)
        self.reply_button .setText("@")
        self.connect(self.reply_button, SIGNAL('clicked()'),
                     lambda: self.emit(SIGNAL('reply(QString, QString)'),
                                       str(self.message_id), '@'+self.author.text()+' '))

        self.forward_button = Plasma.ToolButton(self)
        #recycle
        self.forward_button.setText(QChar(0x267B))
        self.connect(self.forward_button, SIGNAL('clicked()'),
                     lambda: self.emit(SIGNAL('retweet(QString)'),
                                       str(self.message_id)))
        #corners
        lay = QGraphicsAnchorLayout(self)
        lay.setSpacing(4)
        lay.addCornerAnchors(lay, Qt.TopLeftCorner, self.picture, Qt.TopLeftCorner)
        lay.addCornerAnchors(self.picture, Qt.TopRightCorner, self.author, Qt.TopLeftCorner)
        lay.addCornerAnchors(self.author, Qt.BottomLeftCorner, self._from, Qt.TopLeftCorner)
        lay.addCornerAnchors(lay, Qt.TopRightCorner, self.forward_button, Qt.TopRightCorner)
        lay.addCornerAnchors(self.forward_button, Qt.TopLeftCorner, self.reply_button, Qt.TopRightCorner)
        lay.addCornerAnchors(self.reply_button, Qt.TopLeftCorner, self.favorite_button, Qt.TopRightCorner)
        lay.addCornerAnchors(self.favorite_button, Qt.TopLeftCorner, self.author, Qt.TopRightCorner)
        #vertical
        lay.addAnchor(self._from, Qt.AnchorBottom, self.text, Qt.AnchorTop)
        lay.addAnchor(lay, Qt.AnchorBottom, self.text, Qt.AnchorBottom)
        #horizontal
        lay.addAnchor(lay, Qt.AnchorRight, self._from, Qt.AnchorRight)
        lay.addAnchors(lay, self.text, Qt.Horizontal)
        self.message_id = None
        self.is_favorite = False
        self.nam = QNetworkAccessManager()
        self.connect(self.nam, SIGNAL('finished(QNetworkReply*)'), self.set_image)


    def set_image(self, image):
        img = QImage()
        img.loadFromData(image.readAll())
        self.picture.setIcon(QIcon(QPixmap(img)))

    def set_data(self, data, user=True):

        """
       {
         u 'contributors': None,
         u 'truncated': False,
         u 'text': u '@svlzx size e-posta \xfczerinden ilettim.',
         u 'in_reply_to_status_id': None,
         u 'id': 434001383730073602,
         u 'favorite_count': 0,
         u 'source': u 'web',
         u 'retweeted': False,
         u 'coordinates': None,
         u 'entities': {
             u 'symbols': [],
             u 'user_mentions': [{
                 u 'id': 18474340,
                 u 'indices': [0, 6],
                 u 'id_str': u '18474340',
                 u 'screen_name': u 'svlzx',
                 u 'name': u 'Seval U.'
             }],
             u 'hashtags': [],
             u 'urls': []
         },
         u 'in_reply_to_screen_name': None,
         u 'id_str': u '434001383730073602',
         u 'retweet_count': 0,
         u 'in_reply_to_user_id': None,
         u 'favorited': False,
         u 'user': {
             u 'follow_request_sent': False,
             u 'profile_use_background_image': True,
             u 'default_profile_image': False,
             u 'id': 14691809,
             u 'profile_background_image_url_https': u 'https://pbs.twimg.com/profile_background_images/149261242/force-unleashed-2-wallpaper.jpg',
             u 'verified': False,
             u 'profile_text_color': u '1C1F23',
             u 'profile_image_url_https': u 'https://pbs.twimg.com/profile_images/1168139182/49216_687842033_2977_q_normal.jpg',
             u 'profile_sidebar_fill_color': u '928AFF',
             u 'entities': {
                 u 'description': {
                     u 'urls': []
                 }
             },
             u 'followers_count': 107,
             u 'profile_sidebar_border_color': u '9C8DD6',
             u 'id_str': u '14691809',
             u 'profile_background_color': u '07090B',
             u 'listed_count': 5,
             u 'is_translation_enabled': False,
             u 'utc_offset': 7200,
             u 'statuses_count': 928,
             u 'description': u '',
             u 'friends_count': 112,
             u 'location': u '\u0130stanbul',
             u 'profile_link_color': u '002AFA',
             u 'profile_image_url': u 'http://pbs.twimg.com/profile_images/1168139182/49216_687842033_2977_q_normal.jpg',
             u 'following': False,
             u 'geo_enabled': True,
             u 'profile_background_image_url': u 'http://pbs.twimg.com/profile_background_images/149261242/force-unleashed-2-wallpaper.jpg',
             u 'screen_name': u 'selamtux',
             u 'lang': u 'en',
             u 'profile_background_tile': True,
             u 'favourites_count': 5,
             u 'name': u 'selamtux',
             u 'notifications': False,
             u 'url': None,
             u 'created_at': u 'Wed May 07 21:01:34 +0000 2008',
             u 'contributors_enabled': False,
             u 'time_zone': u 'Istanbul',
             u 'protected': False,
             u 'default_profile': False,
             u 'is_translator': False
         },
         u 'geo': None,
         u 'in_reply_to_user_id_str': None,
         u 'lang': u 'tr',
         u 'created_at': u 'Thu Feb 13 16:29:27 +0000 2014',
         u 'in_reply_to_status_id_str': None,
         u 'place': None
     }

        """
        user_ = data['user'] if user else data['sender']
        self.message_id = data['id']
        self.author.setText(user_['screen_name'])
        dt = parser.parse(data['created_at'])
        text = r.sub(r'<a href="\1">\1</a>', data['text'])
        self.text.setText("<p>%s</p>" % text)
        self._from.setText(self.time_ago(dt))
        if user is True:
            self.is_favorite = data['favorited']
            self.favorite_button.setDown(self.is_favorite)
            self.favorite_button.setVisible(True)
            self.forward_button.setVisible(True)
        else:
            self.favorite_button.setVisible(False)
            self.forward_button.setVisible(False)
        self.nam.get(QNetworkRequest(QUrl(user_['profile_image_url'])))

    def time_ago(self, date_time):
        current_datetime = datetime.now(tz=pytz.utc)
        delta = str(current_datetime - date_time)
        if delta.find(',') > 0:
            days, hours = delta.split(',')
            days = int(days.split()[0].strip())
            hours, minutes = hours.split(':')[0:2]
        else:
            hours, minutes = delta.split(':')[0:2]
            days = 0
        days, hours, minutes = int(days), int(hours), int(minutes)
        datelets =[]
        years, months, xdays = None, None, None
        plural = lambda x: 's' if x != 1 else ''
        if days >= 365:
            years = int(days/365)
            datelets.append(str(self.trUtf8('%d year%s')) % (years, plural(years)))
            days = days % 365
        if days >= 30 and days < 365:
            months = int(days/30)
            datelets.append(str(self.trUtf8('%d month%s')) % (months, plural(months)))
            days = days % 30
        if not years and days > 0 and days < 30:
            xdays =days
            datelets.append(str(self.trUtf8('%d day%s')) % (xdays, plural(xdays)))
        if not (months or years) and hours != 0:
            datelets.append(str(self.trUtf8('%d hour%s')) % (hours, plural(hours)))
        if not (xdays or months or years):
            datelets.append(str(self.trUtf8('%d minute%s')) % (minutes, plural(minutes)))
        return ', '.join(datelets) + str(self.trUtf8(' ago.'))