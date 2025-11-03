import time
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse


class IdleLogoutMiddleware:
    """
    Desloga usuários autenticados após um período de inatividade.

    - Armazena a última atividade em `request.session['last_activity']` (epoch seconds)
    - Se o período desde a última atividade exceder `INACTIVITY_TIMEOUT_SECONDS`, faz logout
      e redireciona para a página de login com mensagem.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pular checagem para rotas estáticas
        path = request.path or ''
        if path.startswith('/static/'):
            return self.get_response(request)

        timeout = getattr(settings, 'INACTIVITY_TIMEOUT_SECONDS', 600)
        now = int(time.time())

        if hasattr(request, 'user') and request.user.is_authenticated:
            last = request.session.get('last_activity', now)
            # Se excedeu o tempo de inatividade, faz logout e redireciona
            if isinstance(last, int) and now - last > int(timeout):
                logout(request)
                messages.info(request, 'Você foi desconectado por inatividade.')
                login_url = reverse('login')
                # mantém o destino original para após novo login
                next_target = path or '/'
                return redirect(f"{login_url}?next={next_target}")

            # Atualiza última atividade
            request.session['last_activity'] = now

        return self.get_response(request)