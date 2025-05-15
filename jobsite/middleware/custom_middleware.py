from django.utils.deprecation import MiddlewareMixin

from django_user_agents.utils import get_user_agent
from ipware import get_client_ip
import socket
import posthog


class InterceptRequestMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # print('Middleware fired!')
        # self.identify_user(request)
        pass

        # posthog.capture('user', '$pageview')


    
    def identify_user(self, request):
        print('**********************')
        print(request.build_absolute_uri())
        print('Running checks...')
        print('**********************')
        
        user_agent = get_user_agent(request)
        print(f'UA: {user_agent}')
        if user_agent.is_bot:
            print('This is a bot and has no UA')
        ip, _ = get_client_ip(request)
        print(f'IP: {ip}')

        try:
            host = socket.gethostbyaddr(ip)[0]
            domain_name = ".".join(host.split('.')[1:])
            host_ip = socket.gethostbyname(host)
            print(f'Host: {host}')
            print(f'Domain Name: {domain_name}')
            print(f'Host IP: {host_ip}')
        except (socket.herror, socket.error):
            print('No host found')
            return False

