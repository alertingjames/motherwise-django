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



def testhome(request):
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
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
        pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
        if pl is not None: post.liked = pl.status
        else: post.liked = ''
        comments = Comment.objects.filter(post_id=post.pk)
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(likes.count())
        post.content = emoji.emojize(post.content)
        memb = Member.objects.filter(id=post.member_id).first()
        if memb is not None:
            if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                data = {
                    'member':memb,
                    'post': post,
                    'prevs': prevs,
                }
                postlist.append(data)

    top_posts = Post.objects.filter(sch_status='', status__icontains='top').order_by('-id')
    total_count += top_posts.count()
    for post in top_posts:
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
        pl = PostLike.objects.filter(post_id=post.pk, member_id=me.pk).first()
        if pl is not None: post.liked = pl.status
        else: post.liked = ''
        comments = Comment.objects.filter(post_id=post.pk)
        post.comments = str(comments.count())
        likes = PostLike.objects.filter(post_id=post.pk)
        post.reactions = str(likes.count())
        post.content = emoji.emojize(post.content)
        memb = Member.objects.filter(id=post.member_id).first()
        if memb is not None:
            if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                data = {
                    'member':memb,
                    'post': post,
                    'prevs': prevs,
                }
                postlist.insert(0,data)

    pst = None
    try:
        post_id = request.GET['post_id']
        pst = Post.objects.filter(id=post_id).first()
    except KeyError:
        pass

    return render(request, 'mothers/testhome.html', {'me':me, 'admin':admin, 'groups':groupList, 'list':postlist, 'pst':pst, 'cohorts':cohorts, 'contactors':memberlist, 'total_count':str(total_count)})




