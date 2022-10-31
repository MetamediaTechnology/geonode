#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from django.contrib.auth.decorators import login_required
from geonode.client.hooks import hookset
import json

from django import forms
from django.apps import apps
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.template.response import TemplateResponse
from geonode.base.templatetags.base_tags import facets
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, get_user_model

from geonode import get_version
from geonode.groups.models import GroupProfile
from geonode.geoapps.models import GeoApp

import json
import os
from django.db import connection
import sys
import psycopg2
import requests
from geonode.utils import OGC_Servers_Handler

class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()


def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
            content="ajax login requires HTTP POST",
            status=405,
            content_type="text/plain"
        )
    form = AjaxLoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                content_type="text/plain"
            )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                content="successful login",
                status=200,
                content_type="text/plain"
            )
    else:
        return HttpResponse(
            "The form you submitted doesn't look like a username/password combo.",
            content_type="text/plain",
            status=400)


def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            content_type='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            content_type='text/plain')
    keyword = request.POST['query']
    users = get_user_model().objects.filter(
        Q(username__icontains=keyword)).exclude(Q(username='AnonymousUser') |
                                                Q(is_active=False))
    if request.user and request.user.is_authenticated and request.user.is_superuser:
        groups = GroupProfile.objects.filter(
            Q(title__icontains=keyword) |
            Q(slug__icontains=keyword))
    elif request.user.is_anonymous:
        groups = GroupProfile.objects.filter(
            Q(title__icontains=keyword) |
            Q(slug__icontains=keyword)).exclude(Q(access='private'))
    else:
        groups = GroupProfile.objects.filter(
            Q(title__icontains=keyword) |
            Q(slug__icontains=keyword)).exclude(
                Q(access='private') & ~Q(
                    slug__in=request.user.groupmember_set.values_list("group__slug", flat=True))
        )
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }
    json_dict['groups'] = [({'name': g.slug, 'title': g.title})
                           for g in groups]
    return HttpResponse(
        content=json.dumps(json_dict),
        content_type='text/plain'
    )


def err403(request, exception):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(
            f"{reverse('account_login')}?next={request.get_full_path()}")
    else:
        return TemplateResponse(request, '401.html', {}, status=401).render()


def handler404(request, exception, template_name="404.html"):
    response = render(request, template_name)
    response.status_code = 404
    return response


def handler500(request, template_name="500.html"):
    response = render(request, template_name)
    response.status_code = 500
    return response


def ident_json(request):
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    json_data = {}
    json_data['siteurl'] = site_url
    json_data['name'] = settings.PYCSW['CONFIGURATION']['metadata:main']['identification_title']

    json_data['poc'] = {
        'name': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_name'],
        'email': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_email'],
        'twitter': f'https://twitter.com/{settings.TWITTER_SITE}'
    }

    json_data['version'] = get_version()

    json_data['services'] = {
        'csw': settings.CATALOGUE['default']['URL'],
        'ows': settings.OGC_SERVER['default']['PUBLIC_LOCATION']
    }

    json_data['counts'] = facets({'request': request, 'facet_type': 'home'})

    return HttpResponse(content=json.dumps(json_data),
                        content_type='application/json')


def h_keywords(request):
    from geonode.base.models import HierarchicalKeyword as hk
    p_type = request.GET.get('type', None)
    resource_name = request.GET.get('resource_name', None)
    keywords = hk.resource_keywords_tree(request.user, resource_type=p_type, resource_name=resource_name)

    subtypes = []
    if p_type == 'geoapp':
        for label, app in apps.app_configs.items():
            if hasattr(app, 'type') and app.type == 'GEONODE_APP':
                if hasattr(app, 'default_model'):
                    _model = apps.get_model(label, app.default_model)
                    if issubclass(_model, GeoApp):
                        subtypes.append(_model.__name__.lower())

    for _type in subtypes:
        _bulk_tree = hk.resource_keywords_tree(request.user, resource_type=_type, resource_name=resource_name)
        if isinstance(_bulk_tree, list):
            for _elem in _bulk_tree:
                keywords.append(_elem)
        else:
            keywords.append(_bulk_tree)

    return HttpResponse(content=json.dumps(keywords))


def moderator_contacted(request, inactive_user=None):
    """Used when a user signs up."""
    user = get_user_model().objects.get(id=inactive_user)
    return TemplateResponse(
        request,
        template="account/admin_approval_sent.html",
        context={"email": user.email}
    )


@login_required
def metadata_update_redirect(request):
    url = request.POST['url']
    client_redirect_url = hookset.metadata_update_redirect(url, request=request)
    return HttpResponse(content=client_redirect_url)


