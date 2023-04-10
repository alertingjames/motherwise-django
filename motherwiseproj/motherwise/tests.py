from django.test import TestCase

# import datetime
import difflib
import os
import string
import urllib
from itertools import islice

import io
import requests
import xlrd
import re

from django.core import mail
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.contrib import messages
# from _mysql_exceptions import DataError, IntegrityError
from django.template import RequestContext

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import EmailMultiAlternatives

from django.core.files.storage import FileSystemStorage
import json
from django.contrib import auth
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.cache import cache_control
from numpy import long
from openpyxl.styles import PatternFill

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.fields import empty
from rest_framework.permissions import AllowAny
from time import gmtime, strftime
import time
from xlrd import XLRDError

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings
from django import forms
import sys
from django.core.cache import cache
import random
import emoji

from linkpreview import link_preview
import favicon
import certifi
import ssl
from django.db.models import Q

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import urllib3
from mechanize import Browser
from selenium import webdriver

from pbsonesignal import PybossaOneSignal

from pyfcm import FCMNotification

from motherwise.models import Member, Contact, Group, GroupMember, GroupConnect, Post, PostUrlPreview, Comment, PostPicture, PostLike, Notification, Received, Sent, Replied, Conference, Report
from motherwise.serializers import PostSerializer, CommentSerializer

import pyrebase

config = {
    "apiKey": "AIzaSyDveaXbV1HHMREyZzbvQe53BJEHVIRCf14",
    "authDomain": "motherwise-1585202524394.firebaseapp.com",
    "databaseURL": "https://motherwise-1585202524394.firebaseio.com",
    "storageBucket": "motherwise-1585202524394.appspot.com"
}

firebase = pyrebase.initialize_app(config)


def urlsFromText(str):
    web_urls = re.findall(r'(https?://\S+)', str)
    return web_urls


def assignUrlPreviewToPosts(request):
    posts = Post.objects.all()
    i = 0
    for post in posts:
        if post.content != '':
            web_urls = urlsFromText(post.content)
            for wurl in web_urls:
                try:
                    preview = link_preview(wurl)
                    wtitle = preview.title
                    wdescription = preview.description
                    wimageurl = preview.image
                    wforcetitle = preview.force_title
                    wabsoluteimageurl = preview.absolute_image

                    icon = None
                    icons = favicon.get(wurl)
                    if icons is not None and len(icons) > 0: icon = icons[0]

                    upreview = PostUrlPreview()
                    upreview.post_id = post.pk
                    if wtitle is not None: upreview.title = wtitle
                    elif wforcetitle is not None: upreview.title = wforcetitle
                    if wdescription is not None: upreview.description = wdescription
                    if wimageurl is not None: upreview.image_url = wimageurl
                    elif wabsoluteimageurl is not None: upreview.image_url = wabsoluteimageurl
                    if icon is not None: upreview.icon_url = icon.url
                    upreview.site_url = wurl
                    upreview.save()
                    i += 1
                except:
                    print('Error')
                    try:
                        driver = webdriver.Chrome()
                        driver.get(wurl)
                        wtitle = driver.title

                        icon = None
                        icons = favicon.get(wurl)
                        if icons is not None and len(icons) > 0: icon = icons[0]

                        upreview = PostUrlPreview()
                        upreview.post_id = post.pk
                        if wtitle is not None: upreview.title = wtitle
                        if icon is not None: upreview.icon_url = icon.url
                        upreview.site_url = wurl
                        upreview.save()
                        i += 1
                    except:
                        pass
                else:
                    pass


    return HttpResponse('Progressed: ' + str(i))






















































