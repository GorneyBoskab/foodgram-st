from django.http import JsonResponse

def custom_404(request, exception=None):
    return JsonResponse({'errors': 'Страница не найдена.'}, status=404)
