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

from pbsonesignal import PybossaOneSignal

from pyfcm import FCMNotification

from motherwise.models import Member, Contact, Group, GroupMember, GroupConnect, Post, Comment, PostPicture, PostLike, Notification, Received, Sent, Replied, Conference, Report
from motherwise.serializers import MemberSerializer, GroupSerializer, PostSerializer, PostPictureSerializer, CommentSerializer, NotificationSerializer, ConferenceSerializer

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



def index(request):
    return HttpResponse('Hello I am VaCay Mobile Server!')


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        members = Member.objects.filter(email=email, password=password)
        if members.count() > 0:
            member = members[0]

            serializer = MemberSerializer(member, many=False)

            if member.cohort == 'admin':
                resp = {'result_code': '4'}
                return HttpResponse(json.dumps(resp))
            if member.registered_time == '':
                resp = {'result_code': '2', 'data':serializer.data}
                return HttpResponse(json.dumps(resp))
            elif member.address == '':
                resp = {'result_code': '1', 'data':serializer.data}
                return HttpResponse(json.dumps(resp))
            else:
                resp = {'result_code': '0', 'data':serializer.data}
                return HttpResponse(json.dumps(resp))
        else:
            members = Member.objects.filter(email=email)
            if members.count() > 0:
                member = members[0]
                if member.cohort != 'admin':
                    resp = {'result_code': '3'}
                else:
                    resp = {'result_code': '4'}
            else:
                resp = {'result_code': '4'}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def register(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '0')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        phone_number = request.POST.get('phone_number', '')
        cohort = request.POST.get('cohort', '')

        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')

        fs = FileSystemStorage()

        members = Member.objects.filter(id=member_id)
        member = None
        if members.count() == 0:
            member = Member()
            mbs = Member.objects.filter(email='cayleywetzig@gmail.com')
            admin = mbs[0]
            member.admin_id = admin.pk
        else:
            member = members[0]
        member.name = name
        member.email = email
        if password != "": member.password = password
        member.phone_number = phone_number
        if member.photo_url == '': member.photo_url = settings.URL + '/static/images/ic_profile.png'
        member.cohort = cohort
        if address != '': member.address = address
        if city != '': member.city = city
        if lat != '': member.lat = lat
        if lng != '': member.lng = lng
        if member.registered_time == '': member.registered_time = str(int(round(time.time() * 1000)))

        try:
            private = request.POST.get('private', '')
            if private != '':
                member.status = 'private'
            else:
                member.status = ''
        except KeyError:
            print('no key')

        try:
            f = request.FILES['file']
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            member.photo_url = settings.URL + uploaded_url
        except MultiValueDictKeyError:
            print('no picture updated')

        member.save()

        serializer = MemberSerializer(member, many=False)

        resp = {'result_code': '0', 'data':serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')

        members = Member.objects.filter(email=email)
        memberList = []
        for member in members:
            if member.cohort != 'admin': memberList.append(member)
        if len(memberList) == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = memberList[0]
        admin = Member.objects.get(id=member.admin_id)

        message = 'Hi ' + member.name + ', You are allowed to reset your password from your request.<br>For it, please click this link to reset your password.<br><br><a href=\'' + 'https://www.vacay.company/umobile/resetpassword?email=' + email
        message = message + '\' target=\'_blank\'>' + 'Link to reset password' + '</a><br><br>MotherWise Team'

        html =  """\
                    <html>
                        <head></head>
                        <body>
                            <a href="#"><img src="https://www.vacay.company/static/images/logo.png" style="width:120px;height:120px; margin-left:25px; border-radius:8%;"/></a>
                            <h2 style="color:#02839a;">MotherWise Member's Security Update Information</h2>
                            <div style="font-size:14px; white-space: pre-line; word-wrap: break-word;">
                                {mes}
                            </div>
                        </body>
                    </html>
                """
        html = html.format(mes=message)

        fromEmail = admin.email
        toEmailList = []
        toEmailList.append(email)
        msg = EmailMultiAlternatives('We allowed you to reset your password', '', fromEmail, toEmailList)
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


def resetpassword(request):
    email = request.GET['email']
    return render(request, 'usermobile/resetpwd.html', {'email':email})


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def rstpwd(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        members = Member.objects.filter(email=email)
        memberList = []
        for member in members:
            if member.cohort != 'admin': memberList.append(member)
        if len(memberList) == 0:
            return render(request, 'usermobile/result.html',
                          {'response': 'This email doesn\'t exist.'})

        member = memberList[0]

        member.password = password
        member.save()

        return render(request, 'usermobile/result.html',
                          {'response': 'Your password has been reset successfully!'})



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def addlocation(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]
        member.address = address
        member.city = city
        member.lat = lat
        member.lng = lng
        member.save()

        serializer = MemberSerializer(member, many=False)

        resp = {'result_code': '0', 'data':serializer.data}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def home(request):
    import datetime

    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        if me.cohort == '':
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))

        members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        memberList = []
        for member in members:
            if member.registered_time != '' and member.pk != me.pk and member.status == '':
                member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
                memberList.append(member)
        admin = Member.objects.get(id=me.admin_id)
        memberList.insert(0, admin)
        groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
        groupList = []
        for group in groups:
            gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
            if gms.count() > 0:
                groupList.append(group)

        members_serializer = MemberSerializer(memberList, many=True)
        groups_serializer = GroupSerializer(groupList, many=True)
        admin_serializer = MemberSerializer(admin, many=False)

        resp = {'result_code': '0', 'users':members_serializer.data, 'groups':groups_serializer.data, 'admin':admin_serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def sendmembermessage(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')
        member_id = request.POST.get('member_id', '1')
        message = request.POST.get('message', '')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        members = Member.objects.filter(id=int(member_id))
        if members.count() > 0:
            member = members[0]

            notification = Notification()
            notification.member_id = member.pk
            notification.sender_id = me.pk
            notification.message = message
            notification.notified_time = str(int(round(time.time() * 1000)))
            notification.save()

            rcv = Received()
            rcv.member_id = member.pk
            rcv.sender_id = me.pk
            rcv.noti_id = notification.pk
            rcv.save()

            snt = Sent()
            snt.member_id = member.pk
            snt.sender_id = me.pk
            snt.noti_id = notification.pk
            snt.save()

            title = 'MotherWise Community: The Nest'
            subject = 'You\'ve received a message from a member of MotherWise Community: The Nest'
            msg = 'Dear ' + member.name + ', You\'ve received a message from ' + me.name + '. The message is as following:<br><br>'
            msg = msg + message
            rurl = '/mothers/notifications?noti_id=' + str(notification.pk)
            if member.cohort == 'admin':
                rurl = '/notifications?noti_id=' + str(notification.pk)
            msg = msg + '<br><br><a href=\'' + settings.URL + rurl + '\' target=\'_blank\'>Join website</a>'

            from_email = me.email
            to_emails = []
            to_emails.append(member.email)
            send_mail_message(from_email, to_emails, title, subject, msg)

            ##########################################################################################################################################################################

            db = firebase.database()
            data = {
                "msg": message,
                "date":str(int(round(time.time() * 1000))),
                "sender_id": str(me.pk),
                "sender_name": me.name,
                "sender_email": me.email,
                "sender_photo": me.photo_url,
                "role": "",
                "type": "message",
                "id": str(notification.pk),
                "mes_id": str(notification.pk)
            }

            db.child("notify").child(str(member.pk)).push(data)
            db.child("notify2").child(str(member.pk)).push(data)

            sendFCMPushNotification(member.pk, me.pk, message)

            #################################################################################################################################################################################

            if member.playerID != '':
                playerIDList = []
                playerIDList.append(member.playerID)
                url = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    url = '/notifications?noti_id=' + str(notification.pk)
                msg = member.name + ', You\'ve received a message from ' + me.name + '.\nThe message is as following:\n' + message
                send_push(playerIDList, msg, url)

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))
        else:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))