def get_uid(user_id=None,username=None,resource_id=None,resource_name=None,resource_type=None):
    cursor = connection.cursor()
    if user_id:
        query_string = f"""SELECT uid FROM socialaccount_socialaccount
                    WHERE user_id = {user_id};"""
    elif username:
        query_string = f"""SELECT uid FROM socialaccount_socialaccount social
                    LEFT JOIN people_profile people ON social.user_id = people.id
                    WHERE people.username = '{username}';"""
    elif resource_id:
        query_string = f"""SELECT uid FROM socialaccount_socialaccount social
                    LEFT JOIN base_resourcebase resource ON social.user_id = resource.owner_id
                    WHERE resource.id = {resource_id};"""
    elif resource_name and resource_type:
        query_string = f"""SELECT uid FROM socialaccount_socialaccount social
                    LEFT JOIN base_resourcebase resource ON social.user_id = resource.owner_id
                    WHERE resource.title = '{resource_name}' AND resource.resource_type = '{resource_type}';"""
    else:
        return None
    cursor.execute(query_string)
    result = cursor.fetchall()
    uid = result[0][0] if result else None
    return uid

def get_uid_prep(request):
    user_id_in = request.GET.get('user_id',None)
    user_id = int(user_id_in) if user_id_in else None
    username = request.GET.get('username',None)
    resource_id_in = request.GET.get('resource_id',None)
    resource_id = int(resource_id_in) if resource_id_in else None
    resource_name = request.GET.get('resource_name',None)
    resource_type = request.GET.get('resource_type',None)
    uid = get_uid(user_id=user_id,username=username,resource_id=resource_id,resource_name=resource_name,resource_type=resource_type)
    return HttpResponse(
        content = json.dumps({'uid': uid}),
        status = 200,
        content_type = "application/json"
    )

def getFolderSize(folder):
    total_size = 0
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

def get_resource_size(uid,show_resources=0):
    try:
        ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']
        db = ogc_server_settings.datastore_db
        db_name = os.environ['GEONODE_GEODATABASE']
        user = db['USER']
        password = db['PASSWORD']
        host = os.environ['DATABASE_HOST']
        port = os.environ['DATABASE_PORT']
        conn = None

        conn = psycopg2.connect(dbname=db_name, user=user, host=host, port=port, password=password)
        cur = conn.cursor()

        cursor = connection.cursor()
        cursor.execute(f"""SELECT people.id user_id, people.username, resource.id resource_id, resource.title resource_title, resource.resource_type, resource.alternate, upload.upload_dir, resource.blob, resource.files, resource.subtype
            FROM people_profile people
            LEFT JOIN base_resourcebase resource ON resource.owner_id = people.id
            LEFT JOIN upload_upload upload ON upload.resource_id = resource.id
            LEFT JOIN public.socialaccount_socialaccount social ON people.id = social.user_id
            WHERE resource.state = 'PROCESSED' AND social.uid = '{uid}';""")
        upload_result = cursor.fetchall()
        result_detail = []
        original_size = 0
        database_size = 0
        for row in range(len(upload_result)):
            if upload_result[row][4] == 'dataset':
                if upload_result[row][6]:
                    try:
                        dataset_original_size = round(getFolderSize(upload_result[row][6])/1048576.0,2)
                    except: # if can not find real path
                        dataset_original_size = 0
                else:
                    dataset_original_size = 0
                if dataset_original_size == 0:
                    # try to search upload file path in base_resourcebase.files
                    cursor = connection.cursor()
                    cursor.execute(f"""SELECT files FROM base_resourcebase
                        WHERE id = {upload_result[row][2]}""")
                    file_path = cursor.fetchall()
                    if file_path:
                        file_path_lst = json.loads(file_path[0][0])
                        path = os.path.dirname(file_path_lst[0])
                        try:
                            dataset_original_size = round(getFolderSize(path)/1048576.0,2)
                        except: # if can not find real path
                            dataset_original_size = 0
                file_extension = os.path.splitext(os.path.basename(json.loads(upload_result[row][8])[0]))[1]
                if upload_result[row][9] == 'vector': #and file_extension != '.gpkg':
                    geoserver_table = upload_result[row][5].split(':')[1]
                    cur.execute(f"SELECT pg_total_relation_size('\"{geoserver_table}\"')")
                    dataset_db_size = round(cur.fetchall()[0][0]/1048576.0,2)
                else:
                    dataset_db_size = 0
                dataset_url = os.environ['SITEURL'] + 'catalogue/#/dataset/' + str(upload_result[row][2])
                result_detail.append(
                    {
                    'name': upload_result[row][3],
                    'type': upload_result[row][4],
                    'size': {
                        'original_file': dataset_original_size,
                        'database': dataset_db_size,
                        'net': dataset_original_size + dataset_db_size
                    },
                    'url': dataset_url
                    }
                )
                original_size += dataset_original_size
                database_size += dataset_db_size
            elif upload_result[row][4] == 'document':
                path = json.loads(upload_result[row][8])
                document_original_size = round(os.path.getsize(path[0])/1048576.0,2)
                document_db_size = 0
                document_url = os.environ['SITEURL'] + 'catalogue/#/document/' + str(upload_result[row][2])
                result_detail.append(
                    {
                    'name': upload_result[row][3],
                    'type': upload_result[row][4],
                    'size': {
                        'original_file': document_original_size,
                        'database': document_db_size,
                        'net': document_original_size + document_db_size
                    },
                    'url': document_url
                    }
                )
                original_size += document_original_size
                database_size += document_db_size
            else:
                resource_original_size = round(sys.getsizeof(json.dumps(upload_result[row][7]))/1048576.0,2)
                resource_db_size = 0
                resource_url = os.environ['SITEURL'] + 'catalogue/#/' + upload_result[row][4] + '/' + str(upload_result[row][2])
                result_detail.append(
                    {
                    'name': upload_result[row][3],
                    'type': upload_result[row][4],
                    'size': {
                        'original_file': resource_original_size,
                        'database': resource_db_size,
                        'net': resource_original_size + resource_db_size
                    },
                    'url': resource_url
                    }
                )
                original_size += resource_original_size
                database_size += resource_db_size
    except Exception as e:
        return json.dumps({'error': str(e)})
    finally:
        if conn:
            conn.close()

    if len(upload_result) == 0:
        user_id = None
        username = None
    else:
        user_id = upload_result[0][0]
        username = upload_result[0][1]

    total_size = {
        'original_file': round(original_size,2),
        'database': round(database_size,2),
        'net': round(original_size + database_size,2)
    }

    if show_resources == 1:
        response_json = json.dumps({
            'id': user_id,
            'user': username,
            'total_size': total_size,
            'resources': result_detail
        })
    else:
        response_json = json.dumps({
            'id': user_id,
            'user': username,
            'total_size': total_size,
        })

    return response_json

