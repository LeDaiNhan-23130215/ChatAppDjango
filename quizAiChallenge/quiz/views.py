from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Room
import random
import string

@login_required
def quiz_room(request, code):
    """
    View cho quiz room - yêu cầu đăng nhập
    """
    room = get_object_or_404(Room, code=code)
    
    # Kiểm tra profile đã hoàn thành chưa (optional)
    if hasattr(request.user, 'is_profile_completed'):
        if not request.user.is_profile_completed():
            messages.warning(request, 'Vui lòng hoàn thiện hồ sơ trước khi chơi.')
            return redirect('complete-profile')  # Redirect đến trang hoàn thiện profile
    
    context = {
        'room': room,
        'user': request.user,
    }
    return render(request, 'quiz/room.html', context)


@login_required
def create_room(request):
    """
    Tạo phòng mới
    """
    if request.method == 'POST':
        # Tạo room code ngẫu nhiên
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Đảm bảo code unique
        while Room.objects.filter(code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        room = Room.objects.create(
            code=code,
            created_by=request.user,  # Nếu Room model có field này
            player_count=0,
            started=False
        )
        
        messages.success(request, f'Đã tạo phòng {code}')
        return redirect('quiz:quiz_room', code=code)
    
    return render(request, 'quiz/create_room.html')


@login_required
def join_room(request):
    """
    Join phòng bằng code
    """
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        
        try:
            room = Room.objects.get(code=code)
            
            # Kiểm tra phòng đã đầy chưa
            if room.player_count >= 2:
                messages.error(request, 'Phòng đã đầy!')
                return redirect('quiz:join_room')
            
            # Kiểm tra phòng đã bắt đầu chưa
            if room.started:
                messages.error(request, 'Trận đấu đã bắt đầu!')
                return redirect('quiz:join_room')
            
            return redirect('quiz:quiz_room', code=code)
            
        except Room.DoesNotExist:
            messages.error(request, 'Không tìm thấy phòng!')
            return redirect('quiz:join_room')
    
    return render(request, 'quiz/join_room.html')


def lobby(request):
    """
    Trang chủ - hiển thị các phòng đang chờ
    """
    available_rooms = Room.objects.filter(
        started=False,
        player_count__lt=2
    ).order_by('-id')[:10]
    
    context = {
        'rooms': available_rooms,
        'is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'quiz/home.html', context)