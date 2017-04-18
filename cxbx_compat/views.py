import zipfile

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.template import loader
from django.utils.encoding import force_text

from xdb.utils.cxbx import XboxTitleLog
from xdb.utils.xbe import Xbe
from cxbx_compat.models import Title, Game, Executable, XDKLibrary
from django.contrib.admin.models import LogEntry, ADDITION


# Create your views here.
@login_required(login_url="login/")
def home(request):
    return render(request, "home.html")


@login_required(login_url="login/")
def upload(request):

    success = None

    if request.method == 'POST' and 'file' in request.FILES:

        if request.FILES['file'].content_type == 'text/plain':
            if process_xbe_info(
                    request.FILES.xbe_info_file.read().decode(errors='ignore'),
                    request.FILES['file'].name,
                    request.user.pk):
                success = 'Successfully processed 1 file.'
            else:
                success = 'Nothing new.'

        elif zipfile.is_zipfile(request.FILES['file']):
            return StreamingHttpResponse(process_zip(request.FILES['file'], process_xbe_info, request))
        elif Xbe.is_xbe(request.FILES['file']):
            xbe = Xbe(xbe_file=request.FILES['file'])

            if process_xbe_info(
                    xbe.get_dump(),
                    request.FILES['file'].name,
                    request.user.pk):
                success = 'Successfully processed 1 file.'
            else:
                success = 'Nothing new.'

    return render(request, "home.html", {'upload_success': success})


def process_zip(zfile, handler, request):
    zip_f = zipfile.ZipFile(zfile)
    yield '<!-- \r\n'
    total = len(zip_f.infolist())
    successful = 0
    for zipinfo in zip_f.infolist():
        status_message = ''
        file_in_zip = zip_f.open(zipinfo)
        if handler(
                file_in_zip.read().decode(errors='ignore'),
                file_in_zip.name,
                request.user.pk):
            successful += 1
            status_message = 'Success'
        else:
            status_message = 'Fail'

        yield '{0} - {1}\r\n'.format(status_message, str(zipinfo))

    yield ' -->'

    success = 'Successfully processed {0}/{1}'.format(successful, total)

    tpl = loader.get_template("home.html")

    yield tpl.render({'upload_success': success}, request)


def process_xbe_info(xbe_info_file_data, xbe_info_file_name, user_pk):
    ret = False

    xlog = XboxTitleLog.parse_xbe_info(xbe_info_file_data)

    if xlog['title_id']:
        log_msg = 'Created from file upload ({0})'.format(xbe_info_file_name)

        title = None

        if Title.objects.filter(title_id=xlog['title_id']).exists():
            title = Title.objects.get(title_id=xlog['title_id'])
        else:
            game, created = Game.objects.get_or_create(name=xlog['title_name'])
            if created:
                log_action(game, user_pk, log_msg)

            title, created = Title.objects.get_or_create(title_id=xlog['title_id'], game=game)
            if created:
                log_action(title, user_pk, log_msg)

        try:
            executable, created = Executable.objects.get_or_create(
                signature=xlog['signature'],
                defaults={
                    'disk_path': xlog['disk_path'],
                    'file_name': xlog['file_name'],
                    'title': title,
                    'xbe_info': xlog['contents']
                },

            )

            if created:
                log_action(executable, user_pk, log_msg)

                for lib in xlog['libs']:
                    xdk_lib, lib_created = XDKLibrary.objects.get_or_create(
                        xdk_version=int(lib['ver']),
                        qfe_version=int(lib['QFE']),
                        name=lib['name']
                    )

                    if lib_created:
                        log_action(xdk_lib, user_pk, log_msg)

                    executable.xdk_libraries.add(xdk_lib)
                    executable.xbe_info = xlog['contents']
                executable.save()

            elif not executable.xbe_info:
                executable.xbe_info = xlog['contents']
                executable.save()
                print('Updated {0}'.format(executable))

            ret = created

        except IntegrityError as ex:
            print('Error importing {0}'.format(xbe_info_file_name))
            pass
    return ret


def log_action(obj, user_pk, message=None):
    LogEntry.objects.log_action(
        user_id=user_pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=force_text(obj),
        action_flag=ADDITION,
        change_message=message
    )
