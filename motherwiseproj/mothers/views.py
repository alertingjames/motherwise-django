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
# from motherwise.serializers import

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
            if member.cohort == 'admin':
                return render(request, 'mothers/login.html')
            if member.cohort == '' or member.phone_number == '':
                return render(request, 'mothers/register_profile.html', {'member':member})
            elif member.address == '' or member.city == '':
                return  render(request, 'mothers/location_picker.html', {'address':member.address})
            else:
                return redirect('/mothers/home')
    except KeyError:
        print('no session')
    return render(request, 'mothers/login.html')


def firstpage(request):
    return  render(request, 'mothers/login.html')


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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
                return render(request, 'motherwise/result.html',
                          {'response': 'This account isn\'t allowed to login as a member.'})
            if playerID != '':
                member.playerID = playerID
            member.save()
            request.session['memberID'] = member.pk
            if member.registered_time == '':
                return render(request, 'mothers/register_profile.html', {'member':member})
            elif member.address == '':
                return  render(request, 'mothers/location_picker.html', {'address':member.address})
            else:
                return redirect('/mothers/home')
        else:
            return render(request, 'motherwise/result.html',
                          {'response': 'Login failed'})

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

    if me.cohort == '':
        return render(request, 'mothers/edit_profile.html', {'member':me, 'option':'edit profile', 'note':'add_cohort'})

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

    return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList})


