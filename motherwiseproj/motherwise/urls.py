from django.conf.urls import url
from . import views, v0

app_name='motherwise'

urlpatterns=[

    url(r'post_categories', v0.post_categories, name='post_categories'),
    url(r'savepostcategories', v0.savepostcategories, name='savepostcategories'),
    url(r'cohort_names', v0.cohort_names, name='cohort_names'),
    url(r'savecohortnames', v0.savecohortnames, name='savecohortnames'),
    url(r'membercohortchange',v0.membercohortchange,  name='membercohortchange'),
    url(r'react_post',v0.react_post,  name='react_post'),
    url(r'react_comment',v0.react_comment,  name='react_comment'),
    url(r'subcomments',v0.comment_comment_list,  name='subcomments'),
    url(r'commentdelete',v0.comment_delete,  name='commentdelete'),
    url(r'recipes',v0.comida_recipe,  name='recipes'),
    url(r'saverecipeee',v0.save_recipe,  name='saverecipeee'),
    url(r'delrecipeee',v0.delete_recipe,  name='delrecipeee'),
    url(r'comidaposts',v0.comida_posts,  name='comidaposts'),
    url(r'foodresources',v0.food_resources,  name='foodresources'),
    url(r'FRupload',v0.saveFR,  name='FRupload'),
    url(r'FRdelete',v0.deleteFR,  name='FRdelete'),
    url(r'restoplevelsetup',v0.restoplevelsetup,  name='restoplevelsetup'),




]