def send_mail_message(from_email, to_emails, title, subject, message):
    html =  """\
                <html>
                    <head></head>
                    <body>
                        <a href="#"><img src="https://www.vacay.company/static/images/logo.png" style="width:120px;height:120px;border-radius: 8%; margin-left:25px;"/></a>
                        <h2 style="margin-left:10px; color:#02839a;">{title}</h2>
                        <div style="font-size:14px; white-space: pre-line; word-wrap: break-word;">
                            {mes}
                        </div>
                    </body>
                </html>
            """
    html = html.format(title=title, mes=message)

    msg = EmailMultiAlternatives(subject, '', from_email, to_emails)
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def send_push(playerIDs, message, url):

    client = PybossaOneSignal(api_key=settings.OS_API_KEY, app_id=settings.OS_APP_ID)
    contents = {"en": message}
    headings = {"en": "VaCay Network"}
    launch_url = settings.URL + url
    chrome_web_image = settings.URL + '/static/images/notimage.jpg'
    chrome_web_icon = settings.URL + '/static/images/noticon.png'
    included_segments = []
    include_player_ids = playerIDs
    web_buttons=[{"id": "read-more-button",
                               "text": "Read more",
                               "icon": "http://i.imgur.com/MIxJp1L.png",
                               "url": launch_url}]
    client.push_msg(contents=contents, headings=headings, include_player_ids=include_player_ids, launch_url=launch_url, chrome_web_image=chrome_web_image, chrome_web_icon=chrome_web_icon, included_segments=included_segments, web_buttons=web_buttons)




@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def messageselecteds(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')
        members_json_str = request.POST.get('members', '')
        message = request.POST.get('message', '')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        try:
            decoded = json.loads(members_json_str)
            for data in decoded['members']:

                member_id = data['member_id']
                name = data['name']

                members = Member.objects.filter(id=int(member_id))
                if members.count() > 0:
                    member = members[0]

                    notification = Notification()
                    notification.member_id = member.pk
                    notification.sender_id = me.pk
                    notification.message = message
                    notification.notified_time = str(int(round(time.time() * 1000)))
                    notification.save()

                    rcv = Received()
                    rcv.member_id = member.pk
                    rcv.sender_id = me.pk
                    rcv.noti_id = notification.pk
                    rcv.save()

                    snt = Sent()
                    snt.member_id = member.pk
                    snt.sender_id = me.pk
                    snt.noti_id = notification.pk
                    snt.save()

                    title = 'MotherWise Community: The Nest'
                    subject = 'You\'ve received a message from a member of MotherWise Community: The Nest'
                    msg = 'Dear ' + member.name + ', You\'ve received a message from ' + me.name + '. The message is as following:<br><br>'
                    msg = msg + message
                    rurl = '/mothers/notifications?noti_id=' + str(notification.pk)
                    if member.cohort == 'admin':
                        rurl = '/notifications?noti_id=' + str(notification.pk)
                    msg = msg + '<br><br><a href=\'' + settings.URL + rurl + '\' target=\'_blank\'>Join website</a>'

                    from_email = me.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message(from_email, to_emails, title, subject, msg)

                    #####################################################################################################################################################################

                    db = firebase.database()
                    data = {
                        "msg": message,
                        "date":str(int(round(time.time() * 1000))),
                        "sender_id": str(me.pk),
                        "sender_name": me.name,
                        "sender_email": me.email,
                        "sender_photo": me.photo_url,
                        "role": "",
                        "type": "message",
                        "id": str(notification.pk),
                        "mes_id": str(notification.pk)
                    }

                    db.child("notify").child(str(member.pk)).push(data)
                    db.child("notify2").child(str(member.pk)).push(data)

                    sendFCMPushNotification(member.pk, me.pk, message)

                    ######################################################################################################################################################################

                    if member.playerID != '':
                        playerIDList = []
                        playerIDList.append(member.playerID)
                        msg = member.name + ', You\'ve received a message from ' + me.name + '.\nThe message is as following:\n' + message
                        url = '/mothers/notifications?noti_id=' + str(notification.pk)
                        if member.cohort == 'admin':
                            url = '/notifications?noti_id=' + str(notification.pk)
                        send_push(playerIDList, msg, url)

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))

        except:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))