def torequestpwd(request):
    return  render(request, 'mothers/forgot_password.html')


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def send_mail_forgotpassword(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')

        members = Member.objects.filter(email=email)
        memberList = []
        for member in members:
            if member.cohort != 'admin': memberList.append(member)
        if len(memberList) == 0:
            return render(request, 'motherwise/result.html',
                          {'response': 'This email doesn\'t exist for participants. Please try another one.'})

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

        return render(request, 'motherwise/result.html',
                          {'response': 'We sent a message to your email. Please check and reset your password.'})


def resetpassword(request):
    email = request.GET['email']
    return render(request, 'mothers/resetpwd.html', {'email':email})


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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

        return redirect('/mothers/home')


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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
        if city != '': me.city = city
        if lat != '': me.lat = lat
        if lng != '': me.lng = lng
        me.registered_time = str(int(round(time.time() * 1000)))
        if playerID != '':
            me.playerID = playerID

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

            x = request.POST.get('x', '0')
            y = request.POST.get('y', '0')
            w = request.POST.get('w', '32')
            h = request.POST.get('h', '32')
            #  return HttpResponse(w)
            photo = profile_process(photo, x, y, w, h)

            filename = fs.save(photo.name, photo)
            uploaded_url = fs.url(filename)
            if me.photo_url != '' and '/static/images/ic_profile.png' not in me.photo_url:
                fs.delete(me.photo_url.replace(settings.URL + '/media/', ''))
            me.photo_url = settings.URL + uploaded_url

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

        return render(request, 'mothers/location_picker.html', {'address':me.address})


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

    return render(request, 'mothers/login.html')


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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
                    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
                else:
                    return redirect('/mothers/home')
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
                subject = 'You\'ve received a message from a member of MotherWise Community: The Nest'
                msg = 'Dear ' + member.name + ', You\'ve received a message from ' + me.name + '. The message is as following:<br><br>'
                msg = msg + message
                rurl = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    rurl = '/manager/notifications?noti_id=' + str(notification.pk)
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
                    msg = member.name + ', You\'ve received a message from ' + me.name + '.\nThe message is as following:\n' + message
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
                return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
            else:
                return redirect('/mothers/home')
        else:
            return redirect('/mothers/home')



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

    return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'note':note})



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def do_cohort(request):

    import datetime

    if request.method == 'POST':

        try:
            cohort = request.POST.get('cohort','')
            if cohort == '':
                return redirect('/mothers/home')
            option = request.POST.get('option','')
        except AssertionError:
            return redirect('/mothers/home')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

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
            return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohort': cohort})
        elif option == 'private_chat':
            contacts = update_contact(me, "")
            return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
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

            return render(request, 'mothers/cohort_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort})

    else:
        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

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
                return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
            elif selectedOption == 'members':
                cohort = memberList[0].cohort
                groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
                groupList = []
                for group in groups:
                    gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                    if gms.count() > 0:
                        groupList.append(group)
                return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'cohort': cohort})
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

                return render(request, 'mothers/cohort_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort})

            else:
                return redirect('/mothers/home')
        else:
            return redirect('/mothers/home')


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

    return render(request, 'mothers/cohort_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort})



def conferences(request):
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            return render(request, 'mothers/login.html')
    except KeyError:
        print('no session')
        return render(request, 'mothers/login.html')

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    confs = Conference.objects.filter(member_id=me.admin_id).order_by('-id')
    confs = getConferences(confs, me)
    return render(request, 'mothers/conferences.html', {'confs':confs, 'note':'My Conferences'})


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
def do_group(request):

    import datetime

    if request.method == 'POST':

        try:
            groupid = request.POST.get('groupid','')
            option = request.POST.get('option','')
        except AssertionError:
            return redirect('/mothers/home')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

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
            return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'group': group})
        elif option == 'private_chat':
            contacts = update_contact(me, "")
            return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
        elif option == 'group_chat':
            groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
            groupList = []
            for group in groups:
                gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                if gms.count() > 0:
                    groupList.append(group)
            group = Group.objects.get(id=int(groupid))
            return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'groups':groupList})
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
            return redirect('/mothers/home')

        if len(memberList) > 0:
            if selectedOption == 'members':
                groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
                groupList = []
                for group in groups:
                    gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                    if gms.count() > 0:
                        groupList.append(group)
                group = Group.objects.get(id=int(groupid))
                return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'group': group})
            elif selectedOption == 'private_chat':
                contacts = update_contact(me, "")
                return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
            elif selectedOption == 'group_chat':
                groups = Group.objects.filter(member_id=me.admin_id).order_by('-id')
                groupList = []
                for group in groups:
                    gms = GroupMember.objects.filter(group_id=group.pk, member_id=me.pk)
                    if gms.count() > 0:
                        groupList.append(group)
                group = Group.objects.get(id=int(groupid))
                return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'groups':groupList})
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
                return redirect('/mothers/home')
        else:
            return redirect('/mothers/home')



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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

        search_id = request.POST.get('q', None)

        members = Member.objects.filter(admin_id=me.admin_id, status='').order_by('-id')
        memberList = []
        for member in members:
            memberList.append(member)
        admin = Member.objects.get(id=me.admin_id)
        memberList.insert(0, admin)

        memberList, groupList = get_filtered_members_data(me, memberList, search_id)
        return render(request, 'mothers/home.html', {'me':me, 'admin':admin, 'members':memberList, 'groups':groupList, 'note':'Searched by ' + search_id})



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

    members = Member.objects.filter(id=member_id)
    if members.count() == 0:
        return redirect('/mothers/home')

    member = members[0]
    contacts = update_contact(me, "")

    memberList = []
    memberList.insert(0, member)

    memberIdList = []
    memberIdList.insert(0, member.pk)

    request.session['sel_option'] = 'private_chat'
    request.session['sel_member_list'] = memberIdList

    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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
                    url = '/manager/notifications?noti_id=' + str(notification.pk)
                msg = member.name + ', You\'ve received a message from ' + me.name + '.\nThe message is as following:\n' + message
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

    members = Member.objects.filter(id=member_id)
    if members.count() == 0:
        return redirect('/mothers/home')

    selected_member = members[0]

    memberIdList = []
    try:
        memberIdList = request.session['sel_member_list']
    except KeyError:
        print('No key')

    selectedOption = request.session['sel_option']

    if len(memberIdList) == 0:
        return redirect('/mothers/home')

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
        return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})
    else:
        return redirect('/mothers/home')



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

    contacts = update_contact(me, "")

    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})




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
    return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'group':group, 'groups':groupList})



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
    return render(request, 'mothers/group_chat.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'groups':groupList})


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
                data = {
                    'member':memb,
                    'post': post
                }

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

    return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'users':userList, 'pst':pst})


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

    posts = Post.objects.filter(member_id=me.pk).order_by('-id')

    i = 0
    for post in posts:
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")

        comments = Comment.objects.filter(post_id=post.pk)
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.likes = str(likes.count())

        i = i + 1

        data = {
            'member':me,
            'post': post
        }

        if i % 4 == 1: list1.append(data)
        elif i % 4 == 2: list2.append(data)
        elif i % 4 == 3: list3.append(data)
        elif i % 4 == 0: list4.append(data)

    return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':'My', 'users':userList})


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def create_post(request):
    if request.method == 'POST':

        title = request.POST.get('title', '')
        category = request.POST.get('category', '')
        content = request.POST.get('content', '')
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

        post = Post()
        post.member_id = me.pk
        post.title = title
        post.category = category
        post.content = content
        post.picture_url = ''
        post.comments = '0'
        post.likes = '0'
        post.posted_time = str(int(round(time.time() * 1000)))
        post.save()

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
            postPicture.save()


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

                from_email = admin.email
                to_emails = []
                to_emails.append(member.email)
                send_mail_message(from_email, to_emails, title, subject, msg)

                msg = member.name + ', You\'ve received a message from ' + me.name + '.\n\n'

                if member.cohort == 'admin':
                    msg = msg + 'Click on this link to view the post: ' + settings.URL + '/manager/to_post?post_id=' + str(post.pk)
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


        return redirect('/mothers/posts/')



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

    posts = Post.objects.filter(id=post_id)
    if posts.count() == 0: return redirect('/mothers/posts/')

    post = posts[0]
    post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")

    comments = Comment.objects.filter(post_id=post.pk)
    post.comments = str(comments.count())
    likes = PostLike.objects.filter(post_id=post.pk)
    post.likes = str(likes.count())

    # return HttpResponse(post.member_id + '///' + str(admin.pk))

    if int(post.member_id) != me.pk:

        pls = PostLike.objects.filter(post_id=post.pk, member_id=me.pk)
        if pls.count() > 0: post.liked = 'yes'
        else: post.liked = 'no'

        ppictures = PostPicture.objects.filter(post_id=post.pk)

        comments = Comment.objects.filter(post_id=post_id, member_id=me.pk)
        if comments.count() == 0:
            comments = Comment.objects.filter(post_id=post_id).order_by('-id')
            commentList = []
            for comment in comments:
                comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
                members = Member.objects.filter(id=comment.member_id)
                if members.count() > 0:
                    member = members[0]
                    data = {
                        'comment':comment,
                        'member':member
                    }
                    commentList.append(data)
            members = Member.objects.filter(id=post.member_id)
            if members.count() == 0: return redirect('/mothers/posts/')
            member = members[0]
            data = {
                'post': post,
                'member': member,
                'pictures':ppictures
            }
            return render(request, 'mothers/comment.html', {'post':data, 'me':me, 'comments':commentList})

        else:
            myComment = comments[0]
            comments = Comment.objects.filter(post_id=post_id).order_by('-id')
            commentList = []
            for comment in comments:
                comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
                members = Member.objects.filter(id=comment.member_id)
                if members.count() > 0:
                    member = members[0]
                    data = {
                        'comment':comment,
                        'member':member
                    }
                    commentList.append(data)
            members = Member.objects.filter(id=post.member_id)
            if members.count() == 0: return redirect('/mothers/posts/')
            member = members[0]
            data = {
                'post': post,
                'member': member,
                'pictures':ppictures
            }
            return render(request, 'mothers/comment.html', {'post':data, 'me':me, 'comments':commentList, 'comment':myComment})

    else:
        ppictures = PostPicture.objects.filter(post_id=post.pk)
        comments = Comment.objects.filter(post_id=post_id).order_by('-id')
        commentList = []
        for comment in comments:
            comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
            members = Member.objects.filter(id=comment.member_id)
            if members.count() > 0:
                member = members[0]
                data = {
                    'comment':comment,
                    'member':member
                }
                commentList.append(data)
        data = {
            'post': post,
            'pictures':ppictures,
            'comments':commentList
        }
        return render(request, 'mothers/edit_post.html', {'post':data, 'me':me})



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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

        posts = Post.objects.all().order_by('-id')
        postList = get_filtered_posts_data(me, posts, search_id)

        list1 = []
        list2 = []
        list3 = []
        list4 = []

        i = 0
        for post in postList:
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

            member = Member.objects.get(id=post.member_id)

            data = {
                'member':member,
                'post': post
            }

            if i % 4 == 1: list1.append(data)
            elif i % 4 == 2: list2.append(data)
            elif i % 4 == 3: list3.append(data)
            elif i % 4 == 0: list4.append(data)

        return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':'Searched', 'users':userList})


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
                elif keyword.lower() in post.likes.lower():
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

    allPosts = Post.objects.all().order_by('-id')
    i = 0
    for post in allPosts:
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
                if option == 'last3':
                    if int(round(time.time() * 1000)) - int(post.posted_time) < 3 * 86400 * 1000:
                        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'member':memb,
                            'post': post
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 3 Days'
                elif option == 'last7':
                    if int(round(time.time() * 1000)) - int(post.posted_time) < 7 * 86400 * 1000:
                        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'member':memb,
                            'post': post
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 7 Days'
                elif option == 'last30':
                    if int(round(time.time() * 1000)) - int(post.posted_time) < 30 * 86400 * 1000:
                        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
                        data = {
                            'member':memb,
                            'post': post
                        }
                        if i % 4 == 1: list1.append(data)
                        elif i % 4 == 2: list2.append(data)
                        elif i % 4 == 3: list3.append(data)
                        elif i % 4 == 0: list4.append(data)
                        search = 'Last 30 Days'

    return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':search, 'users':userList})




