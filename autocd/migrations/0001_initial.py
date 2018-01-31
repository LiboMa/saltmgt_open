# Generated by Django 2.0.1 on 2018-01-29 02:28

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AppEnv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='deploy_env',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('env', models.CharField(max_length=200, unique=True)),
                ('pillar', models.TextField()),
                ('state', models.TextField()),
                ('current_version', models.CharField(max_length=200)),
                ('status', models.CharField(blank=True, max_length=200)),
                ('comments', models.CharField(blank=True, max_length=200)),
                ('update_on', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='MGDeployEnv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pillar', models.TextField()),
                ('state', models.TextField()),
                ('current_version', models.CharField(blank=True, max_length=200)),
                ('status', models.CharField(blank=True, max_length=200)),
                ('comments', models.CharField(blank=True, max_length=200)),
                ('update_on', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='minion_groups',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='minions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minion_name', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(blank=True, max_length=200)),
                ('groups_name', models.ManyToManyField(to='autocd.minion_groups')),
            ],
        ),
        migrations.CreateModel(
            name='projects',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='tasks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deploy_url', models.CharField(max_length=200)),
                ('owner', models.CharField(max_length=200)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(blank=True, max_length=200)),
                ('result', models.TextField(blank=True)),
                ('env', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autocd.MGDeployEnv')),
            ],
        ),
        migrations.AddField(
            model_name='minion_groups',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autocd.projects'),
        ),
        migrations.AddField(
            model_name='mgdeployenv',
            name='deploy_env',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='autocd.minion_groups'),
        ),
        migrations.AddField(
            model_name='mgdeployenv',
            name='env_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autocd.AppEnv'),
        ),
        migrations.AddField(
            model_name='mgdeployenv',
            name='project_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autocd.projects'),
        ),
        migrations.AddField(
            model_name='deploy_env',
            name='minion_groups',
            field=models.ManyToManyField(to='autocd.minion_groups'),
        ),
        migrations.AddField(
            model_name='deploy_env',
            name='project_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autocd.projects'),
        ),
    ]
