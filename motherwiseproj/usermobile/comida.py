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
from django.db.models import Q

from pbsonesignal import PybossaOneSignal

from pyfcm import FCMNotification

from motherwise.models import Member, Contact, Group, GroupMember, GroupConnect, Post, PostUrlPreview, Comment, PostPicture, PostLike, Notification, Received, Sent, Replied, Conference, Report, PostBlock, Cohort, PostCategory
from motherwise.models import CommentBlock, CommentLike, Recipe, FoodResource
from motherwise.serializers import MemberSerializer, GroupSerializer, PostSerializer, PostUrlPreviewSerializer, PostPictureSerializer, CommentSerializer, NotificationSerializer, ConferenceSerializer, RecipeSerializer
from motherwise.serializers import FoodResourceSerializer

import pyrebase

config = {
    "apiKey": "AIzaSyDveaXbV1HHMREyZzbvQe53BJEHVIRCf14",
    "authDomain": "motherwise-1585202524394.firebaseapp.com",
    "databaseURL": "https://motherwise-1585202524394.firebaseio.com",
    "storageBucket": "motherwise-1585202524394.appspot.com"
}

firebase = pyrebase.initialize_app(config)


from Crypto.Cipher import AES
from base64 import b64encode, b64decode

class Crypt:

    def __init__(self, salt='SlTKeYOpHygTYkP3'):
        self.salt = salt.encode('utf8')
        self.enc_dec_method = 'utf-8'

    def encrypt(self, str_to_enc, str_key):
        try:
            aes_obj = AES.new(str_key, AES.MODE_CFB, self.salt)
            hx_enc = aes_obj.encrypt(str_to_enc.encode('utf8'))
            mret = b64encode(hx_enc).decode(self.enc_dec_method)
            return mret
        except ValueError as value_error:
            if value_error.args[0] == 'IV must be 16 bytes long':
                raise ValueError('Encryption Error: SALT must be 16 characters long')
            elif value_error.args[0] == 'AES key must be either 16, 24, or 32 bytes long':
                raise ValueError('Encryption Error: Encryption key must be either 16, 24, or 32 characters long')
            else:
                raise ValueError(value_error)

    def decrypt(self, enc_str, str_key):
        try:
            aes_obj = AES.new(str_key.encode('utf8'), AES.MODE_CFB, self.salt)
            str_tmp = b64decode(enc_str.encode(self.enc_dec_method))
            str_dec = aes_obj.decrypt(str_tmp)
            mret = str_dec.decode(self.enc_dec_method)
            return mret
        except ValueError as value_error:
            if value_error.args[0] == 'IV must be 16 bytes long':
                raise ValueError('Decryption Error: SALT must be 16 characters long')
            elif value_error.args[0] == 'AES key must be either 16, 24, or 32 bytes long':
                raise ValueError('Decryption Error: Encryption key must be either 16, 24, or 32 characters long')
            else:
                raise ValueError(value_error)


def encrypt(info):
    crpt = Crypt()
    test_key = 'MyKey4TestingYnP'
    result = crpt.encrypt(info, test_key)
    return result


def decrypt(info):
    crpt = Crypt()
    test_key = 'MyKey4TestingYnP'
    result = crpt.decrypt(info, test_key)
    return result



