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
from motherwise.models import Cohort, CommentLike, Recipe, FoodResource
from motherwise.serializers import PostUrlPreviewSerializer, PostSerializer, CommentSerializer, RecipeSerializer, FoodResourceSerializer

import pyrebase

config = {
    "apiKey": "AIzaSyDveaXbV1HHMREyZzbvQe53BJEHVIRCf14",
    "authDomain": "motherwise-1585202524394.firebaseapp.com",
    "databaseURL": "https://motherwise-1585202524394.firebaseio.com",
    "storageBucket": "motherwise-1585202524394.appspot.com"
}

firebase = pyrebase.initialize_app(config)


def comida_home(request):
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

    admin = Member.objects.get(id=me.admin_id)

    postlist = []

    posts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='') & ~Q(status__icontains='top'))
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

    top_posts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='') & Q(status__icontains='top')).order_by('-id')
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
                    'member':memb,
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

    frs = FoodResource.objects.filter(member_id=me.admin_id).order_by('-id')
    frlist = []
    for fr in frs:
        if 'top' in fr.status: frlist.insert(0, fr)
        else: frlist.append(fr)

    rs = Recipe.objects.filter(admin_id=me.admin_id, category='meat').order_by('-id')

    return render(request, 'mothers/comida.html', {'me':me, 'admin':admin, 'list':postlist, 'pst':pst, 'resources':frlist, 'total_count':str(total_count), 'recipes':rs, 'category':'meat'})



def refresh_recipe(request):
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

    category = request.GET['category']

    rs = Recipe.objects.filter(admin_id=me.admin_id, category=category).order_by('-id')

    html = '<span class="fa fa-close btn-close" onclick="javascript:document.getElementById(\'recipe-section\').style.display=\'none\'; document.getElementById(\'backgroundOverlay\').style.display=\'none\';"></span>'
    html += '<div class="list-ttl">'
    ttl = 'MEAT RECIPES'
    if category == 'meat': ttl = 'MEAT RECIPES'
    elif category == 'vegetarian': ttl = 'VEGETARIAN RECIPES'
    elif category == 'light_bites': ttl = 'LIGHT BITES RECIPES'
    elif category == 'sweet_tooth': ttl = 'SWEET TOOTH RECIPES'
    html += ttl
    html += '</div>'

    if rs.count() > 0:
        html += '<div class="r-container">'
        for r in rs:
            if r.title != '':
                html += '<div class="r-item" id="' + str(r.pk) + '">'
                html += '<div class="form-group r-prev">'
                html += '<div onclick="window.open(\'' + r.site_url + '\');">'
                if r.image_url != '':
                    html += '<img src="' + r.image_url + '" onerror="this.style.display=\'none\';">'
                html += '<div>'
                html += '<label class="max-2lines">' + r.title + '</label>'
                if r.description != '':
                    html += '<div class="singleline">' + r.description + '</div>'
                html += '<div class="r-prev-link d-flex">'
                if r.icon_url != '':
                    html += '<img src="' + r.icon_url + '">'
                html += '<div id="site-link" class="max-2lines">' + r.site_url + '</div>'
                html += '</div>'
                html += '</div>'
                html += '</div>'
                html += '</div>'
                html += '</div>'
            else:
                html += '<div class="r-item" id="' + str(r.id) + '">'
                html += '<div class="form-group">'
                html += '<a href="' + r.site_url + '" target="_blank" class="item-link singleline" id="site-link">'
                html += r.site_url
                html += '</a>'
                html += '</div>'
                html += '</div>'

        html += '</div>'

    else:
        html += '<div class="no-list">'
        html += 'No result found...'
        html += '</div>'

    context = {
        'result': 'success',
        'html': html,
    }
    return HttpResponse(json.dumps(context))




def refresh_comida_home(request):
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

    posts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='') & ~Q(status__icontains='top'))
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
        'endindx': str(int(endindx) + 25),
        'total_count': str(total_count)
    }
    return HttpResponse(json.dumps(context))





def search_comida_home(request):
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

    posts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & (Q(title__icontains=q) | Q(category__icontains=q)) & Q(sch_status='') & ~Q(status__icontains='top'))
    total_count = posts.count()

    # return HttpResponse(endindx)

    posts = posts.order_by('-id')

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
























































