def refresh_home_list(request):
    import datetime
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            context = {
                'result': 'no_auth',
                'html': '',
            }
            return HttpResponse(json.dumps(context))
    except KeyError:
        print('no session')
        context = {
            'result': 'no_auth',
            'html': '',
        }
        return HttpResponse(json.dumps(context))

    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)

    endindx = request.GET['endindx']

    posts = Post.objects.filter(Q(sch_status='') & ~Q(status__icontains='top'))
    total_count = posts.count()

    # return HttpResponse(endindx)

    posts = posts.order_by('-id')[int(endindx):int(endindx) + 25]

    post_html = ''
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
            if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                memb.registered_time = datetime.datetime.fromtimestamp(float(int(memb.registered_time)/1000)).strftime("%b %d, %Y")
                prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                prev_html = ''
                for prev in prevs:
                    prev_html += '<div class="form-group prev">' + '<div onclick="window.open(\'' + prev.site_url + '\');">'
                    if prev.image_url != '':
                        html1 = '<img src="' + prev.image_url + '" onerror="this.style.display=\'none\';">' + '<div>' + '<label class="max-2lines">' + prev.title + '</label>'
                        if prev.description != '':
                            html2 = '<div class="singleline">' + prev.description + '</div>'
                            html1 += html2
                        html1 += '<div class="prev-link d-flex">'
                        if prev.icon_url != '':
                            html2 = '<img src="' + prev.icon_url + '">'
                            html1 += html2
                        html1 += '<div class="max-2lines">' + prev.site_url + '</div></div></div>'
                        prev_html += html1
                    else:
                        html1 = '<div>' + '<label class="max-2lines">' + prev.title + '</label>'
                        if prev.description != '':
                            html2 = '<div class="singleline">' + prev.description + '</div>'
                            html1 += html2
                        html1 += '<div class="prev-link d-flex">'
                        if prev.icon_url != '':
                            html2 = '<img src="' + prev.icon_url + '">'
                            html1 += html2
                        html1 += '<div class="max-2lines">' + prev.site_url + '</div></div></div>'
                        prev_html += html1
                    prev_html += '</div></div>'


                post_html += '<div class="postform" id="' + str(post.pk) + '">' + '<div class="contentform">' + '<div class="post-header">' + '<div class="member-photo-section">' \
                    + '<a href="javascript:void(0)" onclick="showPosterProfile(this)">'
                u_photo = '/static/images/ic_profile.png'
                if memb.photo_url != '': u_photo = memb.photo_url
                elif memb.cohort == 'admin': u_photo = '/static/images/manager.jpg'
                post_html += '<img src="' + u_photo + '" class="member-photo">' + '</a>' + '</div>' + '<a href="javascript:void(0)" onclick="showPosterProfile(this)" style="flex-grow:1;">' \
                    + '<div class="member-name">' + memb.name + '<div>'
                u_cohort = memb.cohort
                if memb.cohort == 'admin': u_cohort = 'Manager'
                post_html += u_cohort + '</div>' + '</div>' + '</a>'
                post_html += '<input hidden id="u-id" value="' + str(memb.pk) + '">'
                post_html += '<input hidden id="u-name" value="' + memb.name + '">'
                post_html += '<input hidden id="u-cohort" value="' + memb.cohort + '">'
                post_html += '<input hidden id="u-city" value="' + memb.city + '">'
                post_html += '<input hidden id="u-admin" value="' + memb.admin_id + '">'
                post_html += '<input hidden id="u-registered" value="' + memb.registered_time + '">'
                post_html += '<input hidden id="u-photo" value="' + memb.photo_url + '">'
                if 'top' in post.status: post_html += '<img src="/static/images/top.png" class="top">'
                post_html += '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '">'
                if memb.pk == me.pk: post_html += '<span class="fa fa-pencil action-btn"></span>'
                else: post_html += '<span class="far fa-comment-alt action-btn"></span>'
                post_html += '</a>'
                if memb.pk == me.pk:
                    post_html += '<a href="javascript:void(0)" onclick="confirmDeletion(\'' + str(post.pk) + '\')">' + '<span class="fa fa-trash action-btn"></span>' + '</a>'
                post_html += '</div>'
                post_html += '<div class="form-group text-center">' + '<div class="text post-title">' + post.title + '</div>' + '<div class="post-category">' + post.category + '</div>' + '<div class="post-time">' + \
                    post.posted_time + '</div>' + '</div>'
                if post.picture_url != '':
                    post_html += '<div class="form-group">' + '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '"><div class="post-picture-frame"><img src="' + post.picture_url + \
                        '" class="post-picture" onerror="this.onerror=null;this.src=\'https://rec.or.id/images/article/no-image-available.jpg\';">'
                    if pp_cnt > 0: post_html += '<label class="pp-cnt">+' + str(pp_cnt) + '</label>'
                    post_html += '</div></a>' + '</div>'
                post_html += '<div class="form-group">' + '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '" class="text post-content">' + post.content + '</a>' + '</div>'
                post_html += prev_html
                #start footer
                post_html += '<div class="post-footer">' + '<div class="post-actions">' + '<a class="FB_reactions" data-reactions-type="horizontal" data-unique-id="' + str(post.pk) + '" data-emoji-class="' + \
                    post.liked + '" style="margin-top:-10px;margin-right:15px;">' + '<span id="flbl-' + str(post.pk) + '">'
                if post.liked != '': post_html += post.liked
                else: post_html += 'Like'
                post_html += '</span>'
                post_html += '</a>'
                post_html += '<div id="ricon-container-' + str(post.pk) + '" class="ricon-container">' + '<img src="/static/reactions/emojis/like.svg" class="ricon" id="like-' + str(post.pk) + '" style="display:'
                if post.likes == '' or int(post.likes) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/love.svg" class="ricon" id="love-' + str(post.pk) + '" style="display:'
                if post.loves == '' or int(post.loves) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/haha.svg" class="ricon" id="haha-' + str(post.pk) + '" style="display:'
                if post.haha == '' or int(post.haha) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/wow.svg" class="ricon" id="wow-' + str(post.pk) + '" style="display:'
                if post.wow == '' or int(post.wow) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/sad.svg" class="ricon" id="sad-' + str(post.pk) + '" style="display:'
                if post.sad == '' or int(post.sad) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/angry.svg" class="ricon" id="angry-' + str(post.pk) + '" style="display:'
                if post.angry == '' or int(post.angry) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '</div>'
                post_html += '<label id="feelings-' + str(post.pk) + '" style="display:'
                if post.reactions == '' or int(post.reactions) == 0: post_html += 'none;'
                post_html += '">'
                post_html += post.reactions + '</label>'
                post_html += '<span class="far fa-comment-alt" style="margin-left:20px;"></span> ' + post.comments + '</div>'
                post_html += '<div class="post-detail-section">' + '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '" class="post-detail-btn">' + '<span class="fas fa-arrow-right"></span>' + '</a>'
                post_html += '</div>' + '</div>'
                # end footer
                # start comments
                post_html += '<div class="pc-section">'
                comments1 = comments[:5]
                for comment in comments1:
                    cm = Member.objects.filter(id=comment.member_id).first()
                    if cm is not None:
                        comment.comment_text = emoji.emojize(comment.comment_text)
                        post_html += '<div>'
                        post_html += '<div>'
                        cm_photo = '/static/images/ic_profile.png'
                        if cm.photo_url != '': cm_photo = cm.photo_url
                        post_html += '<img src="' + cm_photo + '">'
                        post_html += '<span>' + cm.name + '</span>'
                        post_html += '</div>'
                        post_html += '<div class="text pc-item-comment">' + comment.comment_text + '</div>'
                        post_html += '</div>'
                if comments.count() > 5:
                    post_html += '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '">View more comments</a>'
                post_html += '</div>'
                # end comments
                post_html += '</div>' + '</div>' + '<br>'

    context = {
        'result': 'success',
        'html': post_html,
        'endindx': str(int(endindx) + 25),
        'total_count': str(total_count)
    }
    return HttpResponse(json.dumps(context))