@api_view(['GET', 'POST'])
def comida_posts(request):
    if request.method == 'POST':
        import datetime

        member_id = request.POST.get('member_id', '1')

        me = Member.objects.get(id=member_id)
        if me is None:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        userList = []
        for user in users:
            if user.registered_time != '' and user.pk != me.pk:
                user.username = '@' + user.email[0:user.email.find('@')]
                userList.append(user)

        admin = Member.objects.get(id=me.admin_id)
        admin.username = '@' + admin.email[0:admin.email.find('@')]
        userList.insert(0,admin)

        postList = []

        allPosts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='') & ~Q(status__icontains='top')).order_by('-id')[:10]
        i = 0
        for post in allPosts:
            if PostBlock.objects.filter(member_id=post.member_id, blocker_id=member_id, option='poster', status='blocked').count() > 0: continue
            if PostBlock.objects.filter(post_id=post.pk, blocker_id=member_id, option='post', status='blocked').count() > 0: continue
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())
            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())

            member = Member.objects.get(id=post.member_id)
            if member is not None:
                memb = member
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    memb_serializer = MemberSerializer(memb, many=False)
                    post_serializer = PostSerializer(post, many=False)
                    pps = PostPicture.objects.filter(post_id=post.pk)
                    prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                    prev_serializer = PostUrlPreviewSerializer(prevs, many=True)
                    comments1 = comments[:5]
                    commentlist = []
                    for comment in comments1:
                        cm = Member.objects.filter(id=comment.member_id).first()
                        if cm is not None:
                            cdata = {
                                'comment': CommentSerializer(comment, many=False).data,
                                'commented_member': MemberSerializer(cm, many=False).data,
                            }
                            commentlist.append(cdata)
                    data = {
                        'member':memb_serializer.data,
                        'post': post_serializer.data,
                        'prevs': prev_serializer.data,
                        'pics': str(pps.count()),
                        'comments': commentlist,
                    }
                    postList.append(data)
                    # if 'top' in post.status:
                    #     postList.insert(0, data)
                    # else:
                    #     postList.append(data)

        users_serializer = MemberSerializer(userList, many=True)

        topPosts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='') & Q(status__icontains='top')).order_by('-id')
        for post in topPosts:
            if PostBlock.objects.filter(member_id=post.member_id, blocker_id=member_id, option='poster', status='blocked').count() > 0: continue
            if PostBlock.objects.filter(post_id=post.pk, blocker_id=member_id, option='post', status='blocked').count() > 0: continue
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())

            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())

            member = Member.objects.get(id=post.member_id)
            if member is not None:
                memb = member
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    memb_serializer = MemberSerializer(memb, many=False)
                    post_serializer = PostSerializer(post, many=False)
                    pps = PostPicture.objects.filter(post_id=post.pk)
                    prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                    prev_serializer = PostUrlPreviewSerializer(prevs, many=True)
                    comments1 = comments[:5]
                    commentlist = []
                    for comment in comments1:
                        cm = Member.objects.filter(id=comment.member_id).first()
                        if cm is not None:
                            cdata = {
                                'comment': CommentSerializer(comment, many=False).data,
                                'commented_member': MemberSerializer(cm, many=False).data,
                            }
                            commentlist.append(cdata)
                    data = {
                        'member':memb_serializer.data,
                        'post': post_serializer.data,
                        'prevs': prev_serializer.data,
                        'pics': str(pps.count()),
                        'comments': commentlist,
                    }
                    postList.insert(0, data)

        resp = {'result_code':'0', 'posts': postList, 'users':users_serializer.data}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def refresh_comida_posts(request):
    if request.method == 'POST':
        import datetime

        member_id = request.POST.get('member_id', '1')
        num = request.POST.get('num', '0')

        me = Member.objects.get(id=member_id)
        if me is None:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        postList = []

        posts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='') & ~Q(status__icontains='top')).order_by('-id')[int(num):int(num) + 10]
        i = 0
        for post in posts:
            if PostBlock.objects.filter(member_id=post.member_id, blocker_id=member_id, option='poster', status='blocked').count() > 0: continue
            if PostBlock.objects.filter(post_id=post.pk, blocker_id=member_id, option='post', status='blocked').count() > 0: continue
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())

            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())

            member = Member.objects.get(id=post.member_id)
            if member is not None:
                memb = member
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    memb_serializer = MemberSerializer(memb, many=False)
                    post_serializer = PostSerializer(post, many=False)
                    pps = PostPicture.objects.filter(post_id=post.pk)
                    prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                    prev_serializer = PostUrlPreviewSerializer(prevs, many=True)
                    comments1 = comments[:5]
                    commentlist = []
                    for comment in comments1:
                        cm = Member.objects.filter(id=comment.member_id).first()
                        if cm is not None:
                            cdata = {
                                'comment': CommentSerializer(comment, many=False).data,
                                'commented_member': MemberSerializer(cm, many=False).data,
                            }
                            commentlist.append(cdata)
                    data = {
                        'member':memb_serializer.data,
                        'post': post_serializer.data,
                        'prevs': prev_serializer.data,
                        'pics': str(pps.count()),
                        'comments': commentlist,
                    }
                    postList.append(data)

        resp = {'result_code':'0', 'posts': postList}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def recipe_list(request):
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id','')
        category = request.POST.get('category','')

        rs = Recipe.objects.filter(admin_id=admin_id, category=category).order_by('-id')

        return HttpResponse(json.dumps({'result_code':'0', 'data':RecipeSerializer(rs, many=True).data}))

    return HttpResponse(json.dumps({'result_code':'1'}))




@api_view(['GET', 'POST'])
def food_resource_list(request):

    if request.method == 'POST':

        admin_id = request.POST.get('admin_id','')

        frs = FoodResource.objects.filter(member_id=admin_id).order_by('-id')
        frlist = []
        for fr in frs:
            if 'top' in fr.status: frlist.insert(0, fr)
            else: frlist.append(fr)

        return HttpResponse(json.dumps({'result_code':'0', 'data':FoodResourceSerializer(frlist, many=True).data}))

    return HttpResponse(json.dumps({'result_code':'1'}))





































































































