@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def submit_comment(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '')
        content = request.POST.get('content', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

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

            post = Post.objects.get(id=post_id)
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

    posts = Post.objects.filter(id=post_id)
    if posts.count() == 0: return redirect('/mothers/posts/')

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

    return redirect('/mothers/posts/')



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
        if pc.image_url != '':
            fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
        pc.delete()

        post = Post.objects.get(id=post_id)
        post.comments = str(int(post.comments) - 1)
        post.save()

        return redirect('/mothers/add_post_comment?post_id=' + post_id)
    else:
        return redirect('/mothers/posts/')


def delete_post_picture(request):
    picture_id = request.GET['picture_id']
    post_id = request.GET['post_id']
    posts = Post.objects.filter(id=post_id)
    if posts.count() == 0:
        return redirect('/mothers/posts/')
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
        pl.save()

        post.likes = str(int(post.likes) + 1)
        post.save()

    # return redirect('/mothers/add_post_comment?post_id=' + str(post.pk))
    return HttpResponse(post.likes)



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def edit_post(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')
        title = request.POST.get('title', '')
        category = request.POST.get('category', '')
        content = request.POST.get('content', '')

        try:
            if request.session['memberID'] == '' or request.session['memberID'] == 0:
                return render(request, 'mothers/login.html')
        except KeyError:
            print('no session')
            return render(request, 'mothers/login.html')

        memberID = request.session['memberID']
        me = Member.objects.get(id=memberID)

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            return redirect('/mothers/posts/')
        post = posts[0]
        post.title = title
        post.category = category
        post.content = content
        post.save()

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
            postPicture.save()

        return redirect('/mothers/add_post_comment?post_id=' + post_id)


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

    posts = Post.objects.filter(member_id=member_id).order_by('-id')
    i = 0
    for post in posts:
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

        data = {
            'member':member,
            'post': post
        }

        if i % 4 == 1: list1.append(data)
        elif i % 4 == 2: list2.append(data)
        elif i % 4 == 3: list3.append(data)
        elif i % 4 == 0: list4.append(data)

    search = member.name + '\'s'
    if member.pk == int(me.admin_id): search = 'Manager\'s'

    return render(request, 'mothers/posts.html', {'me':me, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'search':search})



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

    return render(request, 'mothers/edit_profile.html', {'member':me, 'option':'edit profile'})



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

        members = Member.objects.filter(email=email)
        if members.count() == 0:
            return redirect('/mothers/home')

        member = members[0]
        contacts = update_contact(me, email)

        memberList = []
        memberList.insert(0, member)

        return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})

    else:
        return redirect('/mothers/home')



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



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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

    return render(request, 'mothers/chat.html', {'members':memberList, 'me': me, 'friend':memberList[0], 'contacts':contacts})