import geonamescache
from geopy.geocoders import Nominatim

def getcoloradocities(request):
    # get a dictionary of cities: 'c'
    gc = geonamescache.GeonamesCache()
    c = gc.get_cities()

    # extract the US city names and coordinates
    US_cities = [c[key]['name'] for key in list(c.keys())
                 if c[key]['countrycode'] == 'US']
    US_longs = [c[key]['longitude'] for key in list(c.keys())
                if c[key]['countrycode'] == 'US']
    US_latts = [c[key]['latitude'] for key in list(c.keys())
                if c[key]['countrycode'] == 'US']
    # find the states of each city
    # WARNING: this takes a while
    US_states = get_states(US_longs, US_latts)
    state_to_city = {}
    for state, city in zip(US_states, US_cities):
        if city:
            state_to_city[state] = city

    return HttpResponse(json.dumps(state_to_city))






def get_states(longs, latts):
    ''' Input two 1D lists of floats/ints '''
    # a list of states
    states = []

    # use a coordinate tool from the geopy library
    geolocator = Nominatim(user_agent="motherwise")
    for lon, lat in zip(longs, latts):
        try:
            # get the state name
            location = geolocator.reverse(str(lat)+', '+str(lon))
            state = location.raw['address']['state']
        except:
            # return empty string
            state = ''
        states.append(state)
    return states




