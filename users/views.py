from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
from .models import User, OTPStorage
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import SignUpForm   #, ProfileUpdateForm
import random
from django.http import HttpResponseForbidden


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_email_verified = False
            user.save()
            
            # Generate and save OTP
            otp = str(random.randint(100000, 999999))
            OTPStorage.objects.create(user=user, otp=otp)  # This line was missing!
            
            # Send OTP via email
            send_mail(
                'Verify Your Email',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            request.session['otp_user_id'] = user.id
            return redirect('users:verify_otp')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        user_id = request.session.get('otp_user_id')
        
        if not user_id:
            messages.error(request, "Session expired. Please register again.")
            return redirect('users:signup')
            
        try:
            user = User.objects.get(id=user_id)
            try:
                stored_otp = OTPStorage.objects.filter(user=user).latest('created_at')
                
                # Check expiration (10 minutes)
                if stored_otp.created_at < timezone.now() - timedelta(minutes=10):
                    messages.error(request, "OTP expired. Please request a new one.")
                    return redirect('users:signup')
                    
                if stored_otp.otp == otp_entered:
                    user.is_email_verified = True
                    user.save()
                    login(request, user)
                    del request.session['otp_user_id']  # Clear session
                    return redirect('events:home')
                else:
                    messages.error(request, "Invalid OTP")
            except OTPStorage.DoesNotExist:
                messages.error(request, "No OTP found. Please register again.")
                return redirect('users:signup')
                
        except User.DoesNotExist:
            messages.error(request, "User not found. Please register again.")
            return redirect('users:signup')
    
    return render(request, 'users/verify_otp.html')



@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        return HttpResponseForbidden()
    users = User.objects.all()
    return render(request, 'users/admin_dashboard.html', {'users': users})



