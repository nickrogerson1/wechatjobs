from django.shortcuts import render
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

import json
import os
import stripe
from django.utils import timezone
from .models import PromotedJob, Job


STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET') 
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')



def create_stripe_checkout_session(user, job):

    print(f'JOB PK: {job}')

    currency = 'CNY'

    if currency == 'USD':
        price = 'price_1Q8SkfIeqTJllgu5CK5tAnId' #live
        payment_method_types = ['card']
        payment_method_options= {}
    else:
    # It's RMB
        price = 'price_1Q8SiWIeqTJllgu5OjYal3xw' #live
        payment_method_types=['alipay', 'wechat_pay']
        payment_method_options={
                'wechat_pay': {
                'client': 'web'
                },
            }

    print('Point 1')
        
    
    checkout_session = stripe.checkout.Session.create(
        payment_method_types = payment_method_types,
        payment_method_options =  payment_method_options,

        line_items=[
            {
                'price': price,
                'quantity': 1,
            },
        ],
        metadata = {
            'job_pk' : job,
        },
        mode="payment",
        success_url='https://wechatjobs.com/payment-successful?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='https://wechatjobs.com/payment-cancelled/',
    )

    print('Point 2')

    return checkout_session.url




@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """
    Stripe webhook view to handle checkout session completed event.
    """

    def post(self, request, format=None):
        payload = request.body
        endpoint_secret = STRIPE_WEBHOOK_SECRET
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        event = None

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            print(e)
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            print(e)
            # Invalid signature
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            print("Payment successful")

            payload_decoded = payload.decode().replace("'", '"')
            data = json.loads(payload_decoded)
            print(json.dumps(data, sort_keys=True, indent=2))

            job_pk = data['data']['object']['metadata']['job_pk']

        # Try and find a PromotedJob owned by this job to update
        # Otherwise make a new one
            try:
                job = PromotedJob.objects.get(job__pk=job_pk)
                job.expiry_date = timezone.now() + timezone.timedelta(days=7)
                job.times_promoted = job.times_promoted + 1
                job.time_updated = timezone.now()
                job.save()
                # Update the parent
                job.job.time_updated = timezone.now()
                job.job.save()
            except PromotedJob.DoesNotExist:
                try:
                    job = Job.objects.get(pk=job_pk)
                
                    PromotedJob.objects.create(
                        expiry_date = timezone.now() + timezone.timedelta(days=7),
                        amount = 300.00,
                        job = job
                    )
                
                # Update the job
                    job.job.time_updated = timezone.now()
                    job.save()

                except Job.DoesNotExist:
                    print('Job doesnt exist')

        return HttpResponse(status=200)
   
   

class SuccessfulPaymentView(View):

    def get(self, request):

        session = stripe.checkout.Session.retrieve(request.GET.get('session_id'))
        job_pk = session['metadata']['job_pk']

        return render(request, 'jobsboard/stripe/success.html', {'job_pk': job_pk})