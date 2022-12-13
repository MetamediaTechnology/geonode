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
import logging
from urllib import request
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import extend_schema
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import DynamicModelViewSet
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from geonode.base import register_event
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.layers.api.serializers import DatasetSerializer
from geonode.maps.api.exception import GeneralMapsException
from geonode.maps.api.permissions import MapPermissionsFilter
from geonode.maps.api.serializers import MapLayerSerializer, MapSerializer
from geonode.maps.contants import _PERMISSION_MSG_SAVE
from geonode.maps.models import Map
from geonode.maps.signals import map_changed_signal
from geonode.monitoring.models import EventType
from geonode.resource.manager import resource_manager
from geonode.utils import resolve_object

from geonode.views import (
    get_resource_size,
    get_mapkey,
    get_uid,
    check_limit_size,
    update_userStorage,
)
import json
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


class MapViewSet(DynamicModelViewSet):
    """
    API endpoint that allows maps to be viewed or edited.
    """

    http_method_names = ['get', 'patch', 'post', 'put']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        MapPermissionsFilter,
    ]
    queryset = Map.objects.all().order_by('-last_updated')
    serializer_class = MapSerializer
    pagination_class = GeoNodeApiPagination

    def list(self, request, *args, **kwargs):
        # Avoid overfetching removing mapslayer of the list.
        request.query_params.add("exclude[]", "maplayers")
        return super(MapViewSet, self).list(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Changes in the m2m `maplayers` are committed before object changes.
        To protect the db, this action is done within an atomic tansation.
        """
        return super(MapViewSet, self).update(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Changes in the m2m `maplayers` are committed before object changes.
        To protect the db, this action is done within an atomic tansation.
        """
        return super(MapViewSet, self).create(request, *args, **kwargs)

    @extend_schema(
        methods=["get"],
        responses={200: MapLayerSerializer(many=True)},
        description="API endpoint allowing to retrieve the MapLayers list.",
    )
    @action(detail=True, methods=["get"])
    def maplayers(self, request, pk=None):
        map = self.get_object()
        resources = map.maplayers
        return Response(MapLayerSerializer(embed=True, many=True).to_representation(resources))

    @extend_schema(
        methods=["get"],
        responses={200: DatasetSerializer(many=True)},
        description="API endpoint allowing to retrieve the local MapLayers.",
    )
    @action(detail=True, methods=["get"])
    def datasets(self, request, pk=None):
        map = self.get_object()
        resources = map.datasets
        return Response(DatasetSerializer(embed=True, many=True).to_representation(resources))

    def perform_create(self, serializer):
        # Thumbnail will be handled later
        post_creation_data = {"thumbnail": serializer.validated_data.pop("thumbnail_url", "")}

        # XSS basic protect and is not standard - if concern please replace this line 129 - 132. Thanks
        appName = self.request.data['title']
        if appName.find("<script>") != -1 or appName.find('javascript') != -1:
            print(appName)
            raise ValidationError("XSS Dectection")

        instance = serializer.save(
            owner=self.request.user,
            resource_type="map",
            uuid=str(uuid4()),
        )


        username = self.request.user
        uid = get_uid(username=username)
        if not self.request.user.is_staff and settings.ENABLE_CHECK_USER_STORAGE:
            is_able_upload = check_limit_size(uid, 0)
            if not is_able_upload:
                raise ValidationError("Storage usage exceed limit.")

        # events and resouce routines
        self._post_change_routines(
            instance=instance,
            create_action_perfomed=True,
            additional_data=post_creation_data,
        )

        # Handle thumbnail generation
        resource_manager.set_thumbnail(instance.uuid, instance=instance, overwrite=False)

        # Get sphere api
        keyclok_uid = get_uid(username=self.request.user)
        if keyclok_uid:
            projectName = 'MapMaker_Map_' + instance.title + '_' + str(instance.id)
            mapKey = get_mapkey(keyclok_uid,projectName,'map','',str(instance.id),projectName)
            if mapKey:
                resource_manager.set_map_key(instance.uuid, instance=instance, overwrite=False,map_key=mapKey)
        
        if settings.ENABLE_CHECK_USER_STORAGE:
            if self.request.user.is_staff:
                if uid is not None:
                    size_after_update = json.loads(get_resource_size(uid, 1))['total_size']['net']
                    update_userStorage(uid, size_after_update)
            else:
                size_after_update = json.loads(get_resource_size(uid, 1))['total_size']['net']
                update_userStorage(uid, size_after_update)

    def perform_update(self, serializer):
        # Check instance permissions with resolve_object
        mapid = serializer.instance.id
        key = "urlsuffix" if Map.objects.filter(urlsuffix=mapid).exists() else "pk"
        map_obj = resolve_object(
            self.request, Map, {key: mapid}, permission="base.change_resourcebase", permission_msg=_PERMISSION_MSG_SAVE
        )
        instance = serializer.instance
        if instance != map_obj:
            raise GeneralMapsException(detail="serializer instance and object are different")
        # Thumbnail will be handled later
        post_change_data = {
            "thumbnail": serializer.validated_data.pop("thumbnail_url", ""),
            "dataset_names_before_changes": [lyr.alternate for lyr in instance.datasets],
        }

        instance = serializer.save()

        uid = get_uid(resource_id=mapid)
        if not self.request.user.is_staff and settings.ENABLE_CHECK_USER_STORAGE:
            size_after_update = json.loads(get_resource_size(uid, 1))['total_size']['net']
            update_userStorage(uid, size_after_update)
            is_able_upload = check_limit_size(uid, 0)
            if not is_able_upload:
                raise ValidationError("Storage usage exceed limit.")

        # thumbnail, events and resouce routines
        self._post_change_routines(
            instance=instance,
            create_action_perfomed=False,
            additional_data=post_change_data,
        )

        if uid and settings.ENABLE_CHECK_USER_STORAGE:
            size_after_update = json.loads(get_resource_size(uid, 1))['total_size']['net']
            update_userStorage(uid, size_after_update)

    def _post_change_routines(self, instance: Map, create_action_perfomed: bool, additional_data: dict):
        # Step 1: Handle Maplayers signals if this is and update action
        if not create_action_perfomed:
            dataset_names_before_changes = additional_data.pop("dataset_names_before_changes", [])
            dataset_names_after_changes = [lyr.alternate for lyr in instance.datasets]
            if dataset_names_before_changes != dataset_names_after_changes:
                map_changed_signal.send_robust(sender=instance, what_changed="datasets")
        # Step 2: Register Event
        event_type = EventType.EVENT_CREATE if create_action_perfomed else EventType.EVENT_CHANGE
        register_event(self.request, event_type, instance)
        # Step 3: Resource Manager
        resource_manager.update(instance.uuid, instance=instance, notify=True)
