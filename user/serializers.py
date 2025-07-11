# user/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserSignupSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password2', 'phone']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        # 비밀번호 확인
        if data['password'] != data['password2']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        # 이메일 중복 확인
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            phone=validated_data['phone'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