def get_resource_size_prep(request):
    uid = request.GET.get('uid',None)
    show_resources = int(request.GET.get('show_resources',0))
    response_json = get_resource_size(uid,show_resources)

    return HttpResponse(
        content = response_json,
        status = 200,
        content_type = "application/json"
    )

def get_userStorage(uid):
    client = requests.session()
    response = client.get(
        url = settings.SPHERE_WEB_SERVICE_URL + "api/userStorage?keycloak_id=" + uid
    )
    response_dict = response.content
    resp_obj = json.loads(response_dict)
    return resp_obj['storageLimit']

def check_limit_size(uid,file_size=0,resource_type=None):
    resource_size_net = json.loads(get_resource_size(uid,1))['total_size']['net']
    if resource_type == 'dataset':
        total_size = resource_size_net + (file_size*4)
    else:
        total_size = resource_size_net + file_size
    size_limit = get_userStorage(uid)
    if total_size <= size_limit:
        return True
    else:
        return False

def check_limit_storage_prep(request):
    uid = request.GET.get('uid',None)
    file_size = float(request.GET.get('file_size',0))
    resource_type = request.GET.get('resource_type',None)
    response = check_limit_size(uid,file_size,resource_type)
    return HttpResponse(
        content = response,
        status = 200
    )

def update_userStorage(uid,storageUsage):
    client = requests.session()
    response = client.put(
        url = settings.SPHERE_WEB_SERVICE_URL + "api/userStorage",
        json = {
            'storageUsage': storageUsage,
            'keycloakId': uid
        }
    )
    if response.status_code == 200:
        return True
    else:
        return False

def get_mapkey(uid,projectName,type,ip,appId,applicationId):
    client = requests.session()
    clients = 'https://'+settings.SITE_HOST_NAME +'/catalogue/#/'+ type +'/'+appId
    try:
        response = client.post(
        url = settings.SPHERE_WEB_SERVICE_URL + "api/apiKey",
        json = {
              'keycloakId': uid,
              'projectName': projectName,
              'clients': clients,
              'allowIps': ip,
              'applicationId': applicationId
        }
    )
        response_json = json.loads(response.text)
        return response_json['key']
    except:
        return 