from django.conf.urls import url
from . import views

app_name='mothers'

urlpatterns=[
    url(r'^$', views.member_login_page, name='member_login_page'),
    url(r'login', views.member_login, name='member_login'),
    url(r'firstpage', views.firstpage, name='firstpage'),
    url(r'home', views.memberhome, name='memberhome'),
    url(r'torequestpwd',views.torequestpwd,  name='torequestpwd'),
    url(r'pwdforgot',views.send_mail_forgotpassword,  name='send_mail_forgotpassword'),
    url(r'resetpassword', views.resetpassword, name='resetpassword'),
    url(r'rstpwd',views.rstpwd,  name='rstpwd'),
    url(r'pick_location',views.pick_location,  name='pick_location'),
    url(r'attach_location_profile',views.attach_location_profile,  name='attach_location_profile'),
    url(r'register',views.register_profile,  name='register_profile'),
    url(r'completeprofile',views.complete_profile,  name='complete_profile'),
    url(r'logout',views.logout,  name='logout'),
    url(r'contact_selecteds',views.contact_selecteds,  name='contact_selecteds'),
    url(r'tohome',views.tohome,  name='tohome'),
    url(r'do_cohort',views.do_cohort,  name='do_cohort'),
    url(r'to_cohort_chat',views.to_cohort_chat,  name='to_cohort_chat'),
    url(r'do_group',views.do_group,  name='do_group'),
    url(r'search_members',views.search_members,  name='search_members'),
    url(r'to_private_chat',views.to_private_chat,  name='to_private_chat'),
    url(r'send_member_message',views.send_member_message,  name='send_member_message'),
    url(r'switch_chat',views.switch_chat,  name='switch_chat'),
    url(r'switch_cohort_chat',views.switch_cohort_chat,  name='switch_cohort_chat'),
    url(r'open_group_chat',views.open_group_chat,  name='open_group_chat'),
    url(r'open_cohort_chat',views.open_cohort_chat,  name='open_cohort_chat'),
    url(r'posts',views.to_posts,  name='to_posts'),
    url(r'mineppppp',views.my_posts,  name='my_posts'),
    url(r'create_post',views.create_post,  name='create_post'),
    url(r'add_post_comment',views.add_post_comment,  name='add_post_comment'),
    url(r'search_post',views.search_post,  name='search_post'),
    url(r'filter',views.filter,  name='filter'),
    url(r'submit_comment',views.submit_comment,  name='submit_comment'),
    url(r'delpost',views.delete_post,  name='delete_post'),
    url(r'delcomment',views.delete_comment,  name='delete_comment'),
    url(r'like_post',views.like_post,  name='like_post'),
    url(r'postdelpicture',views.delete_post_picture,  name='delete_post_picture'),
    url(r'edit_post',views.edit_post,  name='edit_post'),
    url(r'qqqqqqqqqqqq',views.qqqqqqqqqqqq,  name='qqqqqqqqqqqq'),
    url(r'account',views.myaccount,  name='myaccount'),
    url(r'edit_profile',views.edit_profile,  name='edit_profile'),
    url(r'to_chat',views.to_chat,  name='to_chat'),
    url(r'passwordreset',views.passwordreset,  name='passwordreset'),
    url(r'changepassword',views.changepassword,  name='changepassword'),
    url(r'notifications',views.notifications,  name='notifications'),
    url(r'sentnotis',views.sentnotis,  name='sentnotis'),
    url(r'delnoti',views.delete_noti,  name='delete_noti'),
    url(r'process_new_message',views.process_new_message,  name='process_new_message'),
    url(r'noti_search',views.notisearch,  name='notisearch'),
    url(r'fffff',views.fffff,  name='fffff'),
    url(r'delcontact',views.delete_contact,  name='delete_contact'),
    url(r'videotest',views.videotest,  name='videotest'),
    url(r'open_conference',views.open_conference,  name='open_conference'),
    url(r'new_notis',views.new_notis,  name='new_notis'),
    url(r'send_reply_message',views.send_reply_message,  name='send_reply_message'),
    url(r'conferences',views.conferences,  name='conferences'),
    url(r'noti_detail',views.noti_detail,  name='noti_detail'),

    url(r'notify_group_chat',views.notify_group_chat,  name='notify_group_chat'),
    url(r'pushsend',views.sendfcmpush,  name='sendfcmpush'),

    url(r'clearnotihistory',views.clearnotihistory,  name='clearnotihistory'),
]























































