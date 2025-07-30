from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer untuk proses registrasi pengguna baru
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'full_name', 'phone_number')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'full_name': {'required': True},
        }
    
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone_number=validated_data.get('phone_number', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer untuk menampilkan dan mengedit data pengguna
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'phone_number', 
                  'is_admin', 'date_joined', 'last_login')
        read_only_fields = ('id', 'username', 'is_admin', 'date_joined', 'last_login')

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer untuk perubahan password
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")
        return value
