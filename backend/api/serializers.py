from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Conversation, Message, PublicDreamSubmission
from dj_rest_auth.registration.serializers import RegisterSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'picture', 'is_superuser']
        read_only_fields = ['id', 'is_superuser']

    def get_picture(self, obj):
        """Get profile picture from UserProfile if it exists"""
        try:
            return obj.profile.picture
        except:
            return None


class CustomRegisterSerializer(RegisterSerializer):
    """Custom registration serializer that doesn't require username"""
    username = None

    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
        }

    def save(self, request):
        from allauth.account.adapter import get_adapter
        from allauth.account.utils import setup_user_email

        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        user.email = self.cleaned_data.get('email')
        # Set username to email to satisfy Django's User model requirement
        user.username = self.cleaned_data.get('email')
        adapter.save_user(request, user, self)
        setup_user_email(request, user, [])
        user.save()
        return user


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing conversations"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'created_at': last_msg.created_at
            }
        return None


class PublicDreamSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for public dream submissions"""

    class Meta:
        model = PublicDreamSubmission
        fields = ['submission_id', 'dream_text', 'email', 'status', 'created_at']
        read_only_fields = ['submission_id', 'status', 'created_at']


class EmailCaptureSerializer(serializers.Serializer):
    """Serializer for capturing email with submission ID"""
    submission_id = serializers.UUIDField()
    email = serializers.EmailField()


class ConversationCalendarSerializer(serializers.ModelSerializer):
    """Lightweight serializer for calendar view with dream preview"""
    preview = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'preview', 'messages']
        read_only_fields = ['id', 'created_at']

    def get_preview(self, obj):
        """Get first user message as dream preview"""
        first_msg = obj.messages.filter(role='user').first()
        if first_msg:
            content = first_msg.content
            return content[:150] + '...' if len(content) > 150 else content
        return None

    def get_messages(self, obj):
        """Get all messages for the conversation"""
        return MessageSerializer(obj.messages.all(), many=True).data
