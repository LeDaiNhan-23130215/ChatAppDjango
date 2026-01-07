from django.db import models
from django.contrib.auth.models import AbstractUser

LEVEL_CHOICES = (
    ('Beginner', 'Beginner'),
    ('Elementary', 'Elementary'),
    ('Pre-intermediate', 'Pre-intermediate'),
    ('Intermediate', 'Intermediate'),
    ('Upper-intermediate', 'Upper-intermediate'),
    ('University', 'University'),
    ('Advanced', 'Advanced'),
)

GOAL_CHOICES = (
    ('study_abroad', 'Du học'),
    ('job', 'Công việc'),
    ('exam', 'Thi cử'),
    ('communication', 'Giao tiếp'),
)

EDUCATION_CHOICES = (
    ('1/12', '1/12'),
    ('2/12', '2/12'),
    ('3/12', '3/12'),
    ('4/12', '4/12'),
    ('5/12', '5/12'),
    ('6/12', '6/12'),
    ('7/12', '7/12'),
    ('8/12', '8/12'),
    ('9/12', '9/12'),
    ('10/12', '10/12'),
    ('11/12', '11/12'),
    ('12/12', '12/12'),
    ('college', 'Cao đẳng'),
    ('university', 'Đại học'),
    ('master', 'Thạc sĩ'),
)

PROFESSION_CHOICES = (
    ('student', 'Học sinh/Sinh viên'),
    ('teacher', 'Giáo viên'),
    ('engineer', 'Kỹ sư'),
    ('other', 'Khác'),
)

FREQUENCY_CHOICES = (
    ('daily', 'Hàng ngày'),
    ('weekly', 'Hàng tuần'),
    ('monthly', 'Hàng tháng'),
)

HOBBY_CHOICES = (
    ('reading', 'Đọc sách'),
    ('movies', 'Xem phim'),
    ('music', 'Nghe nhạc'),
    ('sports', 'Thể thao'),
    ('travel', 'Du lịch'),
    ('cooking', 'Nấu ăn'),
    ('gaming', 'Chơi game'),
    ('art', 'Vẽ/Thủ công mỹ nghệ'),
    ('photography', 'Nhiếp ảnh'),
    ('gardening', 'Làm vườn'),
    ('fitness', 'Tập gym/Yoga'),
    ('walking', 'Đi bộ/Chạy bộ'),
    ('writing', 'Viết lách'),
    ('collecting', 'Sưu tầm'),
)

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)

    birth_day = models.DateField(null=True, blank=True)
    declared_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    goals = models.CharField(max_length=50, choices=GOAL_CHOICES, null=True, blank=True)
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES, null=True, blank=True)
    profession = models.CharField(max_length=50, choices=PROFESSION_CHOICES, null=True, blank=True)
    referred_frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES, null=True, blank=True)
    motivation_level = models.PositiveSmallIntegerField(null=True, blank=True)
    hobby = models.CharField(max_length=50, choices=HOBBY_CHOICES, null=True, blank=True)

    def is_profile_completed(self):
        required_fields = [
            self.declared_level,
            self.goals,
            self.motivation_level
        ]
        return all(required_fields)