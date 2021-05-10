from django.conf.urls import url
from . import views

app_name='usermobile'

urlpatterns=[
    url(r'^$', views.index, name='index'),
    url(r'login', views.login, name='login'),
    url(r'register', views.register, name='register'),
    url(r'forgotpassword',views.forgotpassword,  name='forgotpassword'),
    url(r'resetpassword', views.resetpassword, name='resetpassword'),
    url(r'rstpwd',views.rstpwd,  name='rstpwd'),
    url(r'addlocation',views.addlocation,  name='addlocation'),
    url(r'home',views.home,  name='home'),
    url(r'sendmembermessage',views.sendmembermessage,  name='sendmembermessage'),
    url(r'messageselecteds',views.messageselecteds,  name='messageselecteds'),
    url(r'networkposts', views.networkposts,  name='networkposts'),
    url(r'likepost', views.likepost,  name='likepost'),
    url(r'getcomments', views.getcomments,  name='getcomments'),
    url(r'submitcomment', views.submitcomment,  name='submitcomment'),
    url(r'deletepost', views.deletepost,  name='deletepost'),
    url(r'deletecomment', views.deletecomment,  name='deletecomment'),
    url(r'getpostpictures', views.getpostpictures,  name='getpostpictures'),
    url(r'createpost', views.createpost,  name='createpost'),
    url(r'delpostpicture', views.delpostpicture,  name='delpostpicture'),
    url(r'getlikes', views.getlikes,  name='getlikes'),
    url(r'getreceivedmessages', views.getreceivedmessages,  name='getreceivedmessages'),
    url(r'delmessage', views.deletemessage,  name='deletemessage'),
    url(r'processnewmessage', views.processnewmessage,  name='processnewmessage'),
    url(r'getsentmessages', views.getsentmessages,  name='getsentmessages'),
    url(r'replymessage', views.replymessage,  name='replymessage'),
    url(r'messagehistory', views.messagehistory,  name='messagehistory'),
    url(r'newnotis',views.newnotis,  name='newnotis'),
    url(r'getconfs',views.getconfs,  name='getconfs'),
    url(r'changepassword',views.changepassword,  name='changepassword'),
    url(r'openconference',views.openconference,  name='openconference'),
    url(r'getgroupmembers',views.getgroupmembers,  name='getgroupmembers'),
    url(r'groupconfs',views.getgroupconfs,  name='getgroupconfs'),
    url(r'notifygroupchatmembers',views.notifygroupchatmembers,  name='notifygroupchatmembers'),
    url(r'uploadfcmtoken',views.fcmregister,  name='fcmregister'),
    url(r'sendfcmpush',views.sendfcmpush,  name='sendfcmpush'),
    url(r'requestvideocall',views.requestvideocall,  name='requestvideocall'),
    url(r'readterms',views.readterms,  name='readterms'),
    url(r'reportmember',views.reportmember,  name='reportmember'),

]














