def update_contact(me, member_email):
    if member_email != '':
        contacts = Contact.objects.filter(member_id=me.pk, contact_email=member_email)
        if contacts.count() == 0:
            contact = Contact()
            contact.member_id = me.pk
            contact.contact_email = member_email
            contact.contacted_time = str(int(round(time.time() * 1000)))
            contact.save()
        else:
            contact = contacts[0]
            contacts = Contact.objects.filter(member_id=me.pk)
            recent_contact = contacts[contacts.count() - 1]
            if contact.pk < recent_contact.pk:
                contact.delete()
                contact = Contact()
                contact.member_id = me.pk
                contact.contact_email = member_email
                contact.contacted_time = str(int(round(time.time() * 1000)))
                contact.save()

    contacts = Contact.objects.filter(member_id=me.pk).order_by('-id')
    contactList = []
    for contact in contacts:
        members = Member.objects.filter(email=contact.contact_email)
        if members.count() > 0:
            member = members[0]
            contactList.append(member)

    return contactList


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def networkposts(request):
    if request.method == 'POST':
        import datetime

        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

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

        allPosts = Post.objects.all().order_by('-id')
        i = 0
        for post in allPosts:
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            pls = PostLike.objects.filter(post_id=post.pk, member_id=me.pk)
            if pls.count() > 0:
                post.liked = 'yes'
            else: post.liked = 'no'

            comments = Comment.objects.filter(post_id=post.pk)
            post.comments = str(comments.count())
            likes = PostLike.objects.filter(post_id=post.pk)
            post.likes = str(likes.count())

            members = Member.objects.filter(id=post.member_id)
            if members.count() > 0:
                memb = members[0]
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    memb_serializer = MemberSerializer(memb, many=False)
                    post_serializer = PostSerializer(post, many=False)
                    pps = PostPicture.objects.filter(post_id=post.pk)
                    data = {
                        'member':memb_serializer.data,
                        'post': post_serializer.data,
                        'pics': str(pps.count())
                    }

                    postList.append(data)

        users_serializer = MemberSerializer(userList, many=True)

        resp = {'result_code':'0', 'posts': postList, 'users':users_serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def likepost(request):

    if request.method == 'POST':

        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]
        pls = PostLike.objects.filter(post_id=post.pk, member_id=me.pk)
        if pls.count() > 0:
            pls[0].delete()
            post.likes = str(int(post.likes) - 1)
            post.save()
        else:
            pl = PostLike()
            pl.post_id = post.pk
            pl.member_id = me.pk
            pl.liked_time = str(int(round(time.time() * 1000)))
            pl.save()

            post.likes = str(int(post.likes) + 1)
            post.save()

        resp = {'result_code': '0', 'likes': str(post.likes)}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getcomments(request):

    import datetime

    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]

        comments = Comment.objects.filter(post_id=post.pk).order_by('-id')
        commentList = []
        for comment in comments:
            comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
            members = Member.objects.filter(id=comment.member_id)
            if members.count() > 0:
                member = members[0]
                comment_serializer = CommentSerializer(comment, many=False)
                member_serializer = MemberSerializer(member, many=False)
                data = {
                    'comment':comment_serializer.data,
                    'member':member_serializer.data
                }
                commentList.append(data)

        resp = {'result_code':'0', 'data':commentList}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def submitcomment(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '')
        content = request.POST.get('content', '')
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        fs = FileSystemStorage()

        comments = Comment.objects.filter(post_id=post_id, member_id=me.pk)
        if comments.count() == 0:
            comment = Comment()
            comment.post_id = post_id
            comment.member_id = me.pk
            comment.comment_text = content
            comment.commented_time = str(int(round(time.time() * 1000)))

            try:
                image = request.FILES['image']
                filename = fs.save(image.name, image)
                uploaded_url = fs.url(filename)
                comment.image_url = settings.URL + uploaded_url
            except MultiValueDictKeyError:
                print('no video updated')

            comment.save()

            posts = Post.objects.filter(id=post_id)
            if posts.count() == 0:
                resp = {'result_code': '2'}
                return HttpResponse(json.dumps(resp))
            post = posts[0]
            post.comments = str(int(post.comments) + 1)
            post.save()

        else:
            comment = comments[0]
            comment.comment_text = content

            try:
                image = request.FILES['image']
                filename = fs.save(image.name, image)
                uploaded_url = fs.url(filename)
                if comment.image_url != '':
                    fs.delete(comment.image_url.replace(settings.URL + '/media/', ''))
                comment.image_url = settings.URL + uploaded_url
            except MultiValueDictKeyError:
                print('no video updated')

            comment.save()

        resp = {'result_code':'0'}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def deletepost(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')

        fs = FileSystemStorage()

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]
        pls = PostLike.objects.filter(post_id=post.pk)
        for pl in pls:
            pl.delete()
        pps = PostPicture.objects.filter(post_id=post.pk)
        for pp in pps:
            if pp.picture_url != '':
                fs.delete(pp.picture_url.replace(settings.URL + '/media/', ''))
            pp.delete()
        pcs = Comment.objects.filter(post_id=post.pk)
        for pc in pcs:
            if pc.image_url != '':
                fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
            pc.delete()

        post.delete()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def deletecomment(request):
    if request.method == 'POST':

        comment_id = request.POST.get('comment_id', '1')

        fs = FileSystemStorage()

        pcs = Comment.objects.filter(id=comment_id)
        if pcs.count() > 0:
            pc = pcs[0]
            post_id = pc.post_id
            if pc.image_url != '':
                fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
            pc.delete()

            post = Post.objects.get(id=post_id)
            post.comments = str(int(post.comments) - 1)
            post.save()

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))
        else:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getpostpictures(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')

        pps = PostPicture.objects.filter(post_id=post_id)

        pps_serializer = PostPictureSerializer(pps, many=True)

        resp = {'result_code': '0', 'data':pps_serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def createpost(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '0')
        title = request.POST.get('title', '')
        category = request.POST.get('category', '')
        content = request.POST.get('content', '')
        members_json_str = request.POST.get('members', '')

        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        admin = Member.objects.get(id=me.admin_id)

        post = None

        if int(post_id) > 0:
            posts = Post.objects.filter(id=int(post_id))
            if posts.count() == 0:
                resp = {'result_code': '1'}
                return HttpResponse(json.dumps(resp))
            post = posts[0]
        else: post = Post()

        post.member_id = me.pk
        post.title = title
        post.category = category
        post.content = content
        post.picture_url = ''
        post.comments = '0'
        post.likes = '0'
        post.posted_time = str(int(round(time.time() * 1000)))
        if int(post_id) > 0: post.status = "updated"
        post.save()

        fs = FileSystemStorage()

        cnt = request.POST.get('pic_count', '0')

        if int(cnt) > 0:
            i = 0
            for i in range(0, int(cnt)):
                f  = request.FILES["file" + str(i)]

                # print("Product File Size: " + str(f.size))
                # if f.size > 1024 * 1024 * 2:
                #     continue

                i = i + 1

                filename = fs.save(f.name, f)
                uploaded_url = fs.url(filename)

                if i == 1:
                    post.picture_url = settings.URL + uploaded_url
                    post.save()
                postPicture = PostPicture()
                postPicture.post_id = post.pk
                postPicture.picture_url = settings.URL + uploaded_url
                postPicture.save()

        if members_json_str != '':
            try:
                decoded = json.loads(members_json_str)
                for data in decoded['members']:

                    member_id = data['member_id']
                    name = data['name']

                    members = Member.objects.filter(id=int(member_id))
                    if members.count() > 0:
                        member = members[0]

                        title = 'MotherWise Community: The Nest'
                        subject = 'You\'ve received a post from ' + me.name
                        msg = 'Dear ' + member.name + ', You\'ve received a post from ' + me.name + '.<br><br>'

                        if member.cohort == 'admin':
                            msg = msg + '<a href=\'' + settings.URL + '/to_post?post_id=' + str(post.pk) + '\' target=\'_blank\'>View the post</a>'
                        else:
                            msg = msg + '<a href=\'' + settings.URL + '/mothers/posts?post_id=' + str(post.pk) + '\' target=\'_blank\'>View the post</a>'

                        from_email = admin.email
                        if member.cohort == 'admin':
                            from_email = settings.ADMIN_EMAIL
                        to_emails = []
                        to_emails.append(member.email)
                        send_mail_message(from_email, to_emails, title, subject, msg)

                        msg = member.name + ', You\'ve received a message from ' + me.name + '.\n\n'

                        if member.cohort == 'admin':
                            msg = msg + 'Click on this link to view the post: ' + settings.URL + '/to_post?post_id=' + str(post.pk)
                        else:
                            msg = msg + 'Click on this link to view the post: ' + settings.URL + '/mothers/posts?post_id=' + str(post.pk)

                        notification = Notification()
                        notification.member_id = member.pk
                        notification.sender_id = me.pk
                        notification.message = msg
                        notification.notified_time = str(int(round(time.time() * 1000)))
                        notification.save()

                        rcv = Received()
                        rcv.member_id = member.pk
                        rcv.sender_id = me.pk
                        rcv.noti_id = notification.pk
                        rcv.save()

                        snt = Sent()
                        snt.member_id = member.pk
                        snt.sender_id = me.pk
                        snt.noti_id = notification.pk
                        snt.save()

                        #####################################################################################################################################################################

                        db = firebase.database()
                        data = {
                            "msg": msg,
                            "date":str(int(round(time.time() * 1000))),
                            "sender_id": str(me.pk),
                            "sender_name": me.name,
                            "sender_email": me.email,
                            "sender_photo": me.photo_url,
                            "role": "",
                            "type": "post",
                            "id": str(post.pk),
                            "mes_id": str(notification.pk)
                        }

                        db.child("notify").child(str(member.pk)).push(data)
                        db.child("notify2").child(str(member.pk)).push(data)

                        sendFCMPushNotification(member.pk, me.pk, msg)

                        ######################################################################################################################################################################

                        if member.playerID != '':
                            playerIDList = []
                            playerIDList.append(member.playerID)
                            url = '/mothers/notifications?noti_id=' + str(notification.pk)
                            if member.cohort == 'admin':
                                url = '/notifications?noti_id=' + str(notification.pk)
                            send_push(playerIDList, msg, url)

                resp = {'result_code': '0'}
                return HttpResponse(json.dumps(resp))

            except:
                resp = {'result_code': '2'}
                return HttpResponse(json.dumps(resp))

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def delpostpicture(request):
    if request.method == 'POST':

        picture_id = request.POST.get('picture_id', '1')
        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))
        post = posts[0]
        pics = PostPicture.objects.filter(id=picture_id, post_id=post_id)
        fs = FileSystemStorage()
        if pics.count() > 0:
            pic = pics[0]
            if pic.picture_url != '':
                fs.delete(pic.picture_url.replace(settings.URL + '/media/', ''))
                if pic.picture_url == post.picture_url:
                    post.picture_url = ''
                    pics = PostPicture.objects.filter(post_id=post_id)
                    if pics.count() > 0:
                        post.picture_url = pics[0].picture_url
                    post.save()
            pic.delete()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getlikes(request):

    import datetime

    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]

        pls = PostLike.objects.filter(post_id=post.pk).order_by('-id')
        likeList = []
        for pl in pls:
            member_id = pl.member_id
            members = Member.objects.filter(id=member_id)
            if members.count() > 0:
                member = members[0]
                member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y %H:%M")
                likeList.append(member)

        serializer = MemberSerializer(likeList, many=True)

        resp = {'result_code':'0', 'data':serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getreceivedmessages(request):

    import datetime

    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        notiList = []

        notis = Received.objects.filter(member_id=me.pk).order_by('-id')

        for noti in notis:
            members = Member.objects.filter(id=noti.sender_id)
            if members.count() > 0:
                sender = members[0]
                nfs = Notification.objects.filter(id=noti.noti_id)
                if nfs.count() > 0:
                    notification = nfs[0]
                    notification.notified_time = datetime.datetime.fromtimestamp(float(int(notification.notified_time)/1000)).strftime("%b %d, %Y %H:%M")

                    sender_serializer = MemberSerializer(sender, many=False)
                    noti_serializer = NotificationSerializer(notification, many=False)
                    data = {
                        'sender':sender_serializer.data,
                        'noti': noti_serializer.data
                    }

                    notiList.append(data)

        resp = {'result_code': '0', 'data': notiList}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def deletemessage(request):

    if request.method == 'POST':
        message_id = request.POST.get('message_id', '1')
        opt = request.POST.get('option', '')

        if opt == 'received':
            notis = Received.objects.filter(noti_id=message_id)
            if notis.count() > 0:
                noti = notis[0]
                noti.delete()
        elif opt == 'sent':
            notis = Sent.objects.filter(noti_id=message_id)
            if notis.count() > 0:
                noti = notis[0]
                noti.delete()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def processnewmessage(request):
    if request.method == 'POST':
        message_id = request.POST.get('message_id', '1')
        notis = Notification.objects.filter(id=message_id)
        if notis.count() > 0:
            noti = notis[0]
            noti.status = 'read'
            noti.save()
        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getsentmessages(request):

    if request.method == 'POST':

        import datetime

        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        notiList = []

        notis = Sent.objects.filter(sender_id=me.pk).order_by('-id')

        for noti in notis:
            members = Member.objects.filter(id=noti.member_id)
            if members.count() > 0:
                receiver = members[0]
                nfs = Notification.objects.filter(id=noti.noti_id)
                if nfs.count() > 0:
                    notification = nfs[0]
                    notification.notified_time = datetime.datetime.fromtimestamp(float(int(notification.notified_time)/1000)).strftime("%b %d, %Y %H:%M")

                    receiver_serializer = MemberSerializer(receiver, many=False)
                    noti_serializer = NotificationSerializer(notification, many=False)
                    data = {
                        'sender':receiver_serializer.data,
                        'noti': noti_serializer.data
                    }

                    notiList.append(data)

        resp = {'result_code': '0', 'data': notiList}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def replymessage(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')
        member_id = request.POST.get('member_id', '1')
        noti_id = request.POST.get('noti_id', '1')
        message = request.POST.get('message', '')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        members = Member.objects.filter(id=int(member_id))
        if members.count() > 0:
            member = members[0]

            # title = 'You\'ve received a message from VaCay Community'
            # subject = 'From VaCay Community'
            # msg = 'Dear ' + member.name + ',<br><br>'
            # msg = msg + message

            # from_email = me.email
            # to_emails = []
            # to_emails.append(member.email)
            # send_mail_message(from_email, to_emails, title, subject, msg)

            msg = member.name + ', You\'ve received a reply message from MotherWise Community.\nThe message is as following:\n' + message

            notification = Notification()
            notification.member_id = member.pk
            notification.sender_id = me.pk
            notification.message = msg
            notification.notified_time = str(int(round(time.time() * 1000)))
            notification.save()

            rcv = Received()
            rcv.member_id = member.pk
            rcv.sender_id = me.pk
            rcv.noti_id = notification.pk
            rcv.save()

            snt = Sent()
            snt.member_id = member.pk
            snt.sender_id = me.pk
            snt.noti_id = notification.pk
            snt.save()

            replieds = Replied.objects.filter(noti_id=noti_id)
            if replieds.count() == 0:
                nfs = Notification.objects.filter(id=noti_id)
                if nfs.count() > 0:
                    noti = nfs[0]
                    replied = Replied()
                    replied.root_id = noti.pk
                    replied.noti_id = noti.pk
                    replied.save()

                    replied = Replied()
                    replied.root_id = noti.pk
                    replied.noti_id = notification.pk
                    replied.save()
            else:
                repl = replieds[0]
                replied = Replied()
                replied.root_id = repl.root_id
                replied.noti_id = notification.pk
                replied.save()

            #####################################################################################################################################################################

            db = firebase.database()
            data = {
                "msg": msg,
                "date":str(int(round(time.time() * 1000))),
                "sender_id": str(me.pk),
                "sender_name": me.name,
                "sender_email": me.email,
                "sender_photo": me.photo_url,
                "role": "",
                "type": "message",
                "id": str(notification.pk),
                "mes_id": str(notification.pk)
            }

            db.child("notify").child(str(member.pk)).push(data)
            db.child("notify2").child(str(member.pk)).push(data)

            sendFCMPushNotification(member.pk, me.pk, msg)

            ######################################################################################################################################################################

            if member.playerID != '':
                playerIDList = []
                playerIDList.append(member.playerID)
                msg = member.name + ', You\'ve received a reply message from MotherWise Community.\nThe message is as following:\n' + message
                url = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    url = '/notifications?noti_id=' + str(notification.pk)
                send_push(playerIDList, msg, url)

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))
        else:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))




