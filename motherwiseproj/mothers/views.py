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
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from selenium import webdriver
from django.db.models import Q
from pbsonesignal import PybossaOneSignal

from pyfcm import FCMNotification

from motherwise.models import Member, Contact, Group, GroupMember, GroupConnect, Post, PostUrlPreview, Comment, PostPicture, PostLike, Notification, Received, Sent, Replied, Conference, Report, PostBlock, PostCategory
from motherwise.models import Cohort, CommentLike
from motherwise.serializers import PostUrlPreviewSerializer, PostSerializer, CommentSerializer

import pyrebase

config = {
    "apiKey": "AIzaSyDveaXbV1HHMREyZzbvQe53BJEHVIRCf14",
    "authDomain": "motherwise-1585202524394.firebaseapp.com",
    "databaseURL": "https://motherwise-1585202524394.firebaseio.com",
    "storageBucket": "motherwise-1585202524394.appspot.com"
}

firebase = pyrebase.initialize_app(config)


def member_login_page(request):
    # return redirect('/mothers/logout')
    try:
        if request.session['memberID'] != '' and request.session['memberID'] != 0:
            member_id = request.session['memberID']
            members = Member.objects.filter(id=member_id)
            if members.count() == 0:
                return render(request, 'mothers/login.html')
            member = members[0]

            c = Cohort.objects.filter(admin_id=member.admin_id).first()
            cohorts = []
            if c is not None:
                if c.cohorts != '': cohorts = c.cohorts.split(',')

            if member.cohort == 'admin':
                return render(request, 'mothers/login.html')
            if member.cohort == '' or member.phone_number == '':
                return render(request, 'mothers/register_profile.html', {'member':member, 'cohorts':cohorts})
            elif member.address == '' or member.city == '':
                return  render(request, 'mothers/location_picker.html', {'address':member.address})
            else:
                return redirect('/mothers/zzzzz')
                # return redirect('/mothers/zzzzz')
    except KeyError:
        print('no session')
    return render(request, 'mothers/login.html')


def firstpage(request):
    return  render(request, 'mothers/login.html')



@api_view(['GET', 'POST'])
def member_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        playerID = request.POST.get('playerID', '')

        members = Member.objects.filter(email=email, password=password)
        if members.count() > 0:
            member = members[0]
            if member.cohort == 'admin':
                return render(request, 'mothers/login.html',
                          {'notice': 'This account is not allowed to login as a member.'})
            if playerID != '':
                member.playerID = playerID
                request.session['playerID'] = playerID
            member.save()

            request.session['memberID'] = member.pk

            c = Cohort.objects.filter(admin_id=member.admin_id).first()
            cohorts = []
            if c is not None:
                if c.cohorts != '': cohorts = c.cohorts.split(',')

            if member.registered_time == '':
                return render(request, 'mothers/register_profile.html', {'member':member, 'cohorts':cohorts})
            elif member.address == '':
                return  render(request, 'mothers/location_picker.html', {'address':member.address})
            else:
                return redirect('/mothers/zzzzz')
                # return redirect('/mothers/home')
        else:
            return render(request, 'mothers/login.html',
                          {'notice': 'The email or password is incorrect.'})

    else:
        return redirect('/mothers/')


def complete_profile(request):
    return HttpResponse('Home page')




def memberhome(request):
    import datetime
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    if me.cohort == '':
        return render(request, 'mothers/edit_profile.html', {'member':me, 'option':'edit profile', 'note':'add_cohort', 'cohorts':cohorts})

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

    return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohorts':cohorts})



##################################################################################### Post Home ######################################################################################################


def posthome(request):
    import datetime
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    if me.email != 'xxx':

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        if me.cohort == '':
            return render(request, 'mothers/edit_profile.html', {'member':me, 'option':'edit profile', 'note':'add_cohort', 'cohorts':cohorts})

        groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
        groupList = []
        for group in groups:
            gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
            if gms.count() > 0:
                groupList.append(group)

        admin = Member.objects.get(id=me.admin_id)

        postlist = []

        senderids = list(Notification.objects.filter(member_id=me.pk).values_list('sender_id', flat=True).distinct())
        memberlist = []
        for senderid in senderids:
            sender = Member.objects.filter(id=senderid).first()
            if sender is not None and sender.cohort != 'admin':
                memberlist.insert(0, sender)
        memberlist.insert(0, Member.objects.filter(cohort='admin').first())

        posts = Post.objects.filter(Q(sch_status='') & ~Q(status__icontains='top'))
        total_count = posts.count()
        posts = posts.order_by('-id')[:25]
        for post in posts:
            pp_cnt = PostPicture.objects.filter(post_id=post.pk).count() - 1
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''
            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())
            post.content = emoji.emojize(post.content)
            memb = Member.objects.filter(id=post.member_id).first()
            if memb is not None:
                memb.registered_time = datetime.datetime.fromtimestamp(float(int(memb.registered_time)/1000)).strftime("%b %d, %Y")
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                    comments1 = comments[:5]
                    commentlist = []
                    for comment in comments1:
                        cm = Member.objects.filter(id=comment.member_id).first()
                        if cm is not None:
                            comment.comment_text = emoji.emojize(comment.comment_text)
                            commentlist.append( { 'comment':comment, 'member':cm } )
                    data = {
                        'member':memb,
                        'post': post,
                        'prevs': prevs,
                        'pp_cnt': str(pp_cnt),
                        'comments': commentlist,
                        'pc-cnt': str(comments.count()),
                    }
                    postlist.append(data)

        top_posts = Post.objects.filter(sch_status='', status__icontains='top').order_by('-id')
        total_count += top_posts.count()
        for post in top_posts:
            pp_cnt = PostPicture.objects.filter(post_id=post.pk).count() - 1
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''
            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())
            post.content = emoji.emojize(post.content)
            memb = Member.objects.filter(id=post.member_id).first()
            if memb is not None:
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    memb.registered_time = datetime.datetime.fromtimestamp(float(int(memb.registered_time)/1000)).strftime("%b %d, %Y")
                    prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                    comments1 = comments[:5]
                    commentlist = []
                    for comment in comments1:
                        cm = Member.objects.filter(id=comment.member_id).first()
                        if cm is not None:
                            comment.comment_text = emoji.emojize(comment.comment_text)
                            commentlist.append( { 'comment':comment, 'member':cm } )

                    data = {
                        'member': memb,
                        'post': post,
                        'prevs': prevs,
                        'pp_cnt': str(pp_cnt),
                        'comments': commentlist,
                        'pc-cnt': str(comments.count()),
                    }
                    postlist.insert(0,data)

        pst = None
        try:
            post_id = request.GET['post_id']
            pst = Post.objects.filter(id=post_id).first()
        except KeyError:
            pass

        return render(request, 'mothers/testhome.html', {'me':me, 'admin':admin, 'groups':groupList, 'list':postlist, 'pst':pst, 'cohorts':cohorts, 'contactors':memberlist, 'total_count':str(total_count)})

    else:

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        uitype = ''
        if request.user_agent.is_mobile:
            uitype = 'mobile'

        if me.cohort == '':
            return render(request, 'mothers/edit_profile.html', {'member':me, 'option':'edit profile', 'note':'add_cohort', 'cohorts':cohorts})

        groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
        groupList = []
        for group in groups:
            gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
            if gms.count() > 0:
                groupList.append(group)

        admin = Member.objects.get(id=me.admin_id)

        list1 = []
        list2 = []
        list3 = []
        list4 = []

        allPosts = Post.objects.filter(sch_status='').order_by('-id')
        i = 0
        itop = 1
        for post in allPosts:
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''
            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())
            post.content = emoji.emojize(post.content)
            members = Member.objects.filter(id=post.member_id)
            if members.count() > 0:
                memb = members[0]
                if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                    prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                    data = {
                        'member':memb,
                        'post': post,
                        'prevs': prevs,
                    }

                    if uitype == 'mobile':
                        if 'top' in post.status:
                            list1.insert(0,data)
                        else:
                            if i % 4 == 1: list1.append(data)
                            elif i % 4 == 2: list2.append(data)
                            elif i % 4 == 3: list3.append(data)
                            elif i % 4 == 0: list4.append(data)
                    else:
                        if 'top' in post.status:
                            if itop == 1:
                                list1.insert(0,data)
                                itop = 2
                            elif itop == 2:
                                list2.insert(0,data)
                                itop = 3
                            elif itop == 3:
                                list3.insert(0,data)
                                itop = 4
                            elif itop == 4:
                                list4.insert(0,data)
                                itop = 1
                        else:
                            if i % 4 == 1: list1.append(data)
                            elif i % 4 == 2: list2.append(data)
                            elif i % 4 == 3: list3.append(data)
                            elif i % 4 == 0: list4.append(data)

        pst = None
        try:
            post_id = request.GET['post_id']
            posts = Post.objects.filter(id=post_id)
            if posts.count() > 0:
                pst = posts[0]
        except KeyError:
            print('no key')

        return render(request, 'mothers/newhome.html', {'me':me, 'admin':admin, 'groups':groupList, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'pst':pst, 'cohorts':cohorts})



#######################################################################################################################################################################################################



def torequestpwd(request):
    return  render(request, 'mothers/forgot_password.html')




