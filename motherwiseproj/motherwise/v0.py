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

from django.db.models import Q

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

from pbsonesignal import PybossaOneSignal

from pyfcm import FCMNotification

from motherwise.models import Member, Contact, Group, GroupMember, GroupConnect, Post, PostUrlPreview, Comment, PostPicture, PostLike, Notification, Received, Sent, Replied, Conference, Report, PostCategory, Cohort
from motherwise.models import Recipe, FoodResource, CommentLike
from motherwise.serializers import PostSerializer, CommentSerializer

import pyrebase

config = {
    "apiKey": "AIzaSyDveaXbV1HHMREyZzbvQe53BJEHVIRCf14",
    "authDomain": "motherwise-1585202524394.firebaseapp.com",
    "databaseURL": "https://motherwise-1585202524394.firebaseio.com",
    "storageBucket": "motherwise-1585202524394.appspot.com"
}

firebase = pyrebase.initialize_app(config)


class UploadFileForm(forms.Form):
    file = forms.FileField()


def post_categories(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return render(request, 'motherwise/admin.html')
    except KeyError:
        print('no session')
        return render(request, 'motherwise/admin.html')

    adminID = request.session['adminID']

    pc = PostCategory.objects.filter(admin_id=adminID).first()
    categories = []
    if pc is None:
        pc = PostCategory(admin_id=adminID)
        pc.save()
    if pc.categories != '': categories = pc.categories.split(',')
    return render(request, 'motherwise/post_categories.html', {'categories':categories})


@api_view(['POST','GET'])
def savepostcategories(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    adminID = request.session['adminID']

    if request.method == 'POST':
        categories = request.POST.get('categories','')
        pc = PostCategory.objects.filter(admin_id=adminID).first()
        if pc is not None:
            pc.categories = categories
            pc.save()
            return HttpResponse('success')
        else:
            PostCategory(admin_id=adminID, categories=categories).save()
            return HttpResponse('success')

    return HttpResponse('error')



def cohort_names(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return render(request, 'motherwise/admin.html')
    except KeyError:
        print('no session')
        return render(request, 'motherwise/admin.html')

    adminID = request.session['adminID']

    c = Cohort.objects.filter(admin_id=adminID).first()
    cohorts = []
    if c is None:
        c = Cohort(admin_id=adminID)
        c.save()
    if c.cohorts != '': cohorts = c.cohorts.split(',')
    return render(request, 'motherwise/cohort_setup.html', {'cohorts':cohorts})


@api_view(['POST','GET'])
def savecohortnames(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    adminID = request.session['adminID']

    if request.method == 'POST':
        cohorts = request.POST.get('cohorts','')
        c = Cohort.objects.filter(admin_id=adminID).first()
        if c is not None:
            c.cohorts = cohorts
            c.save()
            return HttpResponse('success')
    return HttpResponse('error')



@api_view(['POST','GET'])
def membercohortchange(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')
    adminID = request.session['adminID']

    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')
        new_cohort = request.POST.get('new_cohort','')
        member = Member.objects.filter(id=member_id, admin_id=adminID).first()
        if member is not None:
            member.cohort = new_cohort
            member.save()
            return HttpResponse('success')
    return HttpResponse('error')



@api_view(['POST','GET'])
def react_post(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

    if request.method == 'POST':
        post_id = request.POST.get('post_id','0')
        feeling = request.POST.get('feeling','')

        post = Post.objects.filter(id=post_id).first()
        if post is None: return HttpResponse('error')

        pl = PostLike.objects.filter(post_id=post.pk, member_id=admin.pk).first()
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
                pl.member_id = admin.pk
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


@api_view(['POST','GET'])
def react_comment(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

    if request.method == 'POST':
        comment_id = request.POST.get('comment_id','0')
        feeling = request.POST.get('feeling','')

        comment = Comment.objects.filter(id=comment_id).first()
        if comment is None: return HttpResponse('error')

        cl = CommentLike.objects.filter(comment_id=comment.pk, member_id=admin.pk).first()
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
                cl.member_id = admin.pk
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




def comment_comment_list(request):
    import datetime
    post_id = request.GET['post_id']
    comment_id = request.GET['comment_id']

    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
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

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

    comments = Comment.objects.filter(post_id=post_id, comment_id=comment_id)
    comment_html = ''
    for comment in comments:
        cl = CommentLike.objects.filter(comment_id=comment.pk, member_id=admin.pk).first()
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
            if int(comment.member_id) == admin.pk:
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




def comment_delete(request):
    comment_id = request.GET['comment_id']

    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

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






def comida_recipe(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return render(request, 'motherwise/admin.html')
    except KeyError:
        print('no session')
        return render(request, 'motherwise/admin.html')

    adminID = request.session['adminID']

    category = 'meat'
    try: category = request.GET['category']
    except: pass

    rs = Recipe.objects.filter(admin_id=adminID, category=category).order_by('-id')
    return render(request, 'motherwise/recipes.html', {'recipes':rs, 'category':category})



@api_view(['POST','GET'])
def save_recipe(request):
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        print('no session')
        return HttpResponse('error')

    adminID = request.session['adminID']

    if request.method == 'POST':
        recipe_id = request.POST.get('recipe_id','0')
        category = request.POST.get('category','')
        site_url = request.POST.get('site_url','')

        r = Recipe.objects.filter(admin_id=adminID, id=recipe_id).first()
        if r is not None:
            r.category = category
            r.site_url = site_url
            r.save()

            createRecipeUrlPreview(r, site_url)

            return HttpResponse('success')
        else:
            r = Recipe(admin_id=adminID, member_id=adminID, category=category, site_url=site_url)
            r.save()

            createRecipeUrlPreview(r, site_url)

            return HttpResponse('success')

    return HttpResponse('error')



def delete_recipe(request):
    recipe_id = request.GET['rid']
    Recipe.objects.filter(id=recipe_id).delete()

    return HttpResponse('success')


def comida_posts(request):
    import datetime
    try:
        if request.session['adminID'] == 0:
            return render(request, 'motherwise/admin.html')
    except KeyError:
        print('no session')
        return render(request, 'motherwise/admin.html')

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

    users = Member.objects.filter(admin_id=admin.pk).order_by('-id')
    userList = []
    for user in users:
        if user.registered_time != '':
            user.username = '@' + user.email[0:user.email.find('@')]
            userList.append(user)

    list1 = []
    list2 = []
    list3 = []
    list4 = []

    uitype = ''
    if request.user_agent.is_mobile:
        uitype = 'mobile'

    mine = ''
    try: mine = request.GET['mine']
    except: pass

    allPosts = []

    if mine == 'yes': allPosts = Post.objects.filter(Q(member_id=admin.pk) & (Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='')).order_by('-id')
    else: allPosts = Post.objects.filter((Q(category='Food Resource') | Q(category='Recurso alimentario')) & Q(sch_status='')).order_by('-id')

    i = 0
    itop = 1
    for post in allPosts:
        post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
        i = i + 1
        pl = PostLike.objects.filter(post_id=post.pk, member_id=admin.pk).first()
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
            if int(memb.admin_id) == admin.pk or memb.pk == admin.pk:
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
            pst.posted_time = datetime.datetime.fromtimestamp(float(int(pst.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
    except KeyError:
        print('no key')

    categories = []
    pc = PostCategory.objects.filter(admin_id=admin.pk).first()
    if pc is not None:
        if pc.categories != '': categories = pc.categories.split(',')

    return render(request, 'motherwise/comida.html', {'me':admin, 'list1':list1, 'list2':list2, 'list3':list3, 'list4':list4, 'users':userList, 'pst':pst, 'categories':categories})





def food_resources(request):
    import datetime
    try:
        if request.session['adminID'] == 0:
            return render(request, 'motherwise/admin.html')
    except KeyError:
        print('no session')
        return render(request, 'motherwise/admin.html')

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

    FRs = FoodResource.objects.filter(member_id=adminID).order_by('-id')

    list = []

    for res in FRs:
        res.posted_time = datetime.datetime.strptime(res.posted_time, "%Y-%m-%d-%H-%M-%S").strftime("%b %d, %Y %H:%M")
        res.content = emoji.emojize(res.content)
        if 'top' in res.status: list.insert(0, res)
        else: list.append(res)

    return render(request, 'motherwise/food_resource.html', {'me':admin, 'resources':list})



def now():
    from datetime import datetime
    return datetime.now()


@api_view(['GET', 'POST'])
def saveFR(request):
    if request.method == 'POST':

        rid = request.POST.get('rid', '0')
        frtitle = request.POST.get('res-title', '')
        frlocation = request.POST.get('res-location', '')
        frgroup = request.POST.get('res-group', '')
        frmeals = request.POST.get('res-meals', '')
        frlink = request.POST.get('res-link', '')
        frdesc = request.POST.get('res-desc', '')

        try:
            if request.session['adminID'] == '' or request.session['adminID'] == 0:
                return HttpResponse('error')
        except KeyError:
            return HttpResponse('error')

        adminID = request.session['adminID']
        admin = Member.objects.get(id=adminID)

        fs = FileSystemStorage()

        fr = None
        if int(rid) == 0:
            fr = FoodResource(admin_id=adminID, member_id=adminID, title=frtitle, group=frgroup, location=frlocation, daily_meal=frmeals, content=frdesc, link=frlink, posted_time=now().strftime("%Y-%m-%d-%H-%M-%S"))
            fr.save()
        else:
            fr = FoodResource.objects.filter(id=rid).first()
            fr.title = frtitle
            fr.group = frgroup
            fr.location = frlocation
            fr.daily_meal = frmeals
            fr.content = frdesc
            fr.link = frlink
            fr.save()

        try:
            image = request.FILES['image']
            if fr.filename != '': fs.delete(fr.filename)
            elif fr.image_url != '': fs.delete(fr.image_url.replace(settings.URL+'/media/',''))
            filename = fs.save(image.name, image)
            uploaded_url = fs.url(filename)
            fr.image_url = settings.URL + uploaded_url
            fr.filename = filename
            fr.save()
        except MultiValueDictKeyError:
            print('no video updated')

        return HttpResponse('success')




def deleteFR(request):
    rid = request.GET['rid']
    try:
        if request.session['adminID'] == '' or request.session['adminID'] == 0:
            return HttpResponse('error')
    except KeyError:
        return HttpResponse('error')

    adminID = request.session['adminID']
    admin = Member.objects.get(id=adminID)

    fs = FileSystemStorage()

    fr = FoodResource.objects.filter(id=rid).first()
    if fr is None: return HttpResponse('error')

    if fr.filename != '': fs.delete(fr.filename)
    elif fr.image_url != '': fs.delete(fr.image_url.replace(settings.URL+'/media/',''))

    fr.delete()

    return HttpResponse('success')




def restoplevelsetup(request):
    res_id = request.GET['res_id']
    res = FoodResource.objects.filter(id=res_id).first()
    if res is not None:
        if not 'top' in res.status:
            res.status += 'top'
        else:
            res.status = res.status.replace('top','')
        res.save()
    return redirect('/motherwise/foodresources/')




def createRecipeUrlPreview(recipe, wurl):
    if wurl != '':
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

            if wtitle is not None: recipe.title = wtitle
            elif wforcetitle is not None: recipe.title = wforcetitle
            if wdescription is not None: recipe.description = wdescription
            if wimageurl is not None and 'http' in wimageurl: recipe.image_url = wimageurl
            elif wabsoluteimageurl is not None: recipe.image_url = wabsoluteimageurl
            if icon is not None: recipe.icon_url = icon.url
            recipe.site_url = wurl
            recipe.save()
        except:
            print('Error')
            try:
                driver = webdriver.Chrome()
                driver.get(wurl)
                wtitle = driver.title

                icons = favicon.get(wurl)
                icon = None
                if icons is not None and len(icons) > 0: icon = icons[0]

                if wtitle is not None: recipe.title = wtitle
                if icon is not None: recipe.icon_url = icon.url
                recipe.site_url = wurl
                recipe.save()
            except:
                pass
        else:
            pass



























































































































