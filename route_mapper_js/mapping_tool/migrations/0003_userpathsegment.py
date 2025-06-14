# Generated by Django 5.2.2 on 2025-06-10 21:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapping_tool', '0002_board_waystone'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPathSegment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_row', models.PositiveIntegerField()),
                ('start_col', models.PositiveIntegerField()),
                ('end_row', models.PositiveIntegerField()),
                ('end_col', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_path_segments', to='mapping_tool.board')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drawn_path_segments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['board', 'user'], name='mapping_too_board_i_4cf796_idx')],
            },
        ),
    ]