def comment_comment_list(request):
    import datetime
    post_id = request.GET['post_id']
    comment_id = request.GET['comment_id']
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            context = {
                'result': 'no_auth',
                'html': '',
            }
            return HttpResponse(json.dumps(context))
    except KeyError:
        print('no session')
        context = {
            'result': 'no_auth',
            'html': '',
        }
        return HttpResponse(json.dumps(context))
    memberID = request.session['memberID']
    me = Member.objects.get(id=memberID)
    comments = Comment.objects.filter(post_id=post_id, comment_id=comment_id)
    comment_html = ''
    for comment in comments:
        cl = CommentLike.objects.filter(comment_id=comment.pk, member_id=me.pk).first()
        if cl is not None: comment.liked = cl.status
        else: comment.liked = ''
        cmts = Comment.objects.filter(comment_id=comment.pk)
        comment.comments = str(cmts.count())
        likes = CommentLike.objects.filter(comment_id=comment.pk)
        comment.reactions = str(likes.count())
        comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
        memb = Member.objects.filter(id=comment.member_id).first()
        if memb is not None:
            comment.comment_text = emoji.emojize(comment.comment_text)
            u_photo = '/static/images/ic_profile.png'
            if memb.photo_url != '': u_photo = memb.photo_url
            elif memb.cohort == 'admin': u_photo = '/static/images/manager.jpg'
            comment_html += '<div class="user-form"><div class="contentform"><div style="display:flex;"><div>' \
                + '<img src="' + u_photo + '" class="comment-user-picture"></div>'
            comment_html += '<div style="flex-grow:1;"><div class="row comment-member-section"><div class="col-sm-5"><div class="comment-user-name">' \
                + memb.name + '</div><div class="comment-user-cohort">'
            u_cohort = memb.cohort
            if memb.cohort == 'admin': u_cohort = 'Manager'
            comment_html += u_cohort + '</div></div>' + '<div class="col-sm-5 ctime">'
            comment_html += comment.commented_time + '</div></div></div>'
            comment_html += '<div>'
            if int(comment.member_id) == me.pk:
                comment_html += '<a href="javascript:void(0)" id="del-' + str(comment.pk) + '" onclick="showDeleteCommentAlert(this)">' \
                    + '<span class="fa fa-times combtn"></span></a>'
            else:
                comment_html += '<a href="/mothers/to_private_chat?member_id=' + str(memb.pk) + '" target="_blank" style="background-color:transparent;margin-left:15px; margin-right:8px;">' \
                    + '<span class="fa fa-comments combtn"></span></a>'
            comment_html += '</div></div>'
            comment_html += '<div class="divider"></div><div style="text-align:left;"><div id="note" class="note">' + comment.comment_text + '</div>'
            if comment.image_url != '':
                comment_html += '<a href="' + comment.image_url + '" target="_blank"><img src="' + comment.image_url + '" class="comment-attached"></a><br><br>'
            comment_html += '</div>'
            comment_html += '<div class="comment-footer" id="item-footer-' + str(comment.pk) + '"><div class="comment-actions">' + '<a class="COMMENT_reactions" data-reactions-type="horizontal" data-unique-id="' \
                + str(comment.pk) + '" data-emoji-class="' + comment.liked + '" style="margin-top:-10px;margin-right:15px;">' + '<span id="clbl-' + str(comment.pk) + '">'
            if comment.liked != '': comment_html += comment.liked
            else: comment_html += 'Like'
            comment_html += '</span>'
            comment_html += '</a>'
            comment_html += '<div id="ricon-container-' + str(comment.pk) + '" class="ricon-container">' + '<img src="/static/reactions/emojis/like.svg" class="ricon" id="like-' + str(comment.pk) + '" style="display:'
            if comment.likes == '' or int(comment.likes) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += '<img src="/static/reactions/emojis/love.svg" class="ricon" id="love-' + str(comment.pk) + '" style="display:'
            if comment.loves == '' or int(comment.loves) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += '<img src="/static/reactions/emojis/haha.svg" class="ricon" id="haha-' + str(comment.pk) + '" style="display:'
            if comment.haha == '' or int(comment.haha) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += '<img src="/static/reactions/emojis/wow.svg" class="ricon" id="wow-' + str(comment.pk) + '" style="display:'
            if comment.wow == '' or int(comment.wow) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += '<img src="/static/reactions/emojis/sad.svg" class="ricon" id="sad-' + str(comment.pk) + '" style="display:'
            if comment.sad == '' or int(comment.sad) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += '<img src="/static/reactions/emojis/angry.svg" class="ricon" id="angry-' + str(comment.pk) + '" style="display:'
            if comment.angry == '' or int(comment.angry) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += '</div>'
            comment_html += '<label id="feelings-' + str(comment.pk) + '" style="display:'
            if comment.reactions == '' or int(comment.reactions) == 0: comment_html += 'none;'
            comment_html += '">'
            comment_html += comment.reactions + '</label>'
            comsg = 'No comment'
            if int(comment.comments) > 0: comsg = 'View comments'
            comment_html += '<span class="far fa-comment-alt" style="margin-top:2px;" data-toggle="tooltip" data-placement="top" title="' + comsg + '" id="comment-list-btn-' + str(comment.pk) + '" onclick="refreshCommentForComment(this)"></span>' \
                + '<label class="item-comments" style="margin-left:3px;">' + comment.comments + '</label>' \
                + '<span class="fa fa-pencil" style="margin-top:2px;" id="' + str(comment.pk) + '" onclick="openCommentInputSection(this)" data-toggle="tooltip" data-placement="top" title="Add comment"></span></div><div class="sub-comments"></div>'
            comment_html += '</div>' + '</div>' + '</div>'
    context = {
        'result': 'success',
        'html': comment_html,
        'item_count': str(comments.count()),
    }
    return HttpResponse(json.dumps(context))