def videotest(request):
    return render(request, 'mothers/video_test.html')




def open_conference(request):

    import datetime

    group_id = request.GET['group_id']
    cohort = request.GET['cohort']

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

            confs = Conference.objects.filter(member_id=me.admin_id, group_id=group_id, status='notified').order_by('-id')
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
                cfs = Conference.objects.filter(member_id=me.admin_id, group_id=group_id, status='notified', code=code)
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
                return redirect('/mothers/home')

    elif cohort != '':
        members = Member.objects.filter(admin_id=me.admin_id, cohort=cohort, status='')
        if members.count() > 0:
            for member in members:
                memberList.append(member)

            request.session['group_id'] = ''
            request.session['cohort'] = cohort

            memberIdList = []
            for memb in memberList:
                memberIdList.append(memb.pk)

            admin = Member.objects.get(id=me.admin_id)
            memberList.insert(0,admin)
            memberIdList.insert(0,admin.pk)

            request.session['sel_member_list'] = memberIdList

            confs = Conference.objects.filter(member_id=me.admin_id, cohort=cohort, status='notified').order_by('-id')
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
                cfs = Conference.objects.filter(member_id=me.admin_id, cohort=cohort, status='notified', code=code)
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
                return render(request, 'mothers/conference_live.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'confs':confs, 'last_conf':last_conf})
            elif last_conf.type == 'file':
                return render(request, 'mothers/conference_video.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'confs':confs, 'last_conf':last_conf})
            elif last_conf.type == 'youtube':
                return render(request, 'mothers/conference_youtube.html', {'me':me, 'admin':admin, 'members':memberList, 'cohort':cohort, 'confs':confs, 'last_conf':last_conf})
            else:
                return redirect('/mothers/home')


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



@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
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
                url = '/mothers/notifications?noti_id=' + str(notification.pk)
                if member.cohort == 'admin':
                    url = '/manager/notifications?noti_id=' + str(notification.pk)
                send_push(playerIDList, msg, url)

            return redirect('/mothers/notifications/')
        else:
            return render(request, 'motherwise/result.html',
                          {'response': 'This member doesn\'t exist.'})




from twilio.rest import Client

def sendSMS(to_phone, msg):

    # Your Account Sid and Auth Token from twilio.com/console
    # DANGER! This is insecure. See http://twil.io/secure
    account_sid = 'ACac35a6a68298c08ae301c7edf7a0046d'
    auth_token = 'f6d2edd78dba14b7f542026249029c54'
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                         body=msg,
                         from_='+12056712693',
                         to=to_phone
                     )

    print(message.sid)



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
                return redirect('/mothers/home')

            group = groups[0]

            for member_id in ids:
                members = Member.objects.filter(id=int(member_id))
                if members.count() > 0:
                    member = members[0]

                    title = 'MotherWise Community: The Nest'
                    subject = 'You\'ve received a community message from ' + group.name
                    msg = 'Dear ' + member.name + ', You\'ve received a community message from ' + me.name + ' in ' + group.name + '. The message is as following:<br><br>'
                    msg = msg + message + '<br><br>'

                    if member.cohort == 'admin':
                        msg = msg + '<a href=\'' + settings.URL + '/manager/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>Connect the community to view message</a>'
                    else:
                        msg = msg + '<a href=\'' + settings.URL + '/mothers/open_group_chat?group_id=' + groupid + '\' target=\'_blank\'>Connect the community to view message</a>'

                    from_email = admin.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message(from_email, to_emails, title, subject, msg)

                    msg = member.name + ', You\'ve received a community message from ' + me.name + ' in ' + group.name + '. The message is as following:\n\n'
                    msg = msg + message + '\n\n'

                    if member.cohort == 'admin':
                        msg = msg + 'Click on this link to view the message: ' + settings.URL + '/manager/open_group_chat?group_id=' + groupid
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
                    subject = 'You\'ve received a group message from ' + cohort
                    msg = 'Dear ' + member.name + ', You\'ve received a group message from ' + me.name + ' in ' + cohort + '. The message is as following:<br><br>'
                    msg = msg + message + '<br><br>'

                    if member.cohort == 'admin':
                        msg = msg + '<a href=\'' + settings.URL + '/manager/group_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>Connect the group to view message</a>'
                    else:
                        msg = msg + '<a href=\'' + settings.URL + '/mothers/open_cohort_chat?cohort=' + cohort + '\' target=\'_blank\'>Connect the group to view message</a>'

                    from_email = admin.email
                    to_emails = []
                    to_emails.append(member.email)
                    send_mail_message(from_email, to_emails, title, subject, msg)

                    msg = member.name + ', You\'ve received a group message from ' + me.name + ' in ' + cohort + '. The message is as following:\n\n'
                    msg = msg + message + '\n\n'

                    if member.cohort == 'admin':
                        msg = msg + 'Click on this link to view the message: ' + settings.URL + '/manager/group_cohort_chat?cohort=' + cohort
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
                url = '/users/to_private_chat?member_id=' + str(sender.pk)
                if member.cohort == 'admin':
                    url = '/group_private_chat?email=' + sender.email
                msg = member.name + ', You\'ve received a message from ' + sender.name + '.\nThe message is as following:\n' + message
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































































































