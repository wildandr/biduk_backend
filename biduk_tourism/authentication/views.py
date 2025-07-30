from django.shortcuts import render
from rest_framework import status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model, logout
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, inline_serializer

from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer

User = get_user_model()

class RegisterView(APIView):
    """
    View untuk registrasi pengguna baru.
    Endpoint: /api/auth/register
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=inline_serializer(
                    name='RegisterResponse',
                    fields={
                        'user_id': serializers.IntegerField(),
                        'username': serializers.CharField(),
                        'email': serializers.EmailField(),
                        'full_name': serializers.CharField(),
                        'phone_number': serializers.CharField(),
                        'token': serializers.CharField(),
                        'created_at': serializers.DateTimeField(),
                    }
                ),
                description='Pengguna berhasil dibuat dan token autentikasi dikembalikan'
            ),
            400: OpenApiResponse(
                description='Validasi gagal'
            )
        },
        description='Mendaftarkan pengguna baru dan mengembalikan token autentikasi'
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            response_data = serializer.data
            response_data['user_id'] = user.id
            response_data['token'] = token.key
            response_data['created_at'] = user.date_joined
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response({
            'error': 'validation_error',
            'detail': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(ObtainAuthToken):
    """
    View untuk login pengguna.
    Endpoint: /api/auth/login
    """
    @extend_schema(
        request=inline_serializer(
            name='LoginRequest',
            fields={
                'username': serializers.CharField(required=True),
                'password': serializers.CharField(required=True, style={'input_type': 'password'})
            }
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='LoginResponse',
                    fields={
                        'user_id': serializers.IntegerField(),
                        'username': serializers.CharField(),
                        'email': serializers.EmailField(),
                        'full_name': serializers.CharField(),
                        'token': serializers.CharField(),
                        'last_login': serializers.DateTimeField()
                    }
                ),
                description='Login berhasil, token autentikasi dikembalikan'
            ),
            401: OpenApiResponse(
                description='Kredensial tidak valid'
            )
        },
        description='Melakukan autentikasi pengguna dan mengembalikan token akses'
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'token': token.key,
                'last_login': user.last_login
            })
        return Response({
            'error': 'authentication_failed',
            'detail': 'Unable to log in with provided credentials.'
        }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """
    View untuk logout pengguna.
    Endpoint: /api/auth/logout
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='LogoutResponse',
                    fields={
                        'message': serializers.CharField()
                    }
                ),
                description='Logout berhasil dilakukan'
            ),
            401: OpenApiResponse(
                description='Token autentikasi tidak valid'
            )
        },
        description='Mengeluarkan pengguna dari sistem dan menghapus token autentikasi',
        auth=["Bearer"]
    )
    def post(self, request):
        try:
            # Hapus token untuk logout
            request.user.auth_token.delete()
            logout(request)
            return Response({'message': 'Successfully logged out.'})
        except Exception as e:
            return Response({
                'error': 'authentication_failed',
                'detail': 'Invalid token.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class UserDetailView(APIView):
    """
    View untuk mendapatkan dan mengupdate detail pengguna.
    Endpoint: /api/auth/user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description='Tidak terautentikasi')
        },
        description='Mengambil data pengguna yang sedang login',
        auth=["Bearer"]
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Data tidak valid'),
            401: OpenApiResponse(description='Tidak terautentikasi')
        },
        description='Memperbarui data pengguna yang sedang login',
        auth=["Bearer"]
    )
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'validation_error',
            'detail': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    """
    View untuk mengubah password pengguna.
    Endpoint: /api/auth/password/change
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='ChangePasswordResponse',
                    fields={
                        'message': serializers.CharField()
                    }
                ),
                description='Password berhasil diubah'
            ),
            400: OpenApiResponse(description='Validasi gagal'),
            401: OpenApiResponse(description='Tidak terautentikasi')
        },
        description='Mengubah password pengguna yang sedang login',
        auth=["Bearer"]
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password successfully changed.'})
        return Response({
            'error': 'validation_error',
            'detail': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class RequestPasswordResetView(APIView):
    """
    View untuk meminta reset password.
    Endpoint: /api/auth/password/reset
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=inline_serializer(
            name='RequestPasswordResetRequest',
            fields={
                'email': serializers.EmailField(required=True)
            }
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='RequestPasswordResetResponse',
                    fields={
                        'message': serializers.CharField()
                    }
                ),
                description='Email untuk reset password telah dikirim'
            ),
            400: OpenApiResponse(description='Validasi gagal')
        },
        description='Meminta reset password melalui email'
    )
    def post(self, request):
        email = request.data.get('email', None)
        if not email:
            return Response({
                'error': 'validation_error',
                'detail': {'email': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
            # Di sini idealnya kirim email dengan token reset password
            # Tapi untuk sementara kita hanya simulasikan
            return Response({'message': 'Password reset e-mail has been sent.'})
        except User.DoesNotExist:
            return Response({
                'error': 'validation_error',
                'detail': {'email': ['User with this email does not exist.']}
            }, status=status.HTTP_400_BAD_REQUEST)

class ConfirmPasswordResetView(APIView):
    """
    View untuk konfirmasi reset password.
    Endpoint: /api/auth/password/reset/confirm
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=inline_serializer(
            name='ConfirmPasswordResetRequest',
            fields={
                'token': serializers.CharField(required=True),
                'new_password': serializers.CharField(required=True, style={'input_type': 'password'})
            }
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='ConfirmPasswordResetResponse',
                    fields={
                        'message': serializers.CharField()
                    }
                ),
                description='Password berhasil direset'
            ),
            400: OpenApiResponse(description='Validasi gagal atau token tidak valid')
        },
        description='Konfirmasi reset password dengan token dan password baru'
    )
    def post(self, request):
        token = request.data.get('token', None)
        new_password = request.data.get('new_password', None)
        
        if not token or not new_password:
            return Response({
                'error': 'validation_error',
                'detail': {
                    'token': ['This field is required.'] if not token else [],
                    'new_password': ['This field is required.'] if not new_password else [],
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Di implementasi sebenarnya, Anda perlu memverifikasi token dan mengubah password
        # Tapi untuk sementara kita hanya simulasikan
        
        # Simulasi invalid token
        if token != '6b4d7a8e-5f2c-42d1-9e8b-7a3b5f2c1d9e':
            return Response({
                'error': 'validation_error',
                'detail': {'token': ['Invalid or expired token.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulasi validasi password
        if len(new_password) < 8:
            return Response({
                'error': 'validation_error',
                'detail': {'new_password': ['Password must be at least 8 characters long.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'Password has been reset successfully.'})
