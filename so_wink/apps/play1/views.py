# Create your views here.
# from django import http
import jingo


def index(request):
#     return HttpResponse("DjangoPlay!")
    data = {}  # You'd add data here that you're sending to the template.
    return jingo.render(request, 'play1/home.html', data)