@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def messagehistory(request):
    if request.method == 'POST':

        noti_id = request.POST.get('message_id', '1')

        import datetime

        list = []

        replieds = Replied.objects.filter(noti_id=noti_id)
        if replieds.count() > 0:
            repl = replieds[0]
            repls = Replied.objects.filter(root_id=repl.root_id)
            for repl in repls:
                notis = Notification.objects.filter(id=repl.noti_id)
                if notis.count() > 0:
                    noti = notis[0]
                    noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                    members = Member.objects.filter(id=noti.sender_id)
                    if members.count() > 0:
                        sender = members[0]
                        sender_serializer = MemberSerializer(sender, many=False)
                        noti_serializer = NotificationSerializer(noti, many=False)
                        data = {
                            'sender':sender_serializer.data,
                            'noti': noti_serializer.data
                        }

                        list.append(data)

        else:
            notis = Notification.objects.filter(id=noti_id)
            if notis.count() > 0:
                noti = notis[0]
                noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                members = Member.objects.filter(id=noti.sender_id)
                if members.count() > 0:
                    sender = members[0]
                    sender_serializer = MemberSerializer(sender, many=False)
                    noti_serializer = NotificationSerializer(noti, many=False)
                    data = {
                        'sender':sender_serializer.data,
                        'noti': noti_serializer.data
                    }

                    list.append(data)

        resp = {'result_code': '0', 'data': list}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def newnotis(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        unreadNotiList = []
        notis = Received.objects.filter(member_id=me.pk)
        for noti in notis:
            nfs = Notification.objects.filter(id=noti.noti_id)
            if nfs.count() > 0:
                notification = nfs[0]
                if notification.status == '':
                    unreadNotiList.append(notification)

        resp = {'result_code': '0', 'unreads': str(len(unreadNotiList))}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getconfs(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        confs = Conference.objects.filter(member_id=me.admin_id).order_by('-id')
        confs = getConferences(confs, me)

        serializer = ConferenceSerializer(confs, many=True)

        resp = {'result_code': '0', 'data': serializer.data}
        return HttpResponse(json.dumps(resp))


def getConferences(confs, me):
    import datetime
    confList = []
    for conf in confs:
        conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
        if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
        if conf.group_id != '':
            groups = Group.objects.filter(id=int(conf.group_id))
            if groups.count() > 0:
                group = groups[0]
                gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                if gms.count() > 0:
                    conf.gname = group.name
                    confList.append(conf)
        elif conf.cohort != '':
            mbs = Member.objects.filter(id=me.pk, cohort=conf.cohort)
            if mbs.count() > 0:
                conf.gname = conf.cohort
                confList.append(conf)
    return confList



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def changepassword(request):

    if request.method == 'POST':

        email = request.POST.get('email', '')
        oldpassword = request.POST.get('oldpassword', '')
        newpassword = request.POST.get('newpassword', '')

        members = Member.objects.filter(email=email)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        if oldpassword == me.password:
            me.password = newpassword
            me.save()

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))

        else:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def openconference(request):

    if request.method == 'POST':

        me_id = request.POST.get('member_id', '1')
        conf_id = request.POST.get('conf_id', '1')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        # cfs = Conference.objects.filter(id=conf_id, status='notified')
        cfs = Conference.objects.filter(id=conf_id)
        if cfs.count() == 0:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))

        conf = cfs[0]

        group_id = conf.group_id
        cohort = conf.cohort

        memberList = []
        if group_id != '' and int(group_id) > 0:
            group = None
            groups = Group.objects.filter(member_id=me.admin_id, id=group_id).order_by('-id')
            if groups.count() > 0:
                group = groups[0]
                gMembers = GroupMember.objects.filter(group_id=group.pk)
                for gMember in gMembers:
                    members = Member.objects.filter(id=gMember.member_id, status='')
                    if members.count() > 0:
                        memberList.append(members[0])

                admin = Member.objects.get(id=me.admin_id)
                memberList.insert(0,admin)

        elif cohort != '':
            members = Member.objects.filter(admin_id=me.admin_id, cohort=cohort, status='')
            if members.count() > 0:
                for member in members:
                    memberList.append(member)

                admin = Member.objects.get(id=me.admin_id)
                memberList.insert(0,admin)

        users_serializer = MemberSerializer(memberList, many=True)

        resp = {'result_code': '0', 'users': users_serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getgroupmembers(request):

    import datetime

    if request.method == 'POST':

        me_id = request.POST.get('member_id', '1')
        groupid = request.POST.get('group_id','')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        memberList = []
        for member in members:
            gms = GroupMember.objects.filter(group_id=groupid, member_id=member.pk)
            if gms.count() > 0:
                if member.pk != me.pk and member.status == '':
                    if member.registered_time != '':
                        member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
                    member.username = '@' + member.email[0:member.email.find('@')]
                    memberList.append(member)

        admin = Member.objects.get(id=me.admin_id)
        admin.username = '@' + admin.email[0:admin.email.find('@')]
        memberList.insert(0,admin)

        users_serializer = MemberSerializer(memberList, many=True)

        resp = {'result_code': '0', 'users': users_serializer.data}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def getgroupconfs(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')
        group_id = request.POST.get('group_id', '1')
        cohort = request.POST.get('cohort', '')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        confs = []

        if group_id != '' and int(group_id) > 0:
            confs = Conference.objects.filter(member_id=me.admin_id, group_id=group_id).order_by('-id')
        elif cohort != '':
            confs = Conference.objects.filter(member_id=me.admin_id, cohort=cohort).order_by('-id')

        confs = getConferences(confs, me)
        serializer = ConferenceSerializer(confs, many=True)

        resp = {'result_code': '0', 'data': serializer.data}
        return HttpResponse(json.dumps(resp))





@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def notifygroupchatmembers(request):
    if request.method == 'POST':

        message = request.POST.get('message', '')
        cohort = request.POST.get('cohort', '')
        groupid = request.POST.get('group_id', '')
        members_json_str = request.POST.get('members', '')

        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        admin = Member.objects.get(id=me.admin_id)

        if groupid != '':
            groups = Group.objects.filter(id=int(groupid))
            if groups.count() == 0:
                resp = {'result_code': '2'}
                return HttpResponse(json.dumps(resp))

            group = groups[0]

            if members_json_str != '':
                try:
                    decoded = json.loads(members_json_str)
                    for data in decoded['members']:

                        member_id = data['member_id']
                        name = data['name']

                        members = Member.objects.filter(id=int(member_id))
                        if members.count() > 0:
                            member = members[0]

                            title = 'MotherWise Community: The Nest'
                            subject = 'You\'ve received a community message from ' + group.name
                            msg = 'Dear ' + member.name + ', You\'ve received a community message from ' + me.name + ' in ' + group.name + '. The message is as following:<br><br>'
                            msg = msg + message + '<br><br>'

                            if member.cohort == 'admin':
                                msg = msg + '<a href=\'' + settings.URL + '/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>Connect the community to view message</a>'
                            else:
                                msg = msg + '<a href=\'' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>Connect the community to view message</a>'

                            from_email = settings.ADMIN_EMAIL
                            to_emails = []
                            to_emails.append(member.email)
                            send_mail_message(from_email, to_emails, title, subject, msg)

                            msg = member.name + ', You\'ve received a community message from ' + me.name + ' in ' + group.name + '. The message is as following:\n\n'
                            msg = msg + message + '\n\n'

                            if member.cohort == 'admin':
                                msg = msg + 'Click on this link to view the message: ' + settings.URL + '/open_group_chat?group_id=' + groupid
                            else:
                                msg = msg + 'Click on this link to view the message: ' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid

                            notification = Notification()
                            notification.member_id = member.pk
                            notification.sender_id = me.pk
                            notification.message = msg
                            notification.notified_time = str(int(round(time.time() * 1000)))
                            notification.save()

                            rcv = Received()
                            rcv.member_id = member.pk
                            rcv.sender_id = me.pk
                            rcv.noti_id = notification.pk
                            rcv.save()

                            snt = Sent()
                            snt.member_id = member.pk
                            snt.sender_id = me.pk
                            snt.noti_id = notification.pk
                            snt.save()

                            #####################################################################################################################################################################

                            db = firebase.database()
                            data = {
                                "msg": msg,
                                "date":str(int(round(time.time() * 1000))),
                                "sender_id": str(me.pk),
                                "sender_name": me.name,
                                "sender_email": me.email,
                                "sender_photo": me.photo_url,
                                "role": "",
                                "type": "group_chat",
                                "id": str(group.pk),
                                "mes_id": str(notification.pk)
                            }

                            db.child("notify").child(str(member.pk)).push(data)
                            db.child("notify2").child(str(member.pk)).push(data)

                            sendFCMPushNotification(member.pk, me.pk, msg)

                            ######################################################################################################################################################################

                            if member.playerID != '':
                                playerIDList = []
                                playerIDList.append(member.playerID)
                                url = '/mothers/notifications?noti_id=' + str(notification.pk)
                                if member.cohort == 'admin':
                                    url = '/notifications?noti_id=' + str(notification.pk)
                                send_push(playerIDList, msg, url)

                    resp = {'result_code': '0'}
                    return HttpResponse(json.dumps(resp))

                except:
                    resp = {'result_code': '3'}
                    return HttpResponse(json.dumps(resp))

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))


        elif cohort != '':

            if members_json_str != '':
                try:
                    decoded = json.loads(members_json_str)
                    for data in decoded['members']:

                        member_id = data['member_id']
                        name = data['name']

                        members = Member.objects.filter(id=int(member_id))
                        if members.count() > 0:
                            member = members[0]

                            title = 'MotherWise Community: The Nest'
                            subject = 'You\'ve received a group message from ' + cohort
                            msg = 'Dear ' + member.name + ', You\'ve received a group message from ' + me.name + ' in ' + cohort + '. The message is as following:<br><br>'
                            msg = msg + message + '<br><br>'

                            if member.cohort == 'admin':
                                msg = msg + '<a href=\'' + settings.URL + '/group_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>Connect the group to view message</a>'
                            else:
                                msg = msg + '<a href=\'' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>Connect the group to view message</a>'

                            from_email = settings.ADMIN_EMAIL
                            to_emails = []
                            to_emails.append(member.email)
                            send_mail_message(from_email, to_emails, title, subject, msg)

                            msg = member.name + ', You\'ve received a group message from ' + me.name + ' in ' + cohort + '. The message is as following:\n\n'
                            msg = msg + message + '\n\n'

                            if member.cohort == 'admin':
                                msg = msg + 'Click on this link to view the message: ' + settings.URL + '/group_cohort_chat?cohort=' + cohort
                            else:
                                msg = msg + 'Click on this link to view the message: ' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort

                            notification = Notification()
                            notification.member_id = member.pk
                            notification.sender_id = me.pk
                            notification.message = msg
                            notification.notified_time = str(int(round(time.time() * 1000)))
                            notification.save()

                            rcv = Received()
                            rcv.member_id = member.pk
                            rcv.sender_id = me.pk
                            rcv.noti_id = notification.pk
                            rcv.save()

                            snt = Sent()
                            snt.member_id = member.pk
                            snt.sender_id = me.pk
                            snt.noti_id = notification.pk
                            snt.save()

                            #####################################################################################################################################################################

                            db = firebase.database()
                            data = {
                                "msg": msg,
                                "date":str(int(round(time.time() * 1000))),
                                "sender_id": str(me.pk),
                                "sender_name": me.name,
                                "sender_email": me.email,
                                "sender_photo": me.photo_url,
                                "role": "",
                                "type": "cohort_chat",
                                "id": cohort,
                                "mes_id": str(notification.pk)
                            }

                            db.child("notify").child(str(member.pk)).push(data)
                            db.child("notify2").child(str(member.pk)).push(data)

                            sendFCMPushNotification(member.pk, me.pk, msg)

                            ######################################################################################################################################################################

                            if member.playerID != '':
                                playerIDList = []
                                playerIDList.append(member.playerID)
                                url = '/mothers/notifications?noti_id=' + str(notification.pk)
                                if member.cohort == 'admin':
                                    url = '/notifications?noti_id=' + str(notification.pk)
                                send_push(playerIDList, msg, url)


                    resp = {'result_code': '0'}
                    return HttpResponse(json.dumps(resp))

                except:
                    resp = {'result_code': '3'}
                    return HttpResponse(json.dumps(resp))

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def fcmregister(request):
    if request.method == 'POST':

        member_id = request.POST.get('member_id', '1')
        token = request.POST.get('fcm_token', '')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        if token != '':
            me.fcm_token = token
            me.save()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))



