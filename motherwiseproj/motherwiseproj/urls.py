from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from motherwise import views, tests

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r'^motherwise/', include('motherwise.urls')),
    url(r'^mothers/', include('mothers.urls')),
    url(r'^umobile/', include('usermobile.urls')),
    url(r'^$', views.index, name='index'),
    url(r'^nest/mothers', views.index, name='index'),
    url(r'^nest/manager',views.admin,  name='admin'),
    url(r'^admin',views.admin,  name='admin'),
    url(r'^manager/home',views.adminhome,  name='adminhome'),
    url(r'^manager/torequestpwd',views.torequestpwd,  name='torequestpwd'),
    url(r'^manager/logout',views.adminlogout,  name='adminlogout'),
    url(r'^manager/signuppage',views.adminsignuppage,  name='adminsignuppage'),
    url(r'^manager/loginpage',views.adminloginpage,  name='adminloginpage'),
    url(r'^manager/signup',views.adminSignup,  name='adminSignup'),
    url(r'^manager/login',views.adminLogin,  name='adminLogin'),
    url(r'^manager/export_xlsx_member/$', views.export_xlsx_member, name='export_xlsx_member'),
    url(r'^manager/import_view/member/$', views.import_view_member, name='import_view_member'),
    url(r'^manager/import_member/$', views.import_member_data, name='import_member_data'),
    url(r'^manager/add_member/$', views.add_member, name='add_member'),
    url(r'^manager/reinv/$', views.reinvite_member, name='reinvite_member'),
    url(r'^manager/delete_member/$', views.delete_member, name='delete_member'),
    url(r'^manager/active_members/$', views.active_members, name='active_members'),
    url(r'^manager/inactive_members/$', views.inactive_members, name='inactive_members'),
    url(r'^manager/message_to_selected_members/$', views.message_to_selected_members, name='message_to_selected_members'),
    url(r'^to_page',views.to_page,  name='to_page'),
    url(r'^to_previous',views.to_previous,  name='to_previous'),
    url(r'^to_next',views.to_next,  name='to_next'),
    url(r'^manager/do_cohort',views.do_cohort,  name='do_cohort'),
    url(r'^manager/search_members',views.search_members,  name='search_members'),
    url(r'^manager/account',views.admin_account,  name='admin_account'),
    url(r'^manager/edit_account',views.edit_admin_account,  name='edit_admin_account'),
    url(r'^manager/send_cohort_message',views.send_cohort_message,  name='send_cohort_message'),
    url(r'^manager/switch_chat',views.admin_switch_chat,  name='admin_switch_chat'),
    url(r'^manager/to_chat',views.admin_to_chat,  name='admin_to_chat'),
    url(r'^manager/switch_to_cohort',views.admin_switch_to_cohort,  name='admin_switch_to_cohort'),
    url(r'^manager/create_group',views.create_group,  name='create_group'),
    url(r'^manager/message_to_group',views.message_to_group,  name='message_to_group'),
    url(r'^manager/switch_group',views.switch_group,  name='switch_group'),
    url(r'^manager/groups',views.get_groups,  name='get_groups'),
    url(r'^manager/delugroup',views.delete_group_member,  name='delete_group_member'),
    url(r'^manager/open_group_chat',views.open_group_chat,  name='open_group_chat'),
    url(r'^manager/group_cohort_chat',views.group_cohort_chat,  name='group_cohort_chat'),
    url(r'^manager/group_chat_message',views.group_chat_message,  name='group_chat_message'),
    url(r'^manager/group_private_chat',views.group_private_chat,  name='group_private_chat'),
    url(r'^manager/delcontact',views.admin_delete_contact,  name='admin_delete_contact'),
    url(r'^manager/delgroup',views.admin_delete_group,  name='admin_delete_group'),
    url(r'^manager/posts',views.to_posts,  name='to_posts'),
    url(r'^manager/memberposts',views.member_posts,  name='memberposts'),
    url(r'^manager/mineppppp',views.my_posts,  name='my_posts'),
    url(r'^manager/create_post',views.create_post,  name='create_post'),
    url(r'^manager/add_post_comment',views.add_post_comment,  name='add_post_comment'),
    url(r'^manager/search_post',views.search_post,  name='search_post'),
    url(r'^manager/filter',views.filter,  name='filter'),
    url(r'^manager/like_post',views.like_post,  name='like_post'),
    url(r'^manager/submit_comment',views.submit_comment,  name='submit_comment'),
    url(r'^manager/delpost',views.delete_post,  name='delete_post'),
    url(r'^manager/delcomment',views.delete_comment,  name='delete_comment'),
    url(r'^manager/postdelpicture',views.delete_post_picture,  name='delete_post_picture'),
    url(r'^manager/edit_post',views.edit_post,  name='edit_post'),
    url(r'^manager/send_mail_forgotpassword',views.send_mail_forgotpassword,  name='send_mail_forgotpassword'),
    url(r'^resetpassword', views.resetpassword, name='resetpassword'),
    url(r'^manager/rstpwd',views.admin_rstpwd,  name='admin_rstpwd'),
    url(r'^manager/notifications',views.notifications,  name='notifications'),
    url(r'^manager/sentnotis',views.sentnotis,  name='sentnotis'),
    url(r'^manager/delnoti',views.delete_noti,  name='delete_noti'),
    url(r'^manager/processnewmessage',views.processnewmessage,  name='processnewmessage'),
    url(r'^manager/noti_search',views.notisearch,  name='notisearch'),
    url(r'^manager/fffff',views.fffff,  name='fffff'),
    url(r'^manager/videotest',views.videotest,  name='videotest'),
    url(r'^manager/open_conference',views.open_conference,  name='open_conference'),
    url(r'^manager/create_conference',views.create_conference,  name='create_conference'),
    url(r'^manager/delconf',views.delete_conference,  name='delete_conference'),
    url(r'^manager/conference_notify',views.conference_notify,  name='conference_notify'),
    url(r'^manager/video_selected_members',views.video_selected_members,  name='video_selected_members'),
    url(r'^manager/new_notis',views.new_notis,  name='new_notis'),
    url(r'^manager/send_reply_message',views.send_reply_message,  name='send_reply_message'),
    url(r'^manager/send_member_message',views.send_member_message,  name='send_member_message'),
    url(r'^manager/toplevelsetup',views.toplevelsetup,  name='toplevelsetup'),

    url(r'^manager/to_conferences',views.to_conferences,  name='to_conferences'),
    url(r'^manager/noti_detail',views.noti_detail,  name='noti_detail'),
    url(r'^manager/openbroadcast',views.openbroadcast,  name='openbroadcast'),
    url(r'^manager/broadcast', views.broadcast, name='broadcast'),
    url(r'^manager/bexcludedemailsave', views.bexcludedemailsave, name='bexcludedemailsave'),

    url(r'^manager/notify_group_chat',views.notify_group_chat,  name='notify_group_chat'),
    url(r'^verifypwreport',views.verifypwreport,  name='verifypwreport'),

    url(r'^reports',views.reports,  name='reports'),
    url(r'^delreport',views.delreport,  name='delreport'),
    url(r'^warning_message',views.warning_message,  name='warning_message'),

    url(r'manager/tonewpost',views.tonewpost,  name='tonewpost'),
    url(r'manager/newpost',views.newpost,  name='newpost'),
    url(r'manager/analytics',views.analytics,  name='analytics'),

    url(r'pushsend',views.sendfcmpush,  name='sendfcmpush'),

    url(r'^translate',views.open_translate,  name='open_translate'),
    url(r'^process_translate',views.process_translate,  name='process_translate'),
    url(r'^testtranslate',views.testtranslate,  name='testtranslate'),

    # url(r'^manager/sms_send',views.sms_test,  name='sms_test'),

    url(r'^smtp_test',views.smtp_test,  name='smtp_test'),

    url(r'^assignUrlPreviewToPosts',tests.assignUrlPreviewToPosts,  name='assignUrlPreviewToPosts'),

    url(r'^always_on', views.always_on,  name='always_on'),

]


urlpatterns+=static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns=format_suffix_patterns(urlpatterns)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)









































