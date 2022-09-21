#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template.defaultfilters import slugify
from django.shortcuts import redirect

from geonode.security.permissions import DEFAULT_PERMS_SPEC

from .forms import NewDatasetForm
from .utils import create_dataset

from geonode.views import (
    get_resource_size,
    get_uid,
    check_limit_size,
    update_userStorage,
)

@login_required
def dataset_create(request, template='createlayer/dataset_create.html'):
    """
    Create an empty layer.
    """
    error = None
    if request.method == 'POST':
        form = NewDatasetForm(request.POST)
        if form.is_valid():
            if not request.user.is_staff:
                username = request.user
                uid = get_uid(username=username)
                is_able_upload = check_limit_size(uid,0)
            else:
                is_able_upload = True
            if not is_able_upload:
            #raise ValidationError("Storage usage exceed limit.")
                error = 'Storage usage exceed limit.'
            else:
                try:
                    name = form.cleaned_data['name']
                    name = slugify(name.replace(".", "_"))
                    title = form.cleaned_data['title']
                    geometry_type = form.cleaned_data['geometry_type']
                    attributes = form.cleaned_data['attributes']
                    permissions = DEFAULT_PERMS_SPEC
                    layer = create_dataset(name, title, request.user.username, geometry_type, attributes)
                    layer.set_permissions(json.loads(permissions), created=True)

                    if not request.user.is_staff:
                        size_after_update = json.loads(get_resource_size(uid, 1))['total_size']['net']
                        update_userStorage(uid, size_after_update)

                    return redirect(layer)
                except Exception as e:
                    error = f'{e} ({type(e)})'
    else:
        form = NewDatasetForm()

    ctx = {
        'form': form,
        'is_dataset': True,
        'error': error,
    }

    return render(request, template, context=ctx)