def sendFCMPushNotification(member_id, sender_id, notiText):
    members = Member.objects.filter(id=member_id)
    if members.count() > 0:
        member = members[0]
        message_title = 'VaCay User'
        if int(sender_id) > 0:
            senders = Member.objects.filter(id=sender_id)
            if senders.count() > 0:
                sender = senders[0]
                message_title = sender.name
        path_to_fcm = "https://fcm.googleapis.com"
        server_key = settings.FCM_LEGACY_SERVER_KEY
        reg_id = member.fcm_token #quick and dirty way to get that ONE fcmId from table
        if reg_id != '':
            message_body = notiText
            result = FCMNotification(api_key=server_key).notify_single_device(registration_id=reg_id, message_title=message_title, message_body=message_body, sound = 'ping.aiff', badge = 1)



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def sendfcmpush(request):
    if request.method == 'POST':

        sender_id = request.POST.get('sender_id', '1')
        receiver_id = request.POST.get('receiver_id', '1')
        message = request.POST.get('message', '')

        sendFCMPushNotification(receiver_id, sender_id, message)

        senders = Member.objects.filter(id=sender_id)
        if senders.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        sender = senders[0]

        members = Member.objects.filter(id=receiver_id)
        if members.count() > 0:
            member = members[0]
            if member.playerID != '':
                playerIDList = []
                playerIDList.append(member.playerID)
                url = '/mothers/to_private_chat?member_id=' + str(sender.pk)
                if member.cohort == 'admin':
                    url = '/group_private_chat?email=' + sender.email
                msg = member.name + ', You\'ve received a message from ' + sender.name + '.\nThe message is as following:\n' + message
                send_push(playerIDList, msg, url)

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def requestvideocall(request):
    if request.method == 'POST':

        sender_id = request.POST.get('sender_id', '1')
        receiver_id = request.POST.get('receiver_id', '1')
        alias = request.POST.get('alias', '')
        action = request.POST.get('action', '')

        message = 'You have a call'
        if action == 'call_missed':
            message = 'Missed a call'
        sendFCMPushNotification(receiver_id, sender_id, message)

        senders = Member.objects.filter(id=sender_id)
        if senders.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        sender = senders[0]

        receivers = Member.objects.filter(id=receiver_id)
        if receivers.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        receiver = receivers[0]

        db = firebase.database()
        data = {
            "msg": message,
            "date":str(int(round(time.time() * 1000))),
            "sender_id": str(sender.pk),
            "sender_name": sender.name,
            "sender_email": sender.email,
            "sender_photo": sender.photo_url,
            "role": "",
            "type": action,
            "id": alias,
            "mes_id": "0"
        }

        if action == 'call_missed':
            db.child("call").child(str(receiver.pk)).child(str(sender.pk)).remove()

        db.child("call").child(str(receiver.pk)).child(str(sender.pk)).push(data)
        db.child("notify2").child(str(receiver.pk)).push(data)

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def readterms(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')
        members = Member.objects.filter(id=member_id)
        if members.count() == 0 :
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))
        member = members[0]
        member.status2 = "read_terms"
        member.save()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def reportmember(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')
        reporter_id = request.POST.get('reporter_id', '1')
        message = request.POST.get('message', '')
        members = Member.objects.filter(id=member_id)
        if members.count() == 0 :
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))
        report = Report()
        report.member_id = member_id
        report.reporter_id = reporter_id
        report.message = message
        report.reported_time = str(int(round(time.time() * 1000)))
        report.save()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))

































