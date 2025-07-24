from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import stripe

from .models import Taxe, Paiement
from .forms import SignupForm

stripe.api_key = settings.STRIPE_SECRET_KEY

# Inscriptions
class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, 'taxes/signup.html', {'form': form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('taxes_list')
        return render(request, 'taxes/signup.html', {'form': form})

# Catalogue
class TaxeListView(ListView):
    model = Taxe
    template_name = 'taxes/taxes_list.html'
    context_object_name = 'taxes'

class TaxeDetailView(DetailView):
    model = Taxe
    template_name = 'taxes/tax_detail.html'
    context_object_name = 'taxe'

# Panier (simulé avec session)
class PanierView(LoginRequiredMixin, View):
    def get(self, request):
        panier = request.session.get('panier', [])
        taxes = Taxe.objects.filter(id__in=panier)
        total = sum(t.montant for t in taxes)
        return render(request, 'taxes/panier.html', {'taxes': taxes, 'total': total})

    def post(self, request):
        taxe_id = int(request.POST.get('taxe_id'))
        panier = request.session.get('panier', [])
        if taxe_id not in panier:
            panier.append(taxe_id)
        request.session['panier'] = panier
        return redirect('panier')

# Paiement Stripe
class PayerView(LoginRequiredMixin, View):
    def post(self, request):
        panier = request.session.get('panier', [])
        taxes = Taxe.objects.filter(id__in=panier)
        total = sum(t.montant for t in taxes)

        line_items = [{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': taxe.nom},
                'unit_amount': int(taxe.montant * 100),
            },
            'quantity': 1,
        } for taxe in taxes]

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/mes-paiements/'),
            cancel_url=request.build_absolute_uri('/panier/'),
            metadata={'user_id': request.user.id, 'taxe_ids': ','.join(map(str, panier))}
        )

        return redirect(session.url, code=303)

# Webhook Stripe
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        taxe_ids = list(map(int, session['metadata']['taxe_ids'].split(',')))
        taxes = Taxe.objects.filter(id__in=taxe_ids)
        montant_total = sum(t.montant for t in taxes)

        paiement = Paiement.objects.create(
            user_id=user_id,
            montant_total=montant_total,
            stripe_checkout_id=session['id']
        )
        paiement.taxes.set(taxes)

    return HttpResponse(status=200)

# Historique
class MesPaiementsView(LoginRequiredMixin, View):
    def get(self, request):
        paiements = Paiement.objects.filter(user=request.user).order_by('-date')
        return render(request, 'taxes/mes_paiements.html', {'paiements': paiements})
