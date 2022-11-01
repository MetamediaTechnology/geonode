#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import json
from urllib.parse import parse_qsl, urlparse
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from django.shortcuts import reverse
from django.utils.translation import ugettext as _
from django.conf import settings

from geonode.base.api.filters import DynamicSearchFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly, IsSelfOrAdminOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.upload.utils import get_max_amount_of_steps
from geonode.layers.utils import is_vector

from .serializers import (
    UploadSerializer,
    UploadParallelismLimitSerializer,
    UploadSizeLimitSerializer,
)
from .permissions import UploadPermissionsFilter

from ..models import Upload, UploadParallelismLimit, UploadSizeLimit
from ..views import view as upload_view

from geonode.views import (
    get_resource_size,
    get_uid,
    check_limit_size,
    update_userStorage
)
from django.http import HttpResponse
import zipfile

import logging

logger = logging.getLogger(__name__)


class UploadViewSet(DynamicModelViewSet):
    """
    API endpoint that allows uploads to be viewed or edited.
    """
    parser_class = [FileUploadParser, ]

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        UploadPermissionsFilter
    ]
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    pagination_class = GeoNodeApiPagination
    http_method_names = ['get', 'post']

    def _emulate_client_upload_step(self, request, _step):
        """Emulates the calls of a client to the upload flow.
        It alters the content of the request object, so the same request should
        be reused in the next call of this method.

        Args:
            request (Request): A request object with the query params given by the lasted step call.
                               No params for the first call.
            _step (string): The current step, used as an argument in the upload_view call.
                            None for the first call.

        Returns:
            Response: response, upload_view response or a final response.
            string: next_step, the next step to be performed.
            boolean: is_final, True when the last step is executed or in case of errors.
        """
        response = upload_view(request, _step)
        if response.status_code == status.HTTP_200_OK:
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            try:
                data = json.loads(content)
            except json.decoder.JSONDecodeError:
                data = content

            next_step = None
            if isinstance(data, dict):
                response_status = data.get('status', '')
                response_success = data.get('success', False)
                redirect_to = data.get('redirect_to', '')
                if not response_success or not redirect_to or response_status == 'finished':
                    return response, None, True

                # Prepare next step
                parsed_redirect_to = urlparse(redirect_to)
                if reverse("data_upload") not in parsed_redirect_to.path:
                    # Error, next step cannot be performed by `upload_view`
                    return response, None, True
                next_step = parsed_redirect_to.path.split(reverse("data_upload"))[1]
                query_params = parse_qsl(parsed_redirect_to.query)
                request.method = 'GET'
                request.GET.clear()
                for key, value in query_params:
                    request.GET[key] = value
            if next_step:
                return response, next_step, False
        elif response.status_code == status.HTTP_302_FOUND:
            # Get next step, should be final
            parsed_redirect_to = urlparse(response.url)
            if reverse("data_upload") not in parsed_redirect_to.path:
                # Error, next step cannot be performed by `upload_view`
                return response, None, True
            next_step = parsed_redirect_to.path.split(reverse("data_upload"))[1]
            return response, next_step, False
        # Error, next step cannot be performed by `upload_view`
        return response, None, True

    @extend_schema(methods=['post'],
                   responses={201: None},
                   description="""
        Starts an upload session based on the Dataset Upload Form.

        the form params look like:
        ```
            'csrfmiddlewaretoken': self.csrf_token,
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'time': 'false',
            'charset': 'UTF-8',
            'base_file': base_file,
            'dbf_file': dbf_file,
            'shx_file': shx_file,
            'prj_file': prj_file,
            'tif_file': tif_file
        ```
        """)
    @action(detail=False, methods=['post'])
    def upload(self, request, format=None):
        user = request.user
        if not user or not user.is_authenticated:
            raise AuthenticationFailed()

        # Check file size
        if not user.is_staff and settings.ENABLE_CHECK_USER_STORAGE:
            username = user.get_username()
            uid = get_uid(username=username)
            file_name = request.FILES.get('base_file')
            file_size = 0
            if zipfile.is_zipfile(file_name):
                zp = zipfile.ZipFile(file_name)
                size = sum([zinfo.file_size for zinfo in zp.filelist])
                file_size = float(size)/1048576
            else:
                for filename, file in request.FILES.items():
                    if filename != 'shp_file':
                        file_size += request.FILES[filename].size/1048576.0
            # check limit size
            is_able_upload = check_limit_size(uid,file_size,'dataset')
            if not is_able_upload:
                #raise ValidationError("Storage usage exceed limit.")
                return HttpResponse(
                    content = json.dumps({'error':'Storage usage exceed limit.'}),
                    status = 400,
                    content_type = "application/json"
                )

        # Custom upload steps defined by user
        non_interactive = json.loads(
            request.data.get("non_interactive", "false").lower()
        )
        if non_interactive:
            is_vector_dataset = is_vector(request.FILES.get('base_file').name)
            steps_list = (None, "check", "final") if is_vector_dataset else (None, "final")
            # Execute steps and get response
            for step in steps_list:
                response, _, _ = self._emulate_client_upload_step(
                    request,
                    step
                )
            if not user.is_staff and settings.ENABLE_CHECK_USER_STORAGE:
                size_after_upload = json.loads(get_resource_size(uid, 1))['total_size']['net']
                update_userStorage(uid, size_after_upload)
            return response

        # Upload steps defined by geonode.upload.utils._pages
        next_step = None
        max_steps = get_max_amount_of_steps()
        for n in range(max_steps):
            response, next_step, is_final = self._emulate_client_upload_step(
                request,
                next_step
            )
            if is_final:
                if not user.is_staff and settings.ENABLE_CHECK_USER_STORAGE:
                    size_after_upload = json.loads(get_resource_size(uid, 1))['total_size']['net']
                    update_userStorage(uid, size_after_upload)
                return response
        # After performing 7 steps if we don't get any final response
        return response


class UploadSizeLimitViewSet(DynamicModelViewSet):
    http_method_names = ['get', 'post']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadSizeLimit.objects.all()
    serializer_class = UploadSizeLimitSerializer
    pagination_class = GeoNodeApiPagination

    def destroy(self, request, *args, **kwargs):
        protected_objects = [
            'dataset_upload_size',
            'document_upload_size',
            'file_upload_handler',
        ]
        instance = self.get_object()
        if instance.slug in protected_objects:
            detail = _(f"The limit `{instance.slug}` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadParallelismLimitViewSet(DynamicModelViewSet):
    http_method_names = ['get', 'post']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadParallelismLimit.objects.all()
    serializer_class = UploadParallelismLimitSerializer
    pagination_class = GeoNodeApiPagination

    def get_serializer(self, *args, **kwargs):
        serializer = super(UploadParallelismLimitViewSet, self).get_serializer(*args, **kwargs)
        if self.action == "create":
            serializer.fields["slug"].read_only = False
        return serializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.slug == "default_max_parallel_uploads":
            detail = _("The limit `default_max_parallel_uploads` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
