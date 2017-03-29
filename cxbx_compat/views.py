import zipfile

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from xdb.utils.cxbx import XboxTitleLog
from cxbx_compat.models import Title, Game, Executable


# Create your views here.
@login_required(login_url="login/")
def home(request):
    return render(request, "home.html")


@login_required(login_url="login/")
def upload(request):

    success = None

    if request.method == 'POST' and 'file' in request.FILES:

        if request.FILES['file'].content_type == 'text/plain':
            if process_xbe_info(request.FILES['file']):
                success = 'Successfully processed 1 file.'
            else:
                success = 'Nothing new.'

        elif zipfile.is_zipfile(request.FILES['file']):
            zip_f = zipfile.ZipFile(request.FILES['file'])
            total = len(zip_f.infolist())
            successful = 0
            for zipinfo in zip_f.infolist():
                if process_xbe_info(zip_f.open(zipinfo)):
                    successful += 1

            success = 'Successfully processed {0}/{1}'.format(successful, total)

    return render(request, "home.html", {'upload_success': success})


def process_xbe_info(xbe_info_file):
    ret = False

    xlog = XboxTitleLog.parse_xbe_info(xbe_info_file)

    if xlog['title_id']:
        game, created = Game.objects.get_or_create(name=xlog['title_name'])
        title, created = Title.objects.get_or_create(title_id=xlog['title_id'], game=game)

        executable, created = Executable.objects.get_or_create(
            signature=xlog['signature'],
            disk_path=xlog['disk_path'],
            file_name=xlog['file_name'],
            title=title
        )

        executable.save()
        ret = created

    return ret