@api_view(['GET', 'POST'])
def send_mail_forgotpassword(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')

        members = Member.objects.filter(email=email)
        memberList = []
        for member in members:
            if member.cohort != 'admin': memberList.append(member)
        if len(memberList) == 0:
            return render(request, 'mothers/forgot_password.html',
                          {'notice': 'This email does not exist for participants. Please try another one.'})

        me = memberList[0]
        admin = Member.objects.get(id=me.admin_id)

        message = 'You are allowed to reset your password from your request.<br>For it, please click this link to reset your password.<br><br><a href=\'' + 'https://www.vacay.company/mothers/resetpassword?email=' + email
        message = message + '\' target=\'_blank\'>' + 'Link to reset password' + '</a>'

        html =  """\
                    <html>
                        <head></head>
                        <body>
                            <a href="#"><img src="https://www.vacay.company/static/images/logo.png" style="width:120px;height:120px; margin-left:25px;"/></a>
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

        return render(request, 'mothers/forgot_password.html',
                          {'notice': 'We sent a message to your email. Please check and reset your password.'})


def resetpassword(request):
    email = request.GET['email']
    return render(request, 'mothers/resetpwd.html', {'email':email})



@api_view(['GET', 'POST'])
def rstpwd(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        members = Member.objects.filter(email=email)
        if members.count() == 0:
            return render(request, 'motherwise/result.html',
                          {'response': 'This email doesn\'t exist.'})

        member = members[0]
        member.password = password
        member.save()

        return render(request, 'mothers/login.html', {'notify':'password changed'})


def pick_location(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    address = request.GET['address']

    return  render(request, 'mothers/location_picker.html', {'address':address})



@api_view(['GET', 'POST'])
def attach_location_profile(request):
    if request.method == 'POST':
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')

        # return HttpResponse(lat)

        try:
            if request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        me.address = address
        me.city = city
        me.lat = lat
        me.lng = lng
        me.save()

        return redirect('/mothers/zzzzz')



@api_view(['GET', 'POST'])
def register_profile(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        password = request.POST.get('password', '')
        phone_number = request.POST.get('phone_number', '')
        cohort = request.POST.get('cohort', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')
        playerID = request.POST.get('playerID', '')

        fs = FileSystemStorage()

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        me.name = name
        if password != '':
            me.password = password
        me.phone_number = phone_number
        if me.photo_url == '':
            me.photo_url = settings.URL + '/static/images/ic_profile.png'
        me.cohort = cohort
        if address != '': me.address = address
        if city != '':
            me.city = city
            me.address = city
        if lat != '': me.lat = lat
        if lng != '': me.lng = lng
        me.registered_time = str(int(round(time.time() * 1000)))
        if playerID != '':
            me.playerID = playerID
            request.session['playerID'] = playerID

        try:
            private = request.POST.get('private', '')
            if private != '':
                me.status = 'private'
            else:
                me.status = ''
        except KeyError:
            print('no key')

        try:
            photo = request.FILES['photo']

            # x = request.POST.get('x', '0')
            # y = request.POST.get('y', '0')
            # w = request.POST.get('w', '32')
            # h = request.POST.get('h', '32')
            # #  return HttpResponse(w)
            # photo = profile_process(photo, x, y, w, h)

            filename = fs.save(photo.name, photo)
            uploaded_url = fs.url(filename)
            if me.filename != '':
                fs.delete(me.filename)
            elif me.photo_url != '' and '/static/images/ic_profile.png' not in me.photo_url:
                fs.delete(me.photo_url.replace(settings.URL + '/media/', ''))
            me.photo_url = settings.URL + uploaded_url
            me.filename = filename

        except MultiValueDictKeyError:
            print('no file found')
        except ValueError:
            print('No cropping')

        me.save()

        try:
            option = request.POST.get('option', '')
            if option == 'update':
                return redirect('/mothers/account/')
        except KeyError:
            print('no key')

        # return render(request, 'mothers/location_picker.html', {'address':me.address})
        return redirect('/mothers/zzzzz')


from PIL import Image
from mothers.uploadedfile import InMemoryUploadedFile

def profile_process(image, x, y, w, h):
    # return HttpResponse(w)
    x = float(x)
    y = float(y)
    w = float(w)
    h = float(h)
    # return HttpResponse(w)
    file = None
    try:
        thumb_io = io.BytesIO()
        image_file = Image.open(image)
        # resized_image = image_file.resize((600, int(250 * image_file.height / image_file.width)), Image.ANTIALIAS)
        cropped_image = image_file.crop((x, y, w + x, h + y))
        # resized_image = cropped_image.resize((160, 160), Image.ANTIALIAS)
        cropped_image.save(thumb_io, image.content_type.split('/')[-1].upper())

        # creating new InMemoryUploadedFile() based on the modified file
        file = InMemoryUploadedFile(thumb_io,
            u"photo", # important to specify field name here
            "croppedimage.jpg",
            image.content_type,
            None, None)
    except OSError:
        print('Invalid file!')

    return file



def logout(request):
    request.session['memberID'] = 0
    request.session['playerID'] = ''

    return render(request, 'mothers/login.html')



@api_view(['GET', 'POST'])
def contact_selecteds(request):
    if request.method == 'POST':
        ids = request.POST.getlist('users[]')
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        try:
            option = request.POST.get('option','')
            if option == 'private_chat':
                memberList = []
                memberIdList = []
                for member_id in ids:
                    members = Member.objects.filter(id=int(member_id))
                    if members.count() > 0:
                        member = members[0]
                        memberList.append(member)
                        memberIdList.append(member.pk)

                contacts = update_contact(me, "")

                if len(memberList) > 0:
                    request.session['sel_option'] = option
                    request.session['sel_member_list'] = memberIdList
                    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
                else:
                    return redirect('/mothers/zzzzz')
        except KeyError:
            print('no such key')

        message = request.POST.get('message', '')

        for member_id in ids:
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
                subject = 'You\'ve received a message from a member of the Nest (has recibido un mensaje de un miembro de Nest)'
                msg = 'Dear ' + member.name + ', You\'ve received a message from ' + me.name + '. The message is as following:<br><br>'
                msg = msg + message
                rurl = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    rurl = '/manager/notifications?noti_id=' + str(notification.pk)
                msg = msg + '<br><br><a href=\'' + settings.URL + rurl + '\' target=\'_blank\'>Join website</a>'

                title2 = 'Comunidad MotherWise: el Nest'
                msg2 = member.name + ', has recibido un mensaje de ' + me.name + '. el mensaje es el siguiente:<br><br>'
                msg2 = msg2 + message
                rurl = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    rurl = '/manager/notifications?noti_id=' + str(notification.pk)
                msg2 = msg2 + '<br><br><a href=\'' + settings.URL + rurl + '\' target=\'_blank\'>unirse al sitio web</a>'

                from_email = me.email
                to_emails = []
                to_emails.append(member.email)
                send_mail_message0(from_email, to_emails, title, subject, msg, title2, msg2)

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
                    msg = member.name + ', You\'ve received a message from ' + me.name + '.\nThe message is as following:\n' + message
                    msg2 = member.name + ', has recibido un mensaje de ' + me.name + '.\nel mensaje es el siguiente:\n' + message
                    msg = msg + '\n\n' + msg2
                    url = '/mothers/notifications?noti_id=' + str(notification.pk)
                    if member.cohort == 'admin':
                        url = '/manager/notifications?noti_id=' + str(notification.pk)
                    send_push(playerIDList, msg, url)

        return redirect('/mothers/tohome?note=' + 'Message sent to them.')


    else:
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        memberIdList = []
        try:
            memberIdList = request.session['sel_member_list']
        except KeyError:
            print('No key')

        memberList = []
        for member_id in memberIdList:
            members = Member.objects.filter(id=member_id)
            if members.count() > 0:
                member = members[0]
                memberList.append(member)
        selectedOption = request.session['sel_option']

        contacts = update_contact(me, "")

        if len(memberList) == 0:
            return redirect('/mothers/tohome?note=' + 'Mothers don\'t exist')

        if len(memberList) > 0:
            if selectedOption == 'private_chat':
                return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
            else:
                return redirect('/mothers/zzzzz')
        else:
            return redirect('/mothers/zzzzz')



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


def send_mail_message0(from_email, to_emails, title, subject, message, title2, message2):
    html =  """\
                <html>
                    <head></head>
                    <body>
                        <a href="#"><img src="https://www.vacay.company/static/images/logo.png" style="width:120px;height:120px;border-radius: 8%; margin-left:25px;"/></a>
                        <h2 style="margin-left:10px; color:#02839a;">{title}</h2>
                        <div style="font-size:14px; white-space: pre-line; word-wrap: break-word;">
                            {mes}
                        </div>
                        <h2 style="margin-left:10px; color:#02839a;">{title2}</h2>
                        <div style="font-size:14px; white-space: pre-line; word-wrap: break-word;">
                            {mes2}
                        </div>
                    </body>
                </html>
            """
    html = html.format(title=title, mes=message, title2=title2, mes2=message2)

    msg = EmailMultiAlternatives(subject, '', from_email, to_emails)
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


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



def tohome(request):
    import datetime
    note = request.GET['note']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

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

    return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohorts':cohorts, 'note':note})




@api_view(['GET', 'POST'])
def do_cohort(request):

    import datetime

    if request.method == 'POST':

        try:
            cohort = request.POST.get('cohort','')
            if cohort == '':
                return redirect('/mothers/zzzzz')
            option = request.POST.get('option','')
        except AssertionError:
            return redirect('/mothers/zzzzz')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        try:
            playerID = request.session['playerID']
            if playerID != '':
                me.playerID = playerID
                me.save()
        except: pass

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        admin = Member.objects.get(id=me.admin_id)

        members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        memberList = []
        memberIdList = []
        for member in members:
            if member.cohort.lower() == cohort.lower() and member.pk != me.pk and member.status == '':
                if member.registered_time != '':
                    member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
                memberList.append(member)
                memberIdList.append(member.pk)
        admin = Member.objects.get(id=me.admin_id)
        memberList.insert(0, admin)
        memberIdList.insert(0,admin.pk)

        if len(memberList) == 0:
            return redirect('/mothers/tohome?note=' + 'The group\'s members don\'t exist.')

        request.session['sel_member_list'] = memberIdList
        request.session['sel_option'] = option
        if option == 'members':
            groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
            groupList = []
            for group in groups:
                gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                if gms.count() > 0:
                    groupList.append(group)
            return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohort': cohort, 'cohorts':cohorts})
        elif option == 'private_chat':
            contacts = update_contact(me, "")
            return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
        elif option == 'video':
            members = Member.objects.filter(id=me.pk, cohort=cohort)
            if members.count() == 0:
                return render(request, 'motherwise/result.html',
                          {'response': 'Sorry, you are not a member of the group. Please select your group.'})
            # code = request.POST.get('code','')
            # request.session['conf_code'] = code
            # return redirect('/mothers/open_conference?group_id=0&cohort=' + cohort + '&code=' + code)

            confs = Conference.objects.filter(cohort=cohort).order_by('-id')
            for conf in confs:
                conf.gname = cohort
                conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
            return render(request, 'mothers/conferences.html', {'confs':confs, 'note':cohort})

        elif option == 'group_chat':
            members = Member.objects.filter(admin_id=me.admin_id, cohort=cohort).order_by('-id')
            for member in members:
                member.username = '@' + member.email[0:member.email.find('@')]

            request.session['cohort'] = cohort
            request.session['group_id'] = ''

            memberIdList = []
            memberList = []
            for memb in members:
                if memb.registered_time != '' and memb.pk != me.pk:
                    memberList.append(memb)
                    memberIdList.append(memb.pk)
            admin = Member.objects.get(id=me.admin_id)
            admin.username = '@' + admin.email[0:admin.email.find('@')]
            memberList.insert(0,admin)
            memberIdList.insert(0,admin.pk)
            request.session['sel_member_list'] = memberIdList

            return render(request, 'mothers/cohort_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'cohorts':cohorts})

    else:
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        try:
            playerID = request.session['playerID']
            if playerID != '':
                me.playerID = playerID
                me.save()
        except: pass

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        admin = Member.objects.get(id=me.admin_id)

        memberIdList = []
        try:
            memberIdList = request.session['sel_member_list']
        except KeyError:
            print('No key')

        selectedOption = request.session['sel_option']

        memberList = []
        for member_id in memberIdList:
            members = Member.objects.filter(id=member_id)
            if members.count() > 0:
                member = members[0]
                if member.registered_time != '':
                    member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
                memberList.append(member)

        contacts = update_contact(me, "")

        if len(memberList) > 0:
            if selectedOption == 'private_chat':
                return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
            elif selectedOption == 'members':
                cohort = memberList[0].cohort
                groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
                groupList = []
                for group in groups:
                    gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                    if gms.count() > 0:
                        groupList.append(group)
                return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohort': cohort, 'cohorts':cohorts})
            elif selectedOption == 'video':
                cohort = memberList[0].cohort
                members = Member.objects.filter(id=me.pk, cohort=cohort)
                if members.count() == 0:
                    return render(request, 'motherwise/result.html',
                              {'response': 'Sorry, you are not a member of the group. Please select your group.'})
                # code = request.session['conf_code']
                # return redirect('/mothers/open_conference?group_id=0&cohort=' + cohort + '&code=' + code)
                confs = Conference.objects.filter(cohort=cohort).order_by('-id')
                for conf in confs:
                    conf.gname = cohort
                    conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                    if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
                return render(request, 'mothers/conferences.html', {'confs':confs, 'note':cohort})
            elif selectedOption == 'group_chat':
                cohort = memberList[0].cohort
                members = Member.objects.filter(admin_id=me.admin_id, cohort=cohort).order_by('-id')
                for member in members:
                    member.username = '@' + member.email[0:member.email.find('@')]

                memberList = []
                for memb in members:
                    if memb.registered_time != '' and memb.pk != me.pk:
                        memberList.append(memb)
                admin = Member.objects.get(id=me.admin_id)
                admin.username = '@' + admin.email[0:admin.email.find('@')]
                memberList.insert(0,admin)

                return render(request, 'mothers/cohort_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'cohorts':cohorts})

            else:
                return redirect('/mothers/zzzzz')
        else:
            return redirect('/mothers/zzzzz')


def to_cohort_chat(request):
    cohort = request.GET['cohort']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(admin_id=me.admin_id, cohort=cohort).order_by('-id')
    for member in members:
        member.username = '@' + member.email[0:member.email.find('@')]

    request.session['cohort'] = cohort
    request.session['group_id'] = ''

    memberIdList = []
    memberList = []
    for memb in members:
        if memb.registered_time != '' and memb.pk != me.pk:
            memberList.append(memb)
            memberIdList.append(memb.pk)
    admin = Member.objects.get(id=me.admin_id)
    admin.username = '@' + admin.email[0:admin.email.find('@')]
    memberList.insert(0,admin)
    memberIdList.insert(0,admin.pk)
    request.session['sel_member_list'] = memberIdList

    return render(request, 'mothers/cohort_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'cohorts':cohorts})



def conferences(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    confs = Conference.objects.filter(member_id=me.admin_id).order_by('-id')
    confs = getConferences(confs, me)
    return render(request, 'mothers/conferences.html', {'confs':confs, 'note':'My Videos'})


def getConferences(confs, me):
    import datetime
    confList = []
    for conf in confs:
        conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
        if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
        if conf.group_id != '' and int(conf.group_id) > 0:
            groups = Group.objects.filter(id=int(conf.group_id))
            if groups.count() > 0:
                group = groups[0]
                gm = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk).first()
                if gm is not None:
                    conf.gname = group.name
                    confList.append(conf)
        else:
            conf.gname = 'Everyone'
            confList.append(conf)

    return confList



@api_view(['GET', 'POST'])
def do_group(request):

    import datetime

    if request.method == 'POST':

        try:
            groupid = request.POST.get('groupid','')
            option = request.POST.get('option','')
        except AssertionError:
            return redirect('/mothers/zzzzz')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        memberList = []
        memberIdList = []
        for member in members:
            gms = GroupMember.objects.filter(group_id=groupid, member_id=member.pk)
            if gms.count() > 0:
                if member.pk != me.pk and member.status == '':
                    if member.registered_time != '':
                        member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
                    member.username = '@' + member.email[0:member.email.find('@')]
                    memberList.append(member)
                    memberIdList.append(member.pk)

        admin = Member.objects.get(id=me.admin_id)
        admin.username = '@' + admin.email[0:admin.email.find('@')]
        memberList.insert(0,admin)
        memberIdList.insert(0,admin.pk)

        if len(memberList) == 0:
            return redirect('/mothers/tohome?note=' + 'This community doesn\'t have any member else.')

        request.session['sel_member_list'] = memberIdList
        request.session['sel_option'] = option
        request.session['group_id'] = groupid

        if option == 'members':
            groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
            groupList = []
            for group in groups:
                gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                if gms.count() > 0:
                    groupList.append(group)
            group = Group.objects.get(id=int(groupid))
            return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'group': group, 'cohorts':cohorts})
        elif option == 'private_chat':
            contacts = update_contact(me, "")
            return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
        elif option == 'group_chat':
            groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
            groupList = []
            for group in groups:
                gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                if gms.count() > 0:
                    groupList.append(group)
            group = Group.objects.get(id=int(groupid))
            return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'groups':groupList, 'cohorts':cohorts})
        elif option == 'video':
            gms = GroupMember.objects.filter(group_id=groupid, member_id=me.pk)
            if gms.count() == 0:
                return render(request, 'motherwise/result.html',
                          {'response': 'Sorry, you are not a member of the community. Please select your community.'})
            # code = request.POST.get('code','')
            # request.session['conf_code'] = code
            # return redirect('/mothers/open_conference?group_id=' + groupid + '&cohort=&code=' + code)
            confs = Conference.objects.filter(group_id=groupid).order_by('-id')
            group = Group.objects.get(id=int(groupid))
            for conf in confs:
                conf.gname = group.name
                conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
            return render(request, 'mothers/conferences.html', {'confs':confs, 'note':group.name})

    else:
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        admin = Member.objects.get(id=me.admin_id)

        memberIdList = []
        try:
            memberIdList = request.session['sel_member_list']
        except KeyError:
            print('No key')

        selectedOption = request.session['sel_option']

        memberList = []
        for member_id in memberIdList:
            members = Member.objects.filter(id=member_id)
            if members.count() > 0:
                member = members[0]
                if member.registered_time != '':
                    member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
                member.username = '@' + member.email[0:member.email.find('@')]
                memberList.append(member)

        contacts = update_contact(me, "")
        try:
            groupid = request.session['group_id']
        except KeyError:
            print('key error')
            return redirect('/mothers/zzzzz')

        if len(memberList) > 0:
            if selectedOption == 'members':
                groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
                groupList = []
                for group in groups:
                    gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                    if gms.count() > 0:
                        groupList.append(group)
                group = Group.objects.get(id=int(groupid))
                return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'group': group, 'cohorts':cohorts})
            elif selectedOption == 'private_chat':
                contacts = update_contact(me, "")
                return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
            elif selectedOption == 'group_chat':
                groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
                groupList = []
                for group in groups:
                    gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                    if gms.count() > 0:
                        groupList.append(group)
                group = Group.objects.get(id=int(groupid))
                return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'groups':groupList, 'cohorts':cohorts})
            elif selectedOption == 'video':
                gms = GroupMember.objects.filter(group_id=groupid, member_id=me.pk)
                if gms.count() == 0:
                    return render(request, 'motherwise/result.html',
                              {'response': 'Sorry, you are not a member of the community. Please select your community.'})
                # code = request.session['conf_code']
                # return redirect('/mothers/open_conference?group_id=' + groupid + '&cohort=&code=' + code)
                confs = Conference.objects.filter(group_id=groupid).order_by('-id')
                group = Group.objects.get(id=int(groupid))
                for conf in confs:
                    conf.gname = group.name
                    conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                    if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
                return render(request, 'mothers/conferences.html', {'confs':confs, 'note':group.name})
            else:
                return redirect('/mothers/zzzzz')
        else:
            return redirect('/mothers/zzzzz')




@api_view(['GET', 'POST'])
def search_members(request):
    if request.method == 'POST':
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        search_id = request.POST.get('q', None)
        cohort = ''
        try: cohort = request.POST.get('cohort', '')
        except: pass

        members = Member.objects.filter(admin_id=me.admin_id, status='').order_by('-id')
        memberList = []
        for member in members:
            memberList.append(member)
        admin = Member.objects.get(id=me.admin_id)
        memberList.insert(0, admin)

        memberList, groupList = get_filtered_members_data(me, memberList, search_id)
        return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohorts':cohorts, 'cohort':cohort, 'note':'Searched by ' + search_id})



def get_filtered_members_data(me, members, keyword):
    import datetime
    memberList = []
    for member in members:
        if member.registered_time != '' and member.pk != me.pk:
            if member.registered_time != '':
                    member.registered_time = datetime.datetime.fromtimestamp(float(int(member.registered_time)/1000)).strftime("%b %d, %Y")
            if keyword.lower() in member.name.lower():
                memberList.append(member)
            elif keyword.lower() in member.email.lower():
                memberList.append(member)
            elif keyword.lower() in member.phone_number.lower():
                memberList.append(member)
            elif keyword.lower() in member.cohort.lower():
                memberList.append(member)
            elif keyword.lower() in member.address.lower():
                memberList.append(member)
    groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
    groupList = []
    for group in groups:
        gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
        if gms.count() > 0:
            groupList.append(group)

    return memberList, groupList



def to_private_chat(request):

    member_id = request.GET['member_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(id=member_id)
    if members.count() == 0:
        return redirect('/mothers/zzzzz')

    member = members[0]
    contacts = update_contact(me, "")

    memberList = []
    memberList.insert(0, member)

    memberIdList = []
    memberIdList.insert(0, member.pk)

    request.session['sel_option'] = 'private_chat'
    request.session['sel_member_list'] = memberIdList

    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})



@api_view(['GET', 'POST'])
def send_member_message(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')
        message = request.POST.get('message', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

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
                rurl = '/manager/notifications?noti_id=' + str(notification.pk)
            msg = msg + '<br><br><a href=\'' + settings.URL + rurl + '\' target=\'_blank\'>Join website</a>'

            title2 = 'Comunidad MotherWise: el Nest'
            msg2 = member.name + ', has recibido un mensaje de ' + me.name + '. el mensaje es el siguiente:<br><br>'
            msg2 = msg2 + message
            rurl = '/mothers/notifications?noti_id=' + str(notification.pk)
            if member.cohort == 'admin':
                rurl = '/manager/notifications?noti_id=' + str(notification.pk)
            msg2 = msg2 + '<br><br><a href=\'' + settings.URL + rurl + '\' target=\'_blank\'>unirse al sitio web</a>'

            from_email = me.email
            to_emails = []
            to_emails.append(member.email)
            send_mail_message0(from_email, to_emails, title, subject, msg, title2, msg2)

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
                    url = '/manager/notifications?noti_id=' + str(notification.pk)
                msg = member.name + ', You\'ve received a message from ' + me.name + '.\nThe message is as following:\n' + message
                msg2 = member.name + ', has recibido un mensaje de ' + me.name + '.\nel mensaje es el siguiente:\n' + message
                msg = msg + '\n\n' + msg2
                send_push(playerIDList, msg, url)

            return redirect('/mothers/tohome?note=' + 'Message sent.')
        else:
            return redirect('/mothers/tohome?note=' + 'This member doesn\'t exist.')



def switch_chat(request):

    member_id = request.GET['member_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(id=member_id)
    if members.count() == 0:
        return redirect('/mothers/zzzzz')

    selected_member = members[0]

    memberIdList = []
    try:
        memberIdList = request.session['sel_member_list']
    except KeyError:
        print('No key')

    try:
        selectedOption = request.session['sel_option']
        if len(memberIdList) == 0:
            return redirect('/mothers/zzzzz')
    except: pass

    memberList = []
    for member_id in memberIdList:
        members = Member.objects.filter(id=member_id)
        if members.count() > 0:
            member = members[0]
            memberList.append(member)

    for member in memberList:
        if selected_member.pk == member.pk:
            index = memberList.index(member)
            del memberList[index]
            memberList.insert(0, selected_member)

    if selected_member not in memberList:
        memberList.insert(0,selected_member)
        memberIdList.insert(0, selected_member.pk)

    contacts = update_contact(me, "")

    if len(memberList) == 0:
        return render(request, 'motherwise/result.html', {'response': 'The member doesn\'t exist.'})

    if selectedOption == 'private_chat':
        return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})
    else:
        return redirect('/mothers/zzzzz')



def switch_cohort_chat(request):

    cohort = request.GET['cohort']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    memberList = []
    memberIdList = []
    for member in members:
        if member.cohort.lower() == cohort.lower() and member.pk != me.pk and member.status == '':
            memberList.append(member)
            memberIdList.append(member.pk)

    if len(memberList) == 0:
            return render(request, 'motherwise/result.html',
                          {'response': 'The cohort\'s members don\'t exist.'})

    request.session['sel_member_list'] = memberIdList
    request.session['sel_option'] = 'private_chat'

    contacts = update_contact(me, "")

    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})




def open_group_chat(request):
    group_id = request.GET['group_id']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    memberList = []
    memberIdList = []
    for member in members:
        gms = GroupMember.objects.filter(group_id=group_id, member_id=member.pk)
        if gms.count() > 0:
            if member.pk != me.pk and member.status == '':
                member.username = '@' + member.email[0:member.email.find('@')]
                memberList.append(member)
                memberIdList.append(member.pk)

    admin = Member.objects.get(id=me.admin_id)
    admin.username = '@' + admin.email[0:admin.email.find('@')]
    memberList.insert(0,admin)
    memberIdList.insert(0,admin.pk)

    request.session['sel_member_list'] = memberIdList
    request.session['group_id'] = group_id
    request.session['cohort'] = ''

    groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
    groupList = []
    for group in groups:
        gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
        if gms.count() > 0:
            groupList.append(group)
    group = Group.objects.get(id=int(group_id))
    return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'groups':groupList, 'cohorts':cohorts})



def open_cohort_chat(request):
    cohort = request.GET['cohort']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    memberList = []
    memberIdList = []
    for member in members:
        if member.cohort.lower() == cohort.lower() and member.pk != me.pk and member.status == '':
            member.username = '@' + member.email[0:member.email.find('@')]
            memberList.append(member)
            memberIdList.append(member.pk)

    admin = Member.objects.get(id=me.admin_id)
    admin.username = '@' + admin.email[0:admin.email.find('@')]
    memberList.insert(0,admin)
    memberIdList.insert(0,admin.pk)

    request.session['sel_member_list'] = memberIdList

    request.session['cohort'] = cohort
    request.session['group_id'] = ''

    groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
    groupList = []
    for group in groups:
        gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
        if gms.count() > 0:
            groupList.append(group)
    return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'groups':groupList, 'cohorts':cohorts})


def to_posts(request):
    import datetime
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    uitype = ''
    if request.user_agent.is_mobile:
        uitype = 'mobile'

    users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    userList = []
    for user in users:
        if user.registered_time != '' and user.pk != me.pk:
            user.username = '@' + user.email[0:user.email.find('@')]
            userList.append(user)

    admin = Member.objects.get(id=me.admin_id)
    admin.email = '@' + admin.email[0:admin.email.find('@')]
    userList.insert(0,admin)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    allPosts = Post.objects.filter(sch_status='').order_by('-id')
    i = 0
    itop = 1
    for post in allPosts:
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
        i = i + 1
        pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
        if pl is not None: post.liked = pl.status
        else: post.liked = ''
        comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(likes.count())
        post.content = emoji.emojize(post.content)
        members = Member.objects.filter(id=post.member_id)
        if members.count() > 0:
            memb = members[0]
            if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                comments1 = comments[:5]
                commentlist = []
                for comment in comments1:
                    cm = Member.objects.filter(id=comment.member_id).first()
                    if cm is not None:
                        comment.comment_text = emoji.emojize(comment.comment_text)
                        commentlist.append( { 'comment':comment, 'member':cm } )

                data = {
                    'member':memb,
                    'post': post,
                    'prevs': prevs,
                    'comments': commentlist,
                    'pc-cnt': str(comments.count()),
                }

                if uitype == 'mobile':
                    if 'top' in post.status:
                        list1.insert(0,data)
                    else:
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                else:
                    if 'top' in post.status:
                        if itop == 1:
                            list1.insert(0,data)
                            itop = 2
                        elif itop == 2:
                            list2.insert(0,data)
                            itop = 3
                        elif itop == 3:
                            list3.insert(0,data)
                            itop = 4
                        elif itop == 4:
                            list4.insert(0,data)
                            itop = 1
                    else:
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)

    pst = None
    try:
        post_id = request.GET['post_id']
        posts = Post.objects.filter(id=post_id)
        if posts.count() > 0:
            pst = posts[0]
    except KeyError:
        print('no key')

    categories = []
    pc = PostCategory.objects.filter(admin_id=admin.pk).first()
    if pc is not None:
        if pc.categories != '': categories = pc.categories.split(',')

    return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'users':userList, 'pst':pst, 'categories':categories})


def my_posts(request):
    import datetime
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    uitype = ''
    if request.user_agent.is_mobile:
        uitype = 'mobile'

    users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    userList = []
    for user in users:
        if user.registered_time != '' and user.pk != me.pk:
            user.username = '@' + user.email[0:user.email.find('@')]
            userList.append(user)

    admin = Member.objects.get(id=me.admin_id)
    admin.username = '@' + admin.email[0:admin.email.find('@')]
    userList.insert(0,admin)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    posts = Post.objects.filter(member_id=me.pk).order_by('-id')

    i = 0
    itop = 1
    for post in posts:
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")

        comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(likes.count())
        post.content = emoji.emojize(post.content)

        prevs = PostUrlPreview.objects.filter(post_id=post.pk)

        comments1 = comments[:5]
        commentlist = []
        for comment in comments1:
            cm = Member.objects.filter(id=comment.member_id).first()
            if cm is not None:
                comment.comment_text = emoji.emojize(comment.comment_text)
                commentlist.append( { 'comment':comment, 'member':cm } )

        i = i + 1

        data = {
            'member':me,
            'post': post,
            'prevs': prevs,
            'comments': commentlist,
            'pc-cnt': str(comments.count()),
        }

        if uitype == 'mobile':
            if 'top' in post.status:
                list1.insert(0,data)
            else:
                if i % 4 == 1: list1.append(data)
                elif i % 4 == 2: list2.append(data)
                elif i % 4 == 3: list3.append(data)
                elif i % 4 == 0: list4.append(data)
        else:
            if 'top' in post.status:
                if itop == 1:
                    list1.insert(0,data)
                    itop = 2
                elif itop == 2:
                    list2.insert(0,data)
                    itop = 3
                elif itop == 3:
                    list3.insert(0,data)
                    itop = 4
                elif itop == 4:
                    list4.insert(0,data)
                    itop = 1
            else:
                if i % 4 == 1: list1.append(data)
                elif i % 4 == 2: list2.append(data)
                elif i % 4 == 3: list3.append(data)
                elif i % 4 == 0: list4.append(data)

    categories = []
    pc = PostCategory.objects.filter(admin_id=admin.pk).first()
    if pc is not None:
        if pc.categories != '': categories = pc.categories.split(',')

    return render(request, 'mothers/posts.html', {'me':me, 'member':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'users':userList, 'categories':categories})



@api_view(['GET', 'POST'])
def create_post(request):
    if request.method == 'POST':

        title = request.POST.get('title', '')
        category = request.POST.get('category', '')
        content = request.POST.get('content', '')
        scheduled_time = request.POST.get('scheduled_time', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        try:
            playerID = request.session['playerID']
            if playerID != '':
                me.playerID = playerID
                me.save()
        except: pass

        admin = Member.objects.get(id=me.admin_id)

        post = Post()
        post.member_id = me.pk
        post.title = title
        post.category = category
        post.content = emoji.demojize(content)
        post.scheduled_time = scheduled_time
        post.picture_url = ''
        post.comments = '0'
        post.likes = '0'
        post.loves = '0'
        post.haha = '0'
        post.wow = '0'
        post.sad = '0'
        post.angry = '0'
        post.reactions = '0'
        post.posted_time = str(int(round(time.time() * 1000)))

        try:
            ids = request.POST.getlist('users[]')
            if len(ids) > 0: post.notified_members = ",".join(str(i) for i in ids)
        except KeyError:
            print('No key')

        try:
            ids = request.POST.get('selections','')
            if ids != '': post.notified_members = ids
        except KeyError:
            print('No key')

        if scheduled_time != '': post.sch_status = 'scheduled'
        post.save()

        createPostUrlPreview(post)

        fs = FileSystemStorage()
        i = 0
        for f in request.FILES.getlist('pictures'):
            i = i + 1
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            if i == 1:
                post.picture_url = settings.URL + uploaded_url
                post.save()
            postPicture = PostPicture()
            postPicture.post_id = post.pk
            postPicture.picture_url = settings.URL + uploaded_url
            postPicture.filename = filename
            postPicture.save()


        if post.scheduled_time == '':

            for member_id in ids:
                members = Member.objects.filter(id=int(member_id))
                if members.count() > 0:
                    member = members[0]

                    title = 'MotherWise Community: The Nest'
                    subject = 'You\'ve received a post from ' + me.name
                    msg = 'Dear ' + member.name + ', You\'ve received a post from ' + me.name + '.<br><br>'

                    if member.cohort == 'admin':
                        msg = msg + '<a href=\'' + settings.URL + '/manager/to_post?post_id=' + str(post.pk) + '\' target=\'_blank\'>View the post</a>'
                    else:
                        msg = msg + '<a href=\'' + settings.URL + '/mothers/posts?post_id=' + str(post.pk) + '\' target=\'_blank\'>View the post</a>'

                    title2 = 'Comunidad MotherWise: el Nest'
                    msg2 = member.name + ', has recibido una publicación de ' + me.name + '.<br><br>'

                    if member.cohort == 'admin':
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/manager/to_post?post_id=' + str(post.pk) + '\' target=\'_blank\'>ver la publicación</a>'
                    else:
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/mothers/posts?post_id=' + str(post.pk) + '\' target=\'_blank\'>ver la publicación</a>'

                    from_email = admin.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message0(from_email, to_emails, title, subject, msg, title2, msg2)

                    msg = member.name + ', You\'ve received a message from ' + me.name + '.\n\n'
                    if member.cohort == 'admin':
                        msg = msg + 'Click on this link to view the post: ' + settings.URL + '/manager/to_post?post_id=' + str(post.pk)
                    else:
                        msg = msg + 'Click on this link to view the post: ' + settings.URL + '/mothers/posts?post_id=' + str(post.pk)

                    msg2 = member.name + ', has recibido un mensaje de ' + me.name + '.\n\n'
                    if member.cohort == 'admin':
                        msg2 = msg2 + 'haga clic en este enlace para ver la publicación: ' + settings.URL + '/manager/to_post?post_id=' + str(post.pk)
                    else:
                        msg2 = msg2 + 'haga clic en este enlace para ver la publicación: ' + settings.URL + '/mothers/posts?post_id=' + str(post.pk)

                    msg = msg + '\n\n' + msg2

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

                    ##########################################################################################################################################################################

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

                    #################################################################################################################################################################################

                    if member.playerID != '':
                        playerIDList = []
                        playerIDList.append(member.playerID)
                        url = '/mothers/notifications?noti_id=' + str(notification.pk)
                        if member.cohort == 'admin':
                            url = '/manager/notifications?noti_id=' + str(notification.pk)
                        send_push(playerIDList, msg, url)


        return redirect('/mothers/mineppppp/')



def urlsFromText(str):
    web_urls = re.findall(r'(https?://\S+)', str)
    return web_urls


def createPostUrlPreview(post):
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

                icons = favicon.get(wurl)
                icon = None
                if icons is not None and len(icons) > 0: icon = icons[0]

                upreview = PostUrlPreview()
                upreview.post_id = post.pk
                if wtitle is not None: upreview.title = wtitle
                elif wforcetitle is not None: upreview.title = wforcetitle
                if wdescription is not None: upreview.description = wdescription
                if wimageurl is not None and 'http' in wimageurl: upreview.image_url = wimageurl
                elif wabsoluteimageurl is not None: upreview.image_url = wabsoluteimageurl
                if icon is not None: upreview.icon_url = icon.url
                upreview.site_url = wurl
                upreview.save()
            except:
                print('Error')
                try:
                    driver = webdriver.Chrome()
                    driver.get(wurl)
                    wtitle = driver.title

                    icons = favicon.get(wurl)
                    icon = None
                    if icons is not None and len(icons) > 0: icon = icons[0]

                    upreview = PostUrlPreview()
                    upreview.post_id = post.pk
                    if wtitle is not None: upreview.title = wtitle
                    if icon is not None: upreview.icon_url = icon.url
                    upreview.site_url = wurl
                    upreview.save()
                except:
                    pass
            else:
                pass




def add_post_comment(request):

    import datetime

    post_id = request.GET['post_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    posts = Post.objects.filter(id=post_id, sch_status='')
    if posts.count() == 0: return redirect('/mothers/')

    post = posts[0]

    post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")

    pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
    if pl is not None: post.liked = pl.status
    else: post.liked = ''

    comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
    post.comments = str(comments.count())
    likes = PostLike.objects.filter(post_id=post.pk)
    post.reactions = str(likes.count())
    post.content = emoji.emojize(post.content)

    prevs = PostUrlPreview.objects.filter(post_id=post.pk)

    # return HttpResponse(post.member_id + '///' + str(admin.pk))

    if int(post.member_id) != me.pk:

        ppictures = PostPicture.objects.filter(post_id=post.pk)

        comments = Comment.objects.filter(post_id=post_id, comment_id='0')
        commentList = []
        for comment in comments:
            cl = CommentLike.objects.filter(comment_id=comment.pk, member_id=me.pk).first()
            if cl is not None: comment.liked = cl.status
            else: comment.liked = ''
            cmts = Comment.objects.filter(comment_id=comment.pk)
            comment.comments = str(cmts.count())
            likes = CommentLike.objects.filter(comment_id=comment.pk)
            comment.reactions = str(likes.count())
            comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
            members = Member.objects.filter(id=comment.member_id)
            if members.count() > 0:
                member = members[0]
                comment.comment_text = emoji.emojize(comment.comment_text)
                data = {
                    'comment':comment,
                    'member':member
                }
                commentList.append(data)
        members = Member.objects.filter(id=post.member_id)
        if members.count() == 0: return redirect('/mothers/')
        member = members[0]

        data = {
            'post': post,
            'member': member,
            'pictures':ppictures,
            'prevs': prevs,
        }
        return render(request, 'mothers/comment_test.html', {'post':data, 'me':me, 'comments':commentList})

    else:
        ppictures = PostPicture.objects.filter(post_id=post.pk)
        comments = Comment.objects.filter(post_id=post_id, comment_id='0')
        commentList = []
        for comment in comments:
            cl = CommentLike.objects.filter(comment_id=comment.pk, member_id=me.pk).first()
            if cl is not None: comment.liked = cl.status
            else: comment.liked = ''
            cmts = Comment.objects.filter(comment_id=comment.pk)
            comment.comments = str(cmts.count())
            likes = CommentLike.objects.filter(comment_id=comment.pk)
            comment.reactions = str(likes.count())
            comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
            members = Member.objects.filter(id=comment.member_id)
            if members.count() > 0:
                member = members[0]
                comment.comment_text = emoji.emojize(comment.comment_text)
                data = {
                    'comment':comment,
                    'member':member
                }
                commentList.append(data)

        categories = []
        pc = PostCategory.objects.filter(admin_id=me.admin_id).first()
        if pc is not None:
            if pc.categories != '': categories = pc.categories.split(',')

        data = {
            'post': post,
            'pictures':ppictures,
            'comments':commentList,
            'prevs': prevs,
        }
        return render(request, 'mothers/edit_post.html', {'post':data, 'me':me, 'categories':categories})




@api_view(['GET', 'POST'])
def search_post(request):

    import datetime

    if request.method == 'POST':
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        uitype = ''
        if request.user_agent.is_mobile:
            uitype = 'mobile'

        users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        userList = []
        for user in users:
            if user.registered_time != '' and user.pk != me.pk:
                user.username = '@' + user.email[0:user.email.find('@')]
                userList.append(user)

        admin = Member.objects.get(id=me.admin_id)
        admin.email = '@' + admin.email[0:admin.email.find('@')]
        userList.insert(0,admin)

        search_id = request.POST.get('q', None)
        user_id = request.POST.get('u', '0')
        member = Member.objects.filter(id=user_id).first()
        if member is None: return render(request, 'motherwise/result.html', {'response': 'This member doesn\'t exist.'})

        posts = Post.objects.filter(member_id=user_id, sch_status='').order_by('-id')
        postList = get_filtered_posts_data(me, posts, search_id)

        list1 = []
        list2 = []
        list3 = []
        list4 = []

        i = 0
        itop = 1
        for post in postList:
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1

            pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
            if pl is not None: post.liked = pl.status
            else: post.liked = ''

            comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
            post.comments = str(comments.count())
            likes = PostLike.objects.filter(post_id=post.pk)
            post.reactions = str(likes.count())
            post.content = emoji.emojize(post.content)

            prevs = PostUrlPreview.objects.filter(post_id=post.pk)

            member = Member.objects.get(id=post.member_id)

            comments1 = comments[:5]
            commentlist = []
            for comment in comments1:
                cm = Member.objects.filter(id=comment.member_id).first()
                if cm is not None:
                    comment.comment_text = emoji.emojize(comment.comment_text)
                    commentlist.append( { 'comment':comment, 'member':cm } )

            data = {
                'member':member,
                'post': post,
                'prevs': prevs,
                'comments': commentlist,
                'pc-cnt': str(comments.count()),
            }

            if uitype == 'mobile':
                if 'top' in post.status:
                    list1.insert(0,data)
                else:
                    if i % 4 == 1: list1.append(data)
                    elif i % 4 == 2: list2.append(data)
                    elif i % 4 == 3: list3.append(data)
                    elif i % 4 == 0: list4.append(data)
            else:
                if 'top' in post.status:
                    if itop == 1:
                        list1.insert(0,data)
                        itop = 2
                    elif itop == 2:
                        list2.insert(0,data)
                        itop = 3
                    elif itop == 3:
                        list3.insert(0,data)
                        itop = 4
                    elif itop == 4:
                        list4.insert(0,data)
                        itop = 1
                else:
                    if i % 4 == 1: list1.append(data)
                    elif i % 4 == 2: list2.append(data)
                    elif i % 4 == 3: list3.append(data)
                    elif i % 4 == 0: list4.append(data)

        categories = []
        pc = PostCategory.objects.filter(admin_id=admin.pk).first()
        if pc is not None:
            if pc.categories != '': categories = pc.categories.split(',')

        return render(request, 'mothers/posts.html', {'me':me, 'member':member, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':'Searched', 'users':userList, 'categories':categories})


# import datetime
from datetime import datetime

def get_filtered_posts_data(me, posts, keyword):
    postList = []
    for post in posts:
        members = Member.objects.filter(id=post.member_id)
        if members.count() > 0:
            member = members[0]
            if int(member.admin_id) == int(me.admin_id) or int(post.member_id) == int(me.admin_id):
                if keyword.lower() in post.title.lower():
                    postList.append(post)
                elif keyword.lower() in post.category.lower():
                    postList.append(post)
                elif keyword.lower() in post.content.lower():
                    postList.append(post)
                elif keyword.lower() in post.comments.lower():
                    postList.append(post)
                elif keyword.lower() in post.reactions.lower():
                    postList.append(post)
                elif keyword.lower() in member.name.lower():
                    postList.append(post)
                elif keyword.lower() in member.email.lower():
                    postList.append(post)
                elif keyword.lower() in member.phone_number.lower():
                    postList.append(post)
                elif keyword.lower() in member.cohort.lower():
                    postList.append(post)
                elif keyword.lower() in member.address.lower():
                    postList.append(post)
                else:
                    if keyword.isdigit():
                        keyDateObj = datetime.fromtimestamp(int(keyword)/1000)
                        postDateObj = datetime.fromtimestamp(int(post.posted_time)/1000)
                        if keyDateObj.year == postDateObj.year and keyDateObj.month == postDateObj.month and keyDateObj.day == postDateObj.day:
                            postList.append(post)

    return postList



def filter(request):

    import datetime

    option = request.GET['option']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    uitype = ''
    if request.user_agent.is_mobile:
        uitype = 'mobile'

    users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    userList = []
    for user in users:
        if user.registered_time != '' and user.pk != me.pk:
            user.username = '@' + user.email[0:user.email.find('@')]
            userList.append(user)

    admin = Member.objects.get(id=me.admin_id)
    admin.email = '@' + admin.email[0:admin.email.find('@')]
    userList.insert(0,admin)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    search = 'Searched'

    allPosts = Post.objects.filter(sch_status='').order_by('-id')
    i = 0
    itop = 1
    for post in allPosts:
        i = i + 1

        pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
        if pl is not None: post.liked = pl.status
        else: post.liked = ''

        comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(likes.count())
        post.content = emoji.emojize(post.content)

        prevs = PostUrlPreview.objects.filter(post_id=post.pk)

        comments1 = comments[:5]
        commentlist = []
        for comment in comments1:
            cm = Member.objects.filter(id=comment.member_id).first()
            if cm is not None:
                comment.comment_text = emoji.emojize(comment.comment_text)
                commentlist.append( { 'comment':comment, 'member':cm } )

        members = Member.objects.filter(id=post.member_id)
        if members.count() > 0:
            memb = members[0]
            if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                data = None
                if option == 'last3':
                    if int(round(time.time() * 1000)) - int(post.posted_time) < 3 * 86400 * 1000:
                        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'member':memb,
                            'post': post,
                            'prevs': prevs,
                            'comments': commentlist,
                            'pc-cnt': str(comments.count()),
                        }
                        search = 'Last 3 Days'
                elif option == 'last7':
                    if int(round(time.time() * 1000)) - int(post.posted_time) < 7 * 86400 * 1000:
                        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'member':memb,
                            'post': post,
                            'prevs': prevs,
                            'comments': commentlist,
                            'pc-cnt': str(comments.count()),
                        }
                        search = 'Last 7 Days'
                elif option == 'last30':
                    if int(round(time.time() * 1000)) - int(post.posted_time) < 30 * 86400 * 1000:
                        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'member':memb,
                            'post': post,
                            'prevs': prevs,
                            'comments': commentlist,
                            'pc-cnt': str(comments.count()),
                        }
                        search = 'Last 30 Days'

                if data is not None:
                    if uitype == 'mobile':
                        if 'top' in post.status:
                            list1.insert(0,data)
                        else:
                            if i % 4 == 1: list1.append(data)
                            elif i % 4 == 2: list2.append(data)
                            elif i % 4 == 3: list3.append(data)
                            elif i % 4 == 0: list4.append(data)
                    else:
                        if 'top' in post.status:
                            if itop == 1:
                                list1.insert(0,data)
                                itop = 2
                            elif itop == 2:
                                list2.insert(0,data)
                                itop = 3
                            elif itop == 3:
                                list3.insert(0,data)
                                itop = 4
                            elif itop == 4:
                                list4.insert(0,data)
                                itop = 1
                        else:
                            if i % 4 == 1: list1.append(data)
                            elif i % 4 == 2: list2.append(data)
                            elif i % 4 == 3: list3.append(data)
                            elif i % 4 == 0: list4.append(data)

    categories = []
    pc = PostCategory.objects.filter(admin_id=admin.pk).first()
    if pc is not None:
        if pc.categories != '': categories = pc.categories.split(',')

    return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':search, 'users':userList, 'categories':categories})




@api_view(['GET', 'POST'])
def submit_comment(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '0')
        comment_id = request.POST.get('comment_id', '0')
        content = request.POST.get('content', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        try:
            playerID = request.session['playerID']
            if playerID != '':
                me.playerID = playerID
                me.save()
        except: pass

        fs = FileSystemStorage()

        comments = Comment.objects.filter(post_id=post_id, member_id=me.pk)
        if comments.count() == 0:
            comment = Comment()
            comment.post_id = post_id
            comment.comment_id = comment_id
            comment.member_id = me.pk
            comment.comment_text = emoji.demojize(content)
            comment.comments = '0'
            comment.likes = '0'
            comment.commented_time = str(int(round(time.time() * 1000)))

            try:
                image = request.FILES['image']
                filename = fs.save(image.name, image)
                uploaded_url = fs.url(filename)
                comment.image_url = settings.URL + uploaded_url
                comment.filename = filename
            except MultiValueDictKeyError:
                print('no video updated')

            comment.save()

        else:
            comment = comments[0]
            comment.comment_text = emoji.demojize(content)

            try:
                image = request.FILES['image']
                filename = fs.save(image.name, image)
                uploaded_url = fs.url(filename)
                if comment.image_url != '':
                    fs.delete(comment.image_url.replace(settings.URL + '/media/', ''))
                comment.image_url = settings.URL + uploaded_url
                comment.filename = filename
            except MultiValueDictKeyError:
                print('no video updated')

            comment.save()

        return redirect('/mothers/add_post_comment?post_id=' + post_id)




def delete_post(request):
    post_id = request.GET['post_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    fs = FileSystemStorage()

    posts = Post.objects.filter(id=post_id, sch_status='')
    if posts.count() == 0: return redirect('/mothers/mineppppp/')

    post = posts[0]
    pls = PostLike.objects.filter(post_id=post.pk)
    for pl in pls:
        pl.delete()
    pps = PostPicture.objects.filter(post_id=post.pk)
    for pp in pps:
        if pp.filename != '':
            fs.delete(pp.filename)
        elif pp.picture_url != '':
            fs.delete(pp.picture_url.replace(settings.URL + '/media/', ''))
        pp.delete()
    pcs = Comment.objects.filter(post_id=post.pk)
    for pc in pcs:
        if pc.filename != '':
            fs.delete(pc.filename)
        elif pc.image_url != '':
            fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
        pc.delete()

    post.delete()

    try:
        opt = request.GET['opt']
        if opt == 'home': return redirect('/mothers/zzzzz/')
    except:
        pass

    return redirect('/mothers/mineppppp/')



def delete_comment(request):
    comment_id = request.GET['comment_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    fs = FileSystemStorage()

    pcs = Comment.objects.filter(id=comment_id)
    if pcs.count() > 0:
        pc = pcs[0]
        post_id = pc.post_id
        if pc.filename != '':
            fs.delete(pc.filename)
        elif pc.image_url != '':
            fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
        pc.delete()

        return redirect('/mothers/add_post_comment?post_id=' + post_id)
    else:
        return redirect('/mothers/')


def delete_post_picture(request):
    picture_id = request.GET['picture_id']
    post_id = request.GET['post_id']
    posts = Post.objects.filter(id=post_id)
    if posts.count() == 0:
        return redirect('/mothers/mineppppp/')
    post = posts[0]
    pics = PostPicture.objects.filter(id=picture_id, post_id=post_id)
    fs = FileSystemStorage()
    if pics.count() > 0:
        pic = pics[0]
        if pic.filename != '':
            fs.delete(pic.filename)
        elif pic.picture_url != '':
            fs.delete(pic.picture_url.replace(settings.URL + '/media/', ''))
            if pic.picture_url == post.picture_url:
                post.picture_url = ''
                pics = PostPicture.objects.filter(post_id=post_id)
                if pics.count() > 0:
                    post.picture_url = pics[0].picture_url
                post.save()
        pic.delete()
    return redirect('/mothers/add_post_comment?post_id=' + post_id)


def like_post(request):
    post_id = request.GET['post_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    posts = Post.objects.filter(id=post_id)
    if posts.count() == 0: return redirect('/mothers/posts/')

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
        pl.status = 'like'
        pl.save()

        post.likes = str(int(post.likes) + 1)
        post.save()

    # return redirect('/mothers/add_post_comment?post_id=' + str(post.pk))
    return HttpResponse(post.likes)



@api_view(['GET', 'POST'])
def edit_post(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')
        title = request.POST.get('title', '')
        category = request.POST.get('category', '')
        content = request.POST.get('content', '')
        scheduled_time = request.POST.get('scheduled_time', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        try:
            playerID = request.session['playerID']
            if playerID != '':
                me.playerID = playerID
                me.save()
        except: pass

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            return redirect('/mothers/mineppppp/')
        post = posts[0]
        post.title = title
        post.category = category
        post.content = emoji.demojize(content)
        if post.sch_status != '': post.scheduled_time = scheduled_time
        post.save()

        updatePostUrlPreview(post)

        fs = FileSystemStorage()
        i = 0
        for f in request.FILES.getlist('pictures'):
            i = i + 1
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            if i == 1:
                post.picture_url = settings.URL + uploaded_url
                post.save()
            postPicture = PostPicture()
            postPicture.post_id = post.pk
            postPicture.picture_url = settings.URL + uploaded_url
            postPicture.filename = filename
            postPicture.save()

        return redirect('/mothers/add_post_comment?post_id=' + post_id)


def updatePostUrlPreview(post):
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

                icons = favicon.get(wurl)
                icon = None
                if icons is not None and len(icons) > 0: icon = icons[0]

                upreviews = PostUrlPreview.objects.filter(post_id=post.pk, site_url=wurl)
                if upreviews.count() == 0:
                    upreview = PostUrlPreview()
                    upreview.post_id = post.pk
                    if wtitle is not None: upreview.title = wtitle
                    elif wforcetitle is not None: upreview.title = wforcetitle
                    if wdescription is not None: upreview.description = wdescription
                    if wimageurl is not None and 'http' in wimageurl: upreview.image_url = wimageurl
                    elif wabsoluteimageurl is not None: upreview.image_url = wabsoluteimageurl
                    if icon is not None: upreview.icon_url = icon.url
                    upreview.site_url = wurl
                    upreview.save()
            except:
                print('Error')
                try:
                    driver = webdriver.Chrome()
                    driver.get(wurl)
                    wtitle = driver.title

                    icons = favicon.get(wurl)
                    icon = None
                    if icons is not None and len(icons) > 0: icon = icons[0]

                    upreviews = PostUrlPreview.objects.filter(post_id=post.pk, site_url=wurl)
                    if upreviews.count() == 0:
                        upreview = PostUrlPreview()
                        upreview.post_id = post.pk
                        if wtitle is not None: upreview.title = wtitle
                        if icon is not None: upreview.icon_url = icon.url
                        upreview.site_url = wurl
                        upreview.save()
                except:
                    pass
            else:
                pass


        if len(web_urls) > 0:
            upreviews = PostUrlPreview.objects.filter(post_id=post.pk)
            for upreview in upreviews:
                if not upreview.site_url in web_urls:
                    upreview.delete()
        else:
            upreviews = PostUrlPreview.objects.filter(post_id=post.pk)
            upreviews.delete()

    else:
        upreviews = PostUrlPreview.objects.filter(post_id=post.pk)
        upreviews.delete()



def qqqqqqqqqqqq(request):

    import datetime

    member_id = request.GET['user_id']

    members = Member.objects.filter(id=member_id)
    if members.count() == 0:
        return redirect('/mothers/tohome?note=This member doesn\'t exist.')

    member = members[0]

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    posts = Post.objects.filter(member_id=member_id, sch_status='').order_by('-id')
    i = 0
    for post in posts:
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
        i = i + 1
        pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
        if pl is not None: post.liked = pl.status
        else: post.liked = ''

        comments = Comment.objects.filter(post_id=post.pk, comment_id='0')
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(likes.count())
        post.content = emoji.emojize(post.content)

        prevs = PostUrlPreview.objects.filter(post_id=post.pk)

        comments1 = comments[:5]
        commentlist = []
        for comment in comments1:
            cm = Member.objects.filter(id=comment.member_id).first()
            if cm is not None:
                comment.comment_text = emoji.emojize(comment.comment_text)
                commentlist.append( { 'comment':comment, 'member':cm } )

        data = {
            'member':member,
            'post': post,
            'prevs': prevs,
            'comments': commentlist,
            'pc-cnt': str(comments.count()),
        }

        if i % 4 == 1: list1.append(data)
        elif i % 4 == 2: list2.append(data)
        elif i % 4 == 3: list3.append(data)
        elif i % 4 == 0: list4.append(data)

    search = member.name + '\'s'
    if member.pk == int(me.admin_id): search = 'Manager\'s'

    categories = []
    pc = PostCategory.objects.filter(admin_id=me.admin_id).first()
    if pc is not None:
        if pc.categories != '': categories = pc.categories.split(',')

    return render(request, 'mothers/posts.html', {'me':me, 'member':member, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'categories':categories})



def myaccount(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    return render(request, 'mothers/profile.html', {'member':me})


def edit_profile(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    return render(request, 'mothers/edit_profile.html', {'member':me, 'cohorts':cohorts, 'option':'edit profile'})



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def to_chat(request):
    if request.method == 'POST':

        email = request.POST.get('member_email', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        c = Cohort.objects.filter(admin_id=me.admin_id).first()
        cohorts = []
        if c is not None:
            if c.cohorts != '': cohorts = c.cohorts.split(',')

        members = Member.objects.filter(email=email)
        if members.count() == 0:
            return redirect('/mothers/zzzzz')

        member = members[0]
        contacts = update_contact(me, email)

        memberList = []
        memberList.insert(0, member)

        return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})

    else:
        return redirect('/mothers/zzzzz')



def passwordreset(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    return  render(request, 'mothers/password_reset.html', {'me':me})



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def changepassword(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        oldpassword = request.POST.get('oldpassword', '')
        newpassword = request.POST.get('newpassword', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        if email == me.email and oldpassword == me.password:
            me.password = newpassword

            me.save()

        elif email == me.email and oldpassword != me.password:
            return render(request, 'motherwise/result.html',
                          {'response': 'Your old password is incorrect. Please enter your correct password.'})

        else:
            return render(request, 'motherwise/result.html',
                          {'response': 'Your email or password is incorrect. Please enter your correct information.'})

        return  render(request, 'mothers/password_reset.html', {'me':me, 'note':'password_updated'})



def send_push(playerIDs, message, url):

    client = PybossaOneSignal(api_key=settings.OS_API_KEY, app_id=settings.OS_APP_ID)
    contents = {"en": message}
    headings = {"en": "MotherWise Network"}
    launch_url = settings.URL + url
    chrome_web_image = settings.URL + '/static/images/notimage.jpg'
    chrome_web_icon = settings.URL + '/static/images/noticon.png'
    included_segments = []
    include_player_ids = playerIDs
    web_buttons=[{"id": "read-more-button",
                               "text": "Read more",
                               "icon": "http://i.imgur.com/MIxJp1L.png",
                               "url": launch_url}]
    try:
        client.push_msg(contents=contents, headings=headings, include_player_ids=include_player_ids, launch_url=launch_url, chrome_web_image=chrome_web_image, chrome_web_icon=chrome_web_icon, included_segments=included_segments, web_buttons=web_buttons)
    except:
        print('Error')



def notifications(request):

    import datetime

    noti_id = '0'

    try:
        noti_id = request.GET['noti_id']
    except MultiValueDictKeyError:
        print('No key')

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    notis = Received.objects.filter(member_id=me.pk).order_by('-id')

    # return HttpResponse(str(me.pk) + '///' + str(notis.count()))

    i = 0
    for noti in notis:
        i = i + 1
        members = Member.objects.filter(id=noti.sender_id)
        if members.count() > 0:
            sender = members[0]
            nfs = Notification.objects.filter(id=noti.noti_id)
            if nfs.count() > 0:
                notification = nfs[0]
                notification.notified_time = datetime.datetime.fromtimestamp(float(int(notification.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                data = {
                    'sender':sender,
                    'noti': notification
                }

                if i % 4 == 1: list1.append(data)
                elif i % 4 == 2: list2.append(data)
                elif i % 4 == 3: list3.append(data)
                elif i % 4 == 0: list4.append(data)

    return render(request, 'mothers/notifications.html', {'notid':noti_id, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'opt':'received'})



def sentnotis(request):

    import datetime

    noti_id = '0'

    try:
        noti_id = request.GET['noti_id']
    except MultiValueDictKeyError:
        print('No key')

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    notis = Sent.objects.filter(sender_id=me.pk).order_by('-id')

    # return HttpResponse(str(me.pk) + '///' + str(notis.count()))

    i = 0
    for noti in notis:
        i = i + 1
        members = Member.objects.filter(id=noti.member_id)
        if members.count() > 0:
            receiver = members[0]
            nfs = Notification.objects.filter(id=noti.noti_id)
            if nfs.count() > 0:
                notification = nfs[0]
                notification.notified_time = datetime.datetime.fromtimestamp(float(int(notification.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                data = {
                    'receiver':receiver,
                    'noti': notification
                }

                if i % 4 == 1: list1.append(data)
                elif i % 4 == 2: list2.append(data)
                elif i % 4 == 3: list3.append(data)
                elif i % 4 == 0: list4.append(data)

    return render(request, 'mothers/sent_notis.html', {'notid':noti_id, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'opt':'sent'})



def delete_noti(request):
    noti_id = request.GET['noti_id']
    opt = request.GET['opt']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    if opt == 'received':
        notis = Received.objects.filter(noti_id=noti_id)
        if notis.count() > 0:
            noti = notis[0]
            noti.delete()
        return redirect('/mothers/notifications/')
    elif opt == 'sent':
        notis = Sent.objects.filter(noti_id=noti_id)
        if notis.count() > 0:
            noti = notis[0]
            noti.delete()
        return redirect('/mothers/sentnotis/')




@api_view(['GET', 'POST'])
def process_new_message(request):
    if request.method == 'POST':
        noti_id = request.POST.get('noti_id', '1')
        notis = Notification.objects.filter(id=noti_id)
        if notis.count() > 0:
            noti = notis[0]
            noti.status = 'read'
            noti.save()
        return HttpResponse('The message read')




@api_view(['GET', 'POST'])
def notisearch(request):

    import datetime

    if request.method == 'POST':
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        search_id = request.POST.get('q', '')
        opt = request.POST.get('opt', '')

        notis = []
        if opt == 'received':
            notis = Received.objects.filter(member_id=me.pk).order_by('-id')
        elif opt == 'sent':
            notis = Sent.objects.filter(sender_id=me.pk).order_by('-id')
        notiList = []
        for noti in notis:
            nfs = Notification.objects.filter(id=noti.noti_id)
            if nfs.count() > 0:
                notification = nfs[0]
                notiList.append(notification)
        notiList = get_filtered_notis_data(notiList, search_id, opt)

        list1 = []
        list2 = []
        list3 = []
        list4 = []

        i = 0
        for noti in notiList:
            noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            members = []
            if opt == 'received':
                members = Member.objects.filter(id=noti.sender_id)
            elif opt == 'sent':
                members = Member.objects.filter(id=noti.member_id)
            if members.count() > 0:
                member = members[0]
                data = {}
                if opt == 'received':
                    data = {
                        'sender':member,
                        'noti': noti
                    }
                elif opt == 'sent':
                    data = {
                        'receiver':member,
                        'noti': noti
                    }

                if i % 4 == 1: list1.append(data)
                elif i % 4 == 2: list2.append(data)
                elif i % 4 == 3: list3.append(data)
                elif i % 4 == 0: list4.append(data)

        if opt == 'sent':
            return render(request, 'mothers/sent_notis.html', {'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':'Searched', 'opt':'sent'})

        return render(request, 'mothers/notifications.html', {'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':'Searched', 'opt':'received'})


# import datetime
# from datetime import datetime

def get_filtered_notis_data(notis, keyword, option):
    notiList = []
    for noti in notis:
        members = []
        if option == 'received':
            members = Member.objects.filter(id=noti.sender_id)
        elif option == 'sent':
            members = Member.objects.filter(id=noti.member_id)
        if members.count() > 0:
            member = members[0]
            if keyword.lower() in noti.message.lower():
                notiList.append(noti)
            elif keyword.lower() in member.name.lower():
                notiList.append(noti)
            elif keyword.lower() in member.email.lower():
                notiList.append(noti)
            elif keyword.lower() in member.phone_number.lower():
                notiList.append(noti)
            elif keyword.lower() in member.cohort.lower():
                notiList.append(noti)
            elif keyword.lower() in member.address.lower():
                notiList.append(noti)
            else:
                if keyword.isdigit():
                    keyDateObj = datetime.fromtimestamp(int(keyword)/1000)
                    notiDateObj = datetime.fromtimestamp(int(noti.notified_time)/1000)
                    if keyDateObj.year == notiDateObj.year and keyDateObj.month == notiDateObj.month and keyDateObj.day == notiDateObj.day:
                        notiList.append(noti)

    return notiList



def fffff(request):

    import datetime

    option = request.GET['noption']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    search = 'Searched'
    opt = request.GET['opt']

    notis = []
    if opt == 'received':
        notis = Received.objects.filter(member_id=me.pk).order_by('-id')
    elif opt == 'sent':
        notis = Sent.objects.filter(sender_id=me.pk).order_by('-id')

    notiList = []
    for noti in notis:
        nfs = Notification.objects.filter(id=noti.noti_id)
        if nfs.count() > 0:
            notification = nfs[0]
            notiList.append(notification)

    i = 0
    for noti in notiList:
        i = i + 1

        if opt == 'received':
            members = Member.objects.filter(id=noti.sender_id)
            if members.count() > 0:
                sender = members[0]
                if option == 'last3':
                    if int(round(time.time() * 1000)) - int(noti.notified_time) < 3 * 86400 * 1000:
                        noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'sender':sender,
                            'noti': noti
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 3 Days'
                elif option == 'last7':
                    if int(round(time.time() * 1000)) - int(noti.notified_time) < 7 * 86400 * 1000:
                        noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'sender':sender,
                            'noti': noti
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 7 Days'
                elif option == 'last30':
                    if int(round(time.time() * 1000)) - int(noti.notified_time) < 30 * 86400 * 1000:
                        noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'sender':sender,
                            'noti': noti
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 30 Days'

        elif opt == 'sent':
            members = Member.objects.filter(id=noti.member_id)
            if members.count() > 0:
                receiver = members[0]
                if option == 'last3':
                    if int(round(time.time() * 1000)) - int(noti.notified_time) < 3 * 86400 * 1000:
                        noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'receiver':receiver,
                            'noti': noti
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 3 Days'
                elif option == 'last7':
                    if int(round(time.time() * 1000)) - int(noti.notified_time) < 7 * 86400 * 1000:
                        noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'receiver':receiver,
                            'noti': noti
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 7 Days'
                elif option == 'last30':
                    if int(round(time.time() * 1000)) - int(noti.notified_time) < 30 * 86400 * 1000:
                        noti.notified_time = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'receiver':receiver,
                            'noti': noti
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 30 Days'

    if opt == 'sent':
        return render(request, 'mothers/sent_notis.html', {'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':'Searched', 'opt':'sent'})

    return render(request, 'mothers/notifications.html', {'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':search, 'opt':'received'})



def delete_contact(request):

    member_id = request.GET['member_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    c = Cohort.objects.filter(admin_id=me.admin_id).first()
    cohorts = []
    if c is not None:
        if c.cohorts != '': cohorts = c.cohorts.split(',')

    members = Member.objects.filter(id=member_id)
    if members.count() > 0:
        member = members[0]
        contacts = Contact.objects.filter(member_id=me.pk, contact_email=member.email)
        for contact in contacts:
            contact.delete()

    memberIdList = []
    try:
        memberIdList = request.session['sel_member_list']
    except KeyError:
        print('No key')

    memberList = []
    for member_id in memberIdList:
        members = Member.objects.filter(id=member_id)
        if members.count() > 0:
            member = members[0]
            memberList.append(member)

    contacts = update_contact(me, "")

    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts, 'cohorts':cohorts})


def videotest(request):
    return render(request, 'mothers/video_test.html')




def open_conference(request):

    import datetime

    group_id = request.GET['group_id']
    # cohort = request.GET['cohort']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

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

            request.session['group_id'] = group_id
            request.session['cohort'] = ''

            memberIdList = []
            for memb in memberList:
                memberIdList.append(memb.pk)

            admin = Member.objects.get(id=me.admin_id)
            memberList.insert(0,admin)
            memberIdList.insert(0,admin.pk)

            request.session['sel_member_list'] = memberIdList

            confs = Conference.objects.filter(member_id=me.admin_id, group_id=group_id).order_by('-id')
            for conf in confs:
                conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")

            if confs.count() == 0:
                return render(request, 'motherwise/result.html',
                          {'response': 'Sorry, you don\'t have acces to this.'})

            last_conf = confs[0]

            try:
                conf_id = request.GET['conf_id']
                cfs = Conference.objects.filter(id=conf_id)
                if cfs.count() > 0:
                    last_conf = cfs[0]
                    last_conf.created_time = datetime.datetime.fromtimestamp(float(int(last_conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                    if last_conf.event_time != '': last_conf.event_time = datetime.datetime.fromtimestamp(float(int(last_conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
            except KeyError:
                print('no key')

            try:
                code = request.GET['code']
                cfs = Conference.objects.filter(member_id=me.admin_id, group_id=group_id, code=code)
                if cfs.count() > 0:
                    last_conf = cfs[0]
                    last_conf.created_time = datetime.datetime.fromtimestamp(float(int(last_conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                    if last_conf.event_time != '': last_conf.event_time = datetime.datetime.fromtimestamp(float(int(last_conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
                else:
                    return render(request, 'motherwise/result.html',
                          {'response': 'Sorry, the code is incorrect. Please try another one.'})
            except KeyError:
                print('no key')

            if last_conf.type == 'live':
                return render(request, 'mothers/conference_live.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'confs':confs, 'last_conf':last_conf})
            elif last_conf.type == 'file':
                return render(request, 'mothers/conference_video.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'confs':confs, 'last_conf':last_conf})
            elif last_conf.type == 'youtube':
                return render(request, 'mothers/conference_youtube.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'confs':confs, 'last_conf':last_conf})
        else:
            return redirect('/mothers/zzzzz')

    else:
        request.session['group_id'] = ''
        request.session['cohort'] = ''

        memberList = []
        memberIdList = []
        members = Member.objects.filter(admin_id=me.admin_id, status='')
        for memb in members:
            memberList.append(memb)
            memberIdList.append(memb.pk)

        admin = Member.objects.get(id=me.admin_id)
        memberList.insert(0,admin)
        memberIdList.insert(0,admin.pk)

        request.session['sel_member_list'] = memberIdList

        confs = Conference.objects.filter(member_id=me.admin_id, group_id=0).order_by('-id')
        for conf in confs:
            conf.created_time = datetime.datetime.fromtimestamp(float(int(conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
            if conf.event_time != '': conf.event_time = datetime.datetime.fromtimestamp(float(int(conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")

        if confs.count() == 0:
            return render(request, 'motherwise/result.html', {'response': 'Sorry, you don\'t have acces to this.'})

        last_conf = confs[0]

        try:
            conf_id = request.GET['conf_id']
            cfs = Conference.objects.filter(id=conf_id)
            if cfs.count() > 0:
                last_conf = cfs[0]
                last_conf.created_time = datetime.datetime.fromtimestamp(float(int(last_conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                if last_conf.event_time != '': last_conf.event_time = datetime.datetime.fromtimestamp(float(int(last_conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
        except KeyError:
            print('no key')

        try:
            code = request.GET['code']
            cfs = Conference.objects.filter(member_id=me.admin_id, group_id=0, code=code)
            if cfs.count() > 0:
                last_conf = cfs[0]
                last_conf.created_time = datetime.datetime.fromtimestamp(float(int(last_conf.created_time)/1000)).strftime("%b %d, %Y %H:%M")
                if last_conf.event_time != '': last_conf.event_time = datetime.datetime.fromtimestamp(float(int(last_conf.event_time)/1000)).strftime("%b %d, %Y %H:%M")
            else:
                return render(request, 'motherwise/result.html',
                      {'response': 'Sorry, the code is incorrect. Please try another one.'})
        except KeyError:
            print('no key')

        if last_conf.type == 'live':
            return render(request, 'mothers/conference_live.html', {'me':me, 'admin':admin, 'members':memberList, 'group':None, 'confs':confs, 'last_conf':last_conf})
        elif last_conf.type == 'file':
            return render(request, 'mothers/conference_video.html', {'me':me, 'admin':admin, 'members':memberList, 'group':None, 'confs':confs, 'last_conf':last_conf})
        elif last_conf.type == 'youtube':
            return render(request, 'mothers/conference_youtube.html', {'me':me, 'admin':admin, 'members':memberList, 'group':None, 'confs':confs, 'last_conf':last_conf})
        else:
            return redirect('/mothers/zzzzz')




def new_notis(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    unreadNotiList = []
    notis = Received.objects.filter(member_id=me.pk)
    for noti in notis:
        nfs = Notification.objects.filter(id=noti.noti_id)
        if nfs.count() > 0:
            notification = nfs[0]
            if notification.status == '':
                unreadNotiList.append(notification)

    return HttpResponse(len(unreadNotiList))




@api_view(['GET', 'POST'])
def send_reply_message(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')
        noti_id = request.POST.get('noti_id', '1')
        message = request.POST.get('message', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        members = Member.objects.filter(id=int(member_id))
        if members.count() > 0:
            member = members[0]

            # title = 'You\'ve received a message from MotherWise Community:The Nest'
            # subject = 'From MotherWise Community'
            # msg = 'Dear ' + member.name + ',<br><br>'
            # msg = msg + message

            # from_email = me.email
            # to_emails = []
            # to_emails.append(member.email)
            # send_mail_message(from_email, to_emails, title, subject, msg)

            msg = member.name + ', You\'ve received a reply message from MotherWise Community.\nThe message is as following:\n' + message
            msg2 = member.name + ', has recibido un mensaje de respuesta en el Nest.\nel mensaje es el siguiente:\n' + message

            msg = msg + '\n\n' + msg2

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

            ##########################################################################################################################################################################

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

            #################################################################################################################################################################################

            if member.playerID != '':
                playerIDList = []
                playerIDList.append(member.playerID)
                msg = member.name + ', You\'ve received a reply message from MotherWise Community: The Nest.\nThe message is as following:\n' + message
                msg2 = member.name + ', has recibido un mensaje de respuesta en el Nest.\nel mensaje es el siguiente:\n' + message
                msg = msg + '\n\n' + msg2
                url = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    url = '/manager/notifications?noti_id=' + str(notification.pk)
                send_push(playerIDList, msg, url)

            return redirect('/mothers/notifications/')
        else:
            return render(request, 'motherwise/result.html',
                          {'response': 'This member doesn\'t exist.'})




# from twilio.rest import Client

# def sendSMS(to_phone, msg):

#     # Your Account Sid and Auth Token from twilio.com/console
#     # DANGER! This is insecure. See http://twil.io/secure
#     account_sid = 'ACac35a6a68298c08ae301c7edf7a0046d'
#     auth_token = 'f6d2edd78dba14b7f542026249029c54'
#     client = Client(account_sid, auth_token)

#     message = client.messages \
#                     .create(
#                          body=msg,
#                          from_='+12056712693',
#                          to=to_phone
#                      )

#     print(message.sid)



def noti_detail(request):
    import datetime

    noti_id = request.GET['noti_id']
    opt = request.GET['opt']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    list = []
    sender0 = None

    replieds = Replied.objects.filter(noti_id=noti_id)
    if replieds.count() > 0:
        repl = replieds[0]
        repls = Replied.objects.filter(root_id=repl.root_id)
        for repl in repls:
            notis = Notification.objects.filter(id=repl.noti_id)
            if notis.count() > 0:
                noti = notis[0]
                date = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
                members = Member.objects.filter(id=noti.sender_id)
                if members.count() > 0:
                    sender = members[0]
                    if sender.pk != me.pk:
                        sender0 = sender
                    data = {
                        'sender':sender,
                        'noti': noti,
                        'date':date
                    }

                    list.append(data)

    else:
        notis = Notification.objects.filter(id=noti_id)
        if notis.count() > 0:
            noti = notis[0]
            date = datetime.datetime.fromtimestamp(float(int(noti.notified_time)/1000)).strftime("%b %d, %Y %H:%M")
            members = Member.objects.filter(id=noti.sender_id)
            if members.count() > 0:
                sender = members[0]
                sender0 = sender
                data = {
                    'sender':sender,
                    'noti': noti,
                    'date':date
                }

                list.append(data)

    return render(request, 'mothers/noti_detail.html', {'notid':noti_id, 'me':me, 'sender':sender0, 'list':list, 'opt':opt})



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def notify_group_chat(request):
    if request.method == 'POST':

        message = request.POST.get('message', '')
        cohort = request.POST.get('cohort', '')
        groupid = request.POST.get('groupid', '')
        ids = request.POST.getlist('users[]')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        admin = Member.objects.get(id=me.admin_id)

        if groupid != '':
            groups = Group.objects.filter(id=int(groupid))
            if groups.count() == 0:
                return redirect('/mothers/zzzzz')

            group = groups[0]

            for member_id in ids:
                members = Member.objects.filter(id=int(member_id))
                if members.count() > 0:
                    member = members[0]

                    title = 'MotherWise Community: The Nest'
                    subject = 'You\'ve received a community message from (has recibido un mensaje de la comunidad de)' + group.name
                    msg = 'Dear ' + member.name + ', You\'ve received a community message from ' + me.name + ' in ' + group.name + '. The message is as following:<br><br>'
                    msg = msg + message + '<br><br>'

                    if member.cohort == 'admin':
                        msg = msg + '<a href=\'' + settings.URL + '/manager/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>Connect the community to view message</a>'
                    else:
                        msg = msg + '<a href=\'' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>Connect the community to view message</a>'

                    title2 = 'Comunidad MotherWise: el Nest'
                    msg2 = member.name + ', has recibido un mensaje de la comunidad de ' + me.name + ' en ' + group.name + '. el mensaje es el siguiente:<br><br>'
                    msg2 = msg2 + message + '<br><br>'

                    if member.cohort == 'admin':
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/manager/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>conectar la comunidad para ver el mensaje</a>'
                    else:
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>conectar la comunidad para ver el mensaje</a>'

                    from_email = admin.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message0(from_email, to_emails, title, subject, msg, title2, msg2)

                    msg = member.name + ', You\'ve received a community message from ' + me.name + ' in ' + group.name + '. The message is as following:\n\n'
                    msg = msg + message + '\n\n'

                    if member.cohort == 'admin':
                        msg = msg + 'Click on this link to view the message: ' + settings.URL + '/manager/open_group_chat?group_id=' + groupid
                    else:
                        msg = msg + 'Click on this link to view the message: ' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid

                    msg2 = member.name + ', has recibido un mensaje de la comunidad de ' + me.name + ' en ' + group.name + '. el mensaje es el siguiente:\n\n'
                    msg2 = msg2 + message + '\n\n'

                    if member.cohort == 'admin':
                        msg2 = msg2 + 'haga clic en este enlace para ver el mensaje: ' + settings.URL + '/manager/open_group_chat?group_id=' + groupid
                    else:
                        msg2 = msg2 + 'haga clic en este enlace para ver el mensaje: ' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid

                    msg = msg + '\n\n' + msg2

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

                    ##########################################################################################################################################################################

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

                    #################################################################################################################################################################################

                    if member.playerID != '':
                        playerIDList = []
                        playerIDList.append(member.playerID)
                        url = '/mothers/notifications?noti_id=' + str(notification.pk)
                        if member.cohort == 'admin':
                            url = '/manager/notifications?noti_id=' + str(notification.pk)
                        send_push(playerIDList, msg, url)

        elif cohort != '':

            for member_id in ids:
                members = Member.objects.filter(id=int(member_id))
                if members.count() > 0:
                    member = members[0]

                    title = 'MotherWise Community: The Nest'
                    subject = 'You\'ve received a group message from (has recibido un mensaje grupal de)' + cohort
                    msg = 'Dear ' + member.name + ', You\'ve received a group message from ' + me.name + ' in ' + cohort + '. The message is as following:<br><br>'
                    msg = msg + message + '<br><br>'

                    if member.cohort == 'admin':
                        msg = msg + '<a href=\'' + settings.URL + '/manager/group_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>Connect the group to view message</a>'
                    else:
                        msg = msg + '<a href=\'' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>Connect the group to view message</a>'

                    title2 = 'Comunidad MotherWise: el Nest'
                    msg2 = member.name + ', has recibido un mensaje grupal de ' + me.name + ' en ' + cohort + '. el mensaje es el siguiente:<br><br>'
                    msg2 = msg2 + message + '<br><br>'

                    if member.cohort == 'admin':
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/manager/group_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>conectar el grupo para ver el mensaje</a>'
                    else:
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>conectar el grupo para ver el mensaje</a>'

                    from_email = admin.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message0(from_email, to_emails, title, subject, msg, title2, msg2)

                    msg = member.name + ', You\'ve received a group message from ' + me.name + ' in ' + cohort + '. The message is as following:\n\n'
                    msg = msg + message + '\n\n'

                    if member.cohort == 'admin':
                        msg = msg + 'Click on this link to view the message: ' + settings.URL + '/manager/group_cohort_chat?cohort=' + cohort
                    else:
                        msg = msg + 'Click on this link to view the message: ' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort

                    msg2 = member.name + ', has recibido un mensaje grupal de ' + me.name + ' in ' + cohort + '. el mensaje es el siguiente:\n\n'
                    msg2 = msg2 + message + '\n\n'

                    if member.cohort == 'admin':
                        msg2 = msg2 + 'haga clic en este enlace para ver el mensaje: ' + settings.URL + '/manager/group_cohort_chat?cohort=' + cohort
                    else:
                        msg2 = msg2 + 'haga clic en este enlace para ver el mensaje: ' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort

                    msg = msg + '\n\n' + msg2

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

                    ##########################################################################################################################################################################

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

                    #################################################################################################################################################################################

                    if member.playerID != '':
                        playerIDList = []
                        playerIDList.append(member.playerID)
                        url = '/mothers/notifications?noti_id=' + str(notification.pk)
                        if member.cohort == 'admin':
                            url = '/manager/notifications?noti_id=' + str(notification.pk)
                        send_push(playerIDList, msg, url)

        return HttpResponse('success')



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
                msg2 = member.name + ', has recibido un mensaje de ' + sender.name + '.\nel mensaje es el siguiente:\n' + message
                msg = '\n\n' + msg2
                send_push(playerIDList, msg, url)

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
        else:
            message_title = "VaCay Weather"
        path_to_fcm = "https://fcm.googleapis.com"
        server_key = settings.FCM_LEGACY_SERVER_KEY
        reg_id = member.fcm_token #quick and dirty way to get that ONE fcmId from table
        if reg_id != '':
            message_body = notiText
            result = FCMNotification(api_key=server_key).notify_single_device(registration_id=reg_id, message_title=message_title, message_body=message_body, sound = 'ping.aiff', badge = 1)



def clearnotihistory(request):
    notis = Notification.objects.all()
    for noti in notis:
        noti.delete()
    receiveds = Received.objects.all()
    for r in receiveds:
        r.delete()
    sents = Sent.objects.all()
    for s in sents:
        s.delete()
    replieds = Replied.objects.all()
    for r in replieds:
        r.delete()

    # db = firebase.database()
    # db.remove()

    return HttpResponse('Cleared Notification History!')



@api_view(['POST', 'GET'])
def getpostlinks(request):
    content = request.POST.get('content', '')
    if content != '':
        web_urls = urlsFromText(content)
        prevList = []
        i = 0
        for wurl in web_urls:
            i += 1
            try:
                preview = link_preview(wurl)
                wtitle = preview.title
                wdescription = preview.description
                wimageurl = preview.image
                wforcetitle = preview.force_title
                wabsoluteimageurl = preview.absolute_image

                icons = favicon.get(wurl)
                icon = None
                if icons is not None and len(icons) > 0:
                    icon = icons[0]
                    iconurl = icon.url

                upreview = PostUrlPreview()
                upreview.post_id = str(i)
                if wtitle is not None: upreview.title = wtitle
                elif wforcetitle is not None: upreview.title = wforcetitle
                if wdescription is not None: upreview.description = wdescription
                if wimageurl is not None and 'http' in wimageurl: upreview.image_url = wimageurl
                elif wabsoluteimageurl is not None: upreview.image_url = wabsoluteimageurl
                if icon is not None: upreview.icon_url = icon.url
                upreview.site_url = wurl
                prevList.append(upreview)
            except:
                print('Error')
                try:
                    driver = webdriver.Chrome()
                    driver.get(wurl)
                    wtitle = driver.title

                    icons = favicon.get(wurl)
                    icon = None
                    if icons is not None and len(icons) > 0:
                        icon = icons[0]
                        iconurl = icon.url

                    upreview = PostUrlPreview()
                    upreview.post_id = str(i)
                    if wtitle is not None: upreview.title = wtitle
                    if icon is not None: upreview.icon_url = icon.url
                    upreview.site_url = wurl
                    prevList.append(upreview)
                except:
                    pass
            else:
                pass

        ser = PostUrlPreviewSerializer(prevList, many=True)
        return HttpResponse(json.dumps({'result':'success', 'data':ser.data}))

    return HttpResponse(json.dumps({'result':'error'}))




def tonewpost(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)
    users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
    userList = []
    for user in users:
        if user.registered_time != '' and user.pk != me.pk:
            user.username = '@' + user.email[0:user.email.find('@')]
            userList.append(user)

    admin = Member.objects.get(id=me.admin_id)
    admin.username = '@' + admin.email[0:admin.email.find('@')]
    userList.insert(0,admin)

    categories = []
    pc = PostCategory.objects.filter(admin_id=admin.pk).first()
    if pc is not None:
        if pc.categories != '': categories = pc.categories.split(',')

    token = request.GET['token']

    comida = ''
    try: comida = request.GET['comida']
    except: pass

    return render(request, 'mothers/new_post.html', {'me':me, 'users':userList, 'token':token, 'comida':comida, 'categories':categories})



@api_view(['GET', 'POST'])
def newpost(request):
    if request.method == 'POST':

        title = request.POST.get('title', '')
        category = request.POST.get('category', '')
        content = request.POST.get('content', '')
        scheduled_time = request.POST.get('scheduled_time', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return HttpResponse('error')
        except KeyError:
            print('no session')
            return HttpResponse('error')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        admin = Member.objects.get(id=me.admin_id)

        post = Post()
        post.member_id = me.pk
        post.title = title
        post.category = category
        post.content = emoji.demojize(content)
        post.scheduled_time = scheduled_time
        post.picture_url = ''
        post.comments = '0'
        post.likes = '0'
        post.loves = '0'
        post.haha = '0'
        post.wow = '0'
        post.sad = '0'
        post.angry = '0'
        post.reactions = '0'
        post.posted_time = str(int(round(time.time() * 1000)))

        try:
            ids = request.POST.getlist('users[]')
            if len(ids) > 0: post.notified_members = ",".join(str(i) for i in ids)
        except KeyError:
            print('No key')

        try:
            ids = request.POST.get('selections','')
            if ids != '': post.notified_members = ids
        except KeyError:
            print('No key')

        if scheduled_time != '': post.sch_status = 'scheduled'
        post.save()

        createPostUrlPreview(post)

        fs = FileSystemStorage()
        i = 0
        for f in request.FILES.getlist('pictures'):
            i = i + 1
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            if i == 1:
                post.picture_url = settings.URL + uploaded_url
                post.save()
            postPicture = PostPicture()
            postPicture.post_id = post.pk
            postPicture.picture_url = settings.URL + uploaded_url
            postPicture.filename = filename
            postPicture.save()


        if post.scheduled_time == '':

            for member_id in ids:
                members = Member.objects.filter(id=int(member_id))
                if members.count() > 0:
                    member = members[0]

                    title = 'MotherWise Community: The Nest'
                    subject = 'You\'ve received a post from ' + me.name
                    msg = 'Dear ' + member.name + ', You\'ve received a post from ' + me.name + '.<br><br>'

                    if member.cohort == 'admin':
                        msg = msg + '<a href=\'' + settings.URL + '/manager/to_post?post_id=' + str(post.pk) + '\' target=\'_blank\'>View the post</a>'
                    else:
                        msg = msg + '<a href=\'' + settings.URL + '/mothers/posts?post_id=' + str(post.pk) + '\' target=\'_blank\'>View the post</a>'

                    title2 = 'Comunidad MotherWise: el Nest'
                    msg2 = member.name + ', has recibido una publicación de ' + me.name + '.<br><br>'

                    if member.cohort == 'admin':
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/manager/to_post?post_id=' + str(post.pk) + '\' target=\'_blank\'>ver la publicación</a>'
                    else:
                        msg2 = msg2 + '<a href=\'' + settings.URL + '/mothers/posts?post_id=' + str(post.pk) + '\' target=\'_blank\'>ver la publicación</a>'

                    from_email = admin.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message0(from_email, to_emails, title, subject, msg, title2, msg2)

                    msg = member.name + ', You\'ve received a message from ' + me.name + '.\n\n'
                    if member.cohort == 'admin':
                        msg = msg + 'Click on this link to view the post: ' + settings.URL + '/manager/to_post?post_id=' + str(post.pk)
                    else:
                        msg = msg + 'Click on this link to view the post: ' + settings.URL + '/mothers/posts?post_id=' + str(post.pk)

                    msg2 = member.name + ', has recibido un mensaje de ' + me.name + '.\n\n'
                    if member.cohort == 'admin':
                        msg2 = msg2 + 'haga clic en este enlace para ver la publicación: ' + settings.URL + '/manager/to_post?post_id=' + str(post.pk)
                    else:
                        msg2 = msg2 + 'haga clic en este enlace para ver la publicación: ' + settings.URL + '/mothers/posts?post_id=' + str(post.pk)

                    msg = msg + '\n\n' + msg2

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

                    ##########################################################################################################################################################################

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

                    #################################################################################################################################################################################

                    if member.playerID != '':
                        playerIDList = []
                        playerIDList.append(member.playerID)
                        url = '/mothers/notifications?noti_id=' + str(notification.pk)
                        if member.cohort == 'admin':
                            url = '/manager/notifications?noti_id=' + str(notification.pk)
                        send_push(playerIDList, msg, url)


        return HttpResponse('success')



@api_view(['POST','GET'])
def react_post(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    if request.method == 'POST':
        post_id = request.POST.get('post_id','0')
        feeling = request.POST.get('feeling','')

        post = Post.objects.filter(id=post_id).first()
        if post is None: return HttpResponse('error')

        pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
        if pl is not None:
            if feeling == '':
                pl.delete()
            else:
                pl.liked_time = str(int(round(time.time() * 1000)))
                pl.status = feeling
                pl.save()
        else:
            if feeling != '':
                pl = PostLike()
                pl.post_id = post.pk
                pl.member_id = me.pk
                pl.liked_time = str(int(round(time.time() * 1000)))
                pl.status = feeling
                pl.save()

        allfeelings = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(allfeelings.count())
        likes = PostLike.objects.filter(post_id=post.pk, status='like')
        post.likes = str(likes.count())
        loves = PostLike.objects.filter(post_id=post.pk, status='love')
        post.loves = str(loves.count())
        hahas = PostLike.objects.filter(post_id=post.pk, status='haha')
        post.haha = str(hahas.count())
        wows = PostLike.objects.filter(post_id=post.pk, status='wow')
        post.wow = str(wows.count())
        sads = PostLike.objects.filter(post_id=post.pk, status='sad')
        post.sad = str(sads.count())
        angrys = PostLike.objects.filter(post_id=post.pk, status='angry')
        post.angry = str(angrys.count())
        post.save()

        return HttpResponse(json.dumps({'post':PostSerializer(post, many=False).data}))




def analytics(request):

    from datetime import datetime

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    members = Member.objects.filter(admin_id=me.admin_id)
    groups = Cohort.objects.filter(admin_id=me.admin_id).first().cohorts.split(',')
    gcnt = len(groups)
    groups1 = groups[:int(gcnt / 2)]
    groups2 = groups[int(gcnt / 2):gcnt]

    inviteds1 = [0] * len(groups1)
    activateds1 = [0] * len(groups1)
    group_posts1 = [0] * len(groups1)

    inviteds2 = [0] * len(groups2)
    activateds2 = [0] * len(groups2)
    group_posts2 = [0] * len(groups2)

    total_activs = 0
    activ_percentlist_bygroup = []

    monthly_activateds1 = [0,0,0,0,0,0,0,0,0,0,0,0]
    monthly_posts1 = [0,0,0,0,0,0,0,0,0,0,0,0]
    monthly_activateds2 = [0,0,0,0,0,0,0,0,0,0,0,0]
    monthly_posts2 = [0,0,0,0,0,0,0,0,0,0,0,0]
    monthly_activateds3 = [0,0,0,0,0,0,0,0,0,0,0,0]
    monthly_posts3 = [0,0,0,0,0,0,0,0,0,0,0,0]

    cities = []
    activateds_bycity = []
    activated_members_bycity = []

    this_year = datetime.fromtimestamp(time.time()).year
    last_year1 = this_year - 1
    last_year2 = this_year - 2

    for member in members:
        if member.cohort != 'admin' and member.cohort != '':
            if member.cohort in groups1:
                index_invited = groups1.index(member.cohort)
                invits = inviteds1[index_invited] + 1
                inviteds1[index_invited] = invits
                if member.registered_time != '' and int(member.registered_time) > 0:
                    index_activated = groups1.index(member.cohort)
                    activs = activateds1[index_activated] + 1
                    activateds1[index_activated] = activs
                    total_activs = total_activs + 1

                    posts = Post.objects.filter(member_id=member.pk)
                    for post in posts:
                        psts = group_posts1[index_activated] + 1
                        group_posts1[index_activated] = psts
            elif member.cohort in groups2:
                index_invited = groups2.index(member.cohort)
                invits = inviteds2[index_invited] + 1
                inviteds2[index_invited] = invits
                if member.registered_time != '' and int(member.registered_time) > 0:
                    index_activated = groups2.index(member.cohort)
                    activs = activateds2[index_activated] + 1
                    activateds2[index_activated] = activs
                    total_activs = total_activs + 1

                    posts = Post.objects.filter(member_id=member.pk)
                    for post in posts:
                        psts = group_posts2[index_activated] + 1
                        group_posts2[index_activated] = psts


        if member.registered_time != '' and int(member.registered_time) > 0:
            registered_date_obj = datetime.fromtimestamp(int(member.registered_time)/1000)
            if this_year == registered_date_obj.year:
                activs = monthly_activateds1[registered_date_obj.month - 1] + 1
                monthly_activateds1[registered_date_obj.month - 1] = activs
            if last_year1 == registered_date_obj.year:
                activs = monthly_activateds2[registered_date_obj.month - 1] + 1
                monthly_activateds2[registered_date_obj.month - 1] = activs
            if last_year2 == registered_date_obj.year:
                activs = monthly_activateds3[registered_date_obj.month - 1] + 1
                monthly_activateds3[registered_date_obj.month - 1] = activs
            if member.city.replace('\'','').strip() not in cities:
                cities.append(member.city.replace('\'','').strip())
                activateds_bycity.append(0)
                activated_members_bycity.append([])
            activs = activateds_bycity[cities.index(member.city.replace('\'','').strip())] + 1
            activateds_bycity[cities.index(member.city.replace('\'','').strip())] = activs
            activated_members_bycity[cities.index(member.city.replace('\'','').strip())].append(member)

            posts = Post.objects.filter(member_id=member.pk)
            for post in posts:
                posted_date_obj = datetime.fromtimestamp(int(post.posted_time)/1000)
                if this_year == posted_date_obj.year:
                    psts = monthly_posts1[posted_date_obj.month - 1] + 1
                    monthly_posts1[posted_date_obj.month - 1] = psts
                if last_year1 == posted_date_obj.year:
                    psts = monthly_posts2[posted_date_obj.month - 1] + 1
                    monthly_posts2[posted_date_obj.month - 1] = psts
                if last_year2 == posted_date_obj.year:
                    psts = monthly_posts3[posted_date_obj.month - 1] + 1
                    monthly_posts3[posted_date_obj.month - 1] = psts


    cityActivsList = []
    cityActivsChartWidth = 0
    for i in range(0, len(cities)):
        data = {
            'city': cities[i],
            'activsval': activateds_bycity[i],
            'activmembers': activated_members_bycity[i]
        }
        cityActivsList.append(data)
        cityActivsChartWidth = cityActivsChartWidth + 50

    activateds = activateds1 + activateds2

    for i in range(0, len(activateds)):
        percentval = round(activateds[i] * 100 / total_activs, 2)
        data = {
            'group': groups[i],
            'activ_percent': percentval
        }
        activ_percentlist_bygroup.append(data)

    activ_percent = round(total_activs * 100 / members.count(), 2)
    activdata = {
        'percvalue': activ_percent,
        'title': 'Activated'
    }
    inactivdata = {
        'percvalue': round(100 - activ_percent, 2),
        'title': 'Inactivated'
    }

    communities = Group.objects.filter(member_id=me.admin_id)
    comActivsList = []
    comPostsList = []
    for com in communities:
        gms = GroupMember.objects.filter(group_id=com.pk)
        member_count = gms.count()
        data = {
            'com': com.name,
            'activsval': str(member_count),
        }
        comActivsList.append(data)
        post_count = 0
        for gm in gms:
            post_count += Post.objects.filter(member_id=gm.member_id).count()
        data = {
            'com': com.name,
            'postsval': str(post_count),
        }
        comPostsList.append(data)

    context = {
        'this_year': str(this_year),
        'last_year1': str(last_year1),
        'last_year2': str(last_year2),
        'groups': groups,
        'groups1': groups1,
        'groups2': groups2,
        'activateds': activateds,
        'inviteds1': inviteds1,
        'activateds1': activateds1,
        'group_posts1': group_posts1,
        'inviteds2': inviteds2,
        'activateds2': activateds2,
        'group_posts2': group_posts2,
        'activ_percentlist_bygroup': activ_percentlist_bygroup,
        'total_activ_inactiv_percent': [activdata, inactivdata],
        'monthly_activateds1': monthly_activateds1,
        'monthly_posts1': monthly_posts1,
        'monthly_activateds2': monthly_activateds2,
        'monthly_posts2': monthly_posts2,
        'monthly_activateds3': monthly_activateds3,
        'monthly_posts3': monthly_posts3,
        'city_activateds': cityActivsList,
        'cityActivsChartWidth': cityActivsChartWidth,
        'com_activateds': comActivsList,
        'com_posts': comPostsList,
    }

    return render(request, 'mothers/analytics.html', context)




@api_view(['POST','GET'])
def react_comment(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    if request.method == 'POST':
        comment_id = request.POST.get('comment_id','0')
        feeling = request.POST.get('feeling','')

        comment = Comment.objects.filter(id=comment_id).first()
        if comment is None: return HttpResponse('error')

        cl = CommentLike.objects.filter(comment_id=comment.pk, member_id=me.pk).first()
        if cl is not None:
            if feeling == '':
                cl.delete()
            else:
                cl.liked_time = str(int(round(time.time() * 1000)))
                cl.status = feeling
                cl.save()
        else:
            if feeling != '':
                cl = CommentLike()
                cl.comment_id = comment.pk
                cl.member_id = me.pk
                cl.liked_time = str(int(round(time.time() * 1000)))
                cl.status = feeling
                cl.save()

        allfeelings = CommentLike.objects.filter(comment_id=comment.pk)
        comment.reactions = str(allfeelings.count())
        likes = CommentLike.objects.filter(comment_id=comment.pk, status='like')
        comment.likes = str(likes.count())
        loves = CommentLike.objects.filter(comment_id=comment.pk, status='love')
        comment.loves = str(loves.count())
        hahas = CommentLike.objects.filter(comment_id=comment.pk, status='haha')
        comment.haha = str(hahas.count())
        wows = CommentLike.objects.filter(comment_id=comment.pk, status='wow')
        comment.wow = str(wows.count())
        sads = CommentLike.objects.filter(comment_id=comment.pk, status='sad')
        comment.sad = str(sads.count())
        angrys = CommentLike.objects.filter(comment_id=comment.pk, status='angry')
        comment.angry = str(angrys.count())
        comment.save()

        return HttpResponse(json.dumps({'comment':CommentSerializer(comment, many=False).data}))




@api_view(['GET', 'POST'])
def send_comment(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '0')
        comment_id = request.POST.get('comment_id', '0')
        content = request.POST.get('content', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return HttpResponse('error')
        except KeyError:
            print('no session')
            return HttpResponse('error')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        try:
            playerID = request.session['playerID']
            if playerID != '':
                me.playerID = playerID
                me.save()
        except: pass

        fs = FileSystemStorage()

        comment = Comment()
        comment.post_id = post_id
        comment.comment_id = comment_id
        comment.member_id = me.pk
        comment.comment_text = emoji.demojize(content)
        comment.comments = '0'
        comment.likes = '0'
        comment.commented_time = str(int(round(time.time() * 1000)))

        try:
            image = request.FILES['image']
            filename = fs.save(image.name, image)
            uploaded_url = fs.url(filename)
            comment.image_url = settings.URL + uploaded_url
            comment.filename = filename
        except MultiValueDictKeyError:
            print('no video updated')

        comment.save()

        return HttpResponse('success')



def comment_delete(request):
    comment_id = request.GET['comment_id']

    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    try:
        playerID = request.session['playerID']
        if playerID != '':
            me.playerID = playerID
            me.save()
    except: pass

    fs = FileSystemStorage()

    pcs = Comment.objects.filter(id=comment_id)
    if pcs.count() > 0:
        pc = pcs[0]
        post_id = pc.post_id
        if pc.filename != '':
            fs.delete(pc.filename)
        elif pc.image_url != '':
            fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
        pc.delete()

        return HttpResponse('success')
    else:
        return HttpResponse('error')
























































