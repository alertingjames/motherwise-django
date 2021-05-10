from django.db import models

class Member(models.Model):
    admin_id = models.CharField(max_length=11)
    name = models.CharField(max_length=50)
    email=models.CharField(max_length=80)
    password = models.CharField(max_length=30)
    fb_photo = models.CharField(max_length=1000)
    gl_photo = models.CharField(max_length=1000)
    photo_url = models.CharField(max_length=1000)
    phone_number = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    lat = models.CharField(max_length=50)
    lng = models.CharField(max_length=50)
    cohort = models.CharField(max_length=100)
    registered_time = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    status2 = models.CharField(max_length=50)
    playerID = models.CharField(max_length=300)
    username = models.CharField(max_length=100)
    fcm_token = models.CharField(max_length=500)



class Contact(models.Model):
    member_id = models.CharField(max_length=11)
    contact_email = models.CharField(max_length=80)
    contacted_time = models.CharField(max_length=50)


class Group(models.Model):
    member_id = models.CharField(max_length=11)
    name = models.CharField(max_length=100)
    member_count = models.CharField(max_length=11)
    code = models.CharField(max_length=20)
    color = models.CharField(max_length=20)
    created_time = models.CharField(max_length=50)
    last_connected_time = models.CharField(max_length=50)
    status = models.CharField(max_length=20)


class GroupMember(models.Model):
    group_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    invited_time = models.CharField(max_length=50)
    last_connected_time = models.CharField(max_length=50)

class GroupConnect(models.Model):
    member_id = models.CharField(max_length=11)
    group_id = models.CharField(max_length=11)
    last_connected_time = models.CharField(max_length=50)


class Cohort(models.Model):
    member_id = models.CharField(max_length=11)
    cohort = models.CharField(max_length=20)
    registered_time = models.CharField(max_length=50)


class Post(models.Model):
    member_id = models.CharField(max_length=11)
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    content = models.CharField(max_length=5000)
    picture_url = models.CharField(max_length=1000)
    video_url = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000)
    comments = models.CharField(max_length=11)
    posted_time = models.CharField(max_length=100)
    likes = models.CharField(max_length=11)
    liked = models.CharField(max_length=20)
    status = models.CharField(max_length=20)


class PostPicture(models.Model):
    post_id = models.CharField(max_length=11)
    picture_url = models.CharField(max_length=1000)


class Comment(models.Model):
    post_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    comment_text = models.CharField(max_length=2000)
    image_url = models.CharField(max_length=1000)
    commented_time = models.CharField(max_length=100)
    status = models.CharField(max_length=20)


class PostLike(models.Model):
    post_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    liked_time = models.CharField(max_length=50)


class Notification(models.Model):
    member_id = models.CharField(max_length=11)
    sender_id = models.CharField(max_length=11)
    message = models.CharField(max_length=5000)
    notified_time = models.CharField(max_length=50)
    status = models.CharField(max_length=20)

class Received(models.Model):
    member_id = models.CharField(max_length=11)
    sender_id = models.CharField(max_length=11)
    noti_id = models.CharField(max_length=11)

class Sent(models.Model):
    member_id = models.CharField(max_length=11)
    sender_id = models.CharField(max_length=11)
    noti_id = models.CharField(max_length=11)

class Replied(models.Model):
    root_id = models.CharField(max_length=11)
    noti_id = models.CharField(max_length=11)


class Conference(models.Model):
    member_id = models.CharField(max_length=11)
    group_id = models.CharField(max_length=11)
    cohort = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    type = models.CharField(max_length=20)
    video_url = models.CharField(max_length=1000)
    participants = models.CharField(max_length=11)
    event_time = models.CharField(max_length=50)
    created_time = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    likes = models.CharField(max_length=11)
    status = models.CharField(max_length=20)
    gname = models.CharField(max_length=100)


class Report(models.Model):
    member_id = models.CharField(max_length=11)
    reporter_id = models.CharField(max_length=11)
    message = models.CharField(max_length=2000)
    reported_time = models.CharField(max_length=50)
    status = models.CharField(max_length=20)







































































