from django.shortcuts import render, redirect, get_object_or_404
from .models import Room

def home(request):
    return render(request, "quiz/home.html")

def create_room(request):
    code = Room.generate_code()
    Room.objects.create(code=code)
    return redirect("quiz_room", code=code)

def room(request, code):
    room = get_object_or_404(Room, code=code)
    return render(request, "quiz/room.html", {"code": room.code})
