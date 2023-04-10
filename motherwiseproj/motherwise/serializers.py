from rest_framework import serializers
from .models import Member, Group, Post, PostPicture, Comment, Notification, Conference, PostUrlPreview, Recipe, FoodResource

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

class PostPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostPicture
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class ConferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conference
        fields = '__all__'


class PostUrlPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostUrlPreview
        fields = ('__all__')


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('__all__')


class FoodResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodResource
        fields = ('__all__')































