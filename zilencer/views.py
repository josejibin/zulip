from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from zerver.models import get_realm
from zerver.lib.actions import internal_send_message
from zerver.decorator import has_request_variables, REQ, json_to_dict
from zilencer.models import Deployment

from zerver.lib.rest import rest_dispatch as _rest_dispatch
rest_dispatch = csrf_exempt((lambda request, *args, **kwargs: _rest_dispatch(request, globals(), *args, **kwargs)))


def get_ticket_number():
    fn = '/var/tmp/.feedback-bot-ticket-number'
    try:
        ticket_number = int(open(fn).read()) + 1
    except:
        ticket_number = 1
    open(fn, 'w').write('%d' % ticket_number)
    return ticket_number

@has_request_variables
def submit_feedback(request, deployment, message=REQ(converter=json_to_dict)):
    domainish = message["sender_domain"]
    if get_realm("zulip.com") not in deployment.realms.all():
        domainish += " via " + deployment.realms.get(0).domain
    subject = "feedback: %s (%s)" % (message["sender_email"], domainish)

    if len(subject) > 60:
        subject = subject[:57].rstrip() + "..."


    ticket_number = get_ticket_number()
    content = '@support, Please ack this new request.'
    content += '\n~~~'
    content += '\nticket Z%03d' % (ticket_number,)
    content += '\nsender: %s' % (message['sender_full_name'],)
    content += '\nemail: %s' % (message['sender_email'],)
    if 'sender_domain' in message:
        content += '\nrealm: %s' % (message['sender_domain'],)
    content += '\n~~~'

    content += '\n\n'
    content += message['content']

    internal_send_message("feedback@zulip.com", "stream", "support", subject, content)

    return HttpResponse(message['sender_email'])