def search_home_list(request):
    import datetime
    try:
        if request.session['memberID'] == '' or request.session['memberID'] == 0:
            context = {
                'result': 'no_auth',
                'html': '',
            }
            return HttpResponse(json.dumps(context))
    except KeyError:
        print('no session')
        context = {
            'result': 'no_auth',
            'html': '',
        }
        return HttpResponse(json.dumps(context))

    memberID = request.session['memberID']
    me = Member.objects.filter(id=memberID).first()
    if me is None:
        context = {
            'result': 'error',
            'html': '',
            'total_count': '0'
        }
        return HttpResponse(json.dumps(context))

    q = request.POST.get('q','')

    posts = Post.objects.filter((Q(title__icontains=q) | Q(category__icontains=q)) & Q(sch_status='') & ~Q(status__icontains='top')).order_by('-id')
    total_count = posts.count()

    if posts.count() == 0:
        allPosts = Post.objects.filter(sch_status='').order_by('-id')
        posts1 = []
        for p in allPosts:
            m = Member.objects.filter(id=p.member_id, name__istartswith=q.lower()).first()
            if m is not None: posts1.append(p)
        total_count = len(posts1)
        posts = posts1

    # return HttpResponse(endindx)

    post_html = ''
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
            if memb.admin_id == me.admin_id or memb.pk == int(me.admin_id):
                memb.registered_time = datetime.datetime.fromtimestamp(float(int(memb.registered_time)/1000)).strftime("%b %d, %Y")
                prevs = PostUrlPreview.objects.filter(post_id=post.pk)
                prev_html = ''
                for prev in prevs:
                    prev_html += '<div class="form-group prev">' + '<div onclick="window.open(\'' + prev.site_url + '\');">'
                    if prev.image_url != '':
                        html1 = '<img src="' + prev.image_url + '" onerror="this.style.display=\'none\';">' + '<div>' + '<label class="max-2lines">' + prev.title + '</label>'
                        if prev.description != '':
                            html2 = '<div class="singleline">' + prev.description + '</div>'
                            html1 += html2
                        html1 += '<div class="prev-link d-flex">'
                        if prev.icon_url != '':
                            html2 = '<img src="' + prev.icon_url + '">'
                            html1 += html2
                        html1 += '<div class="max-2lines">' + prev.site_url + '</div></div></div>'
                        prev_html += html1
                    else:
                        html1 = '<div>' + '<label class="max-2lines">' + prev.title + '</label>'
                        if prev.description != '':
                            html2 = '<div class="singleline">' + prev.description + '</div>'
                            html1 += html2
                        html1 += '<div class="prev-link d-flex">'
                        if prev.icon_url != '':
                            html2 = '<img src="' + prev.icon_url + '">'
                            html1 += html2
                        html1 += '<div class="max-2lines">' + prev.site_url + '</div></div></div>'
                        prev_html += html1
                    prev_html += '</div></div>'


                post_html += '<div class="postform" id="' + str(post.pk) + '">' + '<div class="contentform">' + '<div class="post-header">' + '<div class="member-photo-section">' \
                    + '<a href="javascript:void(0)" onclick="showPosterProfile(this)">'
                u_photo = '/static/images/ic_profile.png'
                if memb.photo_url != '': u_photo = memb.photo_url
                elif memb.cohort == 'admin': u_photo = '/static/images/manager.jpg'
                post_html += '<img src="' + u_photo + '" class="member-photo">' + '</a>' + '</div>' + '<a href="javascript:void(0)" onclick="showPosterProfile(this)" style="flex-grow:1;">' \
                    + '<div class="member-name">' + memb.name + '<div>'
                u_cohort = memb.cohort
                if memb.cohort == 'admin': u_cohort = 'Manager'
                post_html += u_cohort + '</div>' + '</div>' + '</a>'
                post_html += '<input hidden id="u-id" value="' + str(memb.pk) + '">'
                post_html += '<input hidden id="u-name" value="' + memb.name + '">'
                post_html += '<input hidden id="u-cohort" value="' + memb.cohort + '">'
                post_html += '<input hidden id="u-city" value="' + memb.city + '">'
                post_html += '<input hidden id="u-admin" value="' + memb.admin_id + '">'
                post_html += '<input hidden id="u-registered" value="' + memb.registered_time + '">'
                post_html += '<input hidden id="u-photo" value="' + memb.photo_url + '">'
                if 'top' in post.status: post_html += '<img src="/static/images/top.png" class="top">'
                post_html += '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '">'
                if memb.pk == me.pk: post_html += '<span class="fa fa-pencil action-btn"></span>'
                else: post_html += '<span class="far fa-comment-alt action-btn"></span>'
                post_html += '</a>'
                if memb.pk == me.pk:
                    post_html += '<a href="javascript:void(0)" onclick="confirmDeletion(\'' + str(post.pk) + '\')">' + '<span class="fa fa-trash action-btn"></span>' + '</a>'
                post_html += '</div>'
                post_html += '<div class="form-group text-center">' + '<div class="text post-title">' + post.title + '</div>' + '<div class="post-category">' + post.category + '</div>' + '<div class="post-time">' + \
                    post.posted_time + '</div>' + '</div>'
                if post.picture_url != '':
                    post_html += '<div class="form-group">' + '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '"><div class="post-picture-frame"><img src="' + post.picture_url + \
                        '" class="post-picture" onerror="this.onerror=null;this.src=\'https://rec.or.id/images/article/no-image-available.jpg\';">'
                    if pp_cnt > 0: post_html += '<label class="pp-cnt">+' + str(pp_cnt) + '</label>'
                    post_html += '</div></a>' + '</div>'
                post_html += '<div class="form-group">' + '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '" class="text post-content">' + post.content + '</a>' + '</div>'
                post_html += prev_html
                # start footer
                post_html += '<div class="post-footer">' + '<div class="post-actions">' + '<a class="FB_reactions" data-reactions-type="horizontal" data-unique-id="' + str(post.pk) + '" data-emoji-class="' + \
                    post.liked + '" style="margin-top:-10px;margin-right:15px;">' + '<span id="flbl-' + str(post.pk) + '">'
                if post.liked != '': post_html += post.liked
                else: post_html += 'Like'
                post_html += '</span>'
                post_html += '</a>'
                post_html += '<div id="ricon-container-' + str(post.pk) + '" class="ricon-container">' + '<img src="/static/reactions/emojis/like.svg" class="ricon" id="like-' + str(post.pk) + '" style="display:'
                if post.likes == '' or int(post.likes) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/love.svg" class="ricon" id="love-' + str(post.pk) + '" style="display:'
                if post.loves == '' or int(post.loves) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/haha.svg" class="ricon" id="haha-' + str(post.pk) + '" style="display:'
                if post.haha == '' or int(post.haha) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/wow.svg" class="ricon" id="wow-' + str(post.pk) + '" style="display:'
                if post.wow == '' or int(post.wow) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/sad.svg" class="ricon" id="sad-' + str(post.pk) + '" style="display:'
                if post.sad == '' or int(post.sad) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '<img src="/static/reactions/emojis/angry.svg" class="ricon" id="angry-' + str(post.pk) + '" style="display:'
                if post.angry == '' or int(post.angry) == 0: post_html += 'none;'
                post_html += '">'
                post_html += '</div>'
                post_html += '<label id="feelings-' + str(post.pk) + '" style="display:'
                if post.reactions == '' or int(post.reactions) == 0: post_html += 'none;'
                post_html += '">'
                post_html += post.reactions + '</label>'
                post_html += '<span class="far fa-comment-alt" style="margin-left:20px;"></span> ' + post.comments + '</div>'
                post_html += '<div class="post-detail-section">' + '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '" class="post-detail-btn">' + '<span class="fas fa-arrow-right"></span>' + '</a>'
                post_html += '</div>' + '</div>'
                # end footer
                # start comments
                post_html += '<div class="pc-section">'
                comments1 = comments[:5]
                for comment in comments1:
                    cm = Member.objects.filter(id=comment.member_id).first()
                    if cm is not None:
                        comment.comment_text = emoji.emojize(comment.comment_text)
                        post_html += '<div>'
                        post_html += '<div>'
                        cm_photo = '/static/images/ic_profile.png'
                        if cm.photo_url != '': cm_photo = cm.photo_url
                        post_html += '<img src="' + cm_photo + '">'
                        post_html += '<span>' + cm.name + '</span>'
                        post_html += '</div>'
                        post_html += '<div class="text pc-item-comment">' + comment.comment_text + '</div>'
                        post_html += '</div>'
                if comments.count() > 5:
                    post_html += '<a href="/mothers/add_post_comment?post_id=' + str(post.pk) + '">View more comments</a>'
                post_html += '</div>'
                # end comments
                post_html += '</div>' + '</div>' + '<br>'

    context = {
        'result': 'success',
        'html': post_html,
        'total_count': str(total_count)
    }
    return HttpResponse(json.dumps(context))






































































































































