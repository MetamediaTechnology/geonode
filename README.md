![GeoNode](https://raw.githubusercontent.com/GeoNode/documentation/master/about/img/geonode-logo_for_readme.gif "GeoNode")
![OSGeo Project](https://www.osgeo.cn/qgis/_static/images/osgeoproject.png)

Table of Contents
=================

- [Table of Contents](#table-of-contents)
  - [What is GeoNode?](#what-is-geonode)
  - [Try out GeoNode](#try-out-geonode)
  - [Install](#install)
  - [Learn GeoNode](#learn-geonode)
  - [Development](#development)
  - [Contributing](#contributing)
  - [Roadmap](#roadmap)
  - [Showcase](#showcase)
  - [Most useful links](#most-useful-links)
  - [Licensing](#licensing)

What is GeoNode?
----------------

GeoNode is a geospatial content management system, a platform for the
management and publication of geospatial data. It brings together mature
and stable open-source software projects under a consistent and
easy-to-use interface allowing non-specialized users to share data and
create interactive maps.

Data management tools built into GeoNode allow for integrated creation
of data, metadata, and map visualization. Each dataset in the system can
be shared publicly or restricted to allow access to only specific users.
Social features like user profiles and commenting and rating systems
allow for the development of communities around each platform to
facilitate the use, management, and quality control of the data the
GeoNode instance contains.

It is also designed to be a flexible platform that software developers
can extend, modify or integrate against to meet requirements in their
own applications.

Try out GeoNode
---------------

If you just want to try out GeoNode visit our official Demo online at:
http://master.demo.geonode.org. After your registration you will be able
to test all basic functionalities like uploading layers, creation of
maps, editing metadata, styles and much more. To get an overview what
GeoNode can do we recommend to have a look at the [Users
Workshop](https://docs.geonode.org/en/master/usage/index.html).

Install
-------

    The latest official release is 4.0.0!

GeoNode can be setup in different ways, flavors and plattforms. If
you´re planning to do development or install for production please visit
the offical GeoNode installation documentation:

- [Docker](https://docs.geonode.org/en/master/install/advanced/core/index.html#docker)
- [Ubuntu 20.04 LTS](https://docs.geonode.org/en/master/install/advanced/core/index.html#ubuntu-20-04lts)

Learn GeoNode
-------------

After you´ve finished the setup process make yourself familiar with the
general usage and settings of your GeoNodes instance. - the [User
Training](https://docs.geonode.org/en/master/usage/index.html)
is going in depth into what we can do. - the [Administrators
Workshop](https://docs.geonode.org/en/master/admin/index.html)
will guide you to the most important parts regarding management commands
and configuration settings.

Development
-----------

GeoNode is a web based GIS tool, and as such, in order to do development
on GeoNode itself or to integrate it into your own application, you
should be familiar with basic web development concepts as well as with
general GIS concepts.

For development GeoNode can be run in a 'development environment'. In
contrast to a 'production environment' development differs as it uses
lightweight components to speed up things.

To get you started have a look at the [Install
instructions](#install) which cover all what is needed to run GeoNode
for development. Further visit the the [Developer
workshop](https://docs.geonode.org/en/master/devel/index.html)
for a basic overview.

If you're planning of customizing your GeoNode instance, or to extend
it's functionalities it's not advisable to change core files in any
case. In this case it's common to use setup a [GeoNode Project
Template](https://github.com/GeoNode/geonode-project).

Contributing
------------

GeoNode is an open source project and contributors are needed to keep
this project moving forward. Learn more on how to contribute on our
[Community
Bylaws](https://github.com/GeoNode/geonode/wiki/Community-Bylaws).

Roadmap
-------

GeoNode's development roadmap is documented in a series of GeoNode
Improvement Projects (GNIPS). They are documented at [GeoNode Wiki](https://github.com/GeoNode/geonode/wiki/GeoNode-Improvement-Proposals).

GNIPS are considered to be large undertakings which will add a large
amount of features to the project. As such they are the topic of
community dicussion and guidance. The community discusses these on the
developer mailing list: http://lists.osgeo.org/pipermail/geonode-devel/

Showcase
--------

A handful of other Open Source projects extend GeoNode’s functionality
by tapping into the re-usability of Django applications. Visit our
gallery to see how the community uses GeoNode: [GeoNode
Showcase](https://geonode.org/gallery/).

The development community is very supportive of new projects and
contributes ideas and guidance for newcomers.

Most useful links
-----------------


**General**

- Project homepage: https://geonode.org
- Repository: https://github.com/GeoNode/geonode
- Offical Demo: http://master.demo.geonode.org
- GeoNode Wiki: https://github.com/GeoNode/geonode/wiki
- Issue tracker: https://github.com/GeoNode/geonode-project/issues

    In case of sensitive bugs like security vulnerabilities, please
    contact a GeoNode Core Developer directly instead of using issue
    tracker. We value your effort to improve the security and privacy of
    this project!

**Related projects**

- GeoNode Project: https://github.com/GeoNode/geonode-project
- GeoNode at Docker: https://hub.docker.com/u/geonode
- GeoNode OSGeo-Live: https://live.osgeo.org/en/


**Support**

- User Mailing List: https://lists.osgeo.org/cgi-bin/mailman/listinfo/geonode-users
- Developer Mailing List: https://lists.osgeo.org/cgi-bin/mailman/listinfo/geonode-devel
- Gitter Chat: https://gitter.im/GeoNode/general


**How to develop geonode and mapstore client**

1. Clone geonode project


|git clone https://github.com/MetamediaTechnology/geonode.git|
| :- |

1. ใช้โปรแกรม Vscode  เปิด โฟล์เดอร์โปรเจค Geonode และ เปิด Terminal (MacOS) เมื่ออยู่ใน Root folder ให้ทำการ Clone geonode-mapstore-client ลงมา (หรือสามารถเลือก path ตามสะดวกได้ และจะต้องเปลี่ยน path ใน docker-compose.yml ในขั้นตอนล่าง)


|git clone https://github.com/MetamediaTechnology/geonode-mapstore-client.git|
| :- |

\*\* สามารถเลือกใช้ geonode-mapstore-client repo ได้ตามแต่ละโปรเจค 

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.001.png)

จะได้โฟล์เดอร์ **geonode-mapstore-client**

1. แก้ไขไฟล์ docker-compose.yml  ใน .devcontainer

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.002.png)

1. ทำการเพิ่ม volumes path ในบรรทัดที่ 33-34 


|- './geonode-mapstore-client:/usr/src/django-geonode-mapstore-client'|
| :- |

\*\* การเพิ่มไปยังบรรทัดนี้เพื่อให้บอกให้ Docker copy ไฟล์ทั้งหมดใน geonode-mapstore-client ไปยัง Docker container ชื่อ django4geonode 

Example

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.003.png)

1. ทำการ  package : geonode-mapstore-client.git ใน  ลบ requirement.txt เพื่อไม่ให้ geonode ติดตั้งเข้าไป

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.004.png)

1. กลับมายัง Root folder geonode ใช้คำสั่ง build  image 


|docker-compose --project-name [ชื่อ Container] -f docker-compose.yml -f .devcontainer/docker-compose.yml build|
| :- |

\*\* ในขั้นตอนนี้ใช้เวลาประมาณ 10 - 30 นาทีขึ้นอยู่กับความเร็ว Network และ Computer 

1. ทำการ Run container และ Service ที่เกี่ยวข้องโดยใช้คำสั่ง


|docker-compose --project-name  [ชื่อ Container] -f docker-compose.yml -f .devcontainer/docker-compose.yml up -d|
| :- |

\*\* จนกว่าจะ pull image และ Create เสร็จและ Service start ทุกตัว

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.005.png)



1. ทำการ Shell เข้าไปยัง Container ชื่อว่า django4geonode \* ชื่ออาจจะแตกต่างกันออกไปให้สังเกตุนำหน้าว่า django4xxxx เพื่อเข้าไปลบ geonode-mapstore-client เดิมที่แอบมากับการติดตั้งครั้งแรก และ ใช้ตัวที่เป็นของเราเอง


|ls|
| :- |

หรือสามารถเปิดด้วย Docker UI 

1. ทำการตรวจสอบว่ามีโฟล์เดอร์ django-geonode-mapstore-client ที่ตั้งไว้ให้ docker ![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.006.png)copy เข้าไปยัง path /usr/src หรือไม่ โดยใช้คำสั่ง ls


|<p>cd /usr/src                 </p><p>ls</p>|
| :- |

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.007.png)

1. ` `ลบ geonode-mapstore-client ที่อยู่ใน python package ออก โดยใช้คำสั่ง


|pip uninstall django\_geonode\_mapstore\_client|
| :- |

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.008.png)

**\* ตัวอย่าง output เมื่อทำการลบสำเร็จ**








1. จากนั้นเข้าไปยังโฟล์เดอร์ django-geonode-mapstore-client โดยใช้คำสั่ง cd


|cd django-geonode-mapstore-client|
| :- |

**\*\* ใช้คำสั่ง ls เพื่อตรวจสอบความถูกต้อง**

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.009.png)



1. ติดตั้ง package โดยให้ python เรียกใช้ package ในโฟล์เดอร์นี้


|pip install -e .|
| :- |

ตัวอย่าง Output

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.010.png)

1. เมื่อเสร็จขั้นตอน 12 สามารถ Exit เพื่อปิด Docker shell ได้เลย


|exit|
| :- |

1. เมื่อกลับมายังโฟล์เดอร์ mapstore-client ในเครื่อง local จะพบว่ามีโฟล์เดอร์ที่เพิ่มเข้ามาคือ django\_geonode\_mapstore\_client.egg-info![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.011.png)


1. ในเครื่อง Local นี้สามารถติดตั้ง npm install เพื่อติดตั้ง Dependencies ที่จำเป็นสำหรับการ Start mapstore-client ในรูปแบบ React run ได้ตามปกติ

1. ` `ทำการ Run geonode mode dev อีกครั้งโดย กลับมายัง root folder geonode ใช้คำสั่ง


|docker exec -it [project-name] bash -c "python manage.py runserver 0.0.0.0:8000"|
| :- |

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.012.png)



1. ทดลองเข้าผ่าน Browser <http://localhost:8000>

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.013.png)

\*\* หากไม่มีอะไรผิดพลาด

1. ทำการ Run : geonode mapstore client  (Mode dev)  โดยเข้าไปที่ **path** geonode-mapstore-client/geonode\_mapstore\_client/client


1. ติดตั้ง node package


|npm install|
| :- |

1. สร้างไฟล์ .env และ เพิ่มข้อมูลดังนี้


|<p></p><p>DEV\_SERVER\_PROTOCOL=http</p><p>DEV\_SERVER\_HOSTNAME=localhost</p><p>DEV\_TARGET\_GEONODE\_HOST=localhost:8000</p><p></p>|
| :- |
\*\* 8000 คือ port ของ geonode ที่ run mode dev


1. กรณีฟ้องไม่พบ Mapstore2

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.014.png)

ให้ใช้คำสั่ง

|<p>git submodule init</p><p>git submodule update </p>|
| :- |

และใช้ npm install อีกครั้ง

\*\*\*\* หากไม่มีอะไรเกิดขึ้น ให้ทำการ clone repo mapstore2 ลงมาเองในโฟล์เดอร์ client


|git clone <https://github.com/geosolutions-it/MapStore2.git> -b 2022.01.xx|
| :- |

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.015.png)

และใช้ npm install อีกครั้ง

หากไม่มีอะไรผิดพลาด สามารถใช้คำสั่ง npm start ได้เลย 












1. ทดลองเปิด <http://localhost:8081>

![](Aspose.Words.aa982a3c-8675-4dab-84ef-f7e9f082574c.016.png)

Thank you



Licensing
---------

GeoNode is Copyright 2018 Open Source Geospatial Foundation (OSGeo).

GeoNode is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version. GeoNode is distributed in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with GeoNode. If not, see http://www.gnu.org/licenses.